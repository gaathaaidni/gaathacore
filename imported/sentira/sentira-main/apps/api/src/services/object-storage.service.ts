import { Injectable } from '@nestjs/common';
import { createHash, createHmac } from 'crypto';

export interface StoredObject { key: string; sha256: string; byteSize: number; contentType: string; }

/** Minimal S3-compatible client; credentials are kept solely on the API process. */
@Injectable()
export class ObjectStorageService {
  private readonly endpoint = process.env.MINIO_ENDPOINT; private readonly port = process.env.MINIO_PORT ?? '9000';
  private readonly accessKey = process.env.MINIO_ACCESS_KEY; private readonly secretKey = process.env.MINIO_SECRET_KEY; private readonly bucket = process.env.MINIO_BUCKET ?? 'sentira-evidence';
  private bucketReady = false;
  configured(): boolean { return Boolean(this.endpoint && this.accessKey && this.secretKey); }
  assertTenantScopedKey(organizationId: string, key: string): string {
    if (!organizationId || !key || typeof key !== 'string') {
      throw new Error('tenant-scoped object key is required');
    }
    const normalized = key.replace(/^\/+/, '').replace(/\\/g, '/');
    const segments = normalized.split('/').filter(Boolean);
    if (segments.length < 3 || segments[0] !== 'organizations' || segments[1] !== organizationId || segments.some((segment) => segment === '.' || segment === '..')) {
      throw new Error('tenant-scoped object key required');
    }
    return normalized;
  }
  async put(key: string, bytes: Buffer, contentType: string, metadata: Record<string, string> = {}): Promise<StoredObject> {
    if (!this.configured()) throw new Error('MinIO is not configured');
    await this.ensureBucket();
    const url = this.objectUrl(key); const sha256 = createHash('sha256').update(bytes).digest('hex');
    await this.request('PUT', url, bytes, { 'content-type': contentType, 'content-length': String(bytes.length), 'x-amz-content-sha256': sha256, ...Object.fromEntries(Object.entries(metadata).map(([name, value]) => [`x-amz-meta-${name}`, value])) });
    return { key, sha256, byteSize: bytes.length, contentType };
  }
  async get(key: string): Promise<Buffer> { if (!this.configured()) throw new Error('MinIO is not configured'); const response = await this.request('GET', this.objectUrl(key)); return Buffer.from(await response.arrayBuffer()); }
  async getForOrganization(organizationId: string, key: string): Promise<Buffer> {
    const tenantKey = this.assertTenantScopedKey(organizationId, key);
    return this.get(tenantKey);
  }
  async exists(key: string): Promise<boolean> {
    if (!this.configured()) throw new Error('MinIO is not configured');
    const response = await this.request('HEAD', this.objectUrl(key), undefined, {}, [200, 404]);
    return response.status === 200;
  }
  async existsForOrganization(organizationId: string, key: string): Promise<boolean> {
    const tenantKey = this.assertTenantScopedKey(organizationId, key);
    return this.exists(tenantKey);
  }
  async delete(key: string): Promise<void> {
    if (!this.configured()) throw new Error('MinIO is not configured');
    await this.request('DELETE', this.objectUrl(key), undefined, {}, [204, 404]);
  }
  async deleteForOrganization(organizationId: string, key: string): Promise<void> {
    const tenantKey = this.assertTenantScopedKey(organizationId, key);
    await this.delete(tenantKey);
  }
  private async ensureBucket(): Promise<void> {
    if (this.bucketReady) return;
    const bucketUrl = this.url(`/${encodeURIComponent(this.bucket)}`);
    const found = await this.request('HEAD', bucketUrl, undefined, {}, [200, 404]);
    if (found.status === 404) await this.request('PUT', bucketUrl, Buffer.alloc(0), {}, [200]);
    this.bucketReady = true;
  }
  private objectUrl(key: string): URL {
    // Encode every path component: evidence identifiers are opaque and must not
    // be able to alter the tenant-scoped S3 key through a slash or query string.
    return this.url(`/${encodeURIComponent(this.bucket)}/${key.split('/').map(encodeURIComponent).join('/')}`);
  }
  private url(path: string): URL { return new URL(`http://${this.endpoint}:${this.port}${path}`); }
  private async request(method: string, url: URL, body?: Buffer, headers: Record<string, string> = {}, allowedStatuses: number[] = [200]): Promise<Response> {
    const now = new Date(); const amzDate = now.toISOString().replace(/[-:]|\.\d{3}/g, ''); const date = amzDate.slice(0, 8); const host = url.host;
    const signedHeaders = ['host', 'x-amz-content-sha256', 'x-amz-date'].concat(Object.keys(headers).map((header) => header.toLowerCase()).filter((header, index, all) => !['host', 'x-amz-content-sha256', 'x-amz-date'].includes(header) && all.indexOf(header) === index)).sort();
    const values: Record<string, string> = { host, 'x-amz-date': amzDate, 'x-amz-content-sha256': headers['x-amz-content-sha256'] ?? createHash('sha256').update(body ?? '').digest('hex'), ...Object.fromEntries(Object.entries(headers).map(([key, value]) => [key.toLowerCase(), value])) };
    const canonicalHeaders = signedHeaders.map((header) => `${header}:${values[header].trim()}\n`).join(''); const payloadHash = values['x-amz-content-sha256']; const canonical = [method, url.pathname, '', canonicalHeaders, signedHeaders.join(';'), payloadHash].join('\n'); const scope = `${date}/us-east-1/s3/aws4_request`;
    const signingKey = this.sign(this.sign(this.sign(this.sign(Buffer.from(`AWS4${this.secretKey}`), date), 'us-east-1'), 's3'), 'aws4_request'); const signature = createHmac('sha256', signingKey).update(`AWS4-HMAC-SHA256\n${amzDate}\n${scope}\n${createHash('sha256').update(canonical).digest('hex')}`).digest('hex');
    const response = await fetch(url, { method, body: body ? new Uint8Array(body) : undefined, headers: { ...headers, Host: host, 'x-amz-date': amzDate, 'x-amz-content-sha256': payloadHash, Authorization: `AWS4-HMAC-SHA256 Credential=${this.accessKey}/${scope}, SignedHeaders=${signedHeaders.join(';')}, Signature=${signature}` } });
    if (!allowedStatuses.includes(response.status)) throw new Error(`MinIO ${method} failed with ${response.status}`); return response;
  }
  private sign(key: Buffer, value: string): Buffer { return createHmac('sha256', key).update(value).digest(); }
}

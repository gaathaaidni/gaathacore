import { Injectable } from '@nestjs/common';
import { lookup } from 'dns/promises';
import { Socket } from 'net';
import { CctvConnector, ConnectionVerificationResult } from './cctv-connector';

@Injectable()
export class GenericRtspConnector implements CctvConnector {
  getId() { return 'generic-rtsp'; }
  getName() { return 'Generic RTSP'; }
  supports(deviceType: string) { return ['WIFI_CAMERA', 'IP_CAMERA', 'DVR', 'NVR', 'CAMERA_SYSTEM', 'OTHER'].includes(deviceType); }
  supportsProtocol(protocol: string) { return protocol.toLowerCase() === 'rtsp'; }

  async testStream(input: { streamUrl: string; username?: string; password?: string; timeoutMs: number }): Promise<ConnectionVerificationResult> {
    const started = Date.now();
    let url: URL;
    try { url = new URL(input.streamUrl); } catch { return this.failure('INVALID_RTSP_URL', false, 'The camera address is not valid.', started); }
    if (url.protocol !== 'rtsp:' || url.username || url.password) return this.failure('INVALID_RTSP_URL', false, 'Use an RTSP address without embedded credentials.', started);
    const port = Number(url.port || 554);
    if (!Number.isInteger(port) || port < 1 || port > 65535) return this.failure('INVALID_RTSP_URL', false, 'The camera port is not valid.', started);
    try {
      const addresses = await lookup(url.hostname, { all: true, verbatim: true });
      if (addresses.length === 0 || addresses.some(({ address }) => this.isUnsafeAddress(address))) return this.failure('DEVICE_UNREACHABLE', true, 'This camera must be reached through a Sentira Connector.', started);
      const response = await this.options(addresses[0].address, port, url, input.timeoutMs, input.username || '', input.password || '');
      if (response === 401 || response === 403) return this.failure('AUTHENTICATION_FAILED', true, 'The camera rejected the supplied credentials.', started);
      if (response < 200 || response >= 300) return this.failure('STREAM_UNAVAILABLE', true, 'The device responded but did not provide the requested stream.', started);
      return { status: 'VERIFIED_CONNECTED', protocol: 'RTSP', retryable: true, supportRecommended: false, message: 'The camera accepted an RTSP connection.', durationMs: Date.now() - started };
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      return this.failure(code === 'ETIMEDOUT' ? 'CONNECTION_TIMEOUT' : 'DEVICE_UNREACHABLE', true, 'Sentira could not reach this camera.', started);
    }
  }

  private options(address: string, port: number, url: URL, timeoutMs: number, username = '', password = ''): Promise<number> {
    return new Promise((resolve, reject) => {
      const socket = new Socket();
      let data = '';
      const timer = setTimeout(() => { socket.destroy(); const error = new Error('Connection timeout') as NodeJS.ErrnoException; error.code = 'ETIMEDOUT'; reject(error); }, timeoutMs);
      const finish = (error?: Error) => { clearTimeout(timer); socket.destroy(); error ? reject(error) : resolve(Number(data.match(/^RTSP\/\d\.\d\s+(\d+)/m)?.[1] || 500)); };
      socket.setTimeout(timeoutMs);
      socket.once('error', (error) => finish(error));
      socket.once('timeout', () => { const error = new Error('Connection timeout') as NodeJS.ErrnoException; error.code = 'ETIMEDOUT'; finish(error); });
      socket.on('data', (chunk) => { data += chunk.toString('utf8'); if (data.includes('\r\n\r\n')) finish(); });
      const headers = [
        'CSeq: 1',
        'User-Agent: Sentira',
      ];
      if (username) {
        headers.push(`Authorization: Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`);
      }
      const request = `OPTIONS rtsp://${url.host}${url.pathname} RTSP/1.0\r\n${headers.join('\r\n')}\r\n\r\n`;
      socket.connect(port, address, () => socket.write(request));
    });
  }

  private failure(failureCode: ConnectionVerificationResult['failureCode'], retryable: boolean, message: string, started: number): ConnectionVerificationResult {
    return { status: 'FAILED', failureCode, retryable, supportRecommended: !retryable, protocol: 'RTSP', message, durationMs: Date.now() - started };
  }

  private isUnsafeAddress(address: string) {
    const host = address.toLowerCase();
    if (host === '::1' || host.startsWith('127.') || host.startsWith('10.') || host.startsWith('169.254.') || host.startsWith('192.168.')) return true;
    const parts = host.split('.').map(Number);
    return parts.length === 4 && parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31;
  }
}

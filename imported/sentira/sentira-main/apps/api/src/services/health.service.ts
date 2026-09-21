import { Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { Socket, createConnection } from 'net';
import { RedisStateClient } from './redis-state.client';

export type HealthStatus = 'HEALTHY' | 'DEGRADED' | 'UNAVAILABLE' | 'UNKNOWN';
export interface ServiceHealth { service: string; status: HealthStatus; latencyMs?: number; lastHeartbeat: string; version?: string; error?: string }

export function classifyDependencyHealth(input: { probeConfigured: boolean; reachable?: boolean; latencyMs?: number; stale?: boolean }): HealthStatus {
  if (!input.probeConfigured) return 'UNKNOWN';
  if (input.reachable === false) return 'UNAVAILABLE';
  if (input.reachable !== true) return 'UNKNOWN';
  if (input.stale || (input.latencyMs !== undefined && input.latencyMs > 1000)) return 'DEGRADED';
  return 'HEALTHY';
}

@Injectable()
export class HealthService {
  constructor(private readonly dataSource: DataSource, private readonly redis: RedisStateClient) {}

  private async probeTcp(url: string): Promise<number> {
    const parsed = new URL(url);
    const started = Date.now();
    await new Promise<void>((resolve, reject) => {
      const socket: Socket = createConnection({ host: parsed.hostname, port: Number(parsed.port) }, () => { socket.destroy(); resolve(); });
      socket.setTimeout(3000, () => { socket.destroy(); reject(new Error('Probe timed out')); });
      socket.once('error', reject);
    });
    return Date.now() - started;
  }

  private async probeHttp(url: string): Promise<number> {
    const started = Date.now();
    const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!response.ok) throw new Error(`Probe returned ${response.status}`);
    return Date.now() - started;
  }

  private async dependency(service: string, probe: () => Promise<number>): Promise<ServiceHealth> {
    const now = new Date().toISOString();
    try {
      const latencyMs = await probe();
      return { service, status: classifyDependencyHealth({ probeConfigured: true, reachable: true, latencyMs }), latencyMs, lastHeartbeat: now };
    } catch (error) {
      return { service, status: 'UNAVAILABLE', lastHeartbeat: now, error: 'Probe failed' };
    }
  }

  async getSystemHealth(): Promise<ServiceHealth[]> {
    const now = new Date().toISOString();
    const started = Date.now();
    let postgres: ServiceHealth;
    try { await this.dataSource.query('SELECT 1'); postgres = { service: 'postgresql', status: 'HEALTHY', latencyMs: Date.now() - started, lastHeartbeat: now }; } catch (error) { postgres = { service: 'postgresql', status: 'UNAVAILABLE', lastHeartbeat: now, error: 'Connection failed' }; }
    const dependencies = await Promise.all([
      this.dependency('redis', () => this.redis.command(['PING']).then(() => 0)),
      this.dependency('rabbitmq', () => this.probeTcp(process.env.RABBITMQ_URL ?? '')),
      this.dependency('minio', () => this.probeHttp(`http://${process.env.MINIO_ENDPOINT ?? 'minio'}:${process.env.MINIO_PORT ?? '9000'}/minio/health/live`)),
      this.dependency('ai-worker', () => this.probeHttp(process.env.AI_WORKER_URL ?? 'http://ai-worker:8002/health')),
      this.dependency('stream-gateway', () => this.probeHttp(process.env.STREAM_GATEWAY_URL ?? 'http://stream-gateway:8001/health')),
    ]);
    return [
      { service: 'api', status: 'HEALTHY', lastHeartbeat: now, version: process.env.npm_package_version ?? '0.1.0' },
      postgres,
      ...dependencies,
      { service: 'websocket', status: 'HEALTHY', lastHeartbeat: now },
    ];
  }
}

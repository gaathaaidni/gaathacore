import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { Socket, createConnection } from 'net';

/** Small RESP client for the state primitives used by the rule engine. */
@Injectable()
export class RedisStateClient implements OnModuleDestroy {
  private readonly url = process.env.REDIS_URL;
  async command(parts: string[]): Promise<string | null> {
    if (!this.url) throw new Error('REDIS_URL is required for durable rule state');
    const parsed = new URL(this.url); const port = Number(parsed.port || 6379);
    const commands = parsed.password
      ? [[ 'AUTH', ...(parsed.username ? [decodeURIComponent(parsed.username), decodeURIComponent(parsed.password)] : [decodeURIComponent(parsed.password)]) ], parts]
      : [parts];
    return new Promise((resolve, reject) => {
      const socket: Socket = createConnection({ host: parsed.hostname, port }); let output = '';
      const timer = setTimeout(() => { socket.destroy(); reject(new Error('Redis command timed out')); }, 3000);
      socket.once('error', (error) => { clearTimeout(timer); reject(error); });
      socket.on('data', (chunk) => output += chunk.toString());
      socket.once('end', () => { clearTimeout(timer); if (output.startsWith('-')) reject(new Error(output)); else resolve(output.startsWith('$-1') ? null : output.replace(/^[+]:?/, '').split('\r\n')[0]); });
      socket.once('connect', () => socket.end(commands.map(command => `*${command.length}\r\n${command.map(part => `$${Buffer.byteLength(part)}\r\n${part}\r\n`).join('')}`).join('')));
    });
  }
  async onModuleDestroy() { /* commands use short-lived sockets; no pool to close */ }
}

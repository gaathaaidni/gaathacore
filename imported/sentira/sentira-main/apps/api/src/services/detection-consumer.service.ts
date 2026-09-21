import { Injectable, Logger, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { parseDetectionEnvelope } from './detection-envelope';
import { DetectionProcessorService } from './detection-processor.service';

const EXCHANGE = 'sentira.detections';
const DLX = 'sentira.detections.dlx';
const QUEUE = 'detection.queue';
const DLQ = 'detection.dlq';
const ROUTING_KEY = 'detection';
const MAX_RETRIES = 3;

/** AMQP ingress for the one production detection-processing pipeline. */
@Injectable()
export class DetectionConsumerService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(DetectionConsumerService.name);
  private connection: any;
  private channel: any;
  private reconnectTimer?: NodeJS.Timeout;
  private stopping = false;
  constructor(private readonly processor: DetectionProcessorService) {}
  async onModuleInit(): Promise<void> {
    if (process.env.RABBITMQ_URL) await this.start().catch((error: Error) => this.scheduleReconnect(error));
  }

  async start(): Promise<void> {
    if (this.stopping || this.connection) return;
    // Loading at connection time keeps broker-less unit tests independent of the AMQP runtime.
    // amqplib is nevertheless a required production dependency (not an optional fallback).
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const amqp = require('amqplib');
    try {
      this.connection = await amqp.connect(process.env.RABBITMQ_URL);
      this.connection.on('error', (error: Error) => this.logger.error(JSON.stringify({ message: 'AMQP connection error', error: error.message })));
      this.connection.on('close', () => { this.connection = undefined; this.channel = undefined; if (!this.stopping) this.scheduleReconnect(); });
      this.channel = await this.connection.createChannel();
      await this.channel.assertExchange(EXCHANGE, 'direct', { durable: true });
      await this.channel.assertExchange(DLX, 'direct', { durable: true });
      await this.channel.assertQueue(DLQ, { durable: true });
      await this.channel.bindQueue(DLQ, DLX, 'detection.failed');
      await this.channel.assertQueue(QUEUE, { durable: true, arguments: { 'x-dead-letter-exchange': DLX, 'x-dead-letter-routing-key': 'detection.failed' } });
      await this.channel.bindQueue(QUEUE, EXCHANGE, ROUTING_KEY);
      await this.channel.prefetch(4);
      await this.channel.consume(QUEUE, (message: any) => void this.handle(message), { noAck: false });
      this.logger.log(JSON.stringify({ message: 'AMQP detection consumer connected', queue: QUEUE, exchange: EXCHANGE }));
    } catch (error) { this.connection = undefined; this.channel = undefined; throw error; }
  }

  private scheduleReconnect(error?: Error): void {
    if (this.stopping || this.reconnectTimer) return;
    this.logger.warn(JSON.stringify({ message: 'AMQP detection consumer unavailable; reconnect scheduled', error: error?.message }));
    this.reconnectTimer = setTimeout(() => { this.reconnectTimer = undefined; void this.start().catch((reason: Error) => this.scheduleReconnect(reason)); }, 5000);
  }

  async handle(message: any): Promise<void> {
    if (!message || !this.channel) return;
    const correlationId = message.properties?.correlationId;
    const headers = (message.properties?.headers ?? {}) as Record<string, unknown>;
    try {
      const envelope = parseDetectionEnvelope(JSON.parse(message.content.toString('utf8')));
      const tenantId = typeof headers['x-tenant-id'] === 'string' ? headers['x-tenant-id'] : undefined;
      if (!tenantId || tenantId !== envelope.organizationId) {
        this.logger.warn(JSON.stringify({ message: 'detection tenant mismatch rejected', tenantId, organizationId: envelope.organizationId, cameraId: envelope.cameraId, frameId: envelope.frameId, correlationId }));
        this.channel.nack(message, false, false);
        return;
      }
      await this.processor.process(envelope);
      this.channel.ack(message);
    } catch (error) {
      const retries = Number(headers['x-retry-count'] ?? 0);
      const permanent = error instanceof SyntaxError || (error as { status?: number }).status === 400;
      if (permanent || retries >= MAX_RETRIES) {
        this.logger.warn(JSON.stringify({ message: 'detection dead-lettered', retries, correlationId, error: error instanceof Error ? error.message : 'unknown' }));
        this.channel.nack(message, false, false);
        return;
      }
      const retryDelayMs = Math.min(1000 * 2 ** retries, 30000);
      const nextHeaders = { ...headers, 'x-tenant-id': headers['x-tenant-id'] ?? 'unknown-tenant', 'x-retry-count': retries + 1 };
      this.channel.sendToQueue(QUEUE, message.content, { persistent: true, contentType: 'application/json', correlationId, expiration: String(retryDelayMs), headers: nextHeaders });
      this.channel.ack(message);
    }
  }
  async onModuleDestroy(): Promise<void> { this.stopping = true; if (this.reconnectTimer) clearTimeout(this.reconnectTimer); await this.channel?.close(); await this.connection?.close(); }
}

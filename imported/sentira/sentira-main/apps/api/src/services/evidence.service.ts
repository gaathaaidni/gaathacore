import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { EventMedia } from '../entities/event-media.entity';
import { Event } from '../entities/event.entity';
import { Organization } from '../entities/organization.entity';
import { ObjectStorageService } from './object-storage.service';

@Injectable()
export class EvidenceService {
  constructor(
    @InjectRepository(EventMedia) private readonly mediaRepository: Repository<EventMedia>,
    @InjectRepository(Event) private readonly events: Repository<Event>,
    @InjectRepository(Organization) private readonly organizations: Repository<Organization>,
    private readonly storage: ObjectStorageService,
  ) {}

  storageKey(input: { organizationId: string; siteId?: string; cameraId: string; eventId: string; mediaType: string; extension: string }): string {
    const site = input.siteId ? `/sites/${input.siteId}` : '';
    return `organizations/${input.organizationId}${site}/cameras/${input.cameraId}/events/${input.eventId}/${input.mediaType}.${input.extension}`;
  }

  async getRetentionExpiry(organizationId: string, createdAt = new Date()): Promise<Date> {
    const organization = await this.organizations.findOneBy({ id: organizationId });
    const retentionDays = Math.max(0, Number(organization?.retentionDays ?? 30) || 30);
    return new Date(createdAt.getTime() + retentionDays * 24 * 60 * 60 * 1000);
  }

  async recordPendingEvidence(input: { organizationId: string; cameraId: string; eventId: string; mediaType: 'snapshot' | 'video_clip' | 'detection_json'; durationSeconds?: number; metadataJson?: Record<string, unknown> }): Promise<EventMedia> {
    const extension = input.mediaType === 'detection_json' ? 'json' : input.mediaType === 'snapshot' ? 'jpg' : 'mp4';
    const capturedAt = new Date();
    const expiresAt = await this.getRetentionExpiry(input.organizationId, capturedAt);
    return this.mediaRepository.save({ ...input, storageKey: this.storageKey({ ...input, extension }), capturedAt, expiresAt });
  }

  signedAccessPath(media: EventMedia, ttlSeconds = 300): string {
    const ttl = Math.min(Math.max(1, Number(ttlSeconds) || 300), 300);
    return `/api/events/${media.eventId}/media/${media.id}/signed?ttl=${ttl}`;
  }

  async attachSnapshot(event: Event, jpegBase64: string, correlationId?: string): Promise<EventMedia> {
    const bytes = Buffer.from(jpegBase64, 'base64'); if (!bytes.length) throw new Error('Snapshot frame is empty');
    const storageKey = this.storageKey({ organizationId: event.organizationId, siteId: event.siteId, cameraId: event.cameraId, eventId: event.id, mediaType: 'snapshot', extension: 'jpg' });
    try { const stored = await this.storage.put(storageKey, bytes, 'image/jpeg', { correlationid: correlationId ?? event.correlationId ?? event.id });
      const capturedAt = new Date();
      const expiresAt = await this.getRetentionExpiry(event.organizationId, capturedAt);
      const media = await this.mediaRepository.save({ eventId: event.id, organizationId: event.organizationId, cameraId: event.cameraId, mediaType: 'snapshot', storageKey, capturedAt, expiresAt, sha256: stored.sha256, byteSize: stored.byteSize, contentType: stored.contentType, metadataJson: { correlationId: correlationId ?? event.correlationId } });
      await this.events.update(event.id, { evidenceStatus: 'ready', snapshotUrl: this.signedAccessPath(media) }); return media;
    } catch (error) { await this.events.update(event.id, { evidenceStatus: 'failed' }); throw error; }
  }
  async findAuthorized(mediaId: string, eventId: string, organizationId: string): Promise<EventMedia> {
    const media = await this.mediaRepository.findOneBy({ id: mediaId, eventId, organizationId }); if (!media) throw new NotFoundException('Evidence not found'); return media;
  }
  async readAuthorized(mediaId: string, eventId: string, organizationId: string): Promise<{ media: EventMedia; bytes: Buffer }> {
    const media = await this.findAuthorized(mediaId, eventId, organizationId);
    if (media.expiresAt && media.expiresAt <= new Date()) {
      throw new NotFoundException('Evidence has expired and been removed');
    }
    const bytes = await this.storage.getForOrganization(organizationId, media.storageKey);
    if (media.sha256 && require('crypto').createHash('sha256').update(bytes).digest('hex') !== media.sha256) throw new Error('Stored evidence integrity verification failed');
    return { media, bytes };
  }
}

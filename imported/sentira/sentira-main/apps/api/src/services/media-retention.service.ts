import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { LessThanOrEqual, Repository } from 'typeorm';
import { AuditLog } from '../entities/audit-log.entity';
import { Event } from '../entities/event.entity';
import { EventMedia } from '../entities/event-media.entity';
import { Organization } from '../entities/organization.entity';
import { ObjectStorageService } from './object-storage.service';

@Injectable()
export class MediaRetentionService implements OnModuleInit {
  private readonly logger = new Logger(MediaRetentionService.name);
  private cleanupTimer?: NodeJS.Timeout;

  constructor(
    @InjectRepository(Organization) private readonly organizations: Repository<Organization>,
    @InjectRepository(EventMedia) private readonly mediaRepository: Repository<EventMedia>,
    @InjectRepository(Event) private readonly events: Repository<Event>,
    @InjectRepository(AuditLog) private readonly auditLogs: Repository<AuditLog>,
    private readonly storage: ObjectStorageService,
  ) {}

  onModuleInit() {
    this.scheduleCleanup();
  }

  private scheduleCleanup(): void {
    if (this.cleanupTimer) return;
    this.cleanupTimer = setInterval(() => {
      void this.cleanupExpiredMedia().catch((error) => {
        this.logger.error('Media retention cleanup failed', error instanceof Error ? error.stack : undefined);
      });
    }, 60_000);
  }

  async cleanupExpiredMedia(organizationId?: string): Promise<{ deletedCount: number; failedCount: number; skippedCount: number; errors: string[] }> {
    const now = new Date();
    const expired = await this.mediaRepository.find({
      where: organizationId ? { organizationId, expiresAt: LessThanOrEqual(now) } : { expiresAt: LessThanOrEqual(now) },
      order: { expiresAt: 'ASC' },
      take: 200,
    });

    const result = { deletedCount: 0, failedCount: 0, skippedCount: 0, errors: [] as string[] };
    for (const media of expired) {
      if (!media.expiresAt || media.expiresAt > now) {
        result.skippedCount += 1;
        continue;
      }

      try {
        this.storage.assertTenantScopedKey(media.organizationId, media.storageKey);
      } catch (error) {
        const message = `Skipping media ${media.id} with invalid tenant-scoped storage key`;
        this.logger.warn(message, error instanceof Error ? error.message : String(error));
        result.skippedCount += 1;
        result.errors.push(message);
        continue;
      }

      try {
        await this.storage.deleteForOrganization(media.organizationId, media.storageKey);
      } catch (error) {
        const message = `Retention delete failed for ${media.id}: ${error instanceof Error ? error.message : String(error)}`;
        this.logger.warn(message);
        result.failedCount += 1;
        result.errors.push(message);
        continue;
      }

      try {
        const event = await this.events.findOneBy({ id: media.eventId });
        if (event) {
          let changed = false;
          if (event.snapshotUrl && event.snapshotUrl.includes(`/media/${media.id}`)) {
            event.snapshotUrl = null;
            changed = true;
          }
          if (event.videoClipUrl && event.videoClipUrl.includes(`/media/${media.id}`)) {
            event.videoClipUrl = null;
            changed = true;
          }
          if (changed) {
            await this.events.save(event);
          }
        }

        await this.mediaRepository.delete(media.id);
        await this.auditLogs.save({
          organizationId: media.organizationId,
          userId: null,
          action: 'media.retention.deleted',
          resourceType: 'event_media',
          resourceId: media.id,
          previousValueJson: { storageKey: media.storageKey, expiresAt: media.expiresAt?.toISOString?.() ?? null },
          newValueJson: { deletedAt: now.toISOString(), retentionPolicy: 'expired' },
        });
        result.deletedCount += 1;
      } catch (error) {
        const message = `DB cleanup failed for ${media.id}: ${error instanceof Error ? error.message : String(error)}`;
        this.logger.error(message);
        result.failedCount += 1;
        result.errors.push(message);
      }
    }

    return result;
  }

  async getRetentionExpiryForOrganization(organizationId: string, createdAt = new Date()): Promise<Date> {
    const org = await this.organizations.findOneBy({ id: organizationId });
    const retentionDays = Math.max(0, Number(org?.retentionDays ?? 30) || 30);
    return new Date(createdAt.getTime() + retentionDays * 24 * 60 * 60 * 1000);
  }
}

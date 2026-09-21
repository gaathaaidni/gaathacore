import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Event } from '../../entities/event.entity';
import { AuditLog } from '../../entities/audit-log.entity';

@Injectable()
export class EventsService {
  constructor(
    @InjectRepository(Event)
    private eventsRepository: Repository<Event>,
    @InjectRepository(AuditLog) private auditRepository: Repository<AuditLog>,
  ) {}

  async create(organizationId: string, eventData: Partial<Event>): Promise<Event> {
    return this.eventsRepository.save({
      ...eventData,
      organizationId,
    });
  }

  async findById(id: string, organizationId: string): Promise<Event | null> {
    return this.eventsRepository.findOne({
      where: { id, organizationId },
      relations: ['camera', 'site', 'rule', 'zone'],
    });
  }

  async findByOrganization(organizationId: string, limit = 50, offset = 0): Promise<Event[]> {
    return this.eventsRepository.find({
      where: { organizationId },
      order: { createdAt: 'DESC' },
      take: limit,
      skip: offset,
      relations: ['camera', 'site', 'rule'],
    });
  }

  async updateStatus(id: string, status: Event['status'], organizationId: string, userId?: string, details: Partial<Event> = {}): Promise<Event> {
    const event = await this.findById(id, organizationId);
    if (!event) throw new NotFoundException('Event not found');
    const allowed: Record<Event['status'], Event['status'][]> = { new: ['acknowledged','investigating','escalated','dismissed','false_positive'], acknowledged: ['investigating','escalated','resolved','dismissed','false_positive'], investigating: ['escalated','resolved','dismissed','false_positive'], escalated: ['investigating','resolved','dismissed','false_positive'], resolved: [], dismissed: [], false_positive: [] };
    if (!allowed[event.status].includes(status)) throw new BadRequestException(`Invalid event transition: ${event.status} -> ${status}`);
    const now = new Date(); const timestamps: Partial<Event> = status === 'acknowledged' ? { acknowledgedAt: now, acknowledgedByUserId: userId } : status === 'investigating' ? { investigatingAt: now } : status === 'escalated' ? { escalatedAt: now } : status === 'resolved' ? { resolvedAt: now, resolvedByUserId: userId } : {};
    await this.eventsRepository.update({ id, organizationId }, { ...details, ...timestamps, status });
    await this.auditRepository.save({ organizationId, userId: userId ?? null, action: `event.${status}`, resourceType: 'event', resourceId: id, previousValueJson: { status: event.status }, newValueJson: { status, ...details } });
    return (await this.findById(id, organizationId))!;
  }
}

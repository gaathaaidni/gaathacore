import { Controller, Get, Query, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, SelectQueryBuilder } from 'typeorm';
import { AuditLog, Camera, Event, Notification, Rule } from '../../entities';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { PermissionGuard } from '../../auth/guards/permission.guard';
import { RequirePermission } from '../../auth/decorators/require-permission.decorator';
import { CurrentUser } from '../../auth/decorators/current-user.decorator';
import { CurrentUserDto } from '../../auth/auth.dto';

@Controller('api') @UseGuards(JwtAuthGuard, PermissionGuard)
export class OperationsController {
  constructor(@InjectRepository(Event) private events: Repository<Event>, @InjectRepository(Camera) private cameras: Repository<Camera>, @InjectRepository(Rule) private rules: Repository<Rule>, @InjectRepository(AuditLog) private audit: Repository<AuditLog>, @InjectRepository(Notification) private notifications: Repository<Notification>) {}
  private filtered(user: CurrentUserDto, query: any): SelectQueryBuilder<Event> {
    const q = this.events.createQueryBuilder('e').where('e.organizationId = :organizationId', { organizationId: user.organizationId });
    for (const key of ['siteId', 'cameraId', 'ruleId', 'severity', 'priority', 'status']) if (query[key]) q.andWhere(`e.${key} = :${key}`, { [key]: query[key] });
    if (query.from) q.andWhere('e.createdAt >= :from', { from: query.from }); if (query.to) q.andWhere('e.createdAt <= :to', { to: query.to }); return q;
  }
  @Get('analytics/overview') @RequirePermission('analytics.view') async overview(@CurrentUser() user: CurrentUserDto, @Query() query: any) {
    const q = this.filtered(user, query); const total = await q.getCount();
    const bySeverity = await this.filtered(user, query).select('e.severity', 'key').addSelect('COUNT(*)', 'count').groupBy('e.severity').getRawMany();
    const rates = await this.filtered(user, query).select("COUNT(*) FILTER (WHERE e.status IN ('acknowledged','investigating','escalated','resolved'))::float / NULLIF(COUNT(*),0)", 'acknowledgementRate').addSelect("COUNT(*) FILTER (WHERE e.status = 'resolved')::float / NULLIF(COUNT(*),0)", 'resolutionRate').addSelect("COUNT(*) FILTER (WHERE e.status = 'false_positive')::float / NULLIF(COUNT(*),0)", 'falsePositiveRate').addSelect("AVG(EXTRACT(EPOCH FROM (e.acknowledgedAt - e.createdAt)))", 'averageAcknowledgementSeconds').addSelect("AVG(EXTRACT(EPOCH FROM (e.resolvedAt - e.createdAt)))", 'averageResolutionSeconds').getRawOne();
    return { totalEvents: total, eventsBySeverity: bySeverity, ...rates };
  }
  @Get('analytics/events') @RequirePermission('analytics.view') eventsAnalytics(@CurrentUser() u: CurrentUserDto, @Query() q: any) { return this.filtered(u,q).select('e.eventType','key').addSelect('COUNT(*)','count').groupBy('e.eventType').getRawMany(); }
  @Get('analytics/cameras') @RequirePermission('analytics.view') camerasAnalytics(@CurrentUser() u: CurrentUserDto) { return this.cameras.createQueryBuilder('c').select('c.status','status').addSelect('COUNT(*)','count').where('c.organizationId = :organizationId',{organizationId:u.organizationId}).groupBy('c.status').getRawMany(); }
  @Get('analytics/rules') @RequirePermission('analytics.view') rulesAnalytics(@CurrentUser() u: CurrentUserDto, @Query() q: any) { return this.filtered(u,q).select('e.ruleId','ruleId').addSelect('COUNT(*)','count').groupBy('e.ruleId').orderBy('count','DESC').limit(10).getRawMany(); }
  @Get('analytics/sites') @RequirePermission('analytics.view') sitesAnalytics(@CurrentUser() u: CurrentUserDto, @Query() q: any) { return this.filtered(u,q).select('e.siteId','siteId').addSelect('COUNT(*)','count').groupBy('e.siteId').getRawMany(); }
  @Get('analytics/sla') @RequirePermission('analytics.view') sla(@CurrentUser() u: CurrentUserDto, @Query() q: any) { return this.filtered(u,q).select('e.slaState','state').addSelect('COUNT(*)','count').groupBy('e.slaState').getRawMany(); }
  @Get('analytics/alerts') @RequirePermission('analytics.view') alerts(@CurrentUser() u: CurrentUserDto, @Query() q: any) { return this.filtered(u,q).select("COUNT(*) FILTER (WHERE e.status = 'escalated')",'escalated').addSelect("COUNT(*) FILTER (WHERE e.status = 'false_positive')",'falsePositive').getRawOne(); }
  @Get('audit') @RequirePermission('audit.view') async auditLogs(@CurrentUser() u: CurrentUserDto, @Query() q: any) { const qb=this.audit.createQueryBuilder('a').where('a.organizationId=:organizationId',{organizationId:u.organizationId}).orderBy('a.createdAt','DESC').take(Math.min(Number(q.limit)||100,500)); for(const k of ['userId','action','resourceType','resourceId']) if(q[k]) qb.andWhere(`a.${k}=:${k}`,{[k]:q[k]}); if(q.from)qb.andWhere('a.createdAt>=:from',{from:q.from});if(q.to)qb.andWhere('a.createdAt<=:to',{to:q.to});return qb.getMany(); }
  @Get('reports/events.csv') @RequirePermission('reports.view') async report(@CurrentUser() u: CurrentUserDto,@Query() q:any,@Res() res:Response) { res.setHeader('Content-Type','text/csv; charset=utf-8');res.setHeader('Content-Disposition','attachment; filename="events.csv"');res.write('id,createdAt,severity,priority,status,eventType,cameraId,siteId\n'); const rows=await this.filtered(u,q).select(['e.id','e.createdAt','e.severity','e.priority','e.status','e.eventType','e.cameraId','e.siteId']).orderBy('e.createdAt','DESC').limit(10000).getMany(); for(const e of rows) res.write([e.id,e.createdAt.toISOString(),e.severity,e.priority,e.status,JSON.stringify(e.eventType),e.cameraId,e.siteId].join(',')+'\n'); res.end(); }
}

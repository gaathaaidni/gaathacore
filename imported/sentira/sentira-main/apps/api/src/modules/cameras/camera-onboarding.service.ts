import { BadRequestException, Injectable, NotFoundException, UnauthorizedException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { createHash, randomBytes } from 'crypto';
import { Repository } from 'typeorm';
import { Camera } from '../../entities/camera.entity';
import { CameraOnboardingSession } from '../../entities/camera-onboarding-session.entity';
import { Connector } from '../../entities/connector.entity';
import { DiscoveredCamera } from '../../entities/discovered-camera.entity';
import { Site } from '../../entities/site.entity';
import { AuditLog } from '../../entities/audit-log.entity';
import { CameraEntitlementService } from './camera-entitlement.service';
import { CreateOnboardingSessionDto, PairConnectorDto, ClaimDiscoveredCameraDto, RegisterConnectorDto, ReportDiscoveredCameraDto } from './dto/onboarding.dto';

@Injectable()
export class CameraOnboardingService {
  constructor(
    @InjectRepository(CameraOnboardingSession) private sessions: Repository<CameraOnboardingSession>,
    @InjectRepository(Connector) private connectors: Repository<Connector>,
    @InjectRepository(DiscoveredCamera) private discovered: Repository<DiscoveredCamera>,
    @InjectRepository(Camera) private cameras: Repository<Camera>,
    @InjectRepository(Site) private sites: Repository<Site>,
    @InjectRepository(AuditLog) private audit: Repository<AuditLog>,
    private readonly entitlement: CameraEntitlementService,
  ) {}

  private hash(value: string): string { return createHash('sha256').update(value).digest('hex'); }

  private publicDiscovered(camera: DiscoveredCamera) {
    return { id: camera.id, name: camera.name, manufacturer: camera.manufacturer, model: camera.model, protocol: camera.protocol, capabilities: camera.capabilities, discoveryStatus: camera.discoveryStatus, discoveredAt: camera.discoveredAt };
  }

  async createSession(organizationId: string, userId: string, dto: CreateOnboardingSessionDto) {
    const code = `${randomBytes(2).toString('hex').toUpperCase()}-${randomBytes(2).toString('hex').toUpperCase()}`;
    const session = this.sessions.create({ organizationId, userId, method: dto.method, status: 'waiting_for_connector', pairingCodeHash: this.hash(code), expiresAt: new Date(Date.now() + 10 * 60 * 1000) });
    const saved = await this.sessions.save(session);
    await this.audit.save(this.audit.create({ organizationId, userId, action: 'camera.onboarding.started', resourceType: 'camera_onboarding_session', resourceId: saved.id, newValueJson: { method: dto.method } }));
    return { id: saved.id, method: saved.method, status: saved.status, pairingCode: code, expiresAt: saved.expiresAt, connectorRequired: true };
  }

  async getSession(organizationId: string, id: string) {
    const session = await this.sessions.findOne({ where: { id, organizationId } });
    if (!session) throw new NotFoundException('Onboarding session not found');
    if (session.expiresAt < new Date() && session.status !== 'complete' && session.status !== 'expired') {
      session.status = 'expired';
      await this.sessions.save(session);
    }
    return { id: session.id, method: session.method, status: session.status, expiresAt: session.expiresAt, connectorRequired: session.status === 'waiting_for_connector' };
  }

  async pairConnector(organizationId: string, id: string, dto: PairConnectorDto, userId: string) {
    const session = await this.sessions.findOne({ where: { id, organizationId } });
    if (!session || session.expiresAt < new Date() || session.usedAt) throw new BadRequestException('This pairing code has expired or was already used');
    if (session.pairingCodeHash !== this.hash(dto.pairingCode)) throw new UnauthorizedException('Invalid pairing code');
    const registrationToken = randomBytes(32).toString('hex');
    const connector = await this.connectors.save(this.connectors.create({ organizationId, name: dto.connectorName, status: 'online', lastHeartbeatAt: new Date(), registrationTokenHash: this.hash(registrationToken) }));
    session.connectorId = connector.id;
    session.status = 'connected';
    session.usedAt = new Date();
    session.pairingCodeHash = null;
    await this.sessions.save(session);
    await this.audit.save(this.audit.create({ organizationId, userId, action: 'camera.connector.paired', resourceType: 'connector', resourceId: connector.id, newValueJson: { sessionId: session.id } }));
    return { id: session.id, status: session.status, connector: { id: connector.id, name: connector.name, status: connector.status }, registrationToken };
  }

  async registerConnector(dto: RegisterConnectorDto) {
    const session = await this.sessions.findOne({ where: { id: dto.sessionId } });
    if (!session || session.expiresAt < new Date() || session.usedAt || session.pairingCodeHash !== this.hash(dto.pairingCode)) throw new UnauthorizedException('Invalid or expired connector pairing');
    const registrationToken = randomBytes(32).toString('hex');
    const connector = this.connectors.create({ organizationId: session.organizationId, name: dto.name, status: 'online', version: dto.version, lastHeartbeatAt: new Date(), registrationTokenHash: this.hash(registrationToken) });
    const saved = await this.connectors.save(connector);
    session.connectorId = saved.id;
    session.status = 'connected';
    session.usedAt = new Date();
    session.pairingCodeHash = null;
    await this.sessions.save(session);
    await this.audit.save(this.audit.create({ organizationId: session.organizationId, action: 'camera.connector.registered', resourceType: 'connector', resourceId: saved.id, newValueJson: { sessionId: session.id, version: dto.version || null } }));
    return { connectorId: saved.id, registrationToken, status: saved.status };
  }

  async heartbeat(connectorId: string, token: string) {
    const connector = await this.connectors.findOne({ where: { id: connectorId } });
    if (!connector || !connector.registrationTokenHash || connector.registrationTokenHash !== this.hash(token)) throw new UnauthorizedException('Invalid connector credentials');
    connector.status = 'online'; connector.lastHeartbeatAt = new Date();
    await this.connectors.save(connector);
    return { id: connector.id, status: connector.status, lastHeartbeatAt: connector.lastHeartbeatAt };
  }

  async reportDiscovered(connectorId: string, token: string, dto: ReportDiscoveredCameraDto) {
    const connector = await this.connectors.findOne({ where: { id: connectorId } });
    if (!connector || !connector.registrationTokenHash || connector.registrationTokenHash !== this.hash(token)) throw new UnauthorizedException('Invalid connector credentials');
    const camera = await this.discovered.save(this.discovered.create({ ...dto, organizationId: connector.organizationId, connectorId, discoveredAt: new Date(), discoveryStatus: 'ready' }));
    return this.publicDiscovered(camera);
  }

  async listDiscovered(organizationId: string, sessionId: string) {
    const session = await this.sessions.findOne({ where: { id: sessionId, organizationId } });
    if (!session) throw new NotFoundException('Onboarding session not found');
    if (!session.connectorId) return { status: session.status, cameras: [], message: 'A Sentira Connector is required to discover cameras on this local network.' };
    const cameras = await this.discovered.find({ where: { organizationId, connectorId: session.connectorId, discoveryStatus: 'ready' } });
    return { status: session.status, cameras: cameras.map((camera) => this.publicDiscovered(camera)) };
  }

  async claim(organizationId: string, userId: string, dto: ClaimDiscoveredCameraDto) {
    const discovered = await this.discovered.findOne({ where: { id: dto.discoveredCameraId, organizationId, discoveryStatus: 'ready' } });
    if (!discovered) throw new NotFoundException('Discovered camera not found');
    const site = await this.sites.findOne({ where: { id: dto.siteId, organizationId } });
    if (!site) throw new NotFoundException('Site not found');
    const camera = await this.entitlement.withCameraSlot(organizationId, async (manager) => manager.getRepository(Camera).save(manager.getRepository(Camera).create({ organizationId, siteId: site.id, name: dto.name, streamUrl: null, protocol: 'connector', sourceType: 'connector', connectorId: discovered.connectorId, discoveredCameraId: discovered.id, status: 'connecting' })));
    discovered.discoveryStatus = 'claimed'; await this.discovered.save(discovered);
    await this.audit.save(this.audit.create({ organizationId, userId, action: 'camera.discovered.claimed', resourceType: 'camera', resourceId: camera.id, newValueJson: { discoveredCameraId: discovered.id, connectorId: discovered.connectorId } }));
    return { id: camera.id, name: camera.name, status: camera.status, sourceType: camera.sourceType };
  }
}

import { BadRequestException, Injectable, NotFoundException, UnauthorizedException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { createHash, randomBytes } from 'crypto';
import { Repository } from 'typeorm';
import { AuditLog, Camera, CctvConnectionTest, CctvConnectorCommand, CctvManufacturer, CctvModel, CctvRecorder, CctvRecorderChannel, CctvSetupGuide, CctvSetupSession, CctvSupportRequest, Connector, DiscoveredCamera, Site } from '../../entities';
import { CurrentUserDto } from '../../auth/auth.dto';
import { AcknowledgeConnectorCommandDto, CreateConnectorCommandDto, CreateGuideDto, CreateManufacturerDto, CreateModelDto, CreateSetupSessionDto, CreateSupportRequestDto, DiscoverCamerasDto, EnumerateRecorderChannelsDto, HeartbeatConnectorDto, PairConnectorDto, PollConnectorCommandsDto, ReportConnectorCommandResultDto, ReportDiscoveryResultsDto, TestSetupSessionDto, UpdateSetupSessionDto } from './dto/cctv.dto';
import { GenericRtspConnector } from './connectors/generic-rtsp.connector';
import { OnvifConnector } from './connectors/onvif.connector';

@Injectable()
export class CctvService {
  constructor(
    @InjectRepository(CctvManufacturer) private manufacturers: Repository<CctvManufacturer>,
    @InjectRepository(CctvModel) private models: Repository<CctvModel>,
    @InjectRepository(CctvSetupGuide) private guides: Repository<CctvSetupGuide>,
    @InjectRepository(CctvSetupSession) private sessions: Repository<CctvSetupSession>,
    @InjectRepository(CctvSupportRequest) private support: Repository<CctvSupportRequest>,
    @InjectRepository(CctvConnectionTest) private tests: Repository<CctvConnectionTest>,
    @InjectRepository(Connector) private connectors: Repository<Connector>,
    @InjectRepository(CctvRecorder) private recorders: Repository<CctvRecorder>,
    @InjectRepository(CctvRecorderChannel) private channels: Repository<CctvRecorderChannel>,
    @InjectRepository(DiscoveredCamera) private discovered: Repository<DiscoveredCamera>,
    @InjectRepository(Camera) private cameras: Repository<Camera>,
    @InjectRepository(Site) private sites: Repository<Site>,
    @InjectRepository(AuditLog) private audit: Repository<AuditLog>,
    @InjectRepository(CctvConnectorCommand) private commands: Repository<CctvConnectorCommand>,
    private readonly rtsp: GenericRtspConnector,
    private readonly onvif: OnvifConnector,
  ) {}

  private hash(value: string): string { return createHash('sha256').update(value).digest('hex'); }

  async listManufacturers(search?: string) {
    const query = this.manufacturers.createQueryBuilder('manufacturer').where('manufacturer.active = true').orderBy('manufacturer.name', 'ASC');
    if (search?.trim()) query.andWhere('(LOWER(manufacturer.name) LIKE LOWER(:search) OR LOWER(manufacturer.slug) LIKE LOWER(:search))', { search: `%${search.trim()}%` });
    return query.getMany();
  }

  async listModels(manufacturerId: string, search?: string) {
    const manufacturer = await this.manufacturers.findOne({ where: { id: manufacturerId, active: true } });
    if (!manufacturer) throw new NotFoundException('Manufacturer not found');
    const query = this.models.createQueryBuilder('model').where('model.manufacturerId = :manufacturerId AND model.active = true', { manufacturerId }).orderBy('model.name', 'ASC');
    if (search?.trim()) query.andWhere('(LOWER(model.name) LIKE LOWER(:search) OR LOWER(model.modelNumber) LIKE LOWER(:search))', { search: `%${search.trim()}%` });
    return query.getMany();
  }

  async getModel(modelId: string) {
    const model = await this.models.findOne({ where: { id: modelId, active: true }, relations: ['manufacturer'] });
    if (!model) throw new NotFoundException('CCTV model not found');
    return model;
  }

  async listGuides(modelId?: string, manufacturerId?: string) {
    const where = modelId ? { modelId, active: true } : manufacturerId ? { manufacturerId, active: true } : { active: true };
    return this.guides.find({ where, order: { updatedAt: 'DESC' } });
  }

  async searchHelp(query: string) {
    const value = query?.trim();
    if (!value) return { manufacturers: [], models: [], guides: [] };
    const like = `%${value}%`;
    const [manufacturers, models, guides] = await Promise.all([
      this.manufacturers.createQueryBuilder('item').where('item.active = true AND (item.name ILIKE :like OR item.description ILIKE :like)', { like }).take(20).getMany(),
      this.models.createQueryBuilder('item').where('item.active = true AND (item.name ILIKE :like OR item.modelNumber ILIKE :like OR item.description ILIKE :like)', { like }).take(20).getMany(),
      this.guides.createQueryBuilder('item').where('item.active = true AND (item.title ILIKE :like OR item.description ILIKE :like)', { like }).take(20).getMany(),
    ]);
    return { manufacturers, models, guides };
  }

  async createSession(user: CurrentUserDto, dto: CreateSetupSessionDto) {
    if (dto.siteId) await this.assertSite(dto.siteId, user.organizationId);
    const session = await this.sessions.save(this.sessions.create({ organizationId: user.organizationId, userId: user.id, siteId: dto.siteId, deviceType: dto.deviceType, status: 'STARTED', stage: 'IDENTIFY', answers: {}, completionPercent: 0 }));
    await this.recordAudit(user, 'cctv.setup.started', session.id, { deviceType: dto.deviceType || null });
    return session;
  }

  async createConnectorPairing(user: CurrentUserDto, setupSessionId: string) {
    const session = await this.getSession(user, setupSessionId);
    if (session.status === 'COMPLETED') throw new BadRequestException('Completed setup sessions cannot be paired');
    const pairingCode = `${randomBytes(2).toString('hex').toUpperCase()}-${randomBytes(2).toString('hex').toUpperCase()}`;
    session.pairingCodeHash = this.hash(pairingCode);
    session.pairingExpiresAt = new Date(Date.now() + 10 * 60 * 1000);
    session.pairingUsedAt = null;
    await this.sessions.save(session);
    await this.recordAudit(user, 'cctv.connector.pairing_started', session.id, { expiresAt: session.pairingExpiresAt.toISOString() });
    return { setupSessionId: session.id, pairingCode, expiresAt: session.pairingExpiresAt, singleUse: true };
  }

  async registerConnector(setupSessionId: string, dto: PairConnectorDto) {
    const session = await this.sessions.findOne({ where: { id: setupSessionId } });
    if (!session || !session.pairingCodeHash || session.pairingUsedAt || !session.pairingExpiresAt || session.pairingExpiresAt < new Date()) throw new UnauthorizedException('Invalid or expired connector pairing');
    if (session.pairingCodeHash !== this.hash(dto.pairingCode)) throw new UnauthorizedException('Invalid or expired connector pairing');
    const registrationToken = randomBytes(32).toString('hex');
    const connector = await this.connectors.save(this.connectors.create({ organizationId: session.organizationId, name: dto.connectorName, version: dto.version, status: 'online', lastHeartbeatAt: new Date(), registrationTokenHash: this.hash(registrationToken) }));
    session.connectorId = connector.id;
    session.pairingUsedAt = new Date();
    session.pairingCodeHash = null;
    session.pairingExpiresAt = null;
    session.stage = 'FIND';
    session.status = 'IN_PROGRESS';
    await this.sessions.save(session);
    await this.audit.save(this.audit.create({ organizationId: session.organizationId, action: 'cctv.connector.registered', resourceType: 'connector', resourceId: connector.id, newValueJson: { setupSessionId: session.id, version: dto.version || null } }));
    return { connectorId: connector.id, registrationToken, status: connector.status };
  }

  async heartbeatConnector(dto: HeartbeatConnectorDto) {
    const connector = await this.authorizeConnector(dto.connectorId, dto.registrationToken);
    connector.status = 'online';
    connector.lastHeartbeatAt = new Date();
    if (dto.metadata) connector.capabilities = this.sanitize(dto.metadata);
    await this.connectors.save(connector);
    return { connectorId: connector.id, status: connector.status, lastHeartbeatAt: connector.lastHeartbeatAt };
  }

  async revokeConnector(user: CurrentUserDto, id: string) {
    const connector = await this.connectors.findOne({ where: { id, organizationId: user.organizationId } });
    if (!connector) throw new NotFoundException('Connector not found');
    connector.status = 'disabled';
    connector.registrationTokenHash = null;
    const saved = await this.connectors.save(connector);
    await this.recordAudit(user, 'cctv.connector.revoked', id, { connectorId: id });
    return { connectorId: saved.id, status: saved.status };
  }

  async rotateConnectorToken(user: CurrentUserDto, id: string) {
    const connector = await this.connectors.findOne({ where: { id, organizationId: user.organizationId } });
    if (!connector) throw new NotFoundException('Connector not found');
    const registrationToken = randomBytes(32).toString('hex');
    connector.registrationTokenHash = this.hash(registrationToken);
    connector.status = 'offline';
    await this.connectors.save(connector);
    await this.recordAudit(user, 'cctv.connector.token_rotated', id, { connectorId: id });
    return { connectorId: id, registrationToken, status: connector.status };
  }

  async discoverThroughConnector(dto: DiscoverCamerasDto) {
    const connector = await this.authorizeConnector(dto.connectorId, dto.registrationToken);
    const session = await this.sessions.findOne({ where: { id: dto.setupSessionId, connectorId: connector.id, organizationId: connector.organizationId } });
    if (!session) throw new NotFoundException('Setup session is not paired with this connector');
    return { status: 'DISCOVERY_UNAVAILABLE', retryable: true, supportRecommended: false, cameras: [], message: 'The Sentira Edge Connector contract is ready, but no connector discovery agent is connected to perform a local network scan.' };
  }

  async enumerateConnectorChannels(dto: EnumerateRecorderChannelsDto) {
    const connector = await this.authorizeConnector(dto.connectorId, dto.registrationToken);
    const recorder = await this.recorders.findOne({ where: { id: dto.recorderId, connectorId: connector.id, organizationId: connector.organizationId } });
    if (!recorder) throw new NotFoundException('Recorder not found for this connector');
    return { status: 'CHANNEL_DISCOVERY_UNAVAILABLE', retryable: true, supportRecommended: true, channels: [], message: 'Recorder channel enumeration requires the Sentira Edge Connector implementation.' };
  }

  async createConnectorCommand(user: CurrentUserDto, dto: CreateConnectorCommandDto & { connectorId: string }) {
    const connector = await this.connectors.findOne({ where: { id: dto.connectorId, organizationId: user.organizationId } });
    if (!connector) throw new NotFoundException('Connector not found');
    if (connector.id !== dto.connectorId) throw new NotFoundException('Connector not found');
    if (connector.status === 'disabled') throw new UnauthorizedException('Connector is disabled');
    const now = new Date();
    const expiresAt = new Date(now.getTime() + (dto.expiresInSeconds ?? 300) * 1000);
    const idempotencyKey = dto.idempotencyKey || `${dto.connectorId}:${dto.commandType}:${dto.correlationId || now.toISOString()}`;
    const duplicates = await this.commands.findOne({ where: { idempotencyKey, connectorId: dto.connectorId, organizationId: user.organizationId } });
    if (duplicates) return { ...duplicates, status: duplicates.status, idempotencyKey };
    const command = this.commands.create({
      organizationId: user.organizationId,
      connectorId: dto.connectorId,
      commandType: dto.commandType as CctvConnectorCommand['commandType'],
      status: 'QUEUED',
      payload: this.sanitize(dto.payload || {}) as Record<string, unknown>,
      result: {},
      errorCode: null,
      errorMessage: null,
      queuedAt: now,
      startedAt: null,
      completedAt: null,
      expiresAt,
      attemptCount: 0,
      maxAttempts: dto.maxAttempts ?? 1,
      correlationId: dto.correlationId ?? null,
      idempotencyKey,
      commandVersion: 1,
      leaseUntil: null,
    });
    const saved = await this.commands.save(command);
    await this.recordAudit(user, 'cctv.command.created', saved.id, { commandType: saved.commandType, status: saved.status, connectorId: saved.connectorId });
    return saved;
  }

  async getConnectorCommandsForPolling(connectorId: string, registrationToken: string, limit = 5, wait = 0) {
    const connector = await this.authorizeConnector(connectorId, registrationToken);
    const maxLimit = Math.min(Math.max(1, Number(limit) || 5), 20);
    const maxWait = Math.min(Math.max(0, Number(wait) || 0), 20);
    const now = new Date();
    const pending = (await this.commands.find({
      where: {
        connectorId,
        organizationId: connector.organizationId,
        status: 'QUEUED',
      },
      order: { createdAt: 'ASC' },
      take: maxLimit,
    })) || [];
    const due = pending.filter((item) => !item.expiresAt || item.expiresAt > now);
    const results = await Promise.all(due.map(async (item) => {
      if (item.maxAttempts && item.attemptCount >= item.maxAttempts) {
        item.status = 'FAILED';
        item.errorCode = 'MAX_ATTEMPTS_EXCEEDED';
        item.errorMessage = 'Connector exceeded the configured delivery attempts';
        item.completedAt = now;
        await this.commands.save(item);
        return item;
      }
      item.status = 'DELIVERED';
      item.queuedAt = item.queuedAt || now;
      item.attemptCount = (item.attemptCount || 0) + 1;
      await this.commands.save(item);
      return item;
    }));
    if (maxWait > 0 && results.length === 0) {
      return [];
    }
    return results.slice(0, maxLimit);
  }

  async acknowledgeConnectorCommand(connectorId: string, registrationToken: string, commandId: string) {
    const connector = await this.authorizeConnector(connectorId, registrationToken);
    const command = await this.commands.findOne({ where: { id: commandId, connectorId, organizationId: connector.organizationId } });
    if (!command) throw new NotFoundException('Command not found');
    if (command.status === 'EXPIRED' || (command.expiresAt && command.expiresAt < new Date())) {
      command.status = 'EXPIRED';
      await this.commands.save(command);
      throw new BadRequestException('Command expired');
    }
    if (command.status === 'QUEUED' || command.status === 'DELIVERED') {
      command.status = 'ACKNOWLEDGED';
      command.startedAt = command.startedAt || new Date();
      await this.commands.save(command);
    }
    return command;
  }

  async reportConnectorCommandResult(connectorId: string, registrationToken: string, commandId: string, dto: Partial<ReportConnectorCommandResultDto>) {
    const connector = await this.authorizeConnector(connectorId, registrationToken);
    const command = await this.commands.findOne({ where: { id: commandId } });
    if (!command) throw new NotFoundException('Command not found');
    if (command.organizationId !== connector.organizationId || command.connectorId !== connectorId) throw new UnauthorizedException('Command does not belong to this connector');
    if (command.expiresAt && command.expiresAt < new Date()) {
      command.status = 'EXPIRED';
      await this.commands.save(command);
      throw new BadRequestException('Command expired');
    }
    const status = (dto.status || 'FAILED') as string;
    command.status = status as CctvConnectorCommand['status'];
    command.result = this.sanitize((dto.result || {}) as Record<string, unknown>) as Record<string, unknown>;
    command.errorCode = dto.errorCode || null;
    command.errorMessage = dto.errorMessage || null;
    command.startedAt = command.startedAt || new Date();
    command.completedAt = new Date();
    await this.commands.save(command);
    return command;
  }

  async cancelConnectorCommand(connectorId: string, registrationToken: string, commandId: string) {
    const connector = await this.authorizeConnector(connectorId, registrationToken);
    const command = await this.commands.findOne({ where: { id: commandId, connectorId, organizationId: connector.organizationId } });
    if (!command) throw new NotFoundException('Command not found');
    command.status = 'CANCELLED';
    await this.commands.save(command);
    return command;
  }

  async reportDiscoveryResults(dto: ReportDiscoveryResultsDto) {
    const connector = await this.authorizeConnector(dto.connectorId, dto.registrationToken);
    const session = await this.sessions.findOne({ where: { id: dto.setupSessionId, connectorId: connector.id, organizationId: connector.organizationId } });
    if (!session) throw new NotFoundException('Setup session is not paired with this connector');
    const results = dto.results.slice(0, 64).map((result) => this.discovered.create({
      organizationId: connector.organizationId,
      connectorId: connector.id,
      name: result.name,
      manufacturer: result.manufacturer,
      model: result.model,
      localAddress: result.localAddress,
      protocol: result.protocol,
      capabilities: this.sanitize(result.capabilities || {}),
      discoveryStatus: result.discoveryStatus === 'UNSUPPORTED' ? 'unsupported' : 'ready',
      discoveredAt: new Date(),
    }));
    const saved = results.length ? await this.discovered.save(results) : [];
    session.stage = 'CONNECT';
    session.status = 'IN_PROGRESS';
    session.completionPercent = 60;
    await this.sessions.save(session);
    return { status: 'DISCOVERY_REPORTED', count: saved.length, cameras: saved.map((camera) => ({ id: camera.id, name: camera.name, manufacturer: camera.manufacturer, model: camera.model, protocol: camera.protocol, discoveryStatus: camera.discoveryStatus })) };
  }

  private async authorizeConnector(id: string, token: string) {
    const connector = await this.connectors.findOne({ where: { id } });
    if (!connector || connector.status === 'disabled' || !connector.registrationTokenHash || connector.registrationTokenHash !== this.hash(token)) throw new UnauthorizedException('Invalid connector credentials');
    return connector;
  }

  async getSession(user: CurrentUserDto, id: string) {
    const session = await this.sessions.findOne({ where: { id, organizationId: user.organizationId } });
    if (!session) throw new NotFoundException('CCTV setup session not found');
    return session;
  }

  async getActiveSession(user: CurrentUserDto) {
    return this.sessions.findOne({
      where: [
        { organizationId: user.organizationId, userId: user.id, status: 'STARTED' },
        { organizationId: user.organizationId, userId: user.id, status: 'IN_PROGRESS' },
        { organizationId: user.organizationId, userId: user.id, status: 'PAUSED' },
        { organizationId: user.organizationId, userId: user.id, status: 'SUPPORT_REQUESTED' },
      ],
      order: { updatedAt: 'DESC' },
    });
  }

  async updateSession(user: CurrentUserDto, id: string, dto: UpdateSetupSessionDto) {
    const session = await this.getSession(user, id);
    if (dto.siteId) await this.assertSite(dto.siteId, user.organizationId);
    if (dto.modelId) {
      const model = await this.models.findOne({ where: { id: dto.modelId, active: true } });
      if (!model) throw new NotFoundException('CCTV model not found');
      if (dto.manufacturerId && model.manufacturerId !== dto.manufacturerId) throw new BadRequestException('Model does not belong to the selected manufacturer');
    }
    Object.assign(session, {
      ...(dto.deviceType !== undefined ? { deviceType: dto.deviceType } : {}),
      ...(dto.siteId !== undefined ? { siteId: dto.siteId } : {}),
      ...(dto.manufacturerId !== undefined ? { manufacturerId: dto.manufacturerId } : {}),
      ...(dto.modelId !== undefined ? { modelId: dto.modelId } : {}),
      ...(dto.guideId !== undefined ? { guideId: dto.guideId } : {}),
      ...(dto.currentStep !== undefined ? { currentStep: dto.currentStep } : {}),
      ...(dto.answers !== undefined ? { answers: this.sanitize(dto.answers) } : {}),
    });
    if (session.status === 'STARTED') session.status = 'IN_PROGRESS';
    const progress: Record<string, { stage: CctvSetupSession['stage']; percent: number }> = {
      'viewing-method': { stage: 'FIND', percent: 20 },
      manufacturer: { stage: 'IDENTIFY', percent: 35 },
      model: { stage: 'IDENTIFY', percent: 50 },
      guide: { stage: 'CONNECT', percent: 65 },
      test: { stage: 'TEST', percent: 80 },
    };
    const next = dto.currentStep ? progress[dto.currentStep] : undefined;
    if (next) { session.stage = next.stage; session.completionPercent = next.percent; }
    const saved = await this.sessions.save(session);
    await this.recordAudit(user, 'cctv.setup.updated', id, { stage: saved.stage, completionPercent: saved.completionPercent });
    return saved;
  }

  async testSession(user: CurrentUserDto, id: string, dto: TestSetupSessionDto) {
    const session = await this.getSession(user, id);
    let result: Record<string, unknown>;
    if (dto.streamUrl) {
      const connector = dto.protocol === 'onvif' ? this.onvif : this.rtsp;
      result = await connector.testStream({ streamUrl: dto.streamUrl, username: dto.username, password: dto.password, timeoutMs: 5000 });
      session.testResult = { ...this.sanitize(result), endpointFingerprint: this.endpointFingerprint(dto.streamUrl) };
    } else if (dto.cameraId) {
      const camera = await this.cameras.findOne({ where: { id: dto.cameraId, organizationId: user.organizationId } });
      if (!camera) throw new NotFoundException('Camera not found');
      result = camera.status === 'online'
        ? { status: 'VERIFIED_CONNECTED', message: 'Video is currently available.', retryable: true, supportRecommended: false, protocol: camera.protocol, durationMs: 0 }
        : { status: camera.sourceType === 'connector' ? 'CONNECTOR_REQUIRED' : 'NETWORK_UNREACHABLE', message: 'Sentira could not confirm a live video connection.', retryable: true, supportRecommended: camera.sourceType !== 'connector' };
      session.testResult = { ...result, cameraId: camera.id, checkedAt: new Date().toISOString() };
    } else {
      result = { status: 'FAILED', failureCode: 'SETUP_INCOMPLETE', message: 'Finish the connection details before testing this camera.', retryable: true, supportRecommended: false };
      session.testResult = { ...result, checkedAt: new Date().toISOString() };
    }
    session.stage = 'TEST';
    session.status = result.status === 'VERIFIED_CONNECTED' ? 'VERIFIED' : 'FAILED';
    await this.sessions.save(session);
    await this.tests.save(this.tests.create({ organizationId: user.organizationId, setupSessionId: session.id, cameraId: dto.cameraId, connectorType: dto.streamUrl ? 'generic-rtsp' : 'existing-camera', protocol: String(result.protocol || dto.protocol || 'unknown'), status: result.status === 'VERIFIED_CONNECTED' ? 'VERIFIED_CONNECTED' : 'FAILED', failureCode: result.failureCode as string, diagnostics: this.sanitize(result), durationMs: Number(result.durationMs || 0) }));
    return result;
  }

  async listTests(user: CurrentUserDto, id: string) {
    await this.getSession(user, id);
    return this.tests.find({ where: { organizationId: user.organizationId, setupSessionId: id }, order: { createdAt: 'DESC' } });
  }

  async completeSession(user: CurrentUserDto, id: string, cameraId: string) {
    const session = await this.getSession(user, id);
    if (!session.testResult || session.status !== 'VERIFIED' || session.testResult.status !== 'VERIFIED_CONNECTED') throw new BadRequestException('A verified camera connection is required before completing setup');
    const camera = await this.cameras.findOne({ where: { id: cameraId, organizationId: user.organizationId } });
    if (!camera) throw new NotFoundException('Verified camera not found');
    if (session.testResult.endpointFingerprint && this.endpointFingerprint(camera.streamUrl || '') !== session.testResult.endpointFingerprint) throw new BadRequestException('The verified endpoint does not match this camera');
    session.status = 'COMPLETED'; session.stage = 'FINISH'; session.completionPercent = 100;
    const saved = await this.sessions.save(session);
    await this.recordAudit(user, 'cctv.setup.completed', id, { testStatus: session.testResult.status });
    return saved;
  }

  async createSupportRequest(user: CurrentUserDto, dto: CreateSupportRequestDto) {
    if (dto.siteId) await this.assertSite(dto.siteId, user.organizationId);
    if (dto.cameraId) {
      const camera = await this.cameras.findOne({ where: { id: dto.cameraId, organizationId: user.organizationId } });
      if (!camera) throw new NotFoundException('Camera not found');
    }
    if (dto.setupSessionId) await this.getSession(user, dto.setupSessionId);
    const request = await this.support.save(this.support.create({
      organizationId: user.organizationId,
      userId: user.id,
      setupSessionId: dto.setupSessionId,
      siteId: dto.siteId,
      cameraId: dto.cameraId,
      reason: dto.reason as CctvSupportRequest['reason'],
      priority: (dto.priority || 'NORMAL') as CctvSupportRequest['priority'],
      message: dto.message ? this.sanitizeText(dto.message) : undefined,
      context: this.sanitize(dto.context || {}),
    }));
    await this.recordAudit(user, 'cctv.support.requested', request.id, { reason: request.reason, setupSessionId: request.setupSessionId || null });
    return { id: request.id, status: request.status, priority: request.priority, reason: request.reason, createdAt: request.createdAt };
  }

  async listSupportRequests(user: CurrentUserDto) {
    return this.support.find({ where: { organizationId: user.organizationId }, order: { createdAt: 'DESC' } });
  }

  async createManufacturer(user: CurrentUserDto, dto: CreateManufacturerDto) { return this.adminWrite(user, 'cctv.manufacturer.created', this.manufacturers, dto); }
  async createModel(user: CurrentUserDto, dto: CreateModelDto) {
    const manufacturer = await this.manufacturers.findOne({ where: { id: dto.manufacturerId, active: true } });
    if (!manufacturer) throw new NotFoundException('Manufacturer not found');
    return this.adminWrite(user, 'cctv.model.created', this.models, dto);
  }
  async createGuide(user: CurrentUserDto, dto: CreateGuideDto) { return this.adminWrite(user, 'cctv.guide.created', this.guides, dto); }

  private async adminWrite<T extends object>(user: CurrentUserDto, action: string, repository: Repository<T>, dto: object) {
    const saved = await repository.save(repository.create(dto as T));
    await this.recordAudit(user, action, (saved as any).id, { id: (saved as any).id });
    return saved;
  }

  private async assertSite(id: string, organizationId: string) {
    const site = await this.sites.findOne({ where: { id, organizationId } });
    if (!site) throw new NotFoundException('Site not found');
  }

  private sanitize(value: Record<string, unknown>): Record<string, unknown> {
    const blocked = /password|token|secret|private.?key|authorization|credential/i;
    return Object.fromEntries(Object.entries(value).filter(([key]) => !blocked.test(key)).map(([key, entry]) => [key, Array.isArray(entry) ? entry.map((item) => typeof item === 'object' && item !== null ? this.sanitize(item as Record<string, unknown>) : typeof item === 'string' ? this.sanitizeText(item) : item) : typeof entry === 'object' && entry !== null ? this.sanitize(entry as Record<string, unknown>) : typeof entry === 'string' ? this.sanitizeText(entry) : entry]));
  }

  private sanitizeText(value: string): string {
    return value.replace(/(password|token|secret|authorization|credential)\s*[:=]\s*[^\s,;]+/gi, '$1=[redacted]');
  }

  private endpointFingerprint(value: string): string {
    try {
      const url = new URL(value);
      url.username = '';
      url.password = '';
      return createHash('sha256').update(url.toString()).digest('hex');
    } catch {
      return createHash('sha256').update(value).digest('hex');
    }
  }

  private async recordAudit(user: CurrentUserDto, action: string, resourceId: string, data: Record<string, unknown>) {
    await this.audit.save(this.audit.create({ organizationId: user.organizationId, userId: user.id, action, resourceType: 'cctv', resourceId, newValueJson: this.sanitize(data) }));
  }
}

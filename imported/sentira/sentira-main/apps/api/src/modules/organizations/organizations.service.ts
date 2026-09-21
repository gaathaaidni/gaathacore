import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { MoreThan, Repository } from 'typeorm';
import { Organization } from '../../entities/organization.entity';
import { Site } from '../../entities/site.entity';
import { Event } from '../../entities/event.entity';
import { Camera } from '../../entities/camera.entity';
import { Rule } from '../../entities/rule.entity';
import { CreateOrganizationDto, CreateSiteDto } from './dto/index';

@Injectable()
export class OrganizationsService {
  constructor(
    @InjectRepository(Organization)
    private organizationsRepository: Repository<Organization>,
    @InjectRepository(Site)
    private sitesRepository: Repository<Site>,
    @InjectRepository(Event)
    private eventsRepository: Repository<Event>,
    @InjectRepository(Camera)
    private camerasRepository: Repository<Camera>,
    @InjectRepository(Rule)
    private rulesRepository: Repository<Rule>,
  ) {}

  async create(createOrgDto: CreateOrganizationDto): Promise<Organization> {
    const newOrg = this.organizationsRepository.create(createOrgDto);
    return this.organizationsRepository.save(newOrg);
  }

  async findById(id: string): Promise<Organization | null> {
    return this.organizationsRepository.findOne({ where: { id } });
  }

  async findAll(): Promise<Organization[]> {
    return this.organizationsRepository.find();
  }

  async getSites(organizationId: string): Promise<Site[]> {
    return this.sitesRepository.find({ where: { organizationId } });
  }

  async createSite(
    organizationId: string,
    createSiteDto: CreateSiteDto,
  ): Promise<Site> {
    const site = this.sitesRepository.create({ ...createSiteDto, organizationId });
    return this.sitesRepository.save(site);
  }

  async getDashboardStats(organizationId: string) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const [cameras, eventsToday, unresolvedEvents, activeRules] =
      await Promise.all([
        this.camerasRepository.findAndCount({ where: { organizationId } }),
        this.eventsRepository.count({
          where: { organizationId, createdAt: MoreThan(today) },
        }),
        this.eventsRepository.count({ where: { organizationId, status: 'new' } }),
        this.rulesRepository.count({ where: { organizationId, isActive: true } }),
      ]);

    const [cameraItems, totalCameras] = cameras;
    const onlineCameras = cameraItems.filter((c) => c.status === 'online').length;

    return {
      cameras: {
        total: totalCameras,
        online: onlineCameras,
        offline: totalCameras - onlineCameras,
      },
      events: { today: eventsToday, unresolved: unresolvedEvents },
      rules: { active: activeRules },
    };
  }
}

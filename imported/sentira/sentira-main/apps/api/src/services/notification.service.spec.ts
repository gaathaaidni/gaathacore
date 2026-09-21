import { Test, TestingModule } from '@nestjs/testing';
import { NotificationService } from './notification.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Notification } from '../entities/notification.entity';

describe('NotificationService', () => {
  let service: NotificationService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        NotificationService,
        {
          provide: getRepositoryToken(Notification),
          useValue: {
            save: jest.fn().mockResolvedValue({
              id: 'test-id',
              organizationId: 'org-id',
              channel: 'in_app',
              status: 'sent',
            }),
          },
        },
      ],
    }).compile();

    service = module.get<NotificationService>(NotificationService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should send notification', async () => {
    const result = await service.notify({
      organizationId: 'org-id',
      eventId: 'event-id',
      channel: 'in_app',
      priority: 'high',
      message: 'Test notification',
    });

    expect(result).toBeDefined();
    expect(result.status).toBe('sent');
  });
});

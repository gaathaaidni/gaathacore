import { Test, TestingModule } from '@nestjs/testing';
import { AppController } from './app.controller';
import { AppService } from './app.service';

describe('AppController', () => {
  let appController: AppController;

  beforeEach(async () => {
    const app: TestingModule = await Test.createTestingModule({
      controllers: [AppController],
      providers: [AppService, { provide: require('./services/health.service').HealthService, useValue: { getSystemHealth: jest.fn().mockResolvedValue([]) } }],
    }).compile();

    appController = app.get<AppController>(AppController);
  });

  it('should return health status', () => {
    expect(appController.getHealth()).toMatchObject({
      status: 'ok',
      name: 'Sentira AI API',
    });
    expect(appController.getApiHealth()).toMatchObject({
      status: 'ok',
      name: 'Sentira AI API',
    });
  });

  it('should return ready status', () => {
    expect(appController.getReady()).toMatchObject({
      status: 'ready',
    });
  });
});

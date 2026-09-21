import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHealth() {
    return {
      status: 'ok',
      name: 'Sentira AI API',
      timestamp: new Date().toISOString(),
    };
  }

  getVersionedHealth() {
    return {
      service: 'sentira-api',
      status: 'healthy',
      dependencies: { database: 'unknown' },
    };
  }

  getReady() {
    return {
      status: 'ready',
      features: ['auth', 'multi-tenancy', 'camera-management', 'rule-engine', 'event-service'],
      timestamp: new Date().toISOString(),
    };
  }
}

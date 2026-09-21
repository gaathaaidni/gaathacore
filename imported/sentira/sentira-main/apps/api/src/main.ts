import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';
import { randomUUID } from 'crypto';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.enableCors({ origin: (process.env.CORS_ORIGINS || 'http://localhost:3000').split(','), credentials: false });
  app.use((req: any, res: any, next: any) => { const correlationId = req.headers['x-correlation-id'] || randomUUID(); req.correlationId = correlationId; res.setHeader('x-correlation-id', correlationId); next(); });
  app.useGlobalPipes(new ValidationPipe({ transform: true, whitelist: true }));
  await app.listen(process.env.API_PORT || 4000);
}

bootstrap();

import { TypeOrmModuleOptions } from '@nestjs/typeorm';
import { join } from 'path';

export const databaseConfig = (): TypeOrmModuleOptions => ({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  username: process.env.DB_USER || 'sentira',
  password: process.env.DB_PASSWORD || (process.env.NODE_ENV === 'production' ? undefined : 'sentira_dev_password'),
  database: process.env.DB_NAME || 'sentira',
  // `__dirname` is src/config in development and dist/config in containers.
  entities: [join(__dirname, '..', 'entities', '**', '*.entity.{js,ts}')],
  migrations: [join(__dirname, '..', 'database', 'migrations', '*.{js,ts}')],
  migrationsRun: true,
  synchronize: false,
  logging: process.env.NODE_ENV !== 'production',
  ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: process.env.DB_SSL_REJECT_UNAUTHORIZED !== 'false' } : undefined,
});

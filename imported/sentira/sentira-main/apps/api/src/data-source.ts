import { DataSource } from 'typeorm';
import { databaseConfig } from './config/database.config';

/** TypeORM CLI entrypoint.  Application startup continues to use the same config. */
export default new DataSource(databaseConfig() as any);

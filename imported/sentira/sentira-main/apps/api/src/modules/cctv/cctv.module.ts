import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuditLog, Camera, CctvConnectionTest, CctvConnectorCommand, CctvManufacturer, CctvModel, CctvRecorder, CctvRecorderChannel, CctvSetupGuide, CctvSetupSession, CctvSupportRequest, Connector, DiscoveredCamera, Role, Site } from '../../entities';
import { CctvController } from './cctv.controller';
import { CctvService } from './cctv.service';
import { GenericRtspConnector } from './connectors/generic-rtsp.connector';
import { OnvifConnector } from './connectors/onvif.connector';

@Module({
  imports: [TypeOrmModule.forFeature([AuditLog, Camera, CctvConnectionTest, CctvConnectorCommand, CctvManufacturer, CctvModel, CctvRecorder, CctvRecorderChannel, CctvSetupGuide, CctvSetupSession, CctvSupportRequest, Connector, DiscoveredCamera, Role, Site])],
  controllers: [CctvController],
  providers: [CctvService, GenericRtspConnector, OnvifConnector],
})
export class CctvModule {}

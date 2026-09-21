import {
  WebSocketGateway,
  WebSocketServer,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
  SubscribeMessage,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger, UseGuards } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { CurrentUserDto } from './auth/auth.dto';
import { Event } from './entities';
import { getJwtSecret } from './config/jwt-secret';

const jwtSecret = getJwtSecret();

@WebSocketGateway({
  cors: {
    origin: (process.env.CORS_ORIGINS || 'http://localhost:3000').split(',').map((origin) => origin.trim()),
    credentials: true,
  },
  namespace: '/',
})
export class EventsGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer() server: Server;
  private logger: Logger = new Logger('EventsGateway');

  constructor(private jwtService: JwtService) {}

  afterInit(server: Server) {
    server.use((socket, next) => {
      try {
        const token = socket.handshake.auth?.token;
        if (!token) {
          return next(new Error('Authentication token not provided'));
        }

        const payload: CurrentUserDto = this.jwtService.verify(token, {
          secret: jwtSecret,
        });

        if (!payload.organizationId) {
          return next(new Error('Invalid token: organizationId missing'));
        }

        socket.data.organizationId = payload.organizationId;
        socket.data.user = payload;
        return next();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'Unknown authentication error';
        this.logger.error(`Authentication failed for client ${socket.id}: ${message}`);
        return next(new Error(message));
      }
    });
    this.logger.log('WebSocket Gateway Initialized');
  }

  async handleConnection(client: Socket, ...args: any[]) {
    const organizationId = client.data.organizationId as string | undefined;
    if (!organizationId) {
      this.logger.error(`Client ${client.id} connected without organization context`);
      client.disconnect(true);
      return;
    }

    const room = `organization:${organizationId}`;
    client.join(room);
    this.logger.log(`Client ${client.id} connected and joined room ${room}`);
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
  }

  /**
   * Broadcasts a new event to the appropriate organization room.
   * @param event The event entity that was created.
   */
  broadcastEventCreated(event: Event) {
    const room = `organization:${event.organizationId}`;
    this.server.to(room).emit('event.created', event);
    this.logger.log(`Broadcasted event.created ${event.id} to room ${room}`);
  }

  broadcastNotificationCreated(notification: { organizationId: string; id: string; status: string }) {
    this.server.to(`organization:${notification.organizationId}`).emit('notification.created', notification);
  }

  broadcastCameraStatus(camera: { organizationId: string; id: string; status: string; aiProcessingStatus: string }) {
    this.server.to(`organization:${camera.organizationId}`).emit('camera.status', {
      id: camera.id,
      status: camera.status,
      aiProcessingStatus: camera.aiProcessingStatus,
    });
  }
}
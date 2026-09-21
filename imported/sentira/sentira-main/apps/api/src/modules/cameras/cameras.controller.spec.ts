import { ForbiddenException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { CamerasController } from './cameras.controller';
import { CamerasService } from './cameras.service';

describe('CamerasController', () => {
  const camerasService = {
    findAllInternal: jest.fn(),
  } as unknown as CamerasService;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns internal camera configurations when the internal token is valid', async () => {
    const controller = new CamerasController(camerasService, {
      get: jest.fn().mockReturnValue('stream-gateway-token'),
    } as unknown as ConfigService);
    const cameras = [{ id: 'camera-1' }];
    jest.mocked(camerasService.findAllInternal).mockResolvedValue(cameras as never);

    await expect(controller.findAllInternal('stream-gateway-token')).resolves.toEqual(cameras);
    expect(camerasService.findAllInternal).toHaveBeenCalledTimes(1);
  });

  it('rejects requests with a missing or invalid internal token', async () => {
    const controller = new CamerasController(camerasService, {
      get: jest.fn().mockReturnValue('stream-gateway-token'),
    } as unknown as ConfigService);

    await expect(controller.findAllInternal()).rejects.toBeInstanceOf(ForbiddenException);
    await expect(controller.findAllInternal('incorrect-token')).rejects.toBeInstanceOf(ForbiddenException);
    expect(camerasService.findAllInternal).not.toHaveBeenCalled();
  });

  it('rejects requests when the internal token is not configured', async () => {
    const controller = new CamerasController(camerasService, {
      get: jest.fn().mockReturnValue(undefined),
    } as unknown as ConfigService);

    await expect(controller.findAllInternal()).rejects.toBeInstanceOf(ForbiddenException);
  });
});

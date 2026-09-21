import { Test, TestingModule } from '@nestjs/testing';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';

describe('AuthController', () => {
  let controller: AuthController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [AuthController],
      providers: [{ provide: AuthService, useValue: { login: jest.fn().mockResolvedValue({ accessToken: 'access', refreshToken: 'refresh', user: { email: 'ops@sentira.ai' } }) } }],
    }).compile();

    controller = module.get<AuthController>(AuthController);
  });

  it('delegates credential validation and token issuance', async () => {
    const result = await controller.login({ email: 'ops@sentira.ai', password: 'StrongPass@123' }, { ip: '127.0.0.1', headers: {} });

    expect(result.accessToken).toBe('access');
    expect(result.user.email).toBe('ops@sentira.ai');
  });
});

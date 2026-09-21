import { canCreateCamera, CameraEntitlementService } from './camera-entitlement.service';
import { CAMERA_LIMIT_REACHED, CAMERA_LIMIT_MESSAGE } from '../../common/entitlements';

describe('camera entitlement', () => {
  it.each([[0, true], [1, true], [2, true], [3, false], [4, false]])('camera count %s with a limit of 3 is allowed=%s', (count, expected) => {
    expect(canCreateCamera(count, 3)).toBe(expected);
  });

  it('returns the stable limit error when the organization is full', async () => {
    const service = new CameraEntitlementService({} as any, { transaction: async (callback: any) => callback({ getRepository: (entity: string) => entity === 'cameras' ? { count: async () => 3 } : { findOne: async () => ({ cameraLimit: 3 }) } }) } as any);
    await expect(service.withCameraSlot('org-id', async () => undefined)).rejects.toMatchObject({ response: { code: CAMERA_LIMIT_REACHED, message: CAMERA_LIMIT_MESSAGE } });
  });
});
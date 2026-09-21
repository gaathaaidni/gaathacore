import { Phase7EnterpriseService } from './phase7-enterprise.service';

describe('Phase 7 enterprise intelligence', () => {
  it('creates verifiable evidence integrity metadata', () => {
    const svc = new Phase7EnterpriseService();
    const record = svc.createEvidenceIntegrity({ bytes: Buffer.from('sentira'), mediaType: 'video/mp4', cameraId: 'cam', eventId: 'evt', width: 1920, height: 1080, frameRate: 25, durationSeconds: 12, createdAt: new Date(0) });
    // Verified independently with `sha256sum` / Node's crypto implementation.
    expect(record.sha256).toBe('b94a8cabbc9024f9471f430511363ebf2e2ddfc513beb988d030251a61c4d29c');
    expect(record.resolution).toBe('1920x1080');
  });

  it('hashes the exact evidence bytes rather than a string representation', () => {
    const svc = new Phase7EnterpriseService();
    expect(svc.createEvidenceIntegrity({ bytes: Buffer.from([0, 255, 1]), mediaType: 'image/jpeg', cameraId: 'cam', eventId: 'evt' }).sha256)
      .toBe('47ffa3ea45a70b8a41c2c0825df323c00a8b7a01c1ea06083cc41dddcc001123');
  });

  it('classifies camera states by usable stream health, not process existence', () => {
    const svc = new Phase7EnterpriseService();
    expect(svc.classifyCameraHealth({ enabled: true, connected: false }).state).toBe('OFFLINE');
    expect(svc.classifyCameraHealth({ enabled: true, connected: true, staleFrameMs: 6000 }).state).toBe('DEGRADED');
    expect(svc.classifyCameraHealth({ enabled: true, connected: true, fps: 25, expectedFps: 30 }).state).toBe('ONLINE');
  });

  it('suppresses repeated alerts while allowing later incidents', () => {
    const svc = new Phase7EnterpriseService();
    const scope = { organizationId: 'o', cameraId: 'c', ruleId: 'r', trackingKey: 't', severity: 'critical' as const };
    const policy = { cooldownSeconds: 20, duplicateWindowSeconds: 20, notificationLimit: 2, suppressionWindowSeconds: 60 };
    expect(svc.shouldAlert(scope, policy, 1000).allowed).toBe(true);
    expect(svc.shouldAlert(scope, policy, 2000).reason).toBe('cooldown');
    expect(svc.shouldAlert(scope, policy, 70000).allowed).toBe(true);
  });
});

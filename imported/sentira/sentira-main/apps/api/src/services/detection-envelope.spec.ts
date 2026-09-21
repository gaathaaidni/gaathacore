import { DetectionConsumerService } from './detection-consumer.service';
import { parseDetectionEnvelope } from './detection-envelope';

const envelope = { organizationId: 'org', siteId: 'site', cameraId: 'camera', timestamp: '2026-01-01T00:00:00.000Z', frameId: 'frame', model: 'deterministic', modelVersion: '1', processingTimeMs: 1, objects: [{ class_name: 'person', confidence: 0.9, bbox: [0, 0, 1, 1] }] };
describe('detection envelope', () => {
  it('preserves a normalized detection envelope', () => expect(parseDetectionEnvelope(envelope)).toMatchObject(envelope));
  it('rejects malformed object data before rule evaluation', () => expect(() => parseDetectionEnvelope({ ...envelope, objects: [{ class_name: 'person', confidence: 2, bbox: [] }] })).toThrow('Detection object is invalid'));
  it('rejects tenant-mismatched queue messages before processing', async () => {
    const processor = { process: jest.fn() };
    const service = new DetectionConsumerService(processor as any);
    const channel = { ack: jest.fn(), nack: jest.fn(), sendToQueue: jest.fn() };
    service['channel'] = channel;
    const message = { properties: { correlationId: 'corr-1', headers: { 'x-tenant-id': 'other-tenant' } }, content: Buffer.from(JSON.stringify(envelope)) };
    await service.handle(message as any);
    expect(processor.process).not.toHaveBeenCalled();
    expect(channel.nack).toHaveBeenCalledWith(message, false, false);
  });
  it('rejects queue messages that are missing tenant metadata', async () => {
    const processor = { process: jest.fn() };
    const service = new DetectionConsumerService(processor as any);
    const channel = { ack: jest.fn(), nack: jest.fn(), sendToQueue: jest.fn() };
    service['channel'] = channel;
    const message = { properties: { correlationId: 'corr-2', headers: {} }, content: Buffer.from(JSON.stringify(envelope)) };
    await service.handle(message as any);
    expect(processor.process).not.toHaveBeenCalled();
    expect(channel.nack).toHaveBeenCalledWith(message, false, false);
  });
});

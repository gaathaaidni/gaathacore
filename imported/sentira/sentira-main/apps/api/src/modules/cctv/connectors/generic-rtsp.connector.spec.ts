import { lookup } from 'dns/promises';

jest.mock('dns/promises', () => ({
  lookup: jest.fn(),
}));

import { GenericRtspConnector } from './generic-rtsp.connector';

describe('GenericRtspConnector', () => {
  const connector = new GenericRtspConnector();

  it('rejects embedded credentials instead of logging or using them', async () => {
    await expect(connector.testStream({ streamUrl: 'rtsp://user:secret@example.test/live', timeoutMs: 50 })).resolves.toEqual(expect.objectContaining({ status: 'FAILED', failureCode: 'INVALID_RTSP_URL' }));
  });

  it('requires local cameras to use the edge connector', async () => {
    await expect(connector.testStream({ streamUrl: 'rtsp://192.168.1.20/live', timeoutMs: 50 })).resolves.toEqual(expect.objectContaining({ status: 'FAILED', failureCode: 'DEVICE_UNREACHABLE' }));
  });

  it('forwards supplied RTSP credentials to the verification request', async () => {
    const lookupMock = lookup as jest.MockedFunction<typeof lookup>;
    lookupMock.mockResolvedValue([{ address: '8.8.8.8', family: 4, ttl: 60 }] as any);
    const optionsSpy = jest.spyOn(connector as any, 'options').mockResolvedValue(401);

    await expect(connector.testStream({ streamUrl: 'rtsp://camera.example.test/live', username: 'admin', password: 'secret', timeoutMs: 50 })).resolves.toEqual(expect.objectContaining({ status: 'FAILED', failureCode: 'AUTHENTICATION_FAILED' }));
    expect(lookupMock).toHaveBeenCalled();
    expect(optionsSpy).toHaveBeenCalledWith('8.8.8.8', 554, expect.any(URL), 50, 'admin', 'secret');
  });

  it('returns a deterministic unsupported-protocol capability result', async () => {
    await expect(connector.testStream({ streamUrl: 'http://camera.example.test/live', timeoutMs: 50 })).resolves.toEqual(expect.objectContaining({ status: 'FAILED', failureCode: 'INVALID_RTSP_URL' }));
  });
});

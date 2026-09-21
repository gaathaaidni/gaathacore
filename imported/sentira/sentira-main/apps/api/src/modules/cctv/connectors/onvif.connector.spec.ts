import { OnvifConnector } from './onvif.connector';

describe('OnvifConnector', () => {
  it('does not fake cloud discovery when an edge connector is unavailable', async () => {
    const result = await new OnvifConnector().testStream({ streamUrl: 'onvif://camera', timeoutMs: 1000 });
    expect(result).toEqual(expect.objectContaining({ status: 'FAILED', failureCode: 'DISCOVERY_UNAVAILABLE', protocol: 'ONVIF' }));
  });
});

import { Repository } from 'typeorm';
import { CctvManufacturer } from '../../../entities/cctv-manufacturer.entity';
import { CctvModel, CctvDeviceType } from '../../../entities/cctv-model.entity';
import { CctvSetupGuide, CctvGuideStepType } from '../../../entities/cctv-guide.entity';

type ProtocolStatus = 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNKNOWN' | 'NOT_SUPPORTED' | 'REQUIRES_ASSISTANCE';
type Protocol = { protocol: string; status: ProtocolStatus; verified: boolean; notes?: string };
type ManufacturerSeed = { slug: string; name: string; description: string; websiteUrl: string };
type ModelSeed = {
  manufacturer: string;
  slug: string;
  modelNumber: string;
  name: string;
  deviceType: CctvDeviceType;
  description: string;
  supportedProtocols: Protocol[];
  discoveryMethods: string[];
};
type GuideSeed = {
  manufacturer?: string;
  model?: string;
  title: string;
  description: string;
  prerequisites: string[];
  steps: Array<{ id: string; type: CctvGuideStepType; title: string; body: string; required?: boolean }>;
  troubleshooting: Array<{ condition: string; advice: string }>;
  estimatedMinutes?: number;
};

const protocol = (name: string, status: ProtocolStatus, notes?: string): Protocol => ({
  protocol: name,
  status,
  verified: false,
  ...(notes ? { notes } : {}),
});

export const CCTV_MANUFACTURERS: ManufacturerSeed[] = [
  { slug: 'hikvision', name: 'Hikvision', description: 'Professional cameras and recorders. Menus and protocol availability vary by model and firmware.', websiteUrl: 'https://www.hikvision.com' },
  { slug: 'dahua', name: 'Dahua', description: 'Professional cameras, NVRs, DVRs and XVRs. Confirm features against the exact device.', websiteUrl: 'https://www.dahuasecurity.com' },
  { slug: 'axis', name: 'Axis Communications', description: 'Network cameras and recording systems with model-dependent ONVIF and RTSP capabilities.', websiteUrl: 'https://www.axis.com' },
  { slug: 'hanwha-wisenet', name: 'Hanwha Vision / Wisenet', description: 'Professional IP cameras and recorders. Product and firmware capabilities vary.', websiteUrl: 'https://www.hanwhavision.com' },
  { slug: 'uniview-unv', name: 'Uniview / UNV', description: 'IP cameras and recorders for professional and SMB deployments.', websiteUrl: 'https://global.uniview.com' },
  { slug: 'bosch', name: 'Bosch', description: 'Professional video systems with model and firmware dependent integration options.', websiteUrl: 'https://www.boschsecurity.com' },
  { slug: 'sony', name: 'Sony', description: 'Network camera products with model-dependent integration options.', websiteUrl: 'https://pro.sony' },
  { slug: 'panasonic', name: 'Panasonic', description: 'Network cameras and recorders with model-dependent integration options.', websiteUrl: 'https://security.panasonic.com' },
  { slug: 'reolink', name: 'Reolink', description: 'Consumer and prosumer cameras. ONVIF and RTSP availability depends on device, model and firmware.', websiteUrl: 'https://reolink.com' },
  { slug: 'tp-link-vigi', name: 'TP-Link VIGI', description: 'SMB cameras and NVRs. Confirm ONVIF and RTSP support for the exact VIGI product.', websiteUrl: 'https://www.tp-link.com/business-networking/vigi/' },
  { slug: 'amcrest', name: 'Amcrest', description: 'SMB and prosumer cameras and recorders with common ONVIF and RTSP options.', websiteUrl: 'https://amcrest.com' },
  { slug: 'generic-onvif', name: 'Generic ONVIF', description: 'A standards-based path for compatible network cameras and recorders. Capabilities vary by vendor.', websiteUrl: 'https://www.onvif.org' },
  { slug: 'generic-rtsp', name: 'Generic RTSP', description: 'A direct stream path for devices that provide an RTSP URL. Stream format and authentication vary.', websiteUrl: '' },
];

export const CCTV_MODELS: ModelSeed[] = [
  { manufacturer: 'hikvision', slug: 'ip-camera', modelNumber: 'HIK-IP-CAMERA', name: 'Hikvision IP Camera', deviceType: 'IP_CAMERA', description: 'Hikvision network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'hikvision', slug: 'nvr', modelNumber: 'HIK-NVR', name: 'Hikvision NVR', deviceType: 'NVR', description: 'Hikvision network video recorder and channel-based deployment.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['NVR_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'hikvision', slug: 'dvr-xvr', modelNumber: 'HIK-DVR-XVR', name: 'Hikvision DVR/XVR', deviceType: 'XVR', description: 'Hikvision hybrid recorder for analog and network channels.', supportedProtocols: [protocol('RTSP', 'PARTIALLY_SUPPORTED'), protocol('ONVIF', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'RTSP'] },
  { manufacturer: 'dahua', slug: 'ip-camera', modelNumber: 'DAHUA-IP-CAMERA', name: 'Dahua IP Camera', deviceType: 'IP_CAMERA', description: 'Dahua network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'dahua', slug: 'nvr', modelNumber: 'DAHUA-NVR', name: 'Dahua NVR', deviceType: 'NVR', description: 'Dahua network video recorder and channel-based deployment.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['NVR_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'dahua', slug: 'xvr', modelNumber: 'DAHUA-XVR', name: 'Dahua XVR', deviceType: 'XVR', description: 'Dahua hybrid recorder for analog and network channels.', supportedProtocols: [protocol('RTSP', 'PARTIALLY_SUPPORTED'), protocol('ONVIF', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'RTSP'] },
  { manufacturer: 'axis', slug: 'network-camera', modelNumber: 'AXIS-NETWORK-CAMERA', name: 'Axis Network Camera', deviceType: 'IP_CAMERA', description: 'Axis network camera product family; exact capabilities are model dependent.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'axis', slug: 'camera-station-recorder', modelNumber: 'AXIS-CAMERA-STATION', name: 'Axis Camera Station / Recorder', deviceType: 'NVR', description: 'Axis recorder deployment for cameras managed through a recording system.', supportedProtocols: [protocol('RTSP', 'PARTIALLY_SUPPORTED'), protocol('ONVIF', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'hanwha-wisenet', slug: 'ip-camera', modelNumber: 'HANWHA-IP-CAMERA', name: 'Hanwha/Wisenet IP Camera', deviceType: 'IP_CAMERA', description: 'Hanwha Vision and Wisenet network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'hanwha-wisenet', slug: 'nvr', modelNumber: 'HANWHA-NVR', name: 'Hanwha/Wisenet NVR', deviceType: 'NVR', description: 'Hanwha Vision and Wisenet recorder product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'uniview-unv', slug: 'ip-camera', modelNumber: 'UNV-IP-CAMERA', name: 'UNV IP Camera', deviceType: 'IP_CAMERA', description: 'Uniview network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'uniview-unv', slug: 'nvr', modelNumber: 'UNV-NVR', name: 'UNV NVR', deviceType: 'NVR', description: 'Uniview network video recorder product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'reolink', slug: 'camera', modelNumber: 'REOLINK-CAMERA', name: 'Reolink Camera', deviceType: 'IP_CAMERA', description: 'Reolink camera family; protocol availability is device, model and firmware dependent.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'tp-link-vigi', slug: 'ip-camera', modelNumber: 'VIGI-IP-CAMERA', name: 'TP-Link VIGI IP Camera', deviceType: 'IP_CAMERA', description: 'VIGI network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'tp-link-vigi', slug: 'nvr', modelNumber: 'VIGI-NVR', name: 'TP-Link VIGI NVR', deviceType: 'NVR', description: 'VIGI network video recorder product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'ONVIF', 'RTSP'] },
  { manufacturer: 'amcrest', slug: 'camera', modelNumber: 'AMCREST-CAMERA', name: 'Amcrest Camera', deviceType: 'IP_CAMERA', description: 'Amcrest network camera product family.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF', 'RTSP'] },
  { manufacturer: 'generic-onvif', slug: 'camera', modelNumber: 'GENERIC-ONVIF-CAMERA', name: 'Generic ONVIF Camera', deviceType: 'IP_CAMERA', description: 'A network camera that exposes ONVIF services.', supportedProtocols: [protocol('ONVIF', 'SUPPORTED', 'Capabilities and ports vary by manufacturer.'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['ONVIF'] },
  { manufacturer: 'generic-onvif', slug: 'nvr-recorder', modelNumber: 'GENERIC-ONVIF-NVR', name: 'Generic ONVIF NVR/Recorder', deviceType: 'NVR', description: 'A recorder that exposes ONVIF or channel services.', supportedProtocols: [protocol('ONVIF', 'PARTIALLY_SUPPORTED'), protocol('RTSP', 'PARTIALLY_SUPPORTED')], discoveryMethods: ['RECORDER_CHANNELS', 'ONVIF'] },
  { manufacturer: 'generic-rtsp', slug: 'camera', modelNumber: 'GENERIC-RTSP-CAMERA', name: 'Generic RTSP Camera', deviceType: 'IP_CAMERA', description: 'A camera or encoder that provides a direct RTSP stream URL.', supportedProtocols: [protocol('RTSP', 'SUPPORTED', 'Port 554 is common but not required.')], discoveryMethods: ['RTSP'] },
];

const genericSteps = (kind: 'onvif' | 'rtsp' | 'recorder'): GuideSeed['steps'] => {
  if (kind === 'onvif') return [
    { id: 'reach', type: 'TEXT', title: 'Confirm network access', body: 'The camera must be reachable from the Sentira connector over the private LAN or VPN. Avoid exposing it directly to the public internet.', required: true },
    { id: 'address', type: 'INPUT', title: 'Find the device address', body: 'Record the camera IP or hostname and confirm the ONVIF service port. The port is manufacturer and firmware dependent.', required: true },
    { id: 'enable', type: 'TEXT', title: 'Enable ONVIF', body: 'Enable ONVIF in the device interface and create a dedicated integration user. Menu names vary by manufacturer and firmware.', required: true },
    { id: 'credentials', type: 'WARNING', title: 'Use dedicated credentials', body: 'Use least privilege where supported. Never use a default password, put credentials in frontend code, or share them in support messages.', required: true },
    { id: 'test', type: 'TEST', title: 'Run the Sentira connection test', body: 'Enter the address, ONVIF port and credentials in Sentira, then run the test. Discovery and capabilities vary by manufacturer.', required: true },
    { id: 'profiles', type: 'TEXT', title: 'Review profiles and stream', body: 'Sentira may discover media profiles and retrieve an RTSP URI. Verify the selected profile and live stream before completing onboarding.', required: true },
  ];
  if (kind === 'rtsp') return [
    { id: 'url', type: 'INPUT', title: 'Prepare the RTSP URL', body: 'Provide the vendor-documented URL including host, port and stream path. Port 554 is common, but it is not universal.', required: true },
    { id: 'network', type: 'TEXT', title: 'Confirm network access', body: 'The connector must reach the host and port over a private LAN or VPN. Check firewall rules without exposing the camera unnecessarily.', required: true },
    { id: 'auth', type: 'WARNING', title: 'Check authentication securely', body: 'Use a dedicated account where supported. Never use default passwords or log credentials. Sentira does not return passwords in API responses.', required: true },
    { id: 'codec', type: 'TEXT', title: 'Check stream compatibility', body: 'Confirm the codec, resolution and transport are compatible with your Sentira pipeline. Vendor URL and codec behavior are model dependent.', required: true },
    { id: 'test', type: 'TEST', title: 'Test and verify live video', body: 'Run the connection test, then verify that the intended live stream is available before completing onboarding.', required: true },
  ];
  return [
    { id: 'architecture', type: 'CHOICE', title: 'Identify the video source', body: 'Choose whether Sentira should connect directly to a camera or to the recorder. Many deployments use Camera -> NVR/DVR -> Sentira.', required: true },
    { id: 'recorder', type: 'INPUT', title: 'Prepare recorder details', body: 'Record the recorder IP or hostname, credentials, channel count and any ONVIF or RTSP settings. Use a dedicated least-privilege account.', required: true },
    { id: 'reach', type: 'TEXT', title: 'Confirm recorder access', body: 'The Sentira connector must reach the recorder over a private LAN or VPN. Do not expose cameras or recorders directly to the public internet unnecessarily.', required: true },
    { id: 'discover', type: 'TEST', title: 'Discover or map channels', body: 'Run the connection test and review discovered channels. If discovery is unavailable, map channels manually using the recorder documentation.', required: true },
    { id: 'verify', type: 'SUCCESS', title: 'Verify selected streams', body: 'Check the intended channel names and live streams, then complete onboarding. Recording storage remains distinct from Sentira evidence storage.', required: true },
  ];
};

const guide = (seed: Omit<GuideSeed, 'steps'> & { steps: GuideSeed['steps'] }): GuideSeed => seed;

export const CCTV_GUIDES: GuideSeed[] = [
  guide({ title: 'Connect a Generic ONVIF Camera', manufacturer: 'generic-onvif', model: 'camera', description: 'Guided setup for a network camera using ONVIF discovery, device information, media profiles and an RTSP stream where available.', prerequisites: ['Camera is powered and reachable on the private network or VPN', 'You know the camera IP or hostname', 'You can create or use a dedicated integration account'], steps: genericSteps('onvif'), troubleshooting: [{ condition: 'ONVIF discovery finds no device', advice: 'Check routing, firewall rules, the ONVIF service port, device time and whether ONVIF is enabled. Discovery varies by manufacturer.' }, { condition: 'Profiles are found but video fails', advice: 'Verify the selected profile, RTSP path, codec and account permissions in the vendor documentation.' }] }),
  guide({ title: 'Connect a Generic RTSP Camera', manufacturer: 'generic-rtsp', model: 'camera', description: 'Guided setup for a camera or encoder that provides a direct RTSP stream URL.', prerequisites: ['A vendor-documented RTSP URL', 'Network access from the Sentira connector', 'A dedicated stream account where supported'], steps: genericSteps('rtsp'), troubleshooting: [{ condition: 'Connection times out', advice: 'Confirm the host, port, route and firewall. Port 554 is common, not guaranteed.' }, { condition: 'Authentication or codec fails', advice: 'Check credentials, URL escaping, stream path and codec compatibility against the exact model.' }] }),
  guide({ title: 'Connect an NVR, DVR or XVR Recorder', manufacturer: 'generic-onvif', model: 'nvr-recorder', description: 'Choose the correct architecture when cameras are isolated behind a recorder and configure recorder channels for Sentira.', prerequisites: ['Recorder is powered and reachable', 'Recorder IP or hostname and integration credentials', 'Channel list and recorder documentation'], steps: genericSteps('recorder'), troubleshooting: [{ condition: 'Recorder connects but channels are missing', advice: 'Confirm channel permissions and manually map channels when vendor discovery is unavailable.' }, { condition: 'Camera is reachable but recorder is not', advice: 'Use the recorder as the integration point when cameras are isolated on its private network.' }] }),
];

const manufacturerGuideText = (name: string): GuideSeed => guide({ manufacturer: name, title: `${name} onboarding and protocol checklist`, description: `A manufacturer-level checklist for ${name}. Exact menu names, ports, stream paths and protocol behavior are model and firmware dependent.`, prerequisites: ['Exact model and firmware information', 'Device or recorder is reachable from the Sentira connector', 'Dedicated integration credentials; never use default passwords'], steps: [
  { id: 'identify', type: 'TEXT', title: 'Identify the device', body: 'Record the exact model, firmware and whether this is a direct camera, NVR, DVR/XVR or cloud-managed system.', required: true },
  { id: 'network', type: 'TEXT', title: 'Confirm private network access', body: 'Ensure the Sentira connector can reach the device. Prefer a private LAN or VPN and secure transport where supported.', required: true },
  { id: 'protocol', type: 'CHOICE', title: 'Choose the available protocol', body: 'Use ONVIF for discovery and profiles where supported, or RTSP for direct stream ingestion. Availability is model and firmware dependent.', required: true },
  { id: 'account', type: 'WARNING', title: 'Create an integration account', body: 'Use least privilege where supported. Never place credentials in frontend code, log passwords, or use default credentials.', required: true },
  { id: 'test', type: 'TEST', title: 'Test the connection', body: 'Enter the vendor-documented address, port and credentials, run the Sentira test, and investigate the returned diagnostics.', required: true },
  { id: 'verify', type: 'SUCCESS', title: 'Verify the intended stream or channels', body: 'Confirm live video and channel mapping before completing onboarding. Do not assume support solely from the manufacturer name.', required: true },
], troubleshooting: [{ condition: 'Menu or protocol option is missing', advice: 'Check exact model and firmware documentation. Do not assume another model or firmware UI path applies.' }, { condition: 'Device is cloud-only', advice: 'A vendor cloud account is not automatically a supported Sentira video source. Use a connector integration only where implemented.' }] });

for (const manufacturer of ['hikvision', 'dahua', 'axis', 'hanwha-wisenet', 'uniview-unv', 'bosch', 'sony', 'panasonic', 'reolink', 'tp-link-vigi', 'amcrest']) {
  CCTV_GUIDES.push(manufacturerGuideText(manufacturer));
}

for (const model of CCTV_MODELS) {
  CCTV_GUIDES.push(guide({
    manufacturer: model.manufacturer,
    model: model.slug,
    title: `${model.name} setup guide`,
    description: `Model-family guidance for ${model.name}. Exact ports, menu names, stream paths and capabilities are model and firmware dependent.`,
    prerequisites: ['Exact device model and firmware', 'Device is reachable from the Sentira connector', 'Dedicated integration credentials; never use default passwords'],
    steps: model.deviceType === 'NVR' || model.deviceType === 'DVR' || model.deviceType === 'XVR' ? genericSteps('recorder') : genericSteps('onvif'),
    troubleshooting: [{ condition: 'The documented protocol is unavailable', advice: 'Check the exact model and firmware documentation. Use RTSP only when the vendor provides a valid stream URL, and do not assume a catalog entry proves compatibility.' }, { condition: 'A stream or channel cannot be verified', advice: 'Confirm private network access, credentials, firewall rules, codec and channel permissions with the device administrator.' }],
  }));
}

export async function seedCctvCatalog(
  manufacturerRepo: Repository<CctvManufacturer>,
  modelRepo: Repository<CctvModel>,
  guideRepo: Repository<CctvSetupGuide>,
) {
  const manufacturers = new Map<string, CctvManufacturer>();
  for (const item of CCTV_MANUFACTURERS) {
    let record = await manufacturerRepo.findOne({ where: { slug: item.slug } });
    if (!record) record = await manufacturerRepo.save({ ...item, active: true });
    manufacturers.set(item.slug, record);
  }

  const models = new Map<string, CctvModel>();
  for (const item of CCTV_MODELS) {
    const manufacturer = manufacturers.get(item.manufacturer);
    if (!manufacturer) throw new Error(`CCTV catalog manufacturer missing: ${item.manufacturer}`);
    const key = `${item.manufacturer}:${item.slug}`;
    let record = await modelRepo.findOne({ where: { manufacturerId: manufacturer.id, slug: item.slug } });
    const { manufacturer: manufacturerSlug, ...modelData } = item;
    if (!record) record = await modelRepo.save({ ...modelData, manufacturerId: manufacturer.id });
    models.set(key, record);
  }

  for (const item of CCTV_GUIDES) {
    const manufacturer = item.manufacturer ? manufacturers.get(item.manufacturer) : undefined;
    const model = item.model && item.manufacturer ? models.get(`${item.manufacturer}:${item.model}`) : undefined;
    if (item.manufacturer && !manufacturer) throw new Error(`CCTV guide manufacturer missing: ${item.manufacturer}`);
    if (item.model && !model) throw new Error(`CCTV guide model missing: ${item.model}`);
    const where = { title: item.title, manufacturerId: manufacturer?.id ?? null, modelId: model?.id ?? null };
    const existing = await guideRepo.findOne({ where });
    const { manufacturer: manufacturerSlug, model: modelSlug, ...guideData } = item;
    if (!existing) await guideRepo.save({ ...guideData, manufacturerId: manufacturer?.id ?? null, modelId: model?.id ?? null, active: true, version: 1, verificationStatus: 'unverified' });
  }

  return { manufacturers: manufacturers.size, models: models.size, guides: CCTV_GUIDES.length };
}

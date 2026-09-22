import { DataSource } from 'typeorm';
import * as bcrypt from 'bcrypt';
import {
  Organization,
  Site,
  Role,
  User,
  Camera,
  Zone,
  Rule,
  RuleCondition,
  RuleAction,
  CctvManufacturer,
  CctvModel,
  CctvSetupGuide,
  LegalDocument,
} from '../entities';
import { seedCctvCatalog } from './seeds/cctv/catalog';
import { seedLegalDocuments } from './seeds/legal-documents';

export async function seedDatabase(dataSource: DataSource) {
  const orgRepo = dataSource.getRepository(Organization);
  const siteRepo = dataSource.getRepository(Site);
  const roleRepo = dataSource.getRepository(Role);
  const userRepo = dataSource.getRepository(User);
  const cameraRepo = dataSource.getRepository(Camera);
  const zoneRepo = dataSource.getRepository(Zone);
  const ruleRepo = dataSource.getRepository(Rule);
  const conditionRepo = dataSource.getRepository(RuleCondition);
  const actionRepo = dataSource.getRepository(RuleAction);
  const manufacturerRepo = dataSource.getRepository(CctvManufacturer);
  const modelRepo = dataSource.getRepository(CctvModel);
  const guideRepo = dataSource.getRepository(CctvSetupGuide);
  const legalDocumentRepo = dataSource.getRepository(LegalDocument);

  await seedCctvCatalog(manufacturerRepo, modelRepo, guideRepo);
  await seedLegalDocuments(legalDocumentRepo);

  const manufacturerNames = ['CP PLUS', 'Hikvision', 'Dahua', 'Uniview / UNV', 'Tapo', 'TP-Link', 'EZVIZ', 'Imou', 'Reolink', 'Xmeye-based systems', 'Other', "I don't know"];
  for (const name of manufacturerNames) {
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    if (!(await manufacturerRepo.findOneBy({ slug }))) await manufacturerRepo.save({ name, slug, description: 'Compatibility varies by model and firmware. Sentira will not assume support without verified information.', active: true });
  }
  if (!(await guideRepo.findOneBy({ title: 'Basic CCTV connection check' }))) {
    await guideRepo.save({
      title: 'Basic CCTV connection check',
      description: 'A simple checklist for identifying your CCTV system before Sentira asks for technical details.',
      difficulty: 'beginner',
      estimatedMinutes: 10,
      verificationStatus: 'unverified',
      prerequisites: ['Camera or recorder is powered on', 'You can open the app or screen you normally use'],
      steps: [
        { id: 'power', type: 'TEXT', title: 'Make sure your CCTV is switched on', body: 'Check that the camera or recorder has power and that you can normally view it.' },
        { id: 'view', type: 'CHOICE', title: 'Open the app or screen you normally use', body: 'This helps Sentira understand which setup path may be available.' },
        { id: 'help', type: 'TIP', title: 'It is okay not to know', body: 'If you cannot find a model or connection setting, choose “I do not know” and ask Sentira for help.' },
      ],
      troubleshooting: [{ condition: 'Camera works on phone but not Sentira', advice: 'The phone app may use a private cloud connection. Sentira may need local access or a connector.' }],
      active: true,
    });
  }

  // Create organization
  const org = await orgRepo.save({
    name: 'Demo Restaurant',
    legalName: 'Demo Restaurant Inc.',
    status: 'active',
  });

  // Create role
  const adminRole = await roleRepo.save({
    organizationId: org.id,
    name: 'Admin',
    description: 'Administrator role',
    permissions: {
      'system.admin': true,
      'analytics.view': true,
      'cameras:read': true,
      'cameras:write': true,
      'rules:read': true,
      'rules:write': true,
      'events:read': true,
      'events:write': true,
      'sites:read': true,
      'sites:write': true,
    },
  });

  // Create user
  const password = await bcrypt.hash('demo_password', 10);
  const user = await userRepo.save({
    organizationId: org.id,
    email: 'demo@example.com',
    passwordHash: password,
    firstName: 'Demo',
    lastName: 'User',
    roleId: adminRole.id,
    status: 'active',
  });

  // Create sites
  const diningArea = await siteRepo.save({
    organizationId: org.id,
    name: 'Main Location',
    address: '123 Restaurant Street',
    timezone: 'America/New_York',
    status: 'active',
  });

  // Create cameras
  const camera1 = await cameraRepo.save({
    organizationId: org.id,
    siteId: diningArea.id,
    name: 'Dining Area Camera',
    location: 'Dining Area',
    streamUrlEncrypted: 'encrypted_rtsp_url_1',
    protocol: 'rtsp',
    resolution: '1920x1080',
    fps: 30,
    status: 'online',
    isEnabled: true,
  });

  const camera2 = await cameraRepo.save({
    organizationId: org.id,
    siteId: diningArea.id,
    name: 'Kitchen Camera',
    location: 'Kitchen',
    streamUrlEncrypted: 'encrypted_rtsp_url_2',
    protocol: 'rtsp',
    resolution: '1920x1080',
    fps: 30,
    status: 'online',
    isEnabled: true,
  });

  // Create zones
  const diningZone = await zoneRepo.save({
    organizationId: org.id,
    cameraId: camera1.id,
    name: 'Table 01',
    zoneType: 'table',
    geometryJson: {
      type: 'polygon',
      points: [[0.1, 0.1], [0.3, 0.1], [0.3, 0.3], [0.1, 0.3]],
    },
  });

  const kitchenZone = await zoneRepo.save({
    organizationId: org.id,
    cameraId: camera2.id,
    name: 'Kitchen Area',
    zoneType: 'restricted',
    geometryJson: {
      type: 'polygon',
      points: [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
    },
  });

  // Create rule: Table unattended
  const tableUnattendedRule = await ruleRepo.save({
    organizationId: org.id,
    siteId: diningArea.id,
    cameraId: camera1.id,
    name: 'Table Unattended > 2 minutes',
    description: 'Alert when customer is at table without server attention',
    ruleType: 'table_service',
    status: 'active',
    confidenceThreshold: 0.8,
    isActive: true,
    createdBy: user.id,
    scheduleJson: {
      days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
      start: '08:00',
      end: '22:00',
    },
  });

  // Add conditions to rule
  await conditionRepo.save({
    ruleId: tableUnattendedRule.id,
    conditionType: 'presence',
    fieldName: 'person',
    operator: 'exists_for',
    valueJson: { duration: 120 },
    sequenceOrder: 1,
  });

  // Add actions to rule
  await actionRepo.save({
    ruleId: tableUnattendedRule.id,
    actionType: 'create_event',
    configJson: { severity: 'medium' },
  });

  await actionRepo.save({
    ruleId: tableUnattendedRule.id,
    actionType: 'save_video_clip',
    configJson: { preEventSeconds: 10, postEventSeconds: 10 },
  });

  console.log('✅ Demo database seeded successfully');
  return {
    organization: org,
    user,
    sites: [diningArea],
    cameras: [camera1, camera2],
    zones: [diningZone, kitchenZone],
    rules: [tableUnattendedRule],
  };
}

# Sentira AI - Master Prompt & Complete System Documentation

**Last Updated:** August 16, 2026  
**Status:** Production-Ready Phase 1 (Full Backend with Demo Pipeline)  
**Repository:** https://github.com/gaathaaidni/sentira

---

## Phase 10G status

Phase 10G verified the live Compose stack, migration cycle, RTSP-to-event path, and
refresh replay rejection. It remains not production ready until clip orchestration,
dependency probes, and tenant/WebSocket E2E are complete.

## 📋 Executive Summary

**Sentira AI** is an enterprise-grade AI-powered visual intelligence platform for operational monitoring, incident detection, and evidence-based investigation. The platform enables organizations to monitor multiple camera feeds, automatically detect incidents based on configurable rules, and provide incident management workflows for operators.

**Core Tagline:** "Cameras watch. Sentira understands. Sentira alerts. Humans decide."

**Product Name:** Sentira AI
**Company:** Gaatha Ventures  
**Developer:** Hardikkumar Gajjar

---

## 🏗️ Technical Architecture

### Tech Stack Overview

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Next.js | 14.2.15 |
| | React | 18.3.1 |
| | TypeScript | Latest |
| **Backend API** | NestJS | 11.2.1 |
| | Node.js Runtime | 18+ |
| **Database** | PostgreSQL | 14+ (Docker) |
| **ORM** | TypeORM | 0.3.0 |
| **Authentication** | JWT + Passport | @nestjs/jwt 11.0.2, @nestjs/passport 11.0.5 |
| **Password Hashing** | bcrypt | Latest |
| **Message Queue** | RabbitMQ | Latest (Docker) |
| **Cache/Sessions** | Redis | Latest (Docker) |
| **Media Storage** | MinIO (S3-compatible) | Latest (Docker) |
| **Testing** | Jest | Latest |
| **Type Safety** | TypeScript | Latest |

### Project Structure

```
sentira/
├── apps/
│   ├── api/                          # NestJS backend API
│   │   ├── src/
│   │   │   ├── auth/                 # JWT authentication
│   │   │   │   ├── auth.service.ts
│   │   │   │   ├── auth.controller.ts
│   │   │   │   ├── strategies/jwt.strategy.ts
│   │   │   │   ├── guards/jwt-auth.guard.ts
│   │   │   │   ├── decorators/current-user.decorator.ts
│   │   │   │   └── auth.dto.ts
│   │   │   ├── entities/             # TypeORM entities (13 total)
│   │   │   │   ├── organization.entity.ts
│   │   │   │   ├── site.entity.ts
│   │   │   │   ├── user.entity.ts
│   │   │   │   ├── role.entity.ts
│   │   │   │   ├── camera.entity.ts
│   │   │   │   ├── zone.entity.ts
│   │   │   │   ├── rule.entity.ts
│   │   │   │   ├── rule-condition.entity.ts
│   │   │   │   ├── rule-action.entity.ts
│   │   │   │   ├── event.entity.ts
│   │   │   │   ├── event-media.entity.ts
│   │   │   │   ├── audit-log.entity.ts
│   │   │   │   ├── notification.entity.ts
│   │   │   │   └── index.ts
│   │   │   ├── modules/              # Feature modules (6 domains)
│   │   │   │   ├── organizations/
│   │   │   │   ├── cameras/
│   │   │   │   ├── events/
│   │   │   │   ├── rules/
│   │   │   │   ├── zones/
│   │   │   │   └── users/
│   │   │   ├── services/             # Business logic services
│   │   │   │   ├── event-generator.service.ts
│   │   │   │   ├── rule-engine.service.ts
│   │   │   │   └── notification.service.ts
│   │   │   ├── controllers/          # REST endpoints
│   │   │   │   └── demo.controller.ts
│   │   │   ├── common/               # Shared types
│   │   │   │   └── types.ts
│   │   │   ├── config/               # Configuration
│   │   │   │   └── database.config.ts
│   │   │   ├── app.module.ts         # Root NestJS module
│   │   │   ├── app.controller.ts     # Health endpoints
│   │   │   ├── main.ts               # Application entry point
│   │   │   └── **/*.spec.ts          # Jest unit tests
│   │   ├── jest.config.js
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── web/                          # Next.js frontend (scaffolded)
│   │   ├── pages/
│   │   │   ├── dashboard.tsx
│   │   │   ├── events.tsx
│   │   │   ├── cameras.tsx
│   │   │   ├── rules.tsx
│   │   │   ├── investigation.tsx
│   │   │   └── api/
│   │   ├── components/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── ai-worker/                    # Future: Python/GPU inference
│       └── (planned for Phase 2)
├── packages/
│   └── shared/                       # Shared types and utilities (planned)
├── docker-compose.yml                # Infrastructure: PostgreSQL, Redis, RabbitMQ, MinIO
├── package.json                      # Monorepo root
├── README.md                         # Quick start guide
├── MASTER_PROMPT.md                  # This document
├── ARCHITECTURE.md                   # System design details
├── DATABASE.md                       # Schema and entity definitions
├── API.md                            # REST API contract
├── SECURITY.md                       # Security model and encryption
├── RULE_ENGINE.md                    # Rule definition and evaluation
├── AI_PIPELINE.md                    # AI detection and worker abstraction
├── DEMO.md                           # Demo system and testing guide
└── QUICKSTART_DEMO.md                # Quick reference for demo testing
```

---

## 🔐 Authentication & Authorization

### JWT Authentication Flow

1. **Login Endpoint:** `POST /api/auth/login`
   - User provides email and password
   - AuthService validates credentials against user table
   - Password compared using bcrypt.compare()
   - On success, JwtModule signs token with:
     - `id` (user UUID)
     - `email` (user email)
     - `organizationId` (tenant ID)
     - `roleId` (user's role)
   - Token expires in 24 hours (configurable)

2. **Token Validation:** `@UseGuards(JwtAuthGuard)`
   - JwtStrategy extracts token from `Authorization: Bearer {token}` header
   - PassportJS validates signature and expiration
   - Decoded payload attached to `request.user`
   - CurrentUserDto contains: id, email, organizationId, roleId

3. **Route Protection:**
   - All endpoints except `POST /api/auth/login` require `@UseGuards(JwtAuthGuard)`
   - @CurrentUser() decorator injects authenticated user into handlers
   - Organization isolation enforced by filtering queries with user's organizationId

### Role-Based Access Control (RBAC)

- **Role Entity** stores:
  - `id` (UUID)
  - `organizationId` (tenant scoping)
  - `name` (e.g., "Admin", "Operator", "Viewer")
  - `description`
  - `permissions` (JSON object with boolean flags)
  - `createdAt` / `updatedAt` timestamps

- **Permission Model:** Simple JSON object
  ```json
  {
    "camera_view": true,
    "camera_create": false,
    "event_view": true,
    "event_acknowledge": true,
    "event_resolve": false,
    "rule_create": false,
    "rule_edit": false,
    "report_access": true
  }
  ```

- **Future Enhancement:** Decorator-based permission checking
  ```typescript
  @RequirePermission('event_resolve')
  async resolveEvent() { ... }
  ```

---

## 🗄️ Database Schema & Entities

### 13 Entities (TypeORM)

#### 1. Organization (Root Tenant)
```typescript
@Entity('organizations')
class Organization {
  id: UUID;                    // PrimaryGeneratedColumn
  name: string;                // Tenant name (e.g., "Giovanni's Restaurant")
  legalName: string;           // Legal entity name
  status: 'active' | 'inactive' | 'suspended';
  createdAt: Date;
  updatedAt: Date;
}
```
- Root level tenant
- All data filtered by organizationId
- Supports multi-site, multi-camera deployments

#### 2. Site (Multiple per Organization)
```typescript
@Entity('sites')
class Site {
  id: UUID;
  organizationId: UUID;        // Foreign key to Organization
  name: string;                // Site name (e.g., "Main Location")
  address: string;             // Physical address
  timezone: string;            // Timezone (e.g., "America/New_York")
  status: 'active' | 'inactive' | 'maintenance';
  createdAt: Date;
  updatedAt: Date;
}
```
- Multiple sites per organization
- Each site has independent camera sets
- Timezone for local time context

#### 3. Role (RBAC)
```typescript
@Entity('roles')
class Role {
  id: UUID;
  organizationId: UUID;        // Org-specific or global
  name: string;                // "Admin", "Operator", "Viewer"
  description: string;
  permissions: Record<string, boolean>; // JSON permissions
  createdAt: Date;
  updatedAt: Date;
}
```

#### 4. User (Multiple per Organization)
```typescript
@Entity('users')
class User {
  id: UUID;
  organizationId: UUID;        // Tenant FK
  email: string;               // Unique per org
  passwordHash: string;        // bcrypt hash
  firstName: string;
  lastName: string;
  roleId: UUID;                // Foreign key to Role
  status: 'active' | 'inactive' | 'suspended';
  lastLoginAt: Date;
  createdAt: Date;
  updatedAt: Date;
}
```
- Multi-tenant user management
- Email unique within organization
- Password hashed with bcrypt

#### 5. Camera (Multiple per Site)
```typescript
@Entity('cameras')
class Camera {
  id: UUID;
  organizationId: UUID;
  siteId: UUID;
  name: string;
  rtspUrl: string;             // RTSP stream endpoint
  resolution: string;          // "1920x1080"
  fps: number;                 // Frames per second (30)
  status: 'online' | 'offline' | 'connecting' | 'error' | 'ai_processing' | 'disabled';
  aiProcessingStatus: string;  // Model inference status
  lastHeartbeatAt: Date;       // Last ping from stream gateway
  createdAt: Date;
  updatedAt: Date;
}
```
- Multiple cameras per site
- Stream endpoint management
- Status tracking for operations

#### 6. Zone (Multiple per Camera)
```typescript
@Entity('zones')
class Zone {
  id: UUID;
  organizationId: UUID;
  cameraId: UUID;
  name: string;                // "Kitchen", "Entrance", "Table 1"
  geometryJson: Record<string, any>; // Polygon/ROI definition
  coordinatesJson: Array<[number, number]>; // GeoJSON coordinates
  createdAt: Date;
  updatedAt: Date;
}
```
- Polygonal regions within camera frame
- Used for spatial rule conditions
- Supports complex geometry

#### 7. Rule (Multiple per Organization)
```typescript
@Entity('rules')
class Rule {
  id: UUID;
  organizationId: UUID;
  cameraId: UUID;
  name: string;                // "Kitchen Entry Alert"
  ruleType: string;            // "table_unattended", "kitchen_entry", etc.
  confidenceThreshold: number; // 0.0 - 1.0 (default 0.7)
  status: 'active' | 'inactive' | 'paused';
  isActive: boolean;           // Quick enable/disable
  scheduleJson: Record<string, any>; // Time/day restrictions
  createdAt: Date;
  updatedAt: Date;
}
```
- Business logic definitions
- Confidence threshold filters
- Time-based schedules

#### 8. RuleCondition (Multiple per Rule)
```typescript
@Entity('rule_conditions')
class RuleCondition {
  id: UUID;
  ruleId: UUID;
  conditionType: string;       // "object_detected", "duration", "zone_entry"
  fieldName: string;           // "objectType", "confidence", "duration"
  operator: string;            // "==", ">", "<", "in", "between"
  valueJson: Record<string, any>; // Condition value
  sequenceOrder: number;       // Order for compound conditions
  createdAt: Date;
}
```
- Composable rule conditions
- Temporal and spatial filters
- Evaluation sequencing

#### 9. RuleAction (Multiple per Rule)
```typescript
@Entity('rule_actions')
class RuleAction {
  id: UUID;
  ruleId: UUID;
  actionType: 'create_event' | 'save_video_clip' | 'notify' | 'escalate';
  configJson: Record<string, any>; // Action-specific config
  createdAt: Date;
}
```
- Actions triggered by rule match
- Event creation, video capture, notifications
- Extensible action system

#### 10. Event (Incidents)
```typescript
@Entity('events')
class Event {
  id: UUID;
  organizationId: UUID;
  siteId: UUID;
  cameraId: UUID;
  ruleId: UUID;                // Which rule triggered
  eventType: string;           // "person_detected", "altercation"
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;          // Detection confidence (0.0-1.0)
  description: string;         // Event details
  status: 'new' | 'acknowledged' | 'investigating' | 'escalated' | 'resolved' | 'dismissed' | 'false_positive';
  snapshotUrl: string;         // Snapshot image URL
  videoClipUrl: string;        // Video evidence URL
  assignedUserId: UUID;        // Assigned to operator
  acknowledgedByUserId: UUID;  // Who acknowledged
  resolvedByUserId: UUID;      // Who resolved
  createdAt: Date;
  updatedAt: Date;
}
```
- Incident records
- Full lifecycle tracking
- Evidence URLs for investigation

#### 11. EventMedia (Multiple per Event)
```typescript
@Entity('event_media')
class EventMedia {
  id: UUID;
  organizationId: UUID;
  eventId: UUID;
  mediaType: 'snapshot' | 'video_clip' | 'audio';
  storageUrl: string;          // MinIO/S3 path
  dimensions: string;          // "1920x1080"
  duration: number;            // Seconds (for video)
  createdAt: Date;
}
```
- Multiple media items per event
- Snapshot and video storage
- Metadata for playback

#### 12. AuditLog (Compliance)
```typescript
@Entity('audit_logs')
class AuditLog {
  id: UUID;
  organizationId: UUID;
  userId: UUID;                // Who made change
  action: string;              // "create", "update", "delete"
  resourceType: string;        // "event", "rule", "user"
  resourceId: UUID;            // What changed
  ipAddress: string;           // Request source
  previousValueJson: Record<string, any>; // Before
  newValueJson: Record<string, any>;      // After
  createdAt: Date;
}
```
- Complete audit trail
- Regulatory compliance
- Change tracking

#### 13. Notification
```typescript
@Entity('notifications')
class Notification {
  id: UUID;
  organizationId: UUID;
  eventId: UUID;
  userId: UUID;                // Recipient (nullable)
  channel: 'in_app' | 'email' | 'push' | 'webhook';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'sent' | 'failed' | 'read';
  payload: Record<string, any>; // Message content
  sentAt: Date;
  createdAt: Date;
}
```
- Multi-channel notifications
- Event-driven alerting
- Delivery tracking

---

## 🔗 Database Relationships

```
Organization (1) ─→ (Many) Site
Organization (1) ─→ (Many) User
Organization (1) ─→ (Many) Role
Organization (1) ─→ (Many) Camera
Organization (1) ─→ (Many) Rule
Organization (1) ─→ (Many) Event
Organization (1) ─→ (Many) Zone
Organization (1) ─→ (Many) Notification
Organization (1) ─→ (Many) AuditLog

Site (1) ─→ (Many) Camera
Camera (1) ─→ (Many) Zone
Camera (1) ─→ (Many) Rule
Rule (1) ─→ (Many) RuleCondition
Rule (1) ─→ (Many) RuleAction
Event (1) ─→ (Many) EventMedia

Role (1) ←─ (Many) User
User (1) ←─ (Many) Event (as assignee/acknowledger/resolver)
```

All relationships include:
- Foreign key constraints
- Cascade delete for logical hierarchies
- Soft delete support (via status field)
- Indexes on common query paths

---

## 🚀 Core Services Architecture

### 1. AuthService
**Location:** `src/auth/auth.service.ts`

```typescript
@Injectable()
class AuthService {
  async validateUser(email: string, password: string): Promise<User | null>
  async login(dto: LoginDto): Promise<{ accessToken: string; user: User }>
  async verifyToken(token: string): Promise<any>
}
```

**Responsibilities:**
- User credential validation
- Password comparison with bcrypt
- JWT token generation
- Token verification

**Dependencies:**
- UsersService
- JwtService
- bcrypt

### 2. UsersService
**Location:** `src/modules/users/users.service.ts`

```typescript
@Injectable()
class UsersService {
  async findByEmail(email: string): Promise<User | null>
  async findById(id: string): Promise<User | null>
  async create(user: CreateUserDto): Promise<User>
  async findByOrganization(organizationId: string): Promise<User[]>
  async update(id: string, dto: UpdateUserDto): Promise<User>
}
```

**Multi-Tenancy:** All queries filtered by organizationId from @CurrentUser()

### 3. OrganizationsService
**Location:** `src/modules/organizations/organizations.service.ts`

```typescript
@Injectable()
class OrganizationsService {
  async create(dto: CreateOrgDto): Promise<Organization>
  async findById(id: string): Promise<Organization>
  async findAll(): Promise<Organization[]>
  async getSites(organizationId: string): Promise<Site[]>
  async createSite(organizationId: string, dto: CreateSiteDto): Promise<Site>
  async update(id: string, dto: UpdateOrgDto): Promise<Organization>
}
```

### 4. CamerasService
**Location:** `src/modules/cameras/cameras.service.ts`

```typescript
@Injectable()
class CamerasService {
  async create(organizationId: string, dto: CreateCameraDto): Promise<Camera>
  async findById(id: string, organizationId: string): Promise<Camera>
  async findBySite(siteId: string, organizationId: string): Promise<Camera[]>
  async updateStatus(id: string, organizationId: string, status: CameraStatus): Promise<Camera>
  async delete(id: string, organizationId: string): Promise<void>
}
```

**Key Feature:** All operations scoped to organizationId

### 5. RulesService
**Location:** `src/modules/rules/rules.service.ts`

```typescript
@Injectable()
class RulesService {
  async create(organizationId: string, dto: CreateRuleDto): Promise<Rule>
  async findById(id: string, organizationId: string): Promise<Rule>
  async findByOrganization(organizationId: string): Promise<Rule[]>
  async addCondition(ruleId: string, dto: CreateRuleConditionDto): Promise<RuleCondition>
  async addAction(ruleId: string, dto: CreateRuleActionDto): Promise<RuleAction>
  async update(id: string, organizationId: string, dto: UpdateRuleDto): Promise<Rule>
}
```

### 6. EventsService
**Location:** `src/modules/events/events.service.ts`

```typescript
@Injectable()
class EventsService {
  async create(organizationId: string, dto: CreateEventDto): Promise<Event>
  async findById(id: string, organizationId: string): Promise<Event>
  async findByOrganization(organizationId: string, limit: number, offset: number): Promise<Event[]>
  async updateStatus(id: string, organizationId: string, status: EventStatus): Promise<Event>
  async acknowledge(id: string, organizationId: string, userId: string): Promise<Event>
  async resolve(id: string, organizationId: string, userId: string): Promise<Event>
  async dismiss(id: string, organizationId: string): Promise<Event>
}
```

### 7. ZonesService
**Location:** `src/modules/zones/zones.service.ts`

```typescript
@Injectable()
class ZonesService {
  async create(organizationId: string, dto: CreateZoneDto): Promise<Zone>
  async findById(id: string, organizationId: string): Promise<Zone>
  async findByCamera(cameraId: string, organizationId: string): Promise<Zone[]>
  async update(id: string, organizationId: string, dto: UpdateZoneDto): Promise<Zone>
  async delete(id: string, organizationId: string): Promise<void>
}
```

### 8. EventGeneratorService (Demo)
**Location:** `src/services/event-generator.service.ts`

```typescript
@Injectable()
class EventGeneratorService {
  async createDemoEvent(payload: EventPayload): Promise<Event>
  async createEventFromDetections(
    organizationId: string,
    siteId: string,
    cameraId: string,
    ruleId: string,
    eventType: string,
    severity: Severity,
    confidence: number
  ): Promise<Event>
}
```

**Purpose:** Generates simulated events without real cameras for demos and testing

### 9. RuleEngineService (Demo)
**Location:** `src/services/rule-engine.service.ts`

```typescript
@Injectable()
class RuleEngineService {
  evaluateRule(rule: Rule, context: RuleEvaluationContext): boolean
  evaluateDemoRules(rule: Rule): boolean
}
```

**Demo Logic:** 70% trigger probability for demo rule types

### 10. NotificationService
**Location:** `src/services/notification.service.ts`

```typescript
@Injectable()
class NotificationService {
  async notify(payload: NotificationPayload): Promise<Notification>
  async notifyEvent(event: Event, message: string): Promise<Notification>
}
```

**Channels:** in_app, email, push, webhook (configurable delivery)

---

## 📡 REST API Endpoints

### Authentication
```
POST   /api/auth/login                   # Get JWT token
GET    /api/auth/me                      # Current user info
```

### Organizations
```
GET    /api/organizations/:id
POST   /api/organizations
PUT    /api/organizations/:id
GET    /api/organizations/:id/sites
POST   /api/organizations/:id/sites
```

### Cameras
```
GET    /api/cameras                      # List by organization
GET    /api/cameras/:id
POST   /api/cameras
PUT    /api/cameras/:id
DELETE /api/cameras/:id
GET    /api/cameras/site/:siteId
```

### Events
```
GET    /api/events                       # Paginated list
GET    /api/events/:id
POST   /api/events/:id/acknowledge
POST   /api/events/:id/resolve
POST   /api/events/:id/dismiss
```

### Rules
```
GET    /api/rules
GET    /api/rules/:id
POST   /api/rules
PUT    /api/rules/:id
DELETE /api/rules/:id
```

### Zones
```
GET    /api/zones/:id
GET    /api/zones/camera/:cameraId
POST   /api/zones
PUT    /api/zones/:id
DELETE /api/zones/:id
```

### Demo (Sales & Testing)
```
POST   /api/demo/generate-event          # Create single event
POST   /api/demo/trigger-all-rules       # Batch rule evaluation
GET    /api/demo/dashboard-data          # Mock dashboard stats
```

### Health
```
GET    /health                           # Service health check
GET    /ready                            # Readiness probe
```

**All endpoints (except `/api/auth/login` and `/health`) require:**
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

---

## 🎯 Demo & Testing Pipeline

### Demo Event Generation System

The demo pipeline enables realistic incident simulation without hardware:

#### EventGeneratorService
- Creates Event entities with mock data
- Sets `snapshotUrl` and `videoClipUrl` to demo paths
- Maintains full organizationId scoping

#### RuleEngineService
- **Production Mode:** Evaluates actual detection data
- **Demo Mode:** 70% probabilistic trigger for known rule types
- Supports: confidence thresholds, schedules, day-of-week rules

#### NotificationService
- Creates Notification records on event creation
- Supports 4 channels: in_app, email, push, webhook
- Tracks status: pending, sent, failed, read
- Priority levels: low, medium, high, critical

### Demo Workflow

```
1. User calls /api/demo/trigger-all-rules
       ↓
2. Loop through all org's rules
       ↓
3. For each rule, evaluateDemoRules() returns true 70% of time
       ↓
4. Create Event entity with mock data
       ↓
5. Send Notification via NotificationService
       ↓
6. Return created events array
       ↓
7. Frontend displays events in real-time (with WebSocket)
```

### Demo Rule Types

```typescript
'table_unattended'    // Table left unoccupied (70% trigger)
'kitchen_entry'       // Unauthorized kitchen access
'uniform_violation'   // Staff not in uniform
'altercation'         // Potential conflict
'animal_detected'     // Animal in restricted zone
'smoke_detected'      // Fire/smoke detection
```

### Testing Demo Events

**Get Token:**
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo_password"}'
```

**Create Single Event:**
```bash
curl -X POST http://localhost:3001/api/demo/generate-event \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cameraId": "camera-uuid",
    "ruleId": "rule-uuid"
  }'
```

**Batch Trigger (70% per rule):**
```bash
curl -X POST http://localhost:3001/api/demo/trigger-all-rules \
  -H "Authorization: Bearer $TOKEN"
```

**Dashboard Stats:**
```bash
curl -X GET http://localhost:3001/api/demo/dashboard-data \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Event Lifecycle

```
┌─────────────┐
│   Created   │  (New incident, status: 'new')
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│   Acknowledged      │  (Operator saw it, status: 'acknowledged')
└──────┬──────────────┘
       │
       ├─→ Investigating → Escalated ─┐
       │                               │
       └───────────────────────────────┤
                                      ↓
                            ┌────────────────────┐
                            │ Resolved/Dismissed │
                            └────────────────────┘

Special: 'false_positive' for incorrect alerts
```

**Status Transitions:**
- `new` → `acknowledged` (User sees alert)
- `acknowledged` → `investigating` (Active investigation)
- `investigating` → `escalated` (Needs higher authority)
- Any → `resolved` (Issue handled)
- Any → `dismissed` (False alarm / not actionable)
- Any → `false_positive` (Marked as incorrect detection)

---

## 🔒 Security & Multi-Tenancy

### Multi-Tenancy Model

**Tenant Isolation:** Organization-based scoping

Every database query includes organization filter:
```typescript
// Pattern across all services
const entity = await repository.find({
  where: {
    id: entityId,
    organizationId: user.organizationId  // ← Always enforced
  }
});
```

**No organization can:**
- Query another organization's data
- Access another organization's users/roles
- Trigger rules from other organizations
- View events from other organizations

### Authentication Security

- Passwords hashed with bcrypt (salt rounds: 10)
- JWT tokens signed with environment secret
- Tokens include organizationId (immutable)
- Token expiration: 24 hours (configurable)
- No token refresh mechanism (yet - planned for Phase 2)

### API Security Headers

```
Authorization: Bearer {JWT}          (Required for all protected routes)
Content-Type: application/json       (Required for POST/PUT)
X-Requested-With: XMLHttpRequest     (CORS handling)
```

### Audit Logging

Every sensitive action logged to `AuditLog` table:
- User ID performing action
- Resource type and ID changed
- Previous and new values (JSON)
- IP address of request
- Timestamp (UTC)

Example audit trail:
```json
{
  "userId": "user-123",
  "action": "update",
  "resourceType": "event",
  "resourceId": "event-456",
  "previousValue": { "status": "new" },
  "newValue": { "status": "acknowledged" },
  "ipAddress": "192.168.1.100",
  "createdAt": "2024-08-16T10:30:00Z"
}
```

### Encryption (Phase 2)

Planned but not yet implemented:
- RTSP credentials stored encrypted in database
- API response encryption for sensitive data
- HTTPS enforced in production
- SSL/TLS certificate management

---

## 🧪 Testing & Quality Assurance

### Test Coverage

**Current (10 tests passing):**
- `app.controller.spec.ts` - Health endpoints
- `auth.service.spec.ts` - Login validation
- `auth.controller.spec.ts` - Auth controller
- `rule-engine.service.spec.ts` - Rule evaluation
- `notification.service.spec.ts` - Notification creation

**Running Tests:**
```bash
npm --workspace apps/api run test          # All tests
npm --workspace apps/api run test -- --watch  # Watch mode
npm --workspace apps/api run test -- --coverage  # Coverage report
```

### Build Verification

```bash
npm --workspace apps/api run build         # TypeScript compilation
npm run lint                               # ESLint (all workspaces)
```

**Current Status:** ✅ Zero TypeScript errors, all tests passing

### Jest Configuration

```javascript
// jest.config.js
{
  moduleFileExtensions: ['js', 'json', 'ts'],
  testEnvironment: 'node',
  testRegex: '.*\.spec\.ts$',
  transform: { '^.+\\.(t|j)s$': 'ts-jest' }
}
```

### Testing Best Practices

1. Mock external dependencies (databases, JWT)
2. Test service logic independently from controllers
3. Use `getRepositoryToken()` for database mocks
4. Test authorization (JwtAuthGuard) on controllers
5. Cover multi-tenancy isolation in integration tests

---

## 🔄 Development Workflow

### Local Setup

**Prerequisites:**
- Node.js 18+
- Docker & Docker Compose
- Git

**1. Clone & Install:**
```bash
git clone https://github.com/gaathaaidni/sentira.git
cd sentira
npm install
```

**2. Start Infrastructure:**
```bash
docker-compose up -d
# Starts: PostgreSQL (5432), Redis (6379), RabbitMQ (5672), MinIO (9000)
```

**3. Run Database Migrations:**
```bash
# Currently using TypeORM synchronize: true for development
# Migration setup: TODO for production
```

**4. Start API Server:**
```bash
npm run dev:api
# API runs on http://localhost:4000
```

**5. Start Frontend:**
```bash
npm --workspace apps/web run dev
# Frontend runs on http://localhost:3000
```

### Code Organization Standards

**Services:**
- Must be decorated with `@Injectable()`
- Dependency injection via constructor
- Single responsibility principle
- Multi-tenancy filtering on all queries

**Controllers:**
- Must use `@UseGuards(JwtAuthGuard)` for protected routes
- Public routes: `/api/auth/login`, `/health`
- Use `@CurrentUser()` to access authenticated user
- Validate input with DTOs

**Entities:**
- Must use TypeORM decorators (@Entity, @Column, etc.)
- Include `organizationId` for all tenant resources
- Use proper indexes for common queries
- Include timestamps (createdAt, updatedAt)

**DTOs (Data Transfer Objects):**
- Validate request payloads
- Example: `LoginDto`, `CreateCameraDto`, `UpdateEventDto`
- Use NestJS validation decorators

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/websocket-integration

# Make changes, test locally
npm run build
npm run test

# Commit with clear messages
git commit -m "feat: add WebSocket real-time updates"

# Push and create PR
git push origin feature/websocket-integration
```

---

## 📋 Complete Feature Checklist

### ✅ Implemented (Phase 1 Complete)

**Backend Foundation (Phase 1):**
- [x] NestJS 11 API setup with TypeORM
- [x] PostgreSQL database configuration
- [x] JWT authentication with Passport
- [x] 13 TypeORM entities with relationships
- [x] Role-based access control (RBAC)
- [x] Multi-tenancy enforcement
- [x] 6 core services (Organizations, Cameras, Events, Rules, Zones, Users)
- [x] 6 REST controllers with CRUD operations
- [x] Audit logging infrastructure

**Demo & Testing (Phase 1):**
- [x] EventGeneratorService (simulated incidents)
- [x] RuleEngineService (confidence & schedule evaluation)
- [x] NotificationService (multi-channel alerts)
- [x] DemoController (3 API endpoints)
- [x] Demo rule types (table_unattended, kitchen_entry, etc.)
- [x] 70% probabilistic triggering for demos

**Documentation (Phase 1):**
- [x] Architecture overview (ARCHITECTURE.md)
- [x] Database schema (DATABASE.md)
- [x] API contract (API.md)
- [x] Security model (SECURITY.md)
- [x] Rule engine design (RULE_ENGINE.md)
- [x] AI pipeline abstraction (AI_PIPELINE.md)
- [x] Demo system guide (DEMO.md)
- [x] Quick start (QUICKSTART_DEMO.md)

**Quality (Phase 1):**
- [x] 10 unit tests (all passing)
- [x] Zero TypeScript compilation errors
- [x] ESLint configuration
- [x] Jest test framework
- [x] Docker Compose infrastructure

### ✅ Implemented (Phase 2)

**Real-Time Updates:**
- [x] WebSocket gateway (@nestjs/websockets)
- [x] EventCreated socket event emission
- [x] Organization-scoped socket rooms
- [ ] Frontend real-time dashboard updates

**Frontend Dashboard:**
- [x] Authentication UI & Logic
- [ ] Event list with status filtering
- [ ] Incident severity color coding
- [ ] Acknowledge/Resolve/Dismiss buttons
- [ ] Real-time chart updates
- [ ] Investigation timeline view

### 🔄 In Progress (Phase 2)

**Advanced Rules:**
- [ ] Temporal rule conditions (duration-based)
- [ ] Zone-based spatial logic
- [ ] Multi-condition rule composition
- [ ] Rule condition UI builder

### 📅 Planned (Phase 3+)

**Video Evidence:**
- [ ] RTSP stream gateway
- [ ] Video clip extraction and storage
- [ ] MinIO/S3 upload pipeline
- [ ] Video playback UI

**AI Integration:**
- [ ] AI worker service (Python/GPU)
- [ ] Model abstraction layer
- [ ] Real detection pipeline
- [ ] Performance monitoring

**Production Hardening:**
- [ ] Database migrations
- [ ] Token refresh mechanism
- [ ] Rate limiting
- [ ] Request logging
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (APM)

**Scale & Operations:**
- [ ] Kubernetes deployment manifests
- [ ] Database backup procedures
- [ ] Log aggregation (ELK stack)
- [ ] Alerting on platform metrics
- [ ] SLA compliance reporting

---

## 🚦 Known Limitations & TODOs

### Current (Phase 1)

**Database:**
- Using TypeORM `synchronize: true` (development only)
- No migration scripts (setup for production)
- No backup procedures

**Authentication:**
- Single 24-hour JWT token (no refresh)
- No multi-factor authentication
- No password reset flow
- No rate limiting on login attempts

**API:**
- No pagination (limit/offset only)
- No advanced search/filtering
- No bulk operations
- No response caching

**Frontend:**
- Scaffolded but not implemented
- No dashboard components
- No real-time updates (WebSocket pending)
- No dark mode implementation (planned)

**Security:**
- Credentials in `.env.local` (not secrets management)
- RTSP URLs in plaintext database
- No request encryption
- No rate limiting

### Phase 2 Blockers
- None identified - all Phase 2 items are independent

---

## 🛠️ Environment Configuration

### Required Environment Variables

Create `.env.local` in monorepo root:

```bash
# Application
NODE_ENV=development
API_PORT=4000 # API will run on this port

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=sentira
DB_PASSWORD=sentira_dev_password
DB_NAME=sentira

# JWT
JWT_SECRET=replace-with-a-unique-secret-at-least-32-characters

# Optional: Redis/RabbitMQ/MinIO (defaults provided in docker-compose)
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sentira-media
```

### Docker Services

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:14
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: sentira
      POSTGRES_PASSWORD: sentira_dev_password
      POSTGRES_DB: sentira
  
  redis:
    image: redis:7
    ports: ["6379:6379"]
  
  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]
  
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
```

---

## 🔗 Important Files Reference

| File | Purpose |
|------|---------|
| `apps/api/src/app.module.ts` | Root NestJS module, service/entity registration |
| `apps/api/src/auth/auth.service.ts` | JWT and user authentication |
| `apps/api/src/config/database.config.ts` | TypeORM configuration and entity loading |
| `apps/api/src/entities/index.ts` | Export all 13 entities |
| `apps/api/src/common/types.ts` | Shared TypeScript interfaces |
| `apps/api/src/services/event-generator.service.ts` | Demo event creation |
| `apps/api/src/services/rule-engine.service.ts` | Rule evaluation logic |
| `apps/api/src/services/notification.service.ts` | Notification dispatch |
| `apps/api/src/controllers/demo.controller.ts` | Demo API endpoints |
| `.env.local` | Environment variables (create locally) |
| `docker-compose.yml` | Infrastructure services |
| `jest.config.js` | Testing configuration |
| `ARCHITECTURE.md` | Detailed system design |
| `DATABASE.md` | Schema and relationships |
| `API.md` | Endpoint documentation |
| `DEMO.md` | Demo system guide |

---

## 🎓 Learning Path for New Developers

### Week 1: Foundation
1. **Clone repository** and set up local environment
2. **Read:** ARCHITECTURE.md, README.md
3. **Setup:** Docker, npm install, run docker-compose up
4. **Test:** Verify build and tests pass
5. **Explore:** `curl http://localhost:3001/health`

### Week 2: Backend Deep Dive
1. **Read:** DATABASE.md, API.md
2. **Study:** Entity relationships and multi-tenancy pattern
3. **Code Review:** AuthService, CamerasService, EventsService
4. **Hands-On:** Create a new route (e.g., camera status update)
5. **Test:** Write unit test for new route

### Week 3: Demo System
1. **Read:** DEMO.md, QUICKSTART_DEMO.md
2. **Run:** `npm --workspace apps/api run dev`
3. **Test:** All three demo endpoints
4. **Understand:** EventGeneratorService → RuleEngineService → NotificationService flow
5. **Experiment:** Modify demo trigger probability

### Week 4: Feature Development
1. **Pick feature:** WebSocket OR Advanced Rules OR Video Pipeline
2. **Design:** Create GitHub issue with specification
3. **Implement:** Small commits with tests
4. **PR Review:** Request code review
5. **Iterate:** Incorporate feedback

### Resources
- **NestJS Docs:** https://docs.nestjs.com
- **TypeORM Docs:** https://typeorm.io
- **JWT Auth:** https://tools.ietf.org/html/rfc7519
- **REST API Best Practices:** https://restfulapi.net

---

## 📞 Support & Contact

**Repository:** https://github.com/gaathaaidni/sentira  
**Issues:** GitHub Issues (for bugs and features)  
**Documentation:** See markdown files in repository root  

**Core Team:**
- **Architecture & Design:** Hardikkumar Gajjar
- **Backend Implementation:** NestJS + TypeORM stack
- **Frontend:** Next.js + React (in progress)

---

## 📄 Document Metadata

- **Last Updated:** August 16, 2026
- **Version:** 1.0 (Phase 1 Complete)
- **Status:** Production-Ready Backend
- **Audience:** Developers, AI assistants, stakeholders
- **Compatibility:** Node 18+, PostgreSQL 14+, TypeScript 5+

---

## 🎯 Next Actions

**For AI Assistants (Gemini Pro, ChatGPT):**
1. Reference this document for project context
2. Use ARCHITECTURE.md for detailed design questions
3. Reference API.md for endpoint specifications
4. Check DEMO.md for testing procedures

**For New Developers:**
1. Start with the Learning Path (above)
2. Join GitHub discussions or create issues
3. Follow Development Workflow guidelines
4. Always enforce multi-tenancy in new features

**For Product/Stakeholders:**
1. Phase 1 (Backend + Demo) is complete ✅
2. Phase 2 (WebSocket + Frontend) is in progress ✅
3. Phase 3 (Video + AI) planned Q4 2024
4. Production deployment readiness: Phase 3

---

**END OF MASTER PROMPT**

This document should be shared with:
- ✅ Gemini Pro / ChatGPT (AI context)
- ✅ New developers (onboarding)
- ✅ Future maintainers (reference)
- ✅ Project stakeholders (overview)

## Phase 5 execution note

Phase 5 implementation is tracked in `PHASE5_COMPLETION_REPORT.md`. The repository code is authoritative: features are marked IMPLEMENTED, TESTED, PARTIALLY IMPLEMENTED, CONCEPTUAL, or NOT VERIFIED based on actual code and commands run in the working tree.

## Phase 8
Control-plane additions are tracked in `PHASE_8_COMPLETION_REPORT.md`; only verified integration claims should be promoted to production status.

## Phase 9 verification note

Phase 9 retains the existing architecture and records a truthful, environment-limited verification result in `PHASE_9_COMPLETION_REPORT.md`. Dependencies without an executed health probe are reported as `UNKNOWN`; no physical RTSP, Docker, or external-service integration is claimed by this repository verification.

## Phase 10B integration note

The Phase 10B Compose environment uses Docker service hostnames for all
service-to-service communication. Runtime verification status and limitations are
recorded in `PHASE_10B_COMPLETION_REPORT.md`; configuration alone is not evidence
that an external dependency is healthy.

## Phase 10C integration note

The detection path now has an API ingress contract and asynchronous evidence
attachment boundary. Runtime dependency verification remains separate from source
availability; consult `PHASE_10C_COMPLETION_REPORT.md`.

## Phase 10E verification status

Phase 10E remains partially verified and **not production ready**. AMQP cannot be
claimed installed until `amqplib` is resolvable from a clean, locked install; the
attempt in this environment received npm HTTP 403. Docker is unavailable, so all
Compose-backed golden-path and failure tests remain blocked. See
`PHASE_10E_COMPLETION_REPORT.md`.

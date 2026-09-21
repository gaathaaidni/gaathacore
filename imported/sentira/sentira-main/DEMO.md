# Sentira AI Demo Plan & Event Pipeline

## Demo Overview

The Sentira AI demo system provides a complete vertical slice demonstrating business value without requiring hardware dependency. It includes simulated cameras, synthetic but realistic detections, and a fully functional rule engine for sales demonstrations and testing.

## Core Demo Components

### Simulated Cameras
- **Entrance** - Entry point monitoring
- **Dining Area** - General dining observation
- **Table 01** - Individual table service
- **Table 02** - Individual table service
- **Kitchen** - Staff and food safety monitoring
- **Storage** - Inventory and restricted area access

### Demo Rule Types

1. **Table Unattended** - Table left unoccupied for threshold seconds
2. **Kitchen Entry** - Unauthorized person enters kitchen
3. **Uniform Violation** - Staff not wearing required uniform
4. **Altercation** - Potential conflict or argument detected
5. **Animal Detected** - Animal detected in restricted area
6. **Smoke Detected** - Smoke or fire detection

Each rule type has a **70% trigger probability** during demo evaluation.

## Demo Event Pipeline

### Architecture Flow

```
User Action → Demo Controller → Rule Engine → Event Generator → Notification Service
     ↓              ↓                ↓                ↓                ↓
  API Call    Evaluates Rules    Checks Rules    Creates Event    Sends Alert
```

### Step-by-Step Process

1. **Generate Demo Event** (Single Rule)
   ```
   POST /api/demo/generate-event
   → Select camera & rule
   → Event generator creates incident
   → Notification sent
   → Event appears on dashboard
   ```

2. **Trigger All Rules** (Batch Simulation)
   ```
   POST /api/demo/trigger-all-rules
   → Loop through all organization rules
   → Each rule evaluated (70% trigger chance)
   → Multiple events generated
   → Notifications for each trigger
   → Full dashboard refresh
   ```

3. **Dashboard Statistics**
   ```
   GET /api/demo/dashboard-data
   → Returns mock stats
   → Shows demoMode: true flag
   → Includes demo label on all data
   ```

## API Endpoints

All endpoints require JWT authentication and are organization-scoped.

### POST /api/demo/generate-event
Creates a single demo event from a specific rule.

**Request:**
```json
{
  "cameraId": "cam-uuid",
  "ruleId": "rule-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "event": {
    "id": "event-uuid",
    "organizationId": "org-uuid",
    "cameraId": "cam-uuid",
    "eventType": "person_detected",
    "severity": "high",
    "confidence": 0.87,
    "status": "new",
    "snapshotUrl": "/demo/snapshot/cam-uuid/timestamp.jpg",
    "videoClipUrl": "/demo/video/cam-uuid/timestamp.mp4"
  },
  "message": "Demo event created and notification sent"
}
```

### POST /api/demo/trigger-all-rules
Evaluates all rules for the organization with probabilistic triggering.

**Response:**
```json
{
  "success": true,
  "eventsCreated": 3,
  "events": [
    { /* event 1 */ },
    { /* event 2 */ },
    { /* event 3 */ }
  ]
}
```

### GET /api/demo/dashboard-data
Returns mock dashboard statistics.

**Response:**
```json
{
  "camerasOnline": 128,
  "camerasOffline": 5,
  "eventsToday": 42,
  "criticalEvents": 3,
  "unresolvedEvents": 12,
  "falsePositives": 2,
  "rulesActive": 8,
  "demoMode": true,
  "demoLabel": "DEMO DATA - Simulated Events Only"
}
```

## Testing the Demo

### 1. Get Authentication Token
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sentira.demo","password":"demo123"}'
```

### 2. Create a Demo Event
```bash
curl -X POST http://localhost:3001/api/demo/generate-event \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"cameraId":"{cameraId}","ruleId":"{ruleId}"}'
```

### 3. Trigger All Rules
```bash
curl -X POST http://localhost:3001/api/demo/trigger-all-rules \
  -H "Authorization: Bearer {token}"
```

### 4. View Dashboard
```bash
curl -X GET http://localhost:3001/api/demo/dashboard-data \
  -H "Authorization: Bearer {token}"
```

## Demo Workflow

### For Sales Demonstration

1. **Setup Phase**
   - Deploy Sentira with demo organization
   - Seed 6 cameras and 6 rules
   - Show "Ready for demo" status

2. **Live Interaction**
   - Customer views empty dashboard
   - Trigger rules with `/api/demo/trigger-all-rules`
   - Events appear in real-time
   - Show incident severity and details
   - Demonstrate acknowledgment/resolution

3. **Investigation Phase**
   - Show event timeline
   - Display snapshots and video clips
   - Show rule configuration
   - Demonstrate analytics

### For Testing & QA

1. **Event Generation**
   - Generate predictable incidents
   - Test event status transitions
   - Verify notification delivery
   - Test multi-tenancy isolation

2. **Rule Engine Testing**
   - Test confidence thresholds
   - Verify schedule restrictions
   - Test temporal logic
   - Validate action execution

3. **Load Testing**
   - Generate multiple events
   - Test dashboard responsiveness
   - Verify database scalability
   - Monitor notification delivery

## Demo Labeling & Safety

All demo content includes explicit labeling:
- **Flag:** `demoMode: true` in API responses
- **Label:** "DEMO DATA - Simulated Events Only" in UI
- **Scope:** Organization-scoped to prevent confusion with production
- **Purpose:** Clear distinction from operational incidents

### Important
- Demo system cannot be enabled on production organizations
- All demo events are clearly marked
- No real incidents should be confused with demos
- Demo data is isolated by organization

## Event Lifecycle in Demo

```
Event Created (severity, confidence set)
           ↓
    Notification Sent (in-app, email, push, webhook)
           ↓
Appears on Dashboard (timeline, incident list)
           ↓
User Acknowledges (timestamp recorded)
           ↓
User Resolves (resolution status, notes)
           ↓
Event Archived (still searchable)
```

## Demo Services Architecture

### EventGeneratorService
- Creates events from EventPayload
- Sets demo snapshot/video URLs
- Handles organization scoping
- Returns created event object

### RuleEngineService
- Evaluates rule conditions
- Checks confidence thresholds
- Validates schedules and time windows
- For demo: 70% probabilistic trigger

### NotificationService
- Creates notification records
- Supports 4 channels: in_app, email, push, webhook
- Tracks delivery status
- Logs notification attempts

## Future Demo Enhancements

1. **WebSocket Real-Time Updates**
   - Push events to connected dashboards
   - No page refresh required
   - Live incident notifications

2. **Batch Scenarios**
   - Pre-configured incident sequences
   - Multi-step demonstrations
   - Reproducible demo flows

3. **Historical Replay**
   - Playback past events
   - Show system evolution
   - Demonstrate temporal patterns

4. **Performance Testing Mode**
   - Configurable event generation rate
   - Load testing against dashboard
   - Scalability demonstrations

## Demo Data Retention

- Demo events stored in production database (organization-scoped)
- Retention: Configurable per organization
- Cleanup: Manual or automatic purge option
- Isolation: Organization filters prevent cross-tenant data leakage

## Security Notes

- All demo endpoints require JWT authentication
- Multi-tenancy enforced at database query level
- Organization ID from token used for all operations
- No demo mode override of access controls
- Complete audit trail of demo activities

## Success Metrics

A successful demo should show:
1. ✅ Events created within seconds
2. ✅ Multiple rules triggered in batch mode
3. ✅ Notifications appearing immediately
4. ✅ Dashboard updating live
5. ✅ User able to acknowledge/resolve incidents
6. ✅ All data clearly marked as DEMO
7. ✅ Performance responsive and smooth
8. ✅ Multi-tenancy completely isolated


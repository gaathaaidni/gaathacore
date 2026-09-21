# Quick Demo Reference

## Start the Demo System

### 1. Ensure Services are Running
```bash
docker-compose up -d
npm install
npm --workspace apps/api run dev
```

### 2. Get JWT Token
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo_password"}'
```

Copy the `accessToken` from response.

### 3. Set Token in Shell (Optional)
```bash
export TOKEN="your-token-here"
```

## Demo Endpoints

### Generate Single Event
```bash
curl -X POST http://localhost:3001/api/demo/generate-event \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cameraId": "camera-uuid",
    "ruleId": "rule-uuid"
  }'
```

**What happens:**
- Single event created from specified camera & rule
- Notification sent to dashboard
- Event appears immediately in `/api/events`

### Trigger All Rules (Batch Mode)
```bash
curl -X POST http://localhost:3001/api/demo/trigger-all-rules \
  -H "Authorization: Bearer $TOKEN"
```

**What happens:**
- Loops through ALL organization rules
- Each rule has 70% chance to trigger
- Multiple events created
- Simulates real incident cluster
- Dashboard updates instantly

### Get Dashboard Stats
```bash
curl -X GET http://localhost:3001/api/demo/dashboard-data \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "camerasOnline": 128,
  "camerasOffline": 5,
  "eventsToday": 42,
  "criticalEvents": 3,
  "unresolvedEvents": 12,
  "demoMode": true,
  "demoLabel": "DEMO DATA - Simulated Events Only"
}
```

## Quick Testing Script

Save as `demo-test.sh`:

```bash
#!/bin/bash

TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo_password"}' \
  | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)

echo "✅ Got token: ${TOKEN:0:20}..."

echo ""
echo "📊 Dashboard Stats:"
curl -s -X GET http://localhost:3001/api/demo/dashboard-data \
  -H "Authorization: Bearer $TOKEN" | jq .

echo ""
echo "🎬 Triggering all rules (batch mode)..."
curl -s -X POST http://localhost:3001/api/demo/trigger-all-rules \
  -H "Authorization: Bearer $TOKEN" | jq '.eventsCreated'

echo ""
echo "✅ Events created! Check dashboard at http://localhost:3000"
```

Run with:
```bash
chmod +x demo-test.sh
./demo-test.sh
```

## Verify Events Were Created

```bash
curl -X GET http://localhost:3001/api/events \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, eventType, severity, status}'
```

## Demo Rule Types

The system recognizes these rule types for demo triggering:
- `table_unattended` - Table left unoccupied
- `kitchen_entry` - Unauthorized kitchen entry
- `uniform_violation` - Staff not in uniform
- `altercation` - Potential conflict
- `animal_detected` - Animal in restricted area
- `smoke_detected` - Smoke/fire detection

Each has a 70% chance to trigger during batch evaluation.

## Testing Event Status Transitions

Once events are created, test the event API:

### Acknowledge Event
```bash
curl -X POST http://localhost:3001/api/events/{eventId}/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

### Resolve Event
```bash
curl -X POST http://localhost:3001/api/events/{eventId}/resolve \
  -H "Authorization: Bearer $TOKEN"
```

### Dismiss Event
```bash
curl -X POST http://localhost:3001/api/events/{eventId}/dismiss \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring Notifications

Query created notifications:
```bash
curl -X GET http://localhost:3001/api/notifications \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, channel, priority, status}'
```

## Database Inspection

### View Events Table
```bash
psql -h localhost -U sentira -d sentira -c "SELECT id, event_type, severity, status, created_at FROM events ORDER BY created_at DESC LIMIT 10;"
```

### View Notifications
```bash
psql -h localhost -U sentira -d sentira -c "SELECT id, channel, priority, status, sent_at FROM notifications ORDER BY sent_at DESC LIMIT 10;"
```

### Count Demo Events Today
```bash
psql -h localhost -U sentira -d sentira -c "SELECT COUNT(*) FROM events WHERE DATE(created_at) = TODAY();"
```

## Performance Testing

Generate 100 events in rapid succession:
```bash
for i in {1..100}; do
  curl -s -X POST http://localhost:3001/api/demo/trigger-all-rules \
    -H "Authorization: Bearer $TOKEN" > /dev/null &
done
wait
echo "100 event batches triggered!"
```

Then check performance:
- Dashboard responsiveness
- Database query times
- Notification delivery
- Memory usage

## Troubleshooting

### Events not creating?
```bash
# Check if API is running
curl http://localhost:3001/health

# Verify token is valid
curl -X GET http://localhost:3001/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Check database connection
psql -h localhost -U sentira -d sentira -c "SELECT 1;"
```

### No notifications appearing?
```bash
# Check notification service is running
curl -X GET http://localhost:3001/api/notifications \
  -H "Authorization: Bearer $TOKEN"

# Verify events exist
curl -X GET http://localhost:3001/api/events \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
```

### Rules not triggering?
```bash
# List organization rules
curl -X GET http://localhost:3001/api/rules \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, name, ruleType, isActive}'

# Check rule has a camera
curl -X GET http://localhost:3001/api/rules/{ruleId} \
  -H "Authorization: Bearer $TOKEN" | jq '.cameraId'
```

## Next Steps

1. **Dashboard Frontend** - View demo events in real-time
2. **WebSockets** - Push notifications to browser
3. **Advanced Rules** - Temporal conditions (person present for 120+ seconds)
4. **Video Playback** - Show clip evidence from demo events
5. **Load Testing** - Stress test with 1000+ events/minute

See [DEMO.md](DEMO.md) for complete documentation.

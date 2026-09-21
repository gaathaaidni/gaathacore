# Quick Reference: Multi-Tenant API Usage

## Login Credentials

### Platform Super Admin (Platform Owner)
```
Username: superadmin
Password: superadmin@123
Role: super_admin
Can: Manage all restaurants, create new restaurants, manage all users
```

### Restaurant Admin (Restaurant Operator)
```
Username: rest_admin
Password: rest_admin123
Role: restaurant_admin
Restaurant: Demo Restaurant
Can: Manage Demo Restaurant, update store settings, manage own staff
```

### Legacy Admin (Backward Compatibility)
```
Username: admin
Password: admin
Role: admin
Can: Legacy functionality (non-multitenant)
```

---

## API Usage Examples

### 1. List All Restaurants (Super Admin)
```bash
curl -X GET http://localhost:5000/api/restaurants \
  -H "Authorization: Bearer <superadmin_token>"
```

### 2. List Own Restaurant (Restaurant Admin)
```bash
curl -X GET http://localhost:5000/api/restaurants \
  -H "Authorization: Bearer <rest_admin_token>"
# Returns only Demo Restaurant
```

### 3. Create New Restaurant (Super Admin Only)
```bash
curl -X POST http://localhost:5000/api/restaurants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superadmin_token>" \
  -d '{
    "name": "Pizza Palace",
    "email": "contact@pizzapalace.local",
    "owner_id": 2,
    "phone": "+353-1-999-8888",
    "address": "456 Oak Street",
    "city": "Cork",
    "country": "Ireland",
    "postal_code": "T12",
    "timezone": "Europe/Dublin",
    "locale": "en",
    "currency": "EUR",
    "tax_region": "EU"
  }'
```

### 4. Get Restaurant Details (with Store Settings)
```bash
curl -X GET http://localhost:5000/api/restaurants/1 \
  -H "Authorization: Bearer <rest_admin_token>"

# Response:
{
  "id": 1,
  "name": "Demo Restaurant",
  "email": "demo@restaurant.local",
  "active": true,
  "store_settings": {
    "id": 1,
    "timezone": "Europe/Dublin",
    "locale": "en",
    "currency": "EUR",
    "tax_region": "EU",
    "vat_number": "IE1234567890T",
    "invoice_prefix": "INV"
  }
}
```

### 5. Update Restaurant Details (Restaurant Admin)
```bash
curl -X PUT http://localhost:5000/api/restaurants/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <rest_admin_token>" \
  -d '{
    "name": "Demo Restaurant Updated",
    "phone": "+353-1-111-2222"
  }'
```

### 6. Get Store Settings
```bash
curl -X GET http://localhost:5000/api/restaurants/1/store-settings \
  -H "Authorization: Bearer <rest_admin_token>"
```

### 7. Update Store Settings (Change Timezone, Currency)
```bash
curl -X PUT http://localhost:5000/api/restaurants/1/store-settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <rest_admin_token>" \
  -d '{
    "timezone": "America/New_York",
    "currency": "USD",
    "tax_region": "US-NY"
  }'
```

---

## Database Schema

### User Table
```sql
- id (PK)
- username (unique)
- password_hash
- role (super_admin, restaurant_admin, manager, waiter, kitchen, admin)
- restaurant_id (FK to restaurant.id, nullable)
- is_super_admin (boolean)
- currency (USD, EUR, GBP, INR, etc.)
- locale (en, es, pt, hi, etc.)
- created_at
```

### Restaurant Table
```sql
- id (PK)
- name
- email (unique)
- phone, address, city, country, postal_code
- owner_id (FK to user.id) - restaurant_admin user
- active (boolean)
- created_at, updated_at
```

### StoreSettings Table
```sql
- id (PK)
- restaurant_id (FK to restaurant.id, unique)
- timezone (e.g., 'Europe/Dublin', 'America/New_York', 'Asia/Kolkata')
- locale (en, es, pt, hi, etc.)
- currency (USD, EUR, GBP, INR, BRL, etc.)
- tax_region (EU, US-CA, US-NY, IN, BR, etc.)
- address_format (standard, european, asian)
- business_registration
- vat_number
- payment_terms (days)
- invoice_prefix
- created_at, updated_at
```

---

## Key Features

✓ Multi-tenant isolation (data per restaurant)
✓ Role-based access control (super admin vs restaurant admin)
✓ Per-restaurant configuration (timezone, currency, tax region)
✓ Audit logging (all changes tracked)
✓ Free beta SaaS model
✓ Extensible for monetization

---

## Migration History

```
001_add_new_models.py - Initial schema
002_add_user_currency.py - User currency preference
003_add_exchange_rates.py - Exchange rate tracking
004_add_user_locale.py - User locale preference
005_add_tax_rules.py - Tax configuration per region
006_add_restaurant_store_settings.py - Multi-tenant support
```

---

## Testing

Run tests:
```bash
python3 -m pytest test_currency.py test_tax.py -v
```

Seed data:
```bash
python3 seed.py
```

Start server:
```bash
flask run
```

---

## Error Responses

### 401 Unauthorized
```json
{"error": "User not authenticated"}
```

### 403 Forbidden
```json
{"error": "Unauthorized - super admin only"}
```

### 404 Not Found
```json
{"error": "Restaurant not found"}
```

### 400 Bad Request
```json
{"error": "Missing required fields: ['name', 'email']"}
```

### 500 Server Error
```json
{"error": "Internal server error message"}
```

---

## Future Enhancements

- [ ] Subscription tiers (Free, Pro, Enterprise)
- [ ] Multi-location support per restaurant
- [ ] API keys for 3rd-party integrations
- [ ] Advanced analytics dashboard
- [ ] Loyalty program management
- [ ] Inventory tracking per location
- [ ] Commission/revenue tracking
- [ ] White-label branding
- [ ] GDPR/CCPA compliance
- [ ] 2FA for admin accounts

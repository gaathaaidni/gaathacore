# Sentira AI - VPS Deployment Guide

> **Legacy deployment path:** this guide describes PM2 plus host Nginx. The
> official production method is the Docker Compose stack documented in
> [DEPLOYMENT.md](DEPLOYMENT.md). Do not run both methods on the same host.

**Domain:** sentira.gaatha.tech  
**Status:** Production-Ready Backend with Demo Pipeline  
**Last Updated:** August 16, 2026

---

## ⚠️ Important Considerations

You **cannot simply copy the repo and change the port**. Here's why and what you need to do instead:

### Issues with Simple Copy-Paste

1. **Dependencies Not Installed** - `node_modules/` not in git
2. **Ports Conflict** - Default ports (3001, 3000, 5432) likely in use
3. **Database Credentials** - `.env.local` not in git (for security)
4. **Multiple Services** - PostgreSQL, Redis, RabbitMQ, MinIO need setup
5. **Domain SSL/TLS** - sentira.gaatha.tech needs HTTPS configured
6. **Reverse Proxy** - Nginx/Apache needed to route traffic
7. **Process Management** - PM2 or systemd for auto-restart
8. **Logs & Monitoring** - No centralized logging

---

## 🚀 Production Deployment Checklist

### Phase 1: Server Preparation (1-2 hours)

#### 1.1 SSH into VPS
```bash
ssh user@sentira.gaatha.tech
cd /var/www  # or your preferred directory
```

#### 1.2 Clone Repository
```bash
git clone https://github.com/gaathaaidni/sentira.git sentira-api
cd sentira-api
```

#### 1.3 Install Node.js & npm (if not already installed)
```bash
# Check existing version
node --version
npm --version

# If not installed (Ubuntu/Debian):
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 1.4 Install Dependencies
```bash
npm install
cd apps/api && npm install
cd ../web && npm install
cd ../../
```

---

### Phase 2: Environment Configuration (30 minutes)

#### 2.1 Create Production `.env.local`
```bash
cp apps/api/.env.example apps/api/.env.production
nano apps/api/.env.production
```

**Production `.env.production` settings:**
```bash
# Application
NODE_ENV=production
PORT=4000                    # Internal app port (not exposed)
FRONTEND_URL=https://sentira.gaatha.tech
BACKEND_URL=https://sentira.gaatha.tech/api

# Database (adjust if sharing with other apps)
DB_HOST=localhost
DB_PORT=5432
DB_USER=sentira_user
DB_PASSWORD=STRONG_RANDOM_PASSWORD_HERE
DB_NAME=sentira_prod

# JWT (CHANGE THIS!)
JWT_SECRET=GENERATE_STRONG_SECRET_KEY_HERE

# Optional: Redis/RabbitMQ/MinIO
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sentira-media

# Logging
LOG_LEVEL=info
```

**Generate Secure Secrets:**
```bash
# Generate JWT secret
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Generate DB password
openssl rand -base64 32
```

#### 2.2 Database Setup

**Option A: Use Existing PostgreSQL**
```bash
# If you already have PostgreSQL running:

# Connect to psql
sudo -u postgres psql

# Create database and user
CREATE DATABASE sentira_prod;
CREATE USER sentira_user WITH PASSWORD 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE sentira_prod TO sentira_user;

# Exit
\q
```

**Option B: Use Docker Containers**
```bash
# If PostgreSQL not running and you want containerized:
docker-compose up -d postgres redis rabbitmq minio
```

---

### Phase 3: Port Management (Important!)

Since you have other apps running, use a **reverse proxy** approach:

#### 3.1 Port Allocation Strategy

```
Internet (HTTPS 443) ↓ sentira.gaatha.tech
            ↓
    Nginx (Reverse Proxy on 80/443)
            ↓
    ┌───────┴──────────┬────────────┬───────────┐
    ↓                  ↓            ↓           ↓
Sentira Web      Sentira API  Your App 2   Your App 3
(localhost:3001) (localhost:4000) (localhost:3003) (localhost:3004)
```

#### 3.2 Nginx Configuration

**File:** `/etc/nginx/sites-available/sentira`

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name sentira.gaatha.tech;
    
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sentira.gaatha.tech;

    # SSL Certificates (use Let's Encrypt with certbot)
    ssl_certificate /etc/letsencrypt/live/sentira.gaatha.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sentira.gaatha.tech/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Logging
    access_log /var/log/nginx/sentira-access.log;
    error_log /var/log/nginx/sentira-error.log;

    # Frontend (Next.js on 3000)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API (NestJS on 3001)
    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (for real-time updates)
    location /socket.io {
        proxy_pass http://localhost:3001/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check (internal)
    location /health {
        access_log off;
        proxy_pass http://localhost:3001/health;
    }
}
```

**Enable the site:**
```bash
sudo ln -s /etc/nginx/sites-available/sentira /etc/nginx/sites-enabled/
sudo nginx -t  # Test config
sudo systemctl reload nginx
```

#### 3.3 SSL Certificate Setup

```bash
# Install certbot (if not already)
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate for sentira.gaatha.tech
sudo certbot certonly --nginx -d sentira.gaatha.tech

# Auto-renewal (already configured with systemd)
sudo systemctl enable certbot.timer
```

---

### Phase 4: Process Management with PM2 (30 minutes)

Use **PM2** to manage both API and frontend processes with auto-restart:

#### 4.1 Install PM2
```bash
sudo npm install -g pm2
```

#### 4.2 Create Ecosystem File

**File:** `/var/www/sentira-api/ecosystem.config.js`

```javascript
module.exports = {
  apps: [
    {
      name: 'sentira-api',
      script: './apps/api/dist/main.js',
      cwd: '/var/www/sentira-api',
      instances: 2,              // Run on 2 CPU cores
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3001,
        DB_HOST: 'localhost',
        DB_PORT: 5432
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3001
      },
      watch: false,              // Don't auto-reload
      max_memory_restart: '500M',
      error_file: '/var/log/pm2/sentira-api-error.log',
      out_file: '/var/log/pm2/sentira-api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    },
    {
      name: 'sentira-web',
      script: 'npm run start',
      cwd: '/var/www/sentira-api/apps/web',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PORT: 3001,
        NEXT_PUBLIC_API_URL: 'https://sentira.gaatha.tech'
      },
      watch: false,
      max_memory_restart: '500M',
      error_file: '/var/log/pm2/sentira-web-error.log',
      out_file: '/var/log/pm2/sentira-web-out.log',
      autorestart: true
    }
  ]
};
```

#### 4.3 Build and Start

```bash
# Build API
npm --workspace apps/api run build

# Build Next.js frontend
npm --workspace apps/web run build

# Start with PM2
pm2 start ecosystem.config.js --env production

# Save PM2 config for auto-start on reboot
pm2 save
pm2 startup

# Verify processes
pm2 status
pm2 logs
```

#### 4.4 Monitor & Logs

```bash
# View real-time logs
pm2 logs

# View only API logs
pm2 logs sentira-api

# View only web logs
pm2 logs sentira-web

# Restart specific process
pm2 restart sentira-api

# Stop all
pm2 stop all

# Delete all
pm2 delete all
```

---

### Phase 5: Database Setup & Migrations

#### 5.1 TypeORM Synchronization (Development Mode)

Currently using `synchronize: true` (auto-schema update):

```typescript
// apps/api/src/config/database.config.ts
export function databaseConfig(): TypeOrmModuleOptions {
  return {
    synchronize: process.env.NODE_ENV !== 'production',  // ← Disabled in production
    // ... rest of config
  };
}
```

#### 5.2 Database Initialization

```bash
# Connect to PostgreSQL
psql -h localhost -U sentira_user -d sentira_prod

# You can manually run these SQL statements or create a migration:

CREATE TABLE IF NOT EXISTS organizations (...);
CREATE TABLE IF NOT EXISTS sites (...);
CREATE TABLE IF NOT EXISTS users (...);
-- ... etc for all 13 entities
```

For now, use **manual initialization** or run a one-time sync:

```bash
# On first deployment only:
NODE_ENV=development npm run start

# Then shut it down and switch to:
NODE_ENV=production npm run start
```

#### 5.3 Future: Database Migrations

```bash
# Generate migration (when schema changes):
npm --workspace apps/api run typeorm migration:generate src/migrations/InitialSchema

# Run migrations:
npm --workspace apps/api run typeorm migration:run
```

---

### Phase 6: Monitoring & Health Checks

#### 6.1 Health Endpoint Monitoring

```bash
# Test health endpoint
curl https://sentira.gaatha.tech/health

# Expected response:
# {"status":"ok","name":"Sentira AI API","timestamp":"2024-08-16T..."}
```

#### 6.2 Set Up Monitoring

**Systemd Timer for Health Checks:**

```bash
# File: /etc/systemd/system/sentira-health-check.timer
[Unit]
Description=Sentira Health Check

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

```bash
# File: /etc/systemd/system/sentira-health-check.service
[Unit]
Description=Sentira Health Check

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -f https://sentira.gaatha.tech/health || /usr/bin/systemctl restart sentira-api
```

```bash
sudo systemctl enable sentira-health-check.timer
sudo systemctl start sentira-health-check.timer
```

#### 6.3 Log Aggregation

**Using Journalctl:**
```bash
# View PM2 logs through systemd
journalctl -u pm2-root -f

# View last 100 lines of API logs
journalctl -u sentira-api -n 100
```

---

### Phase 7: Security Hardening

#### 7.1 Firewall Configuration

```bash
# If using UFW (Ubuntu)
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 5432/tcp   # PostgreSQL (localhost only, see below)
sudo ufw enable

# Restrict database access to localhost only
# In PostgreSQL config: /etc/postgresql/*/main/postgresql.conf
listen_addresses = 'localhost'
```

#### 7.2 Environment Variables

**NEVER commit .env files to git!**

```bash
# Create .env.production locally
cat > apps/api/.env.production << EOF
NODE_ENV=production
PORT=3001
DB_HOST=localhost
DB_PORT=5432
DB_USER=sentira_user
DB_PASSWORD=YOUR_SECURE_PASSWORD
DB_NAME=sentira_prod
JWT_SECRET=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
EOF

# Set strict permissions
chmod 600 apps/api/.env.production

# Copy to VPS securely
scp apps/api/.env.production user@sentira.gaatha.tech:/var/www/sentira-api/apps/api/
```

#### 7.3 Database User Privileges

```bash
# Connect as postgres admin
sudo -u postgres psql

# Create restricted user (cannot create databases or roles)
CREATE USER sentira_user WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE sentira_prod TO sentira_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sentira_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sentira_user;

# No DROP privileges
REVOKE ALL ON DATABASE sentira_prod FROM sentira_user;
GRANT CONNECT ON DATABASE sentira_prod TO sentira_user;

\q
```

#### 7.4 API Rate Limiting

**To add (Phase 2):**
```typescript
// apps/api/src/main.ts
import { RateLimitMiddleware } from '@nestjs/throttler';

app.use(
  new RateLimitMiddleware({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 100                    // 100 requests per window
  })
);
```

---

### Phase 8: Backup & Disaster Recovery

#### 8.1 Database Backups

**Daily backup script:**

```bash
#!/bin/bash
# File: /usr/local/bin/sentira-backup.sh

BACKUP_DIR="/backups/sentira"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="sentira_prod"
DB_USER="sentira_user"

mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://your-bucket/sentira-backups/

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

**Cron job (daily at 2 AM):**
```bash
sudo crontab -e

# Add line:
0 2 * * * /usr/local/bin/sentira-backup.sh >> /var/log/sentira-backup.log 2>&1
```

#### 8.2 Application Backups

```bash
# Backup source code
tar -czf /backups/sentira/app_$(date +%Y%m%d).tar.gz /var/www/sentira-api

# Backup environment config
cp /var/www/sentira-api/apps/api/.env.production /backups/sentira/.env.backup
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] VPS server with SSH access
- [ ] Node.js 18+ installed
- [ ] PostgreSQL running (or Docker setup)
- [ ] Domain pointing to VPS IP
- [ ] SSL certificate obtained (Let's Encrypt)

### Deployment Steps
- [ ] Clone repo: `git clone https://github.com/gaathaaidni/netra.git`
- [ ] Install deps: `npm install`
- [ ] Create `.env.production` with secure secrets
- [ ] Setup PostgreSQL database and user
- [ ] Configure Nginx reverse proxy
- [ ] Build API: `npm --workspace apps/api run build`
- [ ] Build Web: `npm --workspace apps/web run build`
- [ ] Install PM2: `sudo npm install -g pm2`
- [ ] Create ecosystem.config.js
- [ ] Start PM2: `pm2 start ecosystem.config.js`
- [ ] Test endpoints: `curl https://sentira.gaatha.tech/health`

### Post-Deployment
- [ ] Verify SSL certificate working
- [ ] Check PM2 logs for errors
- [ ] Test API endpoints with curl
- [ ] Setup database backups
- [ ] Configure health checks
- [ ] Monitor logs for issues
- [ ] Document access credentials

---

## 🔧 Quick Reference Commands

### Check Application Status
```bash
# API health
curl https://sentira.gaatha.tech/health

# Frontend
curl https://sentira.gaatha.tech

# Database connection
psql -h localhost -U sentira_user -d sentira_prod -c "SELECT 1;"

# PM2 status
pm2 status
pm2 logs sentira-api
pm2 logs sentira-web
```

### Restart Services
```bash
# Restart API only
pm2 restart sentira-api

# Restart everything
pm2 restart all

# Rebuild and restart API
npm --workspace apps/api run build && pm2 restart sentira-api
```

### View Logs
```bash
# Real-time logs
pm2 logs

# API only
pm2 logs sentira-api

# Nginx logs
sudo tail -f /var/log/nginx/sentira-error.log
sudo tail -f /var/log/nginx/sentira-access.log
```

### Database Management
```bash
# Connect to database
psql -h localhost -U sentira_user -d sentira_prod

# Backup database
pg_dump -U sentira_user -h localhost sentira_prod > backup.sql

# Restore database
psql -U sentira_user -h localhost sentira_prod < backup.sql
```

---

## 🆘 Troubleshooting

### Application Won't Start
```bash
# Check PM2 logs
pm2 logs sentira-api

# Check Node.js errors
npm --workspace apps/api run dev  # Run in dev to see errors

# Check ports in use (API on 4000, Web on 3001)
lsof -i :4000
lsof -i :3001
```

### Database Connection Error
```bash
# Test PostgreSQL
psql -h localhost -U sentira_user -d sentira_prod -c "SELECT 1;"

# Check PostgreSQL service
sudo systemctl status postgresql

# Verify credentials in .env.production
cat apps/api/.env.production | grep DB_
```

### Nginx Not Routing Correctly
```bash
# Check Nginx config
sudo nginx -t

# View Nginx error log
sudo tail -f /var/log/nginx/sentira-error.log

# Check Nginx is running
sudo systemctl status nginx
```

### SSL Certificate Issues
```bash
# Check certificate
sudo certbot certificates

# Renew manually (auto-renewal handles this)
sudo certbot renew --dry-run

# Check certificate dates
openssl x509 -in /etc/letsencrypt/live/sentira.gaatha.tech/cert.pem -noout -dates
```

---

## 📚 Additional Resources

- **NestJS Deployment:** https://docs.nestjs.com/deployment
- **Next.js Production:** https://nextjs.org/docs/deployment
- **Nginx Configuration:** https://nginx.org/en/docs/
- **PM2 Documentation:** https://pm2.keymetrics.io/docs/usage/quick-start/
- **PostgreSQL Backup:** https://www.postgresql.org/docs/current/backup.html

---

## ⏱️ Estimated Total Setup Time

- **Phase 1 (Preparation):** 1-2 hours
- **Phase 2 (Environment):** 30 minutes
- **Phase 3 (Port Management):** 30 minutes  
- **Phase 4 (Process Management):** 30 minutes
- **Phase 5 (Database):** 30 minutes
- **Phase 6-7 (Monitoring & Security):** 1 hour

**Total: ~5-6 hours for first deployment**

---

## 🎯 Next Steps

1. **Review this guide** with your team
2. **Prepare credentials** (strong passwords, JWT secrets)
3. **Test locally** first (`npm run dev`)
4. **Stage on test VPS** (if available)
5. **Deploy to production** (sentira.gaatha.tech)
6. **Monitor closely** for first 24-48 hours

---

**Important:** Do NOT skip security steps (Phase 7). Always use HTTPS, secure credentials, and database user restrictions.

For questions, refer to individual service documentation or contact the development team.

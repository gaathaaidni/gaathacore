#!/bin/bash

################################################################################
# Sentira AI - VPS Deployment Script
# 
# This script automates the deployment of Sentira AI to production VPS
# Usage: bash deploy.sh
#
# Prerequisites:
# - SSH access to VPS
# - Ubuntu/Debian-based OS
# - Node.js 18+ (optional - script can install)
# - PostgreSQL (optional - script can install via Docker)
#
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="${APP_DIR:-.}"
DOMAIN="${DOMAIN:-sentira.gaatha.tech}"
NODE_PORT="${NODE_PORT:-3001}"
WEB_PORT="${WEB_PORT:-3000}"
DB_NAME="${DB_NAME:-sentira_prod}"
DB_USER="${DB_USER:-sentira_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
ENV_FILE="$APP_DIR/apps/api/.env.production"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_section "Phase 1: Checking Prerequisites"
    
    log_info "Checking Node.js..."
    if ! command -v node &> /dev/null; then
        log_error "Node.js not found. Installing..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
        log_success "Node.js installed"
    else
        NODE_VERSION=$(node --version)
        log_success "Node.js found: $NODE_VERSION"
    fi
    
    log_info "Checking npm..."
    if ! command -v npm &> /dev/null; then
        log_error "npm not found"
        exit 1
    else
        NPM_VERSION=$(npm --version)
        log_success "npm found: $NPM_VERSION"
    fi
    
    log_info "Checking PostgreSQL..."
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL found"
    else
        log_warning "PostgreSQL not found. Install manually or use: docker-compose up -d postgres"
    fi
    
    log_info "Checking PM2..."
    if ! command -v pm2 &> /dev/null; then
        log_info "Installing PM2 globally..."
        sudo npm install -g pm2
        log_success "PM2 installed"
    else
        log_success "PM2 found"
    fi
    
    log_info "Checking Nginx..."
    if ! command -v nginx &> /dev/null; then
        log_warning "Nginx not found. Install with: sudo apt-get install -y nginx"
    else
        log_success "Nginx found"
    fi
}

# Install dependencies
install_dependencies() {
    print_section "Phase 2: Installing Dependencies"
    
    log_info "Installing root dependencies..."
    npm install
    log_success "Root dependencies installed"
    
    log_info "Installing API dependencies..."
    cd "$APP_DIR/apps/api"
    npm install
    cd - > /dev/null
    log_success "API dependencies installed"
    
    log_info "Installing Web dependencies..."
    cd "$APP_DIR/apps/web"
    npm install
    cd - > /dev/null
    log_success "Web dependencies installed"
}

# Setup environment file
setup_environment() {
    print_section "Phase 3: Environment Configuration"
    
    if [ -f "$ENV_FILE" ]; then
        log_warning "Environment file already exists: $ENV_FILE"
        read -p "Overwrite? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping environment setup"
            return
        fi
    fi
    
    log_info "Creating environment file..."
    
    # Generate secrets
    JWT_SECRET=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
    DB_PASSWORD=$(openssl rand -base64 32)
    
    cat > "$ENV_FILE" << EOF
# Application
NODE_ENV=production
PORT=$NODE_PORT
FRONTEND_URL=https://$DOMAIN
BACKEND_URL=https://$DOMAIN/api

# Database
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# JWT
JWT_SECRET=$JWT_SECRET

# Optional
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sentira-media

# Logging
LOG_LEVEL=info
EOF
    
    chmod 600 "$ENV_FILE"
    log_success "Environment file created: $ENV_FILE"
    
    log_info "Generated credentials:"
    echo -e "${YELLOW}DB_USER: $DB_USER${NC}"
    echo -e "${YELLOW}DB_PASSWORD: $DB_PASSWORD${NC}"
    echo -e "${YELLOW}JWT_SECRET: $JWT_SECRET${NC}"
    
    log_warning "Save these credentials in a secure location!"
}

# Setup database
setup_database() {
    print_section "Phase 4: Database Setup"
    
    log_info "Checking PostgreSQL connection..."
    if ! psql -h "$DB_HOST" -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_info "Creating database and user..."
        
        DB_PASSWORD=$(grep "DB_PASSWORD" "$ENV_FILE" | cut -d '=' -f 2)
        
        sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
        
        log_success "Database and user created"
    else
        log_warning "Database already exists: $DB_NAME"
    fi
}

# Build application
build_application() {
    print_section "Phase 5: Building Application"
    
    log_info "Building API..."
    cd "$APP_DIR/apps/api"
    npm run build
    cd - > /dev/null
    log_success "API built"
    
    log_info "Building Web..."
    cd "$APP_DIR/apps/web"
    npm run build
    cd - > /dev/null
    log_success "Web built"
}

# Setup PM2
setup_pm2() {
    print_section "Phase 6: Setting up PM2"
    
    log_info "Creating ecosystem.config.js..."
    
    cat > "$APP_DIR/ecosystem.config.js" << 'EOF'
module.exports = {
  apps: [
    {
      name: 'sentira-api',
      script: './apps/api/dist/main.js',
      instances: 2,
      exec_mode: 'cluster',
      watch: false,
      max_memory_restart: '500M',
      error_file: '/var/log/pm2/sentira-api-error.log',
      out_file: '/var/log/pm2/sentira-api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      autorestart: true
    },
    {
      name: 'sentira-web',
      script: 'npm run start',
      cwd: './apps/web',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '500M',
      error_file: '/var/log/pm2/sentira-web-error.log',
      out_file: '/var/log/pm2/sentira-web-out.log',
      autorestart: true
    }
  ]
};
EOF
    
    log_success "ecosystem.config.js created"
    
    log_info "Starting applications with PM2..."
    pm2 start ecosystem.config.js --env production
    
    log_info "Saving PM2 configuration..."
    pm2 save
    sudo pm2 startup -u $USER --hp /home/$USER
    
    log_success "PM2 configured and started"
    
    log_info "Current PM2 status:"
    pm2 status
}

# Setup Nginx
setup_nginx() {
    print_section "Phase 7: Setting up Nginx"
    
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx not installed. Install with: sudo apt-get install -y nginx"
        return
    fi
    
    NGINX_CONFIG="/etc/nginx/sites-available/sentira"
    
    if [ -f "$NGINX_CONFIG" ]; then
        log_warning "Nginx config already exists"
        read -p "Overwrite? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    log_info "Creating Nginx configuration..."
    
    sudo tee "$NGINX_CONFIG" > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    add_header Strict-Transport-Security "max-age=31536000" always;

    access_log /var/log/nginx/sentira-access.log;
    error_log /var/log/nginx/sentira-error.log;

    location / {
        proxy_pass http://localhost:$WEB_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:$NODE_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /health {
        access_log off;
        proxy_pass http://localhost:$NODE_PORT/health;
    }
}
EOF
    
    log_success "Nginx configuration created"
    
    log_info "Testing Nginx configuration..."
    if sudo nginx -t; then
        log_info "Enabling Nginx site..."
        sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/sentira
        sudo rm -f /etc/nginx/sites-enabled/default
        
        log_info "Reloading Nginx..."
        sudo systemctl reload nginx
        log_success "Nginx configured and reloaded"
    else
        log_error "Nginx configuration test failed"
    fi
}

# Setup SSL
setup_ssl() {
    print_section "Phase 8: SSL Certificate Setup"
    
    if command -v certbot &> /dev/null; then
        log_info "Getting SSL certificate from Let's Encrypt..."
        sudo certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos -m admin@example.com
        log_success "SSL certificate obtained"
    else
        log_warning "Certbot not installed. Install with: sudo apt-get install -y certbot python3-certbot-nginx"
        log_warning "Then run: sudo certbot certonly --nginx -d $DOMAIN"
    fi
}

# Post-deployment checks
post_deployment_checks() {
    print_section "Phase 9: Post-Deployment Checks"
    
    log_info "Waiting 5 seconds for services to start..."
    sleep 5
    
    log_info "Checking API health..."
    if curl -s http://localhost:$NODE_PORT/health > /dev/null; then
        log_success "API is healthy"
    else
        log_error "API health check failed"
    fi
    
    log_info "Checking PM2 status..."
    pm2 status
    
    log_info "Checking Nginx status..."
    sudo systemctl status nginx
}

# Main execution
main() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║       Sentira AI - VPS Deployment Script                     ║"
    echo "║       Domain: $DOMAIN                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_prerequisites
    install_dependencies
    setup_environment
    setup_database
    build_application
    setup_pm2
    setup_nginx
    setup_ssl
    post_deployment_checks
    
    print_section "Deployment Complete!"
    
    echo -e "${GREEN}✓ Sentira AI is now deployed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Access your application: https://$DOMAIN"
    echo "2. Monitor logs: pm2 logs"
    echo "3. View status: pm2 status"
    echo "4. Setup backups: See VPS_DEPLOYMENT.md Phase 8"
    echo ""
    echo "Important credentials saved in: $ENV_FILE"
    echo "Keep this file secure!"
    echo ""
}

# Run main function
main "$@"

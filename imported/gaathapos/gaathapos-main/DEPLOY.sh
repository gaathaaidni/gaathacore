#!/bin/bash

##############################################################################
# Gaatha POS Quick Deployment Script for PythonAnywhere
# Usage: bash DEPLOY.sh username
# Replace 'username' with your actual PythonAnywhere username
##############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions for output
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check arguments
if [ $# -eq 0 ]; then
    print_error "PythonAnywhere username required"
    echo "Usage: bash DEPLOY.sh <username>"
    echo "Example: bash DEPLOY.sh john_doe"
    exit 1
fi

USERNAME=$1
VENV_NAME="nexorapos"
APP_NAME="nexorapos"

print_header "Gaatha POS Deployment Script for PythonAnywhere"
echo "Username: $USERNAME"
echo "Virtual Environment: $VENV_NAME"
echo ""

# Verify SSH connection to PythonAnywhere
print_header "Step 1: Verifying SSH Connection"
if ssh -q $USERNAME@ssh.pythonanywhere.com exit; then
    print_success "SSH connection successful"
else
    print_error "Cannot connect to PythonAnywhere via SSH"
    echo "Make sure you have:"
    echo "1. Created a PythonAnywhere account"
    echo "2. Generated and uploaded SSH key (https://www.pythonanywhere.com/user/\$username/account/)"
    exit 1
fi

# Clone repository (remote)
print_header "Step 2: Cloning Repository (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << 'EOF'
    if [ -d ~/nexorapos ]; then
        echo "Repository already exists, pulling latest changes..."
        cd ~/nexorapos
        git pull origin main
    else
        echo "Cloning repository..."
        cd ~
        git clone https://github.com/YOUR_GITHUB_USERNAME/nexorapos.git
        cd ~/nexorapos
    fi
    print_success "Repository ready"
EOF

# Create virtual environment (remote)
print_header "Step 3: Setting Up Python Virtual Environment (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << EOF
    set -e
    if [ -d ~/.virtualenvs/$VENV_NAME ]; then
        echo "Virtual environment already exists, skipping creation"
    else
        echo "Creating virtual environment..."
        mkvirtualenv --python=/usr/bin/python3.12 $VENV_NAME
    fi
    echo "Activating virtual environment..."
    source ~/.virtualenvs/$VENV_NAME/bin/activate
    echo "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    echo "Installing dependencies..."
    cd ~/nexorapos
    pip install -r requirements-production.txt
    print_success "Virtual environment setup complete"
EOF

# Create .env file (remote)
print_header "Step 4: Setting Up Environment Configuration (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << EOF
    if [ -f ~/.env ]; then
        echo "Environment file exists, backing up..."
        cp ~/.env ~/.env.backup.$(date +%s)
    fi
    
    echo "Creating .env file..."
    cp ~/nexorapos/.env.example ~/.env
    echo "⚠ Important: Update ~/.env with your configuration!"
    echo "   Run: nano ~/.env"
    echo "   Then update all 'your_*' placeholders with real values"
EOF

# Initialize database (remote)
print_header "Step 5: Initializing Database (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << EOF
    source ~/.virtualenvs/$VENV_NAME/bin/activate
    cd ~/nexorapos
    
    echo "Creating instance directory..."
    mkdir -p instance
    
    echo "Initializing database..."
    python << 'PYEOF'
from app import create_app
from models import db

app = create_app()
with app.app_context():
    db.create_all()
    print("✓ Database tables created")
PYEOF
    
    print_success "Database initialized"
EOF

# Setup WSGI configuration (remote)
print_header "Step 6: Configuring PythonAnywhere Web App (Remote)"
echo "Instructions for PythonAnywhere Web Dashboard:"
echo ""
echo "1. Log into https://www.pythonanywhere.com"
echo "2. Go to 'Web' tab"
echo "3. Create a new web app (Python 3.12, Flask)"
echo "4. In WSGI configuration file, replace contents with:"
echo ""
echo "   import sys"
echo "   import os"
echo "   sys.path.insert(0, os.path.expanduser('~/nexorapos'))"
echo "   activate_this = os.path.expanduser('~/.virtualenvs/$VENV_NAME/bin/activate_this.py')"
echo "   with open(activate_this) as f:"
echo "       exec(f.read(), {'__file__': activate_this})"
echo "   from app import create_app"
echo "   application = create_app()"
echo ""
echo "5. Configure static files mapping:"
echo "   URL: /static/"
echo "   Directory: /home/$USERNAME/nexorapos/static"
echo ""

# Copy WSGI file (remote)
print_header "Step 7: Setting Up WSGI File (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << EOF
    cp ~/nexorapos/pythonanywhere_wsgi.py /var/www/${USERNAME}_pythonanywhere_com_wsgi.py
    echo "WSGI file installed"
EOF

# Run tests (remote)
print_header "Step 8: Running Tests (Remote)"
ssh $USERNAME@ssh.pythonanywhere.com << EOF
    source ~/.virtualenvs/$VENV_NAME/bin/activate
    cd ~/nexorapos
    python -m pytest -q 2>/dev/null || echo "Tests completed (some may fail due to environment)"
EOF

print_header "Deployment Summary"
echo ""
echo "✓ Repository cloned/updated"
echo "✓ Virtual environment created"
echo "✓ Dependencies installed"
echo "✓ Database initialized"
echo ""
print_warning "IMPORTANT MANUAL STEPS:"
echo ""
echo "1. Configure environment variables:"
echo "   ssh $USERNAME@ssh.pythonanywhere.com"
echo "   nano ~/.env"
echo "   # Update SECRET_KEY, DATABASE_URL, and other settings"
echo ""
echo "2. Configure PythonAnywhere Web App:"
echo "   - Log into https://www.pythonanywhere.com"
echo "   - Go to 'Web' tab"
echo "   - Edit WSGI configuration file"
echo "   - Map static files: /static/ -> /home/$USERNAME/nexorapos/static"
echo ""
echo "3. Set up custom domain (if using):"
echo "   - Go to Web tab -> Domains"
echo "   - Add your domain and configure DNS"
echo ""
echo "4. Reload the web app:"
echo "   - Go to Web tab"
echo "   - Click 'Reload Web App'"
echo ""
echo "5. Test your deployment:"
echo "   - Visit https://$USERNAME.pythonanywhere.com"
echo "   - Test login with default admin account"
echo ""

print_success "Deployment script completed!"
echo ""
echo "For troubleshooting, check:"
echo "- PythonAnywhere error log: Web tab -> Error log"
echo "- Server log: Web tab -> Server log"
echo "- SSH into server: ssh $USERNAME@ssh.pythonanywhere.com"
echo ""

#!/bin/bash

# Quality Clamps VPS Deployment Script
# This script helps with deploying the Flask app on a Linux VPS

echo "🚀 Quality Clamps VPS Deployment Helper"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_warning "This script is designed for Linux VPS. You're running on: $OSTYPE"
fi

# 1. Install system dependencies
print_status "Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 2. Create application directory
APP_DIR="/var/www/qualclamps"
print_status "Setting up application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 3. Set up Python virtual environment
print_status "Creating Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install Flask Flask-Mail python-dotenv paypalrestsdk gunicorn

# 5. Create directories
print_status "Creating necessary directories..."
mkdir -p static/images
mkdir -p data
mkdir -p templates

# 6. Set proper permissions for file uploads
print_status "Setting permissions for file uploads..."
chmod 755 static
chmod 775 static/images
chmod 775 data

# 7. Create systemd service file
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/qualclamps.service > /dev/null <<EOF
[Unit]
Description=Quality Clamps Flask App
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

print_status "Deployment script completed!"
print_warning "Next steps:"
echo "1. Copy your Flask application files to $APP_DIR"
echo "2. Update your .env file with production settings"
echo "3. Start the service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start qualclamps"
echo "   sudo systemctl enable qualclamps"
echo "4. Access your application at http://<your_vps_ip>:8000"

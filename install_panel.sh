#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║       QVM Panel - One-Click Installer                        ║
# ║       Developer: QVM Panel                           ║
# ║       Version: 1.0                                           ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PANEL_DIR="/opt/qvm-panel"
REPO_URL="${QVM_PANEL_REPO_URL:-https://github.com/stripathi02123-tech/Qvm-Panel.git}"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ██╗  ██╗██╗   ██╗██████╗  ██████╗ ███████╗███╗   ███╗     ║"
echo "║   ██║  ██║██║   ██║██╔══██╗██╔═══██╗██╔════╝████╗ ████║     ║"
echo "║   ███████║██║   ██║██████╔╝██║   ██║███████╗██╔████╔██║     ║"
echo "║   ██╔══██║╚██╗ ██╔╝██╔═══╝ ██║   ██║╚════██║██║╚██╔╝██║     ║"
echo "║   ██║  ██║ ╚████╔╝ ██║     ╚██████╔╝███████║██║ ╚═╝ ██║     ║"
echo "║   ╚═╝  ╚═╝  ╚═══╝  ╚═╝      ╚═════╝ ╚══════╝╚═╝     ╚═╝     ║"
echo "║                                                               ║"
echo "║         QVM Panel Installer — QVM Panel               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/7] Updating system packages...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl lxc lxc-utils lxc-templates > /dev/null 2>&1

echo -e "${YELLOW}[2/7] Cloning QVM Panel repository...${NC}"
if [ -d "$PANEL_DIR" ]; then
    echo -e "${YELLOW}  Panel directory exists, pulling latest...${NC}"
    cd "$PANEL_DIR"
    git pull origin main 2>/dev/null || true
else
    git clone "$REPO_URL" "$PANEL_DIR"
    cd "$PANEL_DIR"
fi

echo -e "${YELLOW}[3/7] Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[4/7] Installing Python dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -e "${YELLOW}[5/7] Configuring environment...${NC}"
if [ ! -f .env ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    cat > .env << EOF
# QVM Panel Configuration
PANEL_NAME=QVM Panel
PANEL_VERSION=1.0
PANEL_DEVELOPER=QVM Panel
SECRET_KEY=${SECRET_KEY}
DATABASE_PATH=avm.db
HOST=0.0.0.0
PORT=5000
MAIN_ADMIN_USERNAME=admin
MAIN_ADMIN_PASSWORD=admin
MAIN_ADMIN_EMAIL=admin@localhost
YOUR_SERVER_IP=$(hostname -I | awk '{print $1}')
DEFAULT_STORAGE_POOL=default
DEBUG_MODE=False
AI_API_KEY=
EOF
    echo -e "${GREEN}  .env file created with random secret key${NC}"
fi

echo -e "${YELLOW}[6/7] Creating systemd service...${NC}"
cat > /etc/systemd/system/qvm-panel.service << EOF
[Unit]
Description=QVM Panel - VPS Management Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PANEL_DIR}
Environment=PATH=${PANEL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=${PANEL_DIR}/venv/bin/python3 avm.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qvm-panel
systemctl start qvm-panel

echo -e "${YELLOW}[7/7] Verifying installation...${NC}"
sleep 3
if curl -s http://127.0.0.1:5000/api/v1/health | grep -q "healthy"; then
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    INSTALLATION COMPLETE                     ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}  Panel URL:  http://$(hostname -I | awk '{print $1}'):5000${NC}"
    echo -e "${CYAN}  Admin User: admin${NC}"
    echo -e "${CYAN}  Admin Pass: admin${NC}"
    echo ""
    echo -e "${YELLOW}  Service: systemctl status qvm-panel${NC}"
    echo -e "${YELLOW}  Logs:    journalctl -u qvm-panel -f${NC}"
    echo -e "${YELLOW}  Config:  ${PANEL_DIR}/.env${NC}"
    echo ""
else
    echo -e "${RED}  Installation may have issues. Check logs:${NC}"
    echo -e "${RED}  journalctl -u qvm-panel -f${NC}"
fi

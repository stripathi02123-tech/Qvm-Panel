#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║       QVM Panel - Node Agent Installer                       ║
# ║       Developer: QVM Panel                           ║
# ║       Version: 1.0                                           ║
# ╚═══════════════════════════════════════════════════════════════╝

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

NODE_DIR="/opt/qvm-node"
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
echo "║       Node Agent Installer — QVM Panel                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get panel URL and API key from user
echo -e "${YELLOW}Enter your QVM Panel details:${NC}"
read -p "  Panel URL (e.g., http://panel.example.com:5000): " PANEL_URL
read -p "  Node API Key (from admin panel → Nodes → Create): " NODE_API_KEY

if [ -z "$PANEL_URL" ] || [ -z "$NODE_API_KEY" ]; then
    echo -e "${RED}Error: Panel URL and API Key are required!${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl lxc lxc-utils lxc-templates > /dev/null 2>&1

echo -e "${YELLOW}[2/6] Cloning QVM Panel repository...${NC}"
if [ -d "$NODE_DIR" ]; then
    echo -e "${YELLOW}  Node directory exists, pulling latest...${NC}"
    cd "$NODE_DIR"
    git pull origin main 2>/dev/null || true
else
    git clone "$REPO_URL" "$NODE_DIR"
    cd "$NODE_DIR"
fi

echo -e "${YELLOW}[3/6] Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[4/6] Installing Python dependencies...${NC}"
pip install --upgrade pip -q
pip install flask requests psutil -q

echo -e "${YELLOW}[5/6] Configuring node agent...${NC}"
cat > .env << EOF
# QVM Node Agent Configuration
API_KEY=${NODE_API_KEY}
HOST=0.0.0.0
PORT=5001
HEALTH_MONITOR_INTERVAL=60
EOF

cat > /etc/systemd/system/qvm-node.service << EOF
[Unit]
Description=QVM Panel Node Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${NODE_DIR}
Environment=PATH=${NODE_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=${NODE_DIR}/venv/bin/python3 node.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable qvm-node
systemctl start qvm-node

echo -e "${YELLOW}[6/6] Verifying node agent...${NC}"
sleep 3
if curl -s http://127.0.0.1:5001/api/health | grep -q "ok"; then
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                  NODE AGENT INSTALLED                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}  Node URL:  http://$(hostname -I | awk '{print $1}'):5001${NC}"
    echo -e "${CYAN}  Panel:     ${PANEL_URL}${NC}"
    echo ""
    echo -e "${YELLOW}  Now add this node in QVM Panel:${NC}"
    echo -e "${YELLOW}  1. Go to Admin → Nodes → Create Node${NC}"
    echo -e "${YELLOW}  2. Enter URL: http://$(hostname -I | awk '{print $1}'):5001${NC}"
    echo -e "${YELLOW}  3. Paste the API Key you used above${NC}"
    echo -e "${YELLOW}  4. Test connection${NC}"
    echo ""
    echo -e "${YELLOW}  Service: systemctl status qvm-node${NC}"
    echo -e "${YELLOW}  Logs:    journalctl -u qvm-node -f${NC}"
else
    echo -e "${RED}  Node agent may have issues. Check logs:${NC}"
    echo -e "${RED}  journalctl -u qvm-node -f${NC}"
fi

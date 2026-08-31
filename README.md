<div align="center">

# ⚡ QVM Panel

### VPS & Virtual Machine Management Panel

**by QVM Panel**

[![Version](https://img.shields.io/badge/Version-v1.0-blue?style=for-the-badge)](https://github.com/stripathi02123-tech/Qvm-Panel)
[![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?style=for-the-badge&logo=vercel&logoColor=white)](https://qvm-panel.vercel.app)

[**🚀 Live Demo**](https://qvm-panel.vercel.app) · [**📖 Documentation**](#-quick-start) · [**💬 Discord**](#-support)

</div>

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🖥️ **LXC Containers** | Create & manage LXC containers with real-time deploy progress |
| 💻 **Virtual Machines** | QEMU/KVM VMs with cloud-init (Debian 12, Ubuntu 24) |
| 🖵 **noVNC Console** | Desktop-like RDP access for VMs |
| ⌨️ **SSH Console** | Browser-based terminal with auto-filled credentials |
| 🤖 **Discord Bot** | Deploy VPS, manage servers from Discord |
| 🔐 **OAuth Login** | Google & Discord authentication |
| 🐳 **Docker Support** | Docker-in-LXC with one toggle |
| 🖥️ **KVM Virtualization** | Nested virtualization with one toggle |
| 📊 **Real-time Stats** | Live CPU, RAM, disk monitoring |
| 🔄 **Auto Backup** | Automated LXC snapshots |
| 🌐 **Port Forwarding** | Manage port forwards per VPS |
| 📱 **Responsive UI** | Works on desktop and mobile |

---

## ⚡ Quick Start

### One-Click Panel Install

```bash
curl -sL https://raw.githubusercontent.com/stripathi02123-tech/Qvm-Panel/master/install_panel.sh | bash
```

> ☝️ **Copy the command above** and paste it into your server terminal.

### One-Click Node Agent Install

```bash
curl -sL https://raw.githubusercontent.com/stripathi02123-tech/Qvm-Panel/master/install_node.sh | bash
```

> ☝️ **Copy the command above** and paste it on each node server.

---

## 🛠️ Manual Installation

### Prerequisites
- Python 3.10+
- LXC/LXD
- MongoDB Atlas account (free)

### Step 1: Clone Repository

```bash
git clone https://github.com/stripathi02123-tech/Qvm-Panel.git
cd QVM-Panel
```

### Step 2: Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
cat > .env << 'EOF'
MONGODB_URI=mongodb+srv://your-connection-string
MONGODB_DB=qvm_panel
PANEL_NAME=QVM Panel
SECRET_KEY=your-secret-key
PORT=5000
EOF
```

### Step 4: Start Server

```bash
python3 avm.py
```

---

## 📋 Default Credentials

| Field | Value |
|-------|-------|
| **URL** | `http://your-server:5000` |
| **Username** | `admin` |
| **Password** | `admin` |

> ⚠️ **Change the default password immediately after first login!**

---

## 🏗️ Architecture

```
QVM Panel
├── avm.py          # Main Flask application
├── node.py         # Node agent for remote servers
├── discord_bot.py  # Discord bot with admin commands
├── db.py           # MongoDB database layer
├── api.py          # REST API endpoints
├── install_panel.sh    # One-click panel installer
├── install_node.sh     # One-click node installer
├── templates/      # HTML templates
├── static/         # CSS, JS, images
└── requirements.txt
```

---

## 🤖 Discord Bot Commands

| Command | Description |
|---------|-------------|
| `!deploy` | Interactive VPS deployment wizard |
| `!status` | View all VPS status |
| `!vps <id>` | View VPS details |
| `!start <id>` | Start a VPS |
| `!stop <id>` | Stop a VPS |
| `!restart <id>` | Restart a VPS |
| `!delete <id>` | Delete a VPS |
| `!nodes` | View node status |
| `!users` | List all users |
| `!stats` | Panel statistics |

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/info` | GET | API information |
| `/api/v1/users` | GET | List users (admin) |
| `/api/v1/vps` | GET | List VPS |
| `/api/v1/vps/<id>/start` | POST | Start VPS |
| `/api/v1/vps/<id>/stop` | POST | Stop VPS |
| `/api/v1/nodes` | GET | List nodes (admin) |

---

## 🌐 Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | — | MongoDB Atlas connection string |
| `MONGODB_DB` | `qvm_panel` | Database name |
| `PANEL_NAME` | `QVM Panel` | Panel display name |
| `SECRET_KEY` | auto-generated | Flask secret key |
| `PORT` | `5000` | Server port |
| `MAIN_ADMIN_USERNAME` | `admin` | Admin username |
| `MAIN_ADMIN_PASSWORD` | `admin` | Admin password |

---

## 🤝 Support

- **GitHub Issues:** [Report a Bug](https://github.com/stripathi02123-tech/Qvm-Panel/issues)
- **Discord:** Join our community server

---

## 📄 License

MIT License - Free to use, modify, and distribute.

---

<div align="center">

**Built with ❤️ by [QVM Panel](https://github.com/stripathi02123-tech/Qvm-Panel)**

⭐ Star this repo if you find it useful!

</div>

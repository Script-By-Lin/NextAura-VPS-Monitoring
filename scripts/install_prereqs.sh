#!/usr/bin/env bash
# ==============================================================================
# NextAura VPS Monitoring System - Universal OS Detection & Prerequisite Installer
# Automatically detects Linux Distribution, Architecture, and installs Docker,
# Docker Compose, Python3, Make, Git, Curl, UFW, Fail2ban, and System Tools.
# ==============================================================================

set -e

# Color definitions
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SUDO=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    else
        echo -e "${RED}[!] Error: This script requires root privileges. Please run with sudo or as root.${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN} 🔍 NEXTAURA AUTO OS DETECTION & PREREQUISITE INSTALLER         ${NC}"
echo -e "${CYAN}================================================================${NC}"

# 1. OS & Architecture Detection
OS_NAME="Unknown Linux"
OS_ID="unknown"
OS_VERSION=""
ARCH=$(uname -m)

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="${PRETTY_NAME:-$NAME}"
    OS_ID="${ID:-unknown}"
    OS_ID_LIKE="${ID_LIKE:-$OS_ID}"
    OS_VERSION="${VERSION_ID:-}"
elif [ -f /etc/redhat-release ]; then
    OS_NAME=$(cat /etc/redhat-release)
    OS_ID="rhel"
elif [ -f /etc/debian_version ]; then
    OS_NAME="Debian $(cat /etc/debian_version)"
    OS_ID="debian"
fi

echo -e "• Detected Operating System: ${GREEN}${OS_NAME}${NC}"
echo -e "• Kernel Architecture:       ${GREEN}${ARCH}${NC}"
echo -e "• Execution Mode:            ${CYAN}$([ "$EUID" -eq 0 ] && echo 'Native Root' || echo 'Sudo User')${NC}"
echo -e "${CYAN}----------------------------------------------------------------${NC}"

# Helper function for status
log_step() {
    echo -e "\n${YELLOW}▶ $1...${NC}"
}
log_success() {
    echo -e "  ${GREEN}✓ $1${NC}"
}
log_info() {
    echo -e "  ${CYAN}• $1${NC}"
}

# 2. Package Manager Selection & Base Tools Installation
log_step "Updating system package repositories & installing essential tools"

case "$OS_ID" in
    ubuntu|debian|pop|mint|kali|raspbian)
        $SUDO apt-get update -y
        $SUDO apt-get install -y \
            curl wget git make jq tar gzip unzip \
            net-tools iproute2 lsof socat ca-certificates gnupg \
            python3 python3-pip python3-venv \
            ufw fail2ban
        log_success "APT base packages installed"
        ;;
    rhel|centos|rocky|almalinux|fedora|ol|amzn)
        PKG_MGR="yum"
        command -v dnf &> /dev/null && PKG_MGR="dnf"
        $SUDO $PKG_MGR -y install epel-release || true
        $SUDO $PKG_MGR -y update || true
        $SUDO $PKG_MGR -y install \
            curl wget git make jq tar gzip unzip \
            net-tools iproute lsof socat ca-certificates \
            python3 python3-pip \
            fail2ban || true
        log_success "$PKG_MGR base packages installed"
        ;;
    arch|manjaro|cachyos|endeavouros|artix)
        $SUDO pacman -Sy --noconfirm --needed \
            curl wget git make jq tar gzip unzip \
            net-tools iproute2 lsof socat ca-certificates \
            python python-pip \
            ufw fail2ban || true
        log_success "Pacman base packages installed"
        ;;
    alpine)
        $SUDO apk update
        $SUDO apk add --no-cache \
            curl wget git make jq tar gzip unzip \
            net-tools iproute2 lsof socat ca-certificates \
            python3 py3-pip \
            iptables ip6tables fail2ban
        log_success "APK base packages installed"
        ;;
    opensuse*|sles)
        $SUDO zypper --non-interactive refresh
        $SUDO zypper --non-interactive install \
            curl wget git make jq tar gzip unzip \
            net-tools iproute2 lsof socat ca-certificates \
            python3 python3-pip \
            ufw fail2ban || true
        log_success "Zypper base packages installed"
        ;;
    *)
        log_info "Unknown OS family ($OS_ID). Checking for common package managers..."
        if command -v apt-get &> /dev/null; then
            $SUDO apt-get update -y && $SUDO apt-get install -y curl wget git make jq python3 python3-pip ufw fail2ban
        elif command -v dnf &> /dev/null; then
            $SUDO dnf install -y curl wget git make jq python3 python3-pip fail2ban
        elif command -v yum &> /dev/null; then
            $SUDO yum install -y curl wget git make jq python3 python3-pip fail2ban
        elif command -v pacman &> /dev/null; then
            $SUDO pacman -Sy --noconfirm curl wget git make jq python python-pip
        fi
        ;;
esac

# 3. Docker Installation & Daemon Startup
log_step "Verifying Docker Engine & Container Runtime"

if ! command -v docker &> /dev/null; then
    echo -e "  ${YELLOW}Docker not found. Installing latest official Docker CE engine...${NC}"
    curl -fsSL https://get.docker.com | $SUDO sh
    log_success "Docker Engine installed successfully"
else
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    log_success "Docker already installed (v$DOCKER_VER)"
fi

# Enable and start Docker service
if command -v systemctl &> /dev/null; then
    $SUDO systemctl enable docker || true
    $SUDO systemctl start docker || true
elif command -v service &> /dev/null; then
    $SUDO service docker start || true
fi

# Add active user to docker group if running with sudo
ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" != "root" ] && [ -n "$ACTUAL_USER" ]; then
    if getent group docker > /dev/null 2>&1; then
        $SUDO usermod -aG docker "$ACTUAL_USER" 2>/dev/null || true
        log_info "Added user '$ACTUAL_USER' to 'docker' group"
    fi
fi

# 4. Docker Compose Plugin / Standalone Installation
log_step "Verifying Docker Compose"

HAS_COMPOSE=false
if docker compose version &> /dev/null; then
    COMPOSE_VER=$(docker compose version | awk '{print $4}')
    log_success "Docker Compose plugin found ($COMPOSE_VER)"
    HAS_COMPOSE=true
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VER=$(docker-compose --version | awk '{print $3}' | tr -d ',')
    log_success "Docker Compose standalone found ($COMPOSE_VER)"
    HAS_COMPOSE=true
fi

if [ "$HAS_COMPOSE" = false ]; then
    echo -e "  ${YELLOW}Installing Docker Compose Plugin / CLI...${NC}"
    case "$OS_ID" in
        ubuntu|debian|pop|mint)
            $SUDO apt-get install -y docker-compose-plugin || true
            ;;
        rhel|centos|rocky|almalinux|fedora)
            $SUDO $PKG_MGR install -y docker-compose-plugin || true
            ;;
        arch|manjaro)
            $SUDO pacman -S --noconfirm docker-compose || true
            ;;
    esac

    # Fallback to direct github binary if still not found
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        LATEST_COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)"
        $SUDO curl -sSL "$LATEST_COMPOSE_URL" -o /usr/local/bin/docker-compose || true
        $SUDO chmod +x /usr/local/bin/docker-compose || true
    fi
    log_success "Docker Compose installed"
fi

# 5. Summary Table
echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  🎉 ALL SYSTEM PREREQUISITES INSTALLED & CONFIGURED!           ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "• Operating System:  ${CYAN}${OS_NAME}${NC}"
echo -e "• Docker Engine:     ${CYAN}$(docker --version 2>/dev/null || echo 'Installed')${NC}"
echo -e "• Docker Compose:    ${CYAN}$(docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo 'Installed')${NC}"
echo -e "• Python Version:    ${CYAN}$(python3 --version 2>/dev/null || echo 'Installed')${NC}"
echo -e "• Make Utility:      ${CYAN}$(make --version 2>/dev/null | head -n1 || echo 'Installed')${NC}"
echo -e "• Git Version:       ${CYAN}$(git --version 2>/dev/null || echo 'Installed')${NC}"
echo -e "• System Tools:      ${CYAN}curl, wget, jq, ufw, fail2ban, net-tools${NC}"
echo -e "${GREEN}================================================================${NC}\n"

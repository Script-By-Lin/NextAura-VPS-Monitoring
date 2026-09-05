#!/usr/bin/env bash
# ==============================================================================
# One-Command Production Observability & Security Platform Setup
# ==============================================================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cat << 'EOF'
    _   __          __  ___                  
   / | / /__  _  __/ /_/   | __  ___________ _
  /  |/ / _ \| |/_/ __/ /| |/ / / / ___/ __ `/
 / /|  /  __/>  </ /_/ ___ / /_/ / /  / /_/ / 
/_/ |_/\___/_/|_|\__/_/  |_\__,_/_/   \__,_/  

      ⚡ VPS OBSERVABILITY & SECURITY PLATFORM ⚡
EOF


echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  🚀 Deploying NextAura VPS Observability & Security Stack     ${NC}"
echo -e "${CYAN}================================================================${NC}"


# 1. Check & Auto-Install Prerequisites (Docker, Compose, Python3, Git, etc.)
echo -e "\n${YELLOW}[1/6] Auto-detecting OS & verifying system prerequisites...${NC}"
if [ -f scripts/install_prereqs.sh ]; then
    bash scripts/install_prereqs.sh
else
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Installing Docker...${NC}"
        curl -fsSL https://get.docker.com | sh
    fi
fi
echo -e "${GREEN}✓ System prerequisites & Docker runtime verified.${NC}"


# 2. Prepare Environment File & Service Discovery Scan
echo -e "\n${YELLOW}[2/6] Preparing environment configuration & host service scan...${NC}"
if [ ! -f .env ]; then
    echo -e "Creating .env from .env.example..."
    cp .env.example .env
fi

# Run non-interactive service discovery check if python3 available
if command -v python3 &> /dev/null && [ -f scripts/scanner.py ]; then
    PYTHONPATH=scripts python3 -c "import scanner; svcs = scanner.scan_listening_ports(); scanner.print_discovery_table(svcs)" 2>/dev/null || true
fi
echo -e "${GREEN}✓ .env configuration is ready.${NC}"


# 3. Create Host Directories & Set Permissions
echo -e "\n${YELLOW}[3/6] Setting up required directories and volume permissions...${NC}"
mkdir -p /tmp/vps_monitoring_logs/fastapi
mkdir -p /tmp/vps_monitoring_logs/nginx
mkdir -p configs/alertmanager/templates
chmod 777 /tmp/vps_monitoring_logs/fastapi /tmp/vps_monitoring_logs/nginx 2>/dev/null || true
echo -e "${GREEN}✓ Directories created.${NC}"

# 4. Pull and Build Containers
echo -e "\n${YELLOW}[4/6] Building FastAPI APM and pulling observability images...${NC}"
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

# 5. Wait for Services to Warm Up
echo -e "\n${YELLOW}[5/6] Waiting for services to initialize...${NC}"
sleep 5

# 6. Verify Health Status
echo -e "\n${YELLOW}[6/6] Verifying system health...${NC}"
if [ -f scripts/healthcheck.sh ]; then
    bash scripts/healthcheck.sh
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  🎉 OBSERVABILITY & SECURITY PLATFORM IS LIVE!                 ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "📊 ${CYAN}Grafana Dashboards:${NC}       http://localhost:3000 (User: admin)"
echo -e "🚀 ${CYAN}FastAPI Application:${NC}      http://localhost:8000"
echo -e "📖 ${CYAN}FastAPI Interactive Docs:${NC} http://localhost:8000/docs"
echo -e "📈 ${CYAN}Prometheus UI:${NC}            http://localhost:9090"
echo -e "🚨 ${CYAN}Alertmanager UI:${NC}          http://localhost:9093"
echo -e "📜 ${CYAN}Loki Log Server:${NC}          http://localhost:3100"
echo -e "⏱️  ${CYAN}Tempo Trace Server:${NC}       http://localhost:3200"
echo -e "🌐 ${CYAN}Nginx Reverse Proxy:${NC}      http://localhost:80"
echo -e "\n💡 Next steps:"
echo -e "   - Run synthetic load test:  ${YELLOW}make test-load${NC} (or python3 scripts/load_test.py)"
echo -e "   - Trigger test alert:       ${YELLOW}make test-alert${NC} (or bash scripts/test_alert.sh)"
echo -e "   - Inspect diagnostics:      ${YELLOW}make healthcheck${NC}"

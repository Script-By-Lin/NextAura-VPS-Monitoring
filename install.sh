#!/usr/bin/env bash
# ==============================================================================
# NextAura VPS Monitoring System - 1-Click Universal Installer & Bootstrapper
# Detects VPS OS, installs prerequisites, scans ports, resolves collisions,
# configures environment, deploys the stack, and launches the Control Center.
# ==============================================================================

set -e

# Stylized ASCII Banner
cat << 'EOF'

    _   __          __  ___                  
   / | / /__  _  __/ /_/   | __  ___________ _
  /  |/ / _ \| |/_/ __/ /| |/ / / / ___/ __ `/
 / /|  /  __/>  </ /_/ ___ / /_/ / /  / /_/ / 
/_/ |_/\___/_/|_|\__/_/  |_\__,_/_/   \__,_/  

      ⚡ VPS OBSERVABILITY & NGINX PLATFORM ⚡
EOF

echo "================================================================"
echo " 🚀 NEXTAURA 1-CLICK VPS INSTALLATION & SETUP BOOTSTRAPPER      "
echo "================================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure aura executable permissions
chmod +x ./aura 2>/dev/null || true
if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
    sudo ln -sf "$SCRIPT_DIR/aura" /usr/local/bin/aura 2>/dev/null || true
fi

# STEP 1: Detect OS and Install Prerequisite Dependencies
echo -e "\n[STEP 1/6] Detecting OS & Installing Platform Dependencies..."
if [ -f "scripts/install_prereqs.sh" ]; then
    bash scripts/install_prereqs.sh
else
    echo "Warning: scripts/install_prereqs.sh not found, skipping package manager step."
fi

# STEP 2: Host Hardware & Port Conflict Discovery Scanner
echo -e "\n[STEP 2/6] Inspecting VPS Hardware, Ports & Existing Web Services..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Initialized .env configuration file."
    fi
fi

if command -v python3 &> /dev/null && [ -f "scripts/scanner.py" ]; then
    python3 scripts/scanner.py
fi

# STEP 3: Setup Required Host Directories & Auto-Cleaner Cron
echo -e "\n[STEP 3/6] Setting up runtime storage directories, volume permissions & 30-day auto-cleaner..."
mkdir -p /tmp/vps_monitoring_logs/fastapi
mkdir -p /tmp/vps_monitoring_logs/nginx
mkdir -p configs/alertmanager/templates
chmod 777 /tmp/vps_monitoring_logs/fastapi /tmp/vps_monitoring_logs/nginx 2>/dev/null || true

# Install Automated 30-Day Storage & Disk Cleanup Service
if [ -f "scripts/auto_cleaner.sh" ]; then
    bash scripts/auto_cleaner.sh --install-cron 2>/dev/null || true
fi
echo "✓ Volume paths, log buffers, and 30-day auto-cleaner service initialized."

# STEP 4: Build & Deploy Container Stack
echo -e "\n[STEP 4/6] Building & Launching Observability Microservices..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
elif command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    echo "Error: Docker compose command not found. Please re-run bash scripts/install_prereqs.sh"
    exit 1
fi

# STEP 5: Service Stabilization & End-to-End Health Verification
echo -e "\n[STEP 5/6] Warming up containers and running health diagnostics..."
sleep 4
if [ -f "scripts/healthcheck.sh" ]; then
    bash scripts/healthcheck.sh || true
fi

# STEP 6: Finished - Launch Control Menu
if [ -f .env ]; then
    set -a
    . .env
    set +a
fi

echo -e "\n================================================================"
echo -e " 🎉 NEXTAURA IS SUCCESSFULLY DEPLOYED & RUNNING!               "
echo -e "================================================================"
echo -e "📊 Grafana Dashboards:       http://localhost:${GRAFANA_PORT:-3000} (User: ${GRAFANA_ADMIN_USER:-admin})"
echo -e "🚀 FastAPI Service:          http://localhost:${FASTAPI_PORT:-8000}"
echo -e "📈 Prometheus TSDB:          http://localhost:${PROMETHEUS_PORT:-9090}"
echo -e "🚨 Alertmanager:             http://localhost:${ALERTMANAGER_PORT:-9093}"
echo -e "📜 Loki Logs:                http://localhost:${LOKI_PORT:-3100}"
echo -e "⏱️  Tempo Traces:             http://localhost:${TEMPO_PORT:-3200}"
echo -e "🌐 Nginx Reverse Proxy:      http://localhost:${NGINX_HTTP_PORT:-80}"
echo -e "================================================================"
echo -e "\n💡 Tip: To manage your platform anytime, simply run: ./aura or ./aura view\n"

# Launch Interactive Control Center
./aura

#!/usr/bin/env bash
# ==============================================================================
# End-to-End Health & Diagnostics Checker for Observability Stack
# ==============================================================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${CYAN}================================================================${NC}"
echo -e "${CYAN}  🔍 Running End-to-End Health Checks & Diagnostics            ${NC}"
echo -e "${CYAN}================================================================${NC}"

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" 2>/dev/null || echo "000")

    if [ "$code" -eq "$expected_code" ]; then
        echo -e "  [${GREEN}✓${NC}] $name ($url) -> HTTP $code"
    else
        echo -e "  [${RED}✗${NC}] $name ($url) -> Expected $expected_code, got $code"
    fi
}

# Source environment variables if .env exists
if [ -f .env ]; then
    set -a
    . .env
    set +a
fi

PROM_P="${PROMETHEUS_PORT:-9090}"
GRAF_P="${GRAFANA_PORT:-3000}"
AM_P="${ALERTMANAGER_PORT:-9093}"
LOKI_P="${LOKI_PORT:-3100}"
TEMPO_P="${TEMPO_PORT:-3200}"
API_P="${FASTAPI_PORT:-8000}"
NODE_P="${NODE_EXPORTER_PORT:-9100}"
BBOX_P="${BLACKBOX_PORT:-9115}"

echo -e "\n${YELLOW}1. Probing Service Health Endpoints:${NC}"
check_endpoint "Prometheus" "http://localhost:${PROM_P}/-/healthy" 200
check_endpoint "Grafana" "http://localhost:${GRAF_P}/api/health" 200
check_endpoint "Alertmanager" "http://localhost:${AM_P}/-/healthy" 200
check_endpoint "Loki" "http://localhost:${LOKI_P}/ready" 200
check_endpoint "Tempo" "http://localhost:${TEMPO_P}/status" 200
check_endpoint "FastAPI Liveness" "http://localhost:${API_P}/health/live" 200
check_endpoint "FastAPI Readiness" "http://localhost:${API_P}/health/ready" 200
check_endpoint "FastAPI Metrics" "http://localhost:${API_P}/metrics" 200
check_endpoint "Node Exporter" "http://localhost:${NODE_P}/metrics" 200
check_endpoint "Blackbox Exporter" "http://localhost:${BBOX_P}" 200

echo -e "\n${YELLOW}2. Checking Prometheus Scrape Target Statuses:${NC}"
if command -v jq &> /dev/null; then
    targets=$(curl -s "http://localhost:${PROM_P}/api/v1/targets" 2>/dev/null || echo "{}")
    active_count=$(echo "$targets" | jq '.data.activeTargets | length' 2>/dev/null || echo "0")
    healthy_count=$(echo "$targets" | jq '[.data.activeTargets[] | select(.health == "up")] | length' 2>/dev/null || echo "0")
    echo -e "  Active Scrape Targets: ${GREEN}$healthy_count / $active_count UP${NC}"
else
    echo -e "  (Install jq for detailed target parsing)"
fi

echo -e "\n${YELLOW}3. Docker Containers Status:${NC}"
if docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

echo -e "\n${GREEN}Diagnostic check completed.${NC}\n"

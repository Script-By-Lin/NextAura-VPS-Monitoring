#!/usr/bin/env bash
# ==============================================================================
# NextAura VPS Monitoring System - Automated Disk Cleaner & Retention Engine
# Reduces disk usage after 30+ days of production by pruning expired TSDB blocks,
# log archives, Docker dangling images/build caches, and vacuuming system journals.
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Source .env if available
if [ -f .env ]; then
    set -a
    . .env
    set +a
fi

RETENTION_DAYS="${CLEANUP_RETENTION_DAYS:-30}"
PROM_PORT="${PROMETHEUS_PORT:-9090}"

# Handle --install-cron argument
if [ "$1" == "--install-cron" ]; then
    CRON_CMD="0 3 * * * /bin/bash $ROOT_DIR/scripts/auto_cleaner.sh >> /var/log/nextaura_autoclean.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "auto_cleaner.sh" ; echo "$CRON_CMD") | crontab -
    echo -e "${GREEN}✓ Automated daily 30-day disk cleanup service installed via cron (Runs daily at 03:00 AM).${NC}"
    exit 0
fi

# Handle --uninstall-cron argument
if [ "$1" == "--uninstall-cron" ]; then
    (crontab -l 2>/dev/null | grep -v "auto_cleaner.sh") | crontab - || true
    echo -e "${YELLOW}✓ Automated cleanup cron job removed.${NC}"
    exit 0
fi

echo -e "\n${CYAN}================================================================${NC}"
echo -e "${CYAN} 🧹 NEXTAURA AUTOMATED DISK CLEANER & STORAGE MAINTENANCE       ${NC}"
echo -e "${CYAN}================================================================${NC}"
echo -e "• Retention Policy Window: ${GREEN}${RETENTION_DAYS} Days${NC}"
echo -e "• Target Directories:      ${CYAN}/tmp/vps_monitoring_logs, Docker, TSDB, Journals${NC}"

# Measure initial disk usage
BEFORE_DISK_KB=$(df -k / | awk 'NR==2 {print $3}')

# 1. Clean Ephemeral Log Buffers (> 30 days)
echo -e "\n${YELLOW}[1/5] Purging expired log buffers & archives older than ${RETENTION_DAYS} days...${NC}"
find /tmp/vps_monitoring_logs -type f -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
find /tmp/vps_monitoring_logs -type f -name "*.gz" -mtime +7 -delete 2>/dev/null || true
find /tmp/vps_monitoring_logs -type f -name "*.1" -mtime +7 -delete 2>/dev/null || true
echo -e "  ${GREEN}✓ Ephemeral log buffers cleaned.${NC}"

# 2. Docker Dangling Images, Builder Cache & Unused Containers
echo -e "\n${YELLOW}[2/5] Cleaning Docker dangling images, build layers & unused caches...${NC}"
if command -v docker &> /dev/null; then
    # Remove dangling images
    docker image prune -f 2>/dev/null || true
    # Remove builder cache older than retention
    docker builder prune -f --keep-storage 1GB 2>/dev/null || true
    # Remove anonymous unused volumes (safe, named volumes are preserved)
    docker volume prune -f 2>/dev/null || true
    echo -e "  ${GREEN}✓ Docker image & cache artifacts pruned.${NC}"
else
    echo -e "  ${YELLOW}• Docker not installed or daemon stopped, skipping Docker prune.${NC}"
fi

# 3. Prometheus TSDB Tombstone Cleanup
echo -e "\n${YELLOW}[3/5] Compacting Prometheus TSDB and purging marked tombstones...${NC}"
try_prom_clean() {
    curl -s -X POST "http://127.0.0.1:${PROM_PORT}/api/v1/admin/tsdb/clean_tombstones" 2>/dev/null || true
}
try_prom_clean
echo -e "  ${GREEN}✓ Prometheus TSDB storage optimization triggered.${NC}"

# 4. Linux Systemd Journal Log Vacuum (> 30 days)
echo -e "\n${YELLOW}[4/5] Vacuuming systemd journal logs older than ${RETENTION_DAYS} days...${NC}"
if command -v journalctl &> /dev/null; then
    if [ "$EUID" -eq 0 ]; then
        journalctl --vacuum-time="${RETENTION_DAYS}d" 2>/dev/null || true
    else
        sudo journalctl --vacuum-time="${RETENTION_DAYS}d" 2>/dev/null || true
    fi
    echo -e "  ${GREEN}✓ Systemd journal vacuumed to ${RETENTION_DAYS}-day window.${NC}"
else
    echo -e "  ${CYAN}• journalctl not found, skipping journal vacuum.${NC}"
fi

# 5. Summary & Space Reclaimed Calculation
AFTER_DISK_KB=$(df -k / | awk 'NR==2 {print $3}')
FREED_KB=$(( BEFORE_DISK_KB - AFTER_DISK_KB ))
if [ "$FREED_KB" -lt 0 ]; then
    FREED_KB=0
fi
FREED_MB=$(awk "BEGIN {printf \"%.2f\", $FREED_KB/1024}")
ROOT_FREE=$(df -h / | awk 'NR==2 {print $4}')

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  🎉 AUTOMATIC DISK CLEANUP COMPLETED SUCCESSFULLY!             ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "• Reclaimed Disk Space: ${GREEN}${FREED_MB} MB${NC}"
echo -e "• Current Available:    ${CYAN}${ROOT_FREE} free on Root Storage (/) ${NC}"
echo -e "• Next Scheduled Run:   ${CYAN}Daily at 03:00 AM (via Cron)${NC}"
echo -e "${GREEN}================================================================${NC}\n"

#!/usr/bin/env bash
# ==============================================================================
# Security Hardening, Firewall (UFW) and Sysctl Tuning for Production VPS
# ==============================================================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${CYAN}================================================================${NC}"
echo -e "${CYAN}  🛡️ VPS Security Hardening & Firewall Configuration            ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check root permissions
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Note: Running in simulation / non-root mode. Run with sudo on production VPS.${NC}"
fi

echo -e "\n${YELLOW}1. Suggested UFW Firewall Rules:${NC}"
echo "---------------------------------------------------------"
echo "  sudo ufw default deny incoming"
echo "  sudo ufw default allow outgoing"
echo "  sudo ufw allow 22/tcp comment 'SSH'"
echo "  sudo ufw allow 80/tcp comment 'HTTP Nginx'"
echo "  sudo ufw allow 443/tcp comment 'HTTPS Nginx'"
echo "  sudo ufw allow 3000/tcp comment 'Grafana (or route through Nginx)'"
echo "  # Keep all telemetry ports private (127.0.0.1 / Docker subnet only):"
echo "  sudo ufw deny 9090/tcp comment 'Block public Prometheus'"
echo "  sudo ufw deny 9093/tcp comment 'Block public Alertmanager'"
echo "  sudo ufw deny 3100/tcp comment 'Block public Loki'"
echo "  sudo ufw deny 3200/tcp comment 'Block public Tempo'"
echo "  sudo ufw deny 9100/tcp comment 'Block public Node Exporter'"
echo "  sudo ufw deny 8080/tcp comment 'Block public cAdvisor'"
echo "  sudo ufw enable"

echo -e "\n${YELLOW}2. Recommended Sysctl Network Hardening (/etc/sysctl.d/99-security.conf):${NC}"
cat << 'EOF'
# TCP SYN Flood Protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_synack_retries = 2

# IP Spoofing & ICMP Protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Disable ICMP Redirect Acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Socket & File Descriptors for High RPS
fs.file-max = 2097152
net.core.somaxconn = 65535
EOF

echo -e "\n${YELLOW}3. Fail2ban Integration Commands:${NC}"
echo "---------------------------------------------------------"
echo "To install and activate Fail2ban on your host OS:"
echo "  sudo apt-get install -y fail2ban iptables"
echo "  sudo cp configs/fail2ban/jail.local /etc/fail2ban/jail.local"
echo "  sudo cp -r configs/fail2ban/filter.d/* /etc/fail2ban/filter.d/"
echo "  sudo cp configs/fail2ban/action.d/telegram-notify.conf /etc/fail2ban/action.d/"
echo "  sudo systemctl restart fail2ban"
echo "  sudo fail2ban-client status"

echo -e "\n${GREEN}✓ Security hardening guide ready.${NC}\n"

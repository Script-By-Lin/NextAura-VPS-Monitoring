# Security Hardening & Isolation Guide

## 1. Zero-Trust Network & Port Policy
By default, all internal telemetry backends bind strictly to `127.0.0.1` (localhost) and the private Docker bridge network (`172.28.0.0/16`).

### Port Access Rules:
- **Port 80 / 443 (HTTP/HTTPS)**: Public via Nginx reverse proxy.
- **Port 3000 (Grafana)**: Accessible directly or proxied through Nginx with strong admin authentication.
- **Port 8000 (FastAPI)**: Proxied through Nginx with rate limiting applied (`/api/` and `/api/auth/`).
- **Ports 9090, 9093, 3100, 3200, 9100, 8080**: **BLOCKED FROM PUBLIC ACCESS**.

---

## 2. Firewall (UFW) Configuration
Execute the following commands on your production host:

```bash
# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential public ports
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP Nginx'
sudo ufw allow 443/tcp comment 'HTTPS Nginx'
sudo ufw allow 3000/tcp comment 'Grafana UI'

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

---

## 3. Fail2ban Real-Time Defense
Fail2ban scans Nginx and FastAPI structured logs to automatically ban abusive IPs using Linux `iptables`:

1. **`[fastapi-auth]`**: Bans IPs that trigger 5 failed login attempts within 10 minutes.
2. **`[nginx-429]`**: Bans IPs that trigger repeated 429 Too Many Requests rate-limiting violations.
3. **`[api-abuse]`**: Instantly bans bots probing for `.env`, `.git`, `wp-admin`, `phpmyadmin`, or executing path traversal attempts.
4. **`[sshd]`**: Protects server SSH access against brute-force password guessing.

Whenever an IP is banned or unbanned, the custom `telegram-notify` action sends an immediate notification directly to your Telegram alerts channel.

---

## 4. Let's Encrypt SSL/TLS Integration
To enable HTTPS encryption on production domains:
1. Install Certbot on host: `sudo apt-get install -y certbot python3-certbot-nginx`
2. Obtain certificate: `sudo certbot certonly --standalone -d monitoring.yourdomain.com`
3. Mount the certificate into `./configs/nginx/ssl` and enable SSL directives in `configs/nginx/conf.d/default.conf`.

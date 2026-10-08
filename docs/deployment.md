# Production Server Deployment Guide

This guide details deploying the self-hosted NSE stock analysis platform to an internet-facing Linux server (Ubuntu 22.04 / 24.04 LTS or Debian 12).

---

## 1. Server Prerequisites & Architecture

- **Hardware:** 2 vCPUs, 4GB RAM minimum (8GB recommended if hosting local Ollama).
- **OS:** Ubuntu 22.04+ or Debian 12 LTS.
- **Firewall:** Open ports 80 (HTTP), 443 (HTTPS), and 22 (SSH).
- **Domain:** A domain or subdomain pointed via DNS A-record to your server's public IP (e.g., `nse.yourdomain.com`).

---

## 2. Hardening the Host Server

### A. Non-Root User & Firewall
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### B. Install Docker & Docker Compose
```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

---

## 3. Deployment Directory Setup

Clone your repository to `/opt/nse-analysis`:
```bash
sudo mkdir -p /opt/nse-analysis
sudo chown -R $USER:$USER /opt/nse-analysis
git clone <your-repo-url> /opt/nse-analysis
cd /opt/nse-analysis
```

Create production `.env`:
```bash
cp .env.example .env
chmod 600 .env
```

### Production `.env` Settings
Ensure the following variables are strictly customized:
```ini
POSTGRES_USER=nse_admin
POSTGRES_PASSWORD=use_a_generated_64_char_alphanumeric_password
POSTGRES_DB=nse_production
DATABASE_URL=postgresql://nse_admin:use_a_generated_64_char_alphanumeric_password@db:5432/nse_production

SECRET_KEY=generate_with_openssl_rand_hex_32
ALLOWED_ORIGINS=https://nse.yourdomain.com

# Enable mandatory API authentication
AUTH_ENABLED=true
APP_API_KEY=generate_strong_secret_api_key

DEFAULT_PROVIDER=yahoo
NEXT_PUBLIC_API_URL=https://nse.yourdomain.com
```

---

## 4. HTTPS & Reverse Proxy Configuration

### Option A: Certbot on Host with Standalone NGINX
If you manage TLS certificates on the host:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

Configure `/etc/nginx/sites-available/nse.yourdomain.com`:
```nginx
server {
    server_name nse.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:80; # Points to containerized NGINX
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Obtain SSL certificate:
```bash
sudo certbot --nginx -d nse.yourdomain.com
```

### Option B: Cloudflare / Reverse Proxy Tunnel
Alternatively, use Cloudflare Tunnels (`cloudflared`) to expose port 80 to `https://nse.yourdomain.com` without opening ports 80/443 on the server firewall.

---

## 5. Starting the Production System

```bash
cd /opt/nse-analysis
docker compose up -d --build
```

Verify services:
```bash
docker compose ps
docker compose logs -f
```

---

## 6. Backup & Restore Procedures

### Automated Daily Database Backup
Create backup script at `/opt/nse-analysis/scripts/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/nse-analysis/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Run pg_dump within container
docker compose -f /opt/nse-analysis/docker-compose.yml exec -T db \
  pg_dump -U nse_admin nse_production | gzip > "$BACKUP_DIR/nse_db_$TIMESTAMP.sql.gz"

# Keep last 14 days of backups
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +14 -delete
```
Make executable:
```bash
chmod +x /opt/nse-analysis/scripts/backup.sh
```

Add to cron (`crontab -e`):
```cron
# Backup database daily at 2:00 AM IST
0 2 * * * /opt/nse-analysis/scripts/backup.sh >> /var/log/nse_backup.log 2>&1
```

### Database Restore Procedure
To restore from a backup:
```bash
# 1. Stop web services
docker compose stop backend worker frontend

# 2. Decompress and restore SQL dump
gunzip -c /opt/nse-analysis/backups/nse_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose exec -T db psql -U nse_admin -d nse_production

# 3. Restart services
docker compose start backend worker frontend
```

---

## 7. Upgrades & Zero-Downtime Deployment

To deploy software updates:
```bash
cd /opt/nse-analysis
git pull origin main

# Rebuild images and migrate database
docker compose build backend worker frontend
docker compose run --rm backend alembic upgrade head
docker compose up -d
```

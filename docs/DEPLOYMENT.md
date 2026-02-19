# DataBridge Pipeline — Deployment Guide

## Server Requirements

| Component   | Minimum                      |
|-------------|------------------------------|
| OS          | RHEL 8/9, Rocky 9, Ubuntu 22 |
| CPU         | 4 cores                      |
| RAM         | 8 GB                         |
| Disk        | 50 GB (OS + app)             |
| Network     | Access to staging/prod mounts |
| PostgreSQL  | 15+ (existing studio server) |
| Redis       | 7+                           |
| Python      | 3.9+                         |
| Node.js     | 20+                          |

## 1. Install System Dependencies

### RHEL / Rocky Linux 9
```bash
# As root
dnf install -y python3.11 python3.11-pip python3.11-devel
dnf install -y gcc libffi-devel openldap-devel
dnf install -y redis
dnf install -y clamav clamav-update    # optional, for virus scanning

# Node.js 20
curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
dnf install -y nodejs

# Start Redis
systemctl enable --now redis
```

### Ubuntu 22.04
```bash
apt update && apt install -y python3.11 python3.11-venv python3-pip
apt install -y build-essential libffi-dev libldap2-dev libsasl2-dev
apt install -y redis-server clamav
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
systemctl enable --now redis-server
```

## 2. PostgreSQL Setup

DataBridge connects to your existing PostgreSQL instance.

```bash
# Connect as postgres superuser
su -c "psql -U postgres" root

# Create database and user
CREATE DATABASE databridge_db;
CREATE USER databridge_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE databridge_db TO databridge_user;
\c databridge_db
GRANT ALL ON SCHEMA public TO databridge_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO databridge_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO databridge_user;
\q
```

## 3. Application Installation

```bash
# Create application directory
mkdir -p /opt/databridge-pipeline
cd /opt/databridge-pipeline

# Clone the repository
git clone <repo-url> .

# Backend setup
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary

# Frontend build
cd ../frontend
npm ci --production=false
npm run build
cd ..
```

## 4. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with production values:

```ini
# Database
DATABASE_URL=postgresql+asyncpg://databridge_user:STRONG_PASSWORD@db-server:5432/databridge_db

# Redis (local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# LDAP
LDAP_ENABLED=true
LDAP_SERVER=ldap://your-ad-server:389
LDAP_BASE_DN=dc=yourstudio,dc=com
LDAP_BIND_DN=cn=databridge,ou=services,dc=yourstudio,dc=com
LDAP_BIND_PASSWORD=your_ldap_bind_password

# ShotGrid
SHOTGRID_ENABLED=true
SHOTGRID_URL=https://yourstudio.shotgrid.autodesk.com
SHOTGRID_SCRIPT_NAME=databridge
SHOTGRID_API_KEY=your_api_key

# JWT (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your_64_char_random_string_here

# Paths
STAGING_NETWORK_PATH=/mnt/staging
PRODUCTION_NETWORK_PATH=/mnt/production
UPLOAD_TEMP_PATH=/tmp/databridge_uploads

# SMTP
SMTP_HOST=smtp.yourstudio.com
SMTP_PORT=587
SMTP_FROM_EMAIL=databridge@yourstudio.com

# ClamAV
CLAMAV_ENABLED=true

# Production settings
DEBUG=false
LOG_LEVEL=INFO
```

## 5. LDAP Configuration

DataBridge maps AD groups to application roles. Configure the role mapping in `.env`:

```ini
# JSON format for LDAP_ROLE_MAP
LDAP_ROLE_MAP='{"cn=artists,ou=groups,dc=studio,dc=com":"artist","cn=team-leads,ou=groups,dc=studio,dc=com":"team_lead","cn=supervisors,ou=groups,dc=studio,dc=com":"supervisor","cn=line-producers,ou=groups,dc=studio,dc=com":"line_producer","cn=data-team,ou=groups,dc=studio,dc=com":"data_team","cn=it-team,ou=groups,dc=studio,dc=com":"it_team","cn=admins,ou=groups,dc=studio,dc=com":"admin"}'
```

The highest-priority group match determines the user's role (admin > it_team > data_team > line_producer > supervisor > team_lead > artist).

## 6. ShotGrid Script Setup

1. In ShotGrid Admin → Scripts, create a new API script named `databridge`
2. Copy the API key
3. Set permissions: Read on Project, Shot, Asset, Task, HumanUser; Create/Update on Version, Note
4. Add the script name and key to `.env`

## 7. Network Mount Setup

Ensure staging and production mounts are accessible:

```bash
# Verify mounts
mount | grep staging
mount | grep production

# Example /etc/fstab entries
nfs-server:/studio/staging    /mnt/staging    nfs    defaults,rw    0 0
nfs-server:/studio/production /mnt/production nfs    defaults,rw    0 0

# Create temp upload directory
mkdir -p /tmp/databridge_uploads
chmod 755 /tmp/databridge_uploads
```

## 8. Run Database Migrations

```bash
cd /opt/databridge-pipeline/backend
source .venv/bin/activate
alembic upgrade head
```

## 9. Create Service User

```bash
useradd -r -s /sbin/nologin -d /opt/databridge-pipeline databridge
chown -R databridge:databridge /opt/databridge-pipeline
```

## 10. Systemd Service Files

Copy the service files:

```bash
cp scripts/databridge.service /etc/systemd/system/
cp scripts/databridge-celery.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now databridge
systemctl enable --now databridge-celery
```

### Verify

```bash
systemctl status databridge
systemctl status databridge-celery
journalctl -u databridge -f
```

## 11. ClamAV Setup (Optional)

```bash
# Update virus definitions
freshclam

# Verify clamscan works
echo "test" > /tmp/testfile.txt
clamscan /tmp/testfile.txt
rm /tmp/testfile.txt
```

Set `CLAMAV_ENABLED=true` in `.env`. If ClamAV is not installed, scans will be skipped gracefully.

## Log File Locations

| Log                  | Location                              |
|----------------------|---------------------------------------|
| Application          | `/var/log/databridge/`                |
| Systemd (app)        | `journalctl -u databridge`            |
| Systemd (celery)     | `journalctl -u databridge-celery`     |
| PostgreSQL           | `/var/log/postgresql/`                |
| Redis                | `/var/log/redis/`                     |
| ClamAV               | `/var/log/clamav/`                    |

Create the log directory:
```bash
mkdir -p /var/log/databridge
chown databridge:databridge /var/log/databridge
```

## Health Check

```bash
curl http://localhost:8000/health
# {"status":"healthy","app":"DataBridge"}
```

## Updating

```bash
cd /opt/databridge-pipeline
git pull origin main

# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd ../frontend
npm ci --production=false
npm run build

# Restart
systemctl restart databridge
systemctl restart databridge-celery
```

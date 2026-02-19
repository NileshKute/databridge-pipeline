# DataBridge Pipeline

Staging-to-Production data transfer management for VFX/Animation studios.

## Requirements
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 (existing studio server)
- Redis (local install)
- LDAP / Active Directory (studio)
- ShotGrid instance (studio)

## Quick Start

1. Clone and setup:
```bash
git clone <repo-url>
cd databridge-pipeline
bash scripts/setup.sh
```

2. Edit `.env` with your credentials (PostgreSQL, LDAP, ShotGrid)

3. Create the database:
```bash
psql -h localhost -U postgres -c "CREATE DATABASE databridge_db;"
psql -h localhost -U postgres -c "CREATE USER databridge_user WITH PASSWORD 'your_password';"
psql -h localhost -U postgres -c "GRANT ALL ON DATABASE databridge_db TO databridge_user;"
```

4. Run migrations:
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

5. Build frontend and start:
```bash
cd frontend && npm run build && cd ..
bash scripts/start.sh
```

6. Open: http://your-server:8000

## Dev Login (when LDAP_ENABLED=false)
| Username | Password | Role |
|----------|----------|------|
| artist1 | artist123 | Artist |
| teamlead1 | teamlead123 | Team Lead |
| supervisor1 | super123 | Supervisor |
| producer1 | producer123 | Line Producer |
| datateam1 | data123 | Data Team |
| it1 | it123 | IT Team |
| admin1 | admin123 | Admin |

## Architecture
- Single server: FastAPI serves React build + API on one port
- Celery workers handle scanning/transfer in background
- Connects to existing PostgreSQL and LDAP
- Network paths: /mnt/staging → /mnt/production

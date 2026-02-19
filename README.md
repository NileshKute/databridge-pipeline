# DataBridge Pipeline v1.0

Staging-to-Production data transfer management for VFX/Animation studios.

Multi-stage approval workflow, ClamAV virus scanning, SHA-256 checksum verification, ShotGrid integration, and role-based access control — all served from a single port on a studio Linux server.

## Requirements

- Python 3.9+
- Node.js 20+
- PostgreSQL 15 (existing studio server)
- Redis (local install)
- LDAP / Active Directory (studio) — optional for development
- ShotGrid instance (studio) — optional for development

## Quick Start

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd databridge-pipeline

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install psycopg2-binary   # needed for Alembic migrations
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2. Environment configuration

```bash
cp .env.example .env
# Edit .env with your credentials
```

Key settings to update:
```ini
DATABASE_URL=postgresql+asyncpg://databridge_user:your_password@localhost:5432/databridge_db
REDIS_URL=redis://localhost:6379/0
LDAP_ENABLED=false          # set to false for local development
SHOTGRID_ENABLED=false      # set to false for local development
```

### 3. Create the database

**Option A** — Using the helper script:
```bash
cd backend
source .venv/bin/activate
python -m scripts.create_db
```

**Option B** — Manually via psql:
```bash
su -c "psql -U postgres" root

# In psql:
CREATE DATABASE databridge_db;
CREATE USER databridge_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE databridge_db TO databridge_user;
\c databridge_db
GRANT ALL ON SCHEMA public TO databridge_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO databridge_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO databridge_user;
\q
```

### 4. Run database migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### 5. Seed development data (optional)

Creates 8 users, 10 sample transfers in various states, approvals, history, and notifications:

```bash
cd backend
source .venv/bin/activate
python -m scripts.seed_data
```

### 6. Build frontend

```bash
cd frontend
npm run build
```

### 7. Start the server

```bash
cd backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 8. Start Celery workers (separate terminal)

```bash
cd backend
source .venv/bin/activate
celery -A backend.app.core.celery_app worker -l info -Q default,scanning,transfer,notifications
```

Open: **http://your-server:8000**

## Production Deployment

For production, use the systemd service files:

```bash
cp scripts/databridge.service /etc/systemd/system/
cp scripts/databridge-celery.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now databridge
systemctl enable --now databridge-celery
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full production deployment guide.

## Development Mode

Run the backend and frontend dev servers separately:

```bash
# Terminal 1 — Backend API
cd backend && source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend dev server (proxies /api to :8000)
cd frontend && npm run dev
```

Frontend dev server runs on **http://localhost:3000**

## Running Tests

```bash
cd backend
source .venv/bin/activate
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v
```

## Dev Login (when LDAP_ENABLED=false)

| Username    | Password     | Role           |
|-------------|--------------|----------------|
| artist1     | artist123    | Artist         |
| artist2     | artist123    | Artist         |
| teamlead1   | teamlead123  | Team Lead      |
| supervisor1 | super123     | Supervisor     |
| producer1   | producer123  | Line Producer  |
| datateam1   | data123      | Data Team      |
| it1         | it123        | IT Team        |
| admin1      | admin123     | Admin          |

## Sample Transfers (after seeding)

| Reference   | Name                  | Status              | Priority |
|-------------|-----------------------|---------------------|----------|
| TRF-00001   | Scene_042_Final_v3    | Pending Supervisor  | Normal   |
| TRF-00002   | Char_Dragon_Textures  | Pending Team Lead   | Normal   |
| TRF-00003   | Env_Forest_Lighting   | Scanning            | High     |
| TRF-00004   | Audio_Score_Ep3       | Transferred         | Normal   |
| TRF-00005   | Anim_Fight_Seq_v4     | Rejected            | High     |
| TRF-00006   | Comp_Explosion_Final  | Pending Line Prod.  | Urgent   |
| TRF-00007   | Env_City_Assets       | Transferred         | Normal   |
| TRF-00008   | Char_Hero_Rig_v5      | Pending Team Lead   | High     |
| TRF-00009   | Tex_Vehicle_Pack      | Approved            | Normal   |
| TRF-00010   | Light_Interior_v2     | Uploaded            | Low      |

## Pipeline Flow

```
Artist Upload → Team Lead Review → Supervisor Review → Line Producer Approval
    → Data Team Scan (ClamAV + SHA-256) → IT Transfer (rsync/cp)
    → Checksum Verification → Production Delivery
```

## Architecture

- **Single server**: FastAPI serves React build + API on one port (:8000)
- **Celery workers**: Handle scanning, file transfer, email notifications
- **PostgreSQL**: Existing studio database server
- **Redis**: Local — JWT blacklist, Celery broker, result backend
- **LDAP**: Authenticates against studio Active Directory
- **ShotGrid**: Links transfers to shots/assets, creates versions
- **Network paths**: `/mnt/staging` → `/mnt/production`

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, component diagrams |
| [docs/API.md](docs/API.md) | Complete REST API reference with examples |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment, systemd, LDAP, ShotGrid setup |

## Database Migrations

```bash
cd backend
source .venv/bin/activate

# Apply all migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Roll back everything
alembic downgrade base

# Re-seed after rollback
alembic upgrade head && python -m scripts.seed_data
```

## Project Structure

```
databridge-pipeline/
├── backend/
│   ├── alembic/             # Database migrations
│   │   ├── versions/        # Migration files
│   │   └── env.py           # Alembic configuration
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── core/            # Config, database, security, celery
│   │   ├── integrations/    # LDAP, ShotGrid clients
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic layer
│   │   ├── tasks/           # Celery background tasks
│   │   ├── middleware/       # Request logging
│   │   └── main.py          # FastAPI app entry point
│   ├── scripts/             # DB setup, seed data
│   ├── tests/               # pytest test suite
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios API client
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks (useAuth, useRole)
│   │   ├── pages/           # Route pages
│   │   ├── store/           # Zustand stores
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Formatters, constants
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md      # System design
│   ├── API.md               # API reference
│   └── DEPLOYMENT.md        # Production guide
├── scripts/
│   ├── databridge.service   # Systemd service (app)
│   ├── databridge-celery.service  # Systemd service (workers)
│   ├── setup.sh             # Initial setup
│   └── init_db.sh           # DB initialization
├── .env.example
├── .gitignore
└── README.md
```

## License

Internal studio tool — proprietary.

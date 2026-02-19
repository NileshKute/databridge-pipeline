# DataBridge Pipeline — Architecture

## System Overview

DataBridge Pipeline is a full-stack web application that manages secure data transfers from staging to production networks in a VFX/Animation studio. It enforces a multi-stage approval workflow, virus scanning, checksum verification, and integrates with ShotGrid for asset tracking.

## Data Flow

```
Artist Upload → Team Lead Review → Supervisor Review → Line Producer Approval
    → Data Team Scan (ClamAV + SHA-256) → IT Transfer (rsync/cp)
    → Checksum Verification → Production Delivery
```

### Detailed Pipeline

1. **Upload** — Artist creates a transfer, uploads files to staging storage
2. **Approval Chain** — Sequential review: Team Lead → Supervisor → Line Producer
3. **Scanning** — Data Team initiates virus scan (ClamAV) + SHA-256 checksum calculation
4. **Preparation** — Production directory created, files staged for transfer
5. **Transfer** — IT Team triggers rsync/cp from staging to production
6. **Verification** — Post-transfer checksum comparison ensures integrity
7. **Delivery** — ShotGrid Version entity created, stakeholders notified

### Rejection Flow

At any approval stage, a reviewer can reject the transfer with a reason. The transfer returns to the artist for re-submission. The rejection reason and full history are preserved.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (React SPA)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │Transfers │ │Approvals │ │ Upload   │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └─────────────┴────────────┴─────────────┘                 │
│                         │  Axios API calls                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │  HTTP :8000
┌─────────────────────────┼───────────────────────────────────────┐
│                    FastAPI Server                                 │
│  ┌──────────────────────┴──────────────────────┐                 │
│  │              REST API  /api/v1/              │                 │
│  │  auth | transfers | approvals | shotgrid     │                 │
│  │  scanning | transfer-ops | notifications     │                 │
│  │  activity | users                            │                 │
│  └──────┬──────────────┬───────────────┬────────┘                │
│         │              │               │                          │
│  ┌──────┴───┐  ┌───────┴────┐  ┌──────┴──────┐                  │
│  │ Services │  │Dependencies│  │ Middleware   │                  │
│  │ Layer    │  │ (JWT, RBAC)│  │ (Logging)   │                  │
│  └──────┬───┘  └────────────┘  └─────────────┘                  │
│         │                                                         │
│  ┌──────┴────────────────────────────────────┐                   │
│  │         SQLAlchemy Async ORM               │                   │
│  │  Users | Transfers | Files | Approvals     │                   │
│  │  History | Notifications                   │                   │
│  └──────┬────────────────────────────────────┘                   │
└─────────┼────────────────────────────────────────────────────────┘
          │
┌─────────┼──────────┐  ┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL 15     │  │    Redis          │  │  Celery Workers  │
│  ┌──────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │
│  │ 6 tables     │  │  │  │JWT blacklist│  │  │  │ scanning   │  │
│  │ + enums      │  │  │  │Celery broker│  │  │  │ transfer   │  │
│  └──────────────┘  │  │  │Result store │  │  │  │ email      │  │
└────────────────────┘  │  └────────────┘  │  │  │ maintenance│  │
                        └──────────────────┘  │  └────────────┘  │
                                              └──────────────────┘
          │                                            │
┌─────────┴──────────────────────────────────┐  ┌─────┴──────────┐
│           Filesystem                        │  │  External      │
│  /mnt/staging/TRF-XXXXX/  (uploaded files)  │  │  ┌──────────┐  │
│  /mnt/production/{project}/{category}/      │  │  │ LDAP / AD│  │
│  /tmp/databridge_uploads/  (temp)           │  │  │ ShotGrid │  │
└─────────────────────────────────────────────┘  │  │ ClamAV   │  │
                                                  │  │ SMTP     │  │
                                                  │  └──────────┘  │
                                                  └────────────────┘
```

## Security

### Authentication
- **LDAP/AD**: Primary authentication against studio Active Directory
- **Fallback**: Local bcrypt password auth when LDAP is disabled (development)
- **JWT Tokens**: Access (8h) + Refresh (7d) tokens, HS256 signed
- **Token Blacklist**: Redis-backed blacklist for logout/revocation

### Authorization (RBAC)
| Role           | Capabilities                                    |
|----------------|------------------------------------------------|
| Artist         | Create transfers, upload files, view own         |
| Team Lead      | Approve/reject at TL stage                      |
| Supervisor     | Approve/reject at SV stage                      |
| Line Producer  | Approve/reject at LP stage                      |
| Data Team      | Initiate scans, process approved transfers      |
| IT Team        | Execute transfers, verify checksums              |
| Admin          | Full access, override approvals                  |

### File Security
- **Virus Scanning**: ClamAV subprocess scan on all uploaded files
- **Checksums**: SHA-256 calculated at upload, verified post-transfer
- **Path Isolation**: Each transfer gets its own staging directory

## Network & Storage

```
Studio Network:
  ┌───────────────┐     rsync/cp      ┌──────────────────┐
  │  /mnt/staging  │ ───────────────► │  /mnt/production  │
  │  (NFS mount)   │                   │  (NFS mount)      │
  └───────────────┘                   └──────────────────┘

  Upload flow:  Browser → /tmp/databridge_uploads → /mnt/staging/TRF-XXXXX/
  Transfer:     /mnt/staging/TRF-XXXXX/ → /mnt/production/{project}/{category}/TRF-XXXXX/
```

## Technology Stack

| Layer       | Technology                                |
|-------------|------------------------------------------|
| Frontend    | React 18, TypeScript, Vite, TailwindCSS  |
| State       | Zustand                                   |
| Backend     | Python 3.9+, FastAPI, SQLAlchemy 2.0     |
| Database    | PostgreSQL 15                             |
| Cache/Queue | Redis                                    |
| Background  | Celery (scanning, transfer, email queues) |
| Auth        | LDAP3, PyJWT, Passlib                    |
| Pipeline    | ShotGrid Python API                       |
| Transfer    | rsync / cp                                |
| Scanning    | ClamAV (clamscan)                         |

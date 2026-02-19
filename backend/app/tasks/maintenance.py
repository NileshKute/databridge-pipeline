from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import Transfer, TransferStatus
from backend.app.models.user import User, UserRole

logger = logging.getLogger("databridge.tasks.maintenance")

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(name="backend.app.tasks.maintenance.cleanup_stale_transfers")
def cleanup_stale_transfers() -> dict:
    db: Session = SyncSession()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stale_statuses = [
            TransferStatus.SCANNING,
            TransferStatus.TRANSFERRING,
            TransferStatus.VERIFYING,
            TransferStatus.COPYING,
        ]

        stale = db.query(Transfer).filter(
            Transfer.status.in_(stale_statuses),
            Transfer.updated_at < cutoff,
        ).all()

        if not stale:
            logger.info("No stale transfers found")
            return {"stale_count": 0}

        admins = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
        ).all()

        refs = [t.reference for t in stale]
        msg = (
            f"{len(stale)} transfer(s) have been stuck for >24 hours: "
            f"{', '.join(refs[:10])}"
        )

        for admin in admins:
            db.add(Notification(
                user_id=admin.id,
                type=NotificationType.SYSTEM,
                title="Stale transfers detected",
                message=msg,
            ))

        db.commit()
        logger.warning("Found %d stale transfers: %s", len(stale), ", ".join(refs))
        return {"stale_count": len(stale), "references": refs}

    except Exception:
        logger.exception("Error in cleanup_stale_transfers")
        db.rollback()
        return {"error": "Failed"}
    finally:
        db.close()


@celery_app.task(name="backend.app.tasks.maintenance.sync_shotgrid_users")
def sync_shotgrid_users() -> dict:
    if not settings.SHOTGRID_ENABLED:
        logger.info("ShotGrid disabled — skipping user sync")
        return {"synced": 0, "skipped": True}

    db: Session = SyncSession()
    try:
        from backend.app.integrations.shotgrid import shotgrid_client

        users = db.query(User).filter(
            User.is_active.is_(True),
            User.shotgrid_user_id.is_(None),
        ).all()

        synced = 0
        for user in users:
            sg_user = shotgrid_client.get_user_by_login(user.username)
            if sg_user and sg_user.get("id"):
                user.shotgrid_user_id = sg_user["id"]
                synced += 1
                logger.info("Linked SG user: %s → id=%d", user.username, sg_user["id"])

        db.commit()
        logger.info("ShotGrid user sync: %d/%d linked", synced, len(users))
        return {"synced": synced, "total_checked": len(users)}

    except Exception:
        logger.exception("Error in sync_shotgrid_users")
        db.rollback()
        return {"error": "Failed"}
    finally:
        db.close()

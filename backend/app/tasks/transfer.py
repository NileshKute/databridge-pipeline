from __future__ import annotations

import hashlib
import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.models.history import TransferHistory
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus
from backend.app.models.user import User, UserRole

logger = logging.getLogger("databridge.tasks.transfer")

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)

CHUNK_SIZE = 1024 * 1024


def _compute_checksum(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _notify_role(db: Session, role: UserRole, transfer: Transfer, ntype: NotificationType, title: str, message: str):
    users = db.query(User).filter(User.role == role, User.is_active.is_(True)).all()
    for u in users:
        db.add(Notification(
            user_id=u.id,
            transfer_id=transfer.id,
            type=ntype,
            title=title,
            message=message,
        ))


@celery_app.task(bind=True, name="backend.app.tasks.transfer.prepare_for_transfer")
def prepare_for_transfer(self, transfer_id: int) -> dict:
    db: Session = SyncSession()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        files = db.query(TransferFile).filter(TransferFile.transfer_id == transfer_id).all()
        scan_ok = all(
            tf.virus_scan_status in ("clean", None) and tf.checksum_verified is not False
            for tf in files
        )

        if not scan_ok:
            transfer.status = TransferStatus.SCAN_FAILED
            transfer.scan_passed = False
            db.add(TransferHistory(
                transfer_id=transfer.id,
                action="scan_failed",
                description="Pre-transfer verification failed — files did not pass scan",
            ))
            db.commit()
            return {"error": "Scan verification failed", "transfer_id": transfer_id}

        project_name = "unlinked"
        if transfer.shotgrid_project_id:
            try:
                from backend.app.integrations.shotgrid import shotgrid_client
                proj = shotgrid_client.get_project(transfer.shotgrid_project_id)
                if proj and proj.get("name"):
                    project_name = proj["name"].replace(" ", "_").lower()
            except Exception:
                pass

        category = transfer.category.value if transfer.category else "other"
        production_dir = (
            Path(settings.PRODUCTION_NETWORK_PATH)
            / project_name
            / category
            / transfer.reference
        )
        production_dir.mkdir(parents=True, exist_ok=True)
        transfer.production_path = str(production_dir)

        transfer.status = TransferStatus.READY_FOR_TRANSFER
        transfer.scan_passed = True
        transfer.scan_completed_at = datetime.now(timezone.utc)

        db.add(TransferHistory(
            transfer_id=transfer.id,
            action="ready_for_transfer",
            description=f"Scans passed. Production path: {production_dir}",
        ))

        _notify_role(
            db, UserRole.IT_TEAM, transfer,
            NotificationType.TRANSFER_STARTED,
            f"Ready for transfer: {transfer.reference}",
            f"Transfer '{transfer.name}' is ready for file transfer to production.",
        )

        db.commit()
        logger.info("Transfer %s prepared — production path: %s", transfer.reference, production_dir)
        return {"transfer_id": transfer_id, "production_path": str(production_dir)}

    except Exception:
        logger.exception("Fatal error in prepare_for_transfer for %d", transfer_id)
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="backend.app.tasks.transfer.execute_transfer")
def execute_transfer(self, transfer_id: int) -> dict:
    db: Session = SyncSession()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        transfer.status = TransferStatus.TRANSFERRING
        transfer.transfer_started_at = datetime.now(timezone.utc)
        transfer.transfer_method = settings.TRANSFER_METHOD
        db.commit()

        staging = transfer.staging_path
        production = transfer.production_path

        if not staging or not production:
            transfer.status = TransferStatus.SCAN_FAILED
            db.add(TransferHistory(
                transfer_id=transfer.id,
                action="transfer_error",
                description="Missing staging or production path",
            ))
            db.commit()
            return {"error": "Missing staging or production path"}

        if settings.TRANSFER_METHOD == "rsync":
            src = staging.rstrip("/") + "/"
            dst = production.rstrip("/") + "/"
            cmd = ["rsync", "-avz", "--checksum", src, dst]
            logger.info("Running: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            if result.returncode != 0:
                logger.error("rsync failed: %s", result.stderr)
                transfer.status = TransferStatus.SCAN_FAILED
                db.add(TransferHistory(
                    transfer_id=transfer.id,
                    action="transfer_error",
                    description=f"rsync failed (exit {result.returncode}): {result.stderr[:500]}",
                ))
                db.commit()
                return {"error": f"rsync failed: {result.stderr[:200]}"}
        else:
            shutil.copytree(staging, production, dirs_exist_ok=True)

        transfer.status = TransferStatus.VERIFYING
        db.add(TransferHistory(
            transfer_id=transfer.id,
            action="transfer_verifying",
            description=f"Files transferred via {settings.TRANSFER_METHOD}, now verifying",
        ))
        db.commit()

        logger.info("Transfer %s files copied via %s, now verifying", transfer.reference, settings.TRANSFER_METHOD)
        return {"transfer_id": transfer_id, "status": "verifying"}

    except subprocess.TimeoutExpired:
        logger.exception("Transfer timed out for %d", transfer_id)
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if transfer:
            transfer.status = TransferStatus.SCAN_FAILED
            db.add(TransferHistory(
                transfer_id=transfer.id,
                action="transfer_error",
                description="File transfer timed out after 2 hours",
            ))
            db.commit()
        raise
    except Exception:
        logger.exception("Fatal error in execute_transfer for %d", transfer_id)
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="backend.app.tasks.transfer.verify_transfer")
def verify_transfer(self, transfer_id: int) -> dict:
    db: Session = SyncSession()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        files = db.query(TransferFile).filter(TransferFile.transfer_id == transfer_id).all()
        production_path = Path(transfer.production_path) if transfer.production_path else None

        if not production_path or not production_path.exists():
            transfer.status = TransferStatus.SCAN_FAILED
            transfer.transfer_verified = False
            db.commit()
            return {"error": "Production path missing"}

        mismatches = []
        for tf in files:
            prod_file = production_path / tf.filename
            if not prod_file.exists():
                mismatches.append(tf.filename)
                tf.checksum_verified = False
                continue

            prod_checksum = _compute_checksum(str(prod_file))
            if tf.checksum_sha256 and prod_checksum == tf.checksum_sha256:
                tf.checksum_verified = True
            else:
                tf.checksum_verified = False
                mismatches.append(tf.filename)
                logger.warning(
                    "Production checksum mismatch: %s (expected=%s got=%s)",
                    tf.filename, tf.checksum_sha256, prod_checksum,
                )

        db.commit()

        if mismatches:
            transfer.status = TransferStatus.SCAN_FAILED
            transfer.transfer_verified = False
            transfer.transfer_completed_at = datetime.now(timezone.utc)

            db.add(TransferHistory(
                transfer_id=transfer.id,
                action="verification_failed",
                description=f"Checksum mismatch for {len(mismatches)} file(s): {', '.join(mismatches[:5])}",
                metadata_json={"mismatched_files": mismatches},
            ))

            msg = f"Transfer '{transfer.name}' ({transfer.reference}) failed verification: {len(mismatches)} mismatched file(s)."
            _notify_role(db, UserRole.DATA_TEAM, transfer, NotificationType.TRANSFER_FAILED, f"Verification failed: {transfer.reference}", msg)
            _notify_role(db, UserRole.IT_TEAM, transfer, NotificationType.TRANSFER_FAILED, f"Verification failed: {transfer.reference}", msg)

            db.commit()
            logger.error("Transfer %s verification FAILED: %d mismatches", transfer.reference, len(mismatches))
            return {"status": "failed", "mismatches": len(mismatches)}

        transfer.status = TransferStatus.TRANSFERRED
        transfer.transfer_verified = True
        transfer.transfer_completed_at = datetime.now(timezone.utc)

        db.add(TransferHistory(
            transfer_id=transfer.id,
            action="transferred",
            description=f"All {len(files)} files verified and delivered to production",
        ))
        db.commit()

        try:
            from backend.app.services.shotgrid_service import shotgrid_service
            import asyncio
            loop = asyncio.new_event_loop()
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            async_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
            async_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
            async def _run_sg():
                async with async_factory() as async_db:
                    from sqlalchemy import select
                    result = await async_db.execute(select(Transfer).where(Transfer.id == transfer_id))
                    t = result.scalar_one_or_none()
                    if t:
                        await shotgrid_service.on_transfer_complete(t, async_db)
                await async_engine.dispose()
            loop.run_until_complete(_run_sg())
            loop.close()
        except Exception:
            logger.exception("ShotGrid completion callback failed for %s", transfer.reference)

        success_msg = (
            f"Transfer '{transfer.name}' ({transfer.reference}) has been successfully "
            f"delivered to production. {len(files)} files verified."
        )

        db.add(Notification(
            user_id=transfer.artist_id,
            transfer_id=transfer.id,
            type=NotificationType.TRANSFER_COMPLETE,
            title=f"Transfer complete: {transfer.reference}",
            message=success_msg,
        ))

        from backend.app.models.approval import Approval, ApprovalStatus
        approvers = db.query(Approval).filter(
            Approval.transfer_id == transfer_id,
            Approval.status == ApprovalStatus.APPROVED,
            Approval.approver_id.isnot(None),
        ).all()
        notified_ids = {transfer.artist_id}
        for a in approvers:
            if a.approver_id not in notified_ids:
                db.add(Notification(
                    user_id=a.approver_id,
                    transfer_id=transfer.id,
                    type=NotificationType.TRANSFER_COMPLETE,
                    title=f"Transfer complete: {transfer.reference}",
                    message=success_msg,
                ))
                notified_ids.add(a.approver_id)

        _notify_role(db, UserRole.DATA_TEAM, transfer, NotificationType.TRANSFER_COMPLETE, f"Transfer complete: {transfer.reference}", success_msg)
        _notify_role(db, UserRole.IT_TEAM, transfer, NotificationType.TRANSFER_COMPLETE, f"Transfer complete: {transfer.reference}", success_msg)

        db.commit()
        logger.info("Transfer %s COMPLETE — %d files delivered", transfer.reference, len(files))
        return {"status": "transferred", "files": len(files)}

    except Exception:
        logger.exception("Fatal error in verify_transfer for %d", transfer_id)
        raise
    finally:
        db.close()

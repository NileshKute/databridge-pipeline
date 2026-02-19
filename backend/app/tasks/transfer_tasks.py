from __future__ import annotations

import hashlib
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.core.celery_app import celery_app
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus

logger = logging.getLogger("databridge.tasks.transfer")

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)

CHUNK_SIZE = 64 * 1024


def _compute_checksum(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


@celery_app.task(bind=True, name="execute_transfer")
def execute_transfer_task(self, transfer_id: int) -> dict:
    db: Session = SyncSessionLocal()
    try:
        transfer: Transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        transfer.status = TransferStatus.TRANSFERRING
        transfer.transfer_started_at = datetime.now(timezone.utc)
        transfer.transfer_method = settings.TRANSFER_METHOD
        db.commit()

        files: list[TransferFile] = (
            db.query(TransferFile).filter(TransferFile.transfer_id == transfer_id).all()
        )
        total_files = len(files)
        transferred_count = 0

        staging = Path(transfer.staging_path) if transfer.staging_path else None
        production = Path(transfer.production_path) if transfer.production_path else None

        if not staging or not production:
            transfer.status = TransferStatus.SCAN_FAILED
            transfer.transfer_completed_at = datetime.now(timezone.utc)
            db.commit()
            return {"error": "Missing staging or production path"}

        for tf in files:
            try:
                src_file = staging / tf.original_path
                dest_file = production / tf.filename
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(str(src_file), str(dest_file))

                tf.checksum_sha256 = _compute_checksum(str(dest_file))
                src_checksum = _compute_checksum(str(src_file))
                tf.checksum_verified = tf.checksum_sha256 == src_checksum

                transferred_count += 1
                db.commit()

                self.update_state(
                    state="PROGRESS",
                    meta={"current": transferred_count, "total": total_files},
                )

            except Exception as exc:
                tf.virus_scan_detail = f"Transfer error: {exc}"
                db.commit()
                logger.exception("Error transferring file %s", tf.filename)

        transfer.status = TransferStatus.VERIFYING
        db.commit()

        failed = [f for f in files if not f.checksum_verified]
        if failed:
            transfer.transfer_verified = False
        else:
            transfer.transfer_verified = True
            transfer.status = TransferStatus.TRANSFERRED

        transfer.transfer_completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Transfer %s finished: %s (%d/%d files)",
            transfer.reference,
            transfer.status.value,
            transferred_count - len(failed),
            total_files,
        )

        return {
            "transfer_id": transfer.id,
            "reference": transfer.reference,
            "status": transfer.status.value,
            "files_ok": transferred_count - len(failed),
            "files_failed": len(failed),
            "total_files": total_files,
        }

    except Exception as exc:
        logger.exception("Fatal error in transfer task %d", transfer_id)
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if transfer:
            transfer.transfer_completed_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()

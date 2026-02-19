from __future__ import annotations

import hashlib
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus

logger = logging.getLogger("databridge.tasks.scanning")

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)

CHUNK_SIZE = 1024 * 1024


@celery_app.task(bind=True, name="backend.app.tasks.scanning.virus_scan_transfer")
def virus_scan_transfer(self, transfer_id: int) -> dict:
    db: Session = SyncSession()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        files = db.query(TransferFile).filter(TransferFile.transfer_id == transfer_id).all()
        scan_results = {"total": len(files), "clean": 0, "infected": 0, "errors": 0, "skipped": 0}

        if not settings.CLAMAV_ENABLED:
            logger.warning("ClamAV disabled — marking all %d files as clean", len(files))
            for tf in files:
                tf.virus_scan_status = "clean"
                tf.virus_scan_detail = "ClamAV disabled — scan skipped"
            scan_results["skipped"] = len(files)
            transfer.scan_result = scan_results
            db.commit()
            return scan_results

        for tf in files:
            file_path = Path(tf.original_path)
            if not file_path.exists():
                tf.virus_scan_status = "error"
                tf.virus_scan_detail = "File not found on disk"
                scan_results["errors"] += 1
                continue

            try:
                result = subprocess.run(
                    ["clamscan", "--no-summary", str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    tf.virus_scan_status = "clean"
                    tf.virus_scan_detail = "No threats detected"
                    scan_results["clean"] += 1
                elif result.returncode == 1:
                    tf.virus_scan_status = "infected"
                    tf.virus_scan_detail = result.stdout.strip()
                    scan_results["infected"] += 1
                    logger.warning("INFECTED: %s — %s", tf.filename, result.stdout.strip())
                else:
                    tf.virus_scan_status = "error"
                    tf.virus_scan_detail = result.stderr.strip()
                    scan_results["errors"] += 1

            except subprocess.TimeoutExpired:
                tf.virus_scan_status = "error"
                tf.virus_scan_detail = "Scan timed out after 300s"
                scan_results["errors"] += 1
            except FileNotFoundError:
                logger.error("clamscan binary not found — marking remaining as skipped")
                tf.virus_scan_status = "clean"
                tf.virus_scan_detail = "clamscan not installed — scan skipped"
                scan_results["skipped"] += 1
            except Exception as exc:
                tf.virus_scan_status = "error"
                tf.virus_scan_detail = str(exc)[:500]
                scan_results["errors"] += 1

            db.commit()
            self.update_state(state="PROGRESS", meta=scan_results)

        transfer.scan_result = scan_results
        db.commit()

        logger.info(
            "Virus scan complete for %s: %d clean, %d infected, %d errors, %d skipped",
            transfer.reference, scan_results["clean"], scan_results["infected"],
            scan_results["errors"], scan_results["skipped"],
        )
        return scan_results

    except Exception:
        logger.exception("Fatal error in virus_scan_transfer for %d", transfer_id)
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="backend.app.tasks.scanning.checksum_verify_transfer")
def checksum_verify_transfer(self, transfer_id: int) -> dict:
    db: Session = SyncSession()
    try:
        transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
        if not transfer:
            return {"error": "Transfer not found"}

        files = db.query(TransferFile).filter(TransferFile.transfer_id == transfer_id).all()
        results = {"total": len(files), "verified": 0, "failed": 0, "missing": 0}

        for tf in files:
            file_path = Path(tf.original_path)
            if not file_path.exists():
                tf.checksum_verified = False
                results["missing"] += 1
                continue

            sha = hashlib.sha256()
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    sha.update(chunk)

            computed = sha.hexdigest()
            if tf.checksum_sha256 and computed == tf.checksum_sha256:
                tf.checksum_verified = True
                results["verified"] += 1
            else:
                tf.checksum_verified = False
                results["failed"] += 1
                logger.warning(
                    "Checksum mismatch for %s: stored=%s computed=%s",
                    tf.filename, tf.checksum_sha256, computed,
                )

            db.commit()

        all_ok = results["failed"] == 0 and results["missing"] == 0
        if not all_ok:
            transfer.scan_passed = False

        db.commit()

        logger.info(
            "Checksum verification for %s: %d ok, %d failed, %d missing",
            transfer.reference, results["verified"], results["failed"], results["missing"],
        )
        return results

    except Exception:
        logger.exception("Fatal error in checksum_verify_transfer for %d", transfer_id)
        raise
    finally:
        db.close()

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.history import TransferHistory
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus
from backend.app.models.user import User, UserRole

logger = logging.getLogger("databridge.scanning_service")


class ScanningService:

    async def start_scan(
        self,
        transfer_id: int,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if user_role not in ("data_team", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only data_team or admin can start scans",
            )

        if transfer.status != TransferStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot scan — transfer status is '{transfer.status.value}', expected 'approved'",
            )

        transfer.status = TransferStatus.SCANNING
        transfer.scan_started_at = datetime.now(timezone.utc)

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="scan_started",
            description=f"Scanning started by {user.display_name}",
        ))

        await db.flush()
        await db.commit()
        await db.refresh(transfer)

        from backend.app.tasks.scanning import virus_scan_transfer, checksum_verify_transfer
        virus_scan_transfer.delay(transfer_id)
        checksum_verify_transfer.delay(transfer_id)

        logger.info("Scan started for transfer %s by %s", transfer.reference, user.username)
        return transfer

    async def complete_scan(
        self,
        transfer_id: int,
        user: User,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if user_role not in ("data_team", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only data_team or admin can complete scans",
            )

        if transfer.status != TransferStatus.SCANNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer status is '{transfer.status.value}', expected 'scanning'",
            )

        files_result = await db.execute(
            select(TransferFile).where(TransferFile.transfer_id == transfer_id)
        )
        files = list(files_result.scalars().all())

        infected = [f for f in files if f.virus_scan_status == "infected"]
        checksum_failed = [f for f in files if f.checksum_verified is False]

        if infected or checksum_failed:
            transfer.status = TransferStatus.SCAN_FAILED
            transfer.scan_passed = False
            transfer.scan_completed_at = datetime.now(timezone.utc)

            detail_parts = []
            if infected:
                detail_parts.append(f"{len(infected)} infected file(s)")
            if checksum_failed:
                detail_parts.append(f"{len(checksum_failed)} checksum failure(s)")

            db.add(TransferHistory(
                transfer_id=transfer.id,
                user_id=user.id,
                action="scan_failed",
                description=f"Scan failed: {', '.join(detail_parts)}",
            ))

            db.add(Notification(
                user_id=transfer.artist_id,
                transfer_id=transfer.id,
                type=NotificationType.SCAN_FAILED,
                title=f"Scan failed: {transfer.reference}",
                message=f"Your transfer failed scanning: {', '.join(detail_parts)}",
            ))

            await db.flush()
            await db.commit()
            await db.refresh(transfer)

            logger.warning("Scan FAILED for %s: %s", transfer.reference, ", ".join(detail_parts))
            return transfer

        transfer.status = TransferStatus.SCAN_PASSED
        transfer.scan_passed = True
        transfer.scan_completed_at = datetime.now(timezone.utc)

        db.add(TransferHistory(
            transfer_id=transfer.id,
            user_id=user.id,
            action="scan_passed",
            description=f"All {len(files)} files passed scanning",
        ))

        await db.flush()
        await db.commit()
        await db.refresh(transfer)

        from backend.app.tasks.transfer import prepare_for_transfer
        prepare_for_transfer.delay(transfer_id)

        logger.info("Scan PASSED for %s — dispatching prepare_for_transfer", transfer.reference)
        return transfer

    async def get_scan_status(
        self,
        transfer_id: int,
        db: AsyncSession,
    ) -> dict:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

        files_result = await db.execute(
            select(TransferFile).where(TransferFile.transfer_id == transfer_id)
        )
        files = list(files_result.scalars().all())

        scan_summary = {
            "transfer_id": transfer.id,
            "reference": transfer.reference,
            "status": transfer.status.value if hasattr(transfer.status, "value") else transfer.status,
            "scan_started_at": transfer.scan_started_at.isoformat() if transfer.scan_started_at else None,
            "scan_completed_at": transfer.scan_completed_at.isoformat() if transfer.scan_completed_at else None,
            "scan_passed": transfer.scan_passed,
            "scan_result": transfer.scan_result,
            "files": {
                "total": len(files),
                "clean": sum(1 for f in files if f.virus_scan_status == "clean"),
                "infected": sum(1 for f in files if f.virus_scan_status == "infected"),
                "pending": sum(1 for f in files if f.virus_scan_status == "pending"),
                "error": sum(1 for f in files if f.virus_scan_status == "error"),
                "checksum_verified": sum(1 for f in files if f.checksum_verified is True),
                "checksum_failed": sum(1 for f in files if f.checksum_verified is False),
            },
        }
        return scan_summary


scanning_service = ScanningService()

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import BinaryIO, List, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.transfer import Transfer, TransferFile, TransferStatus
from backend.app.models.user import User

logger = logging.getLogger("databridge.file_service")

UPLOADABLE_STATUSES = {TransferStatus.UPLOADED, TransferStatus.REJECTED}
CHUNK_SIZE = 1024 * 1024  # 1 MB


class FileService:
    def __init__(self) -> None:
        self._upload_tmp = Path(settings.UPLOAD_TEMP_PATH)
        self._staging = Path(settings.STAGING_NETWORK_PATH)
        self._upload_tmp.mkdir(parents=True, exist_ok=True)
        self._staging.mkdir(parents=True, exist_ok=True)
        logger.info(
            "FileService ready (tmp=%s, staging=%s)",
            self._upload_tmp,
            self._staging,
        )

    def _staging_dir_for(self, reference: str) -> Path:
        d = self._staging / reference
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def _calculate_checksum_and_save(
        file_stream: BinaryIO,
        dest_path: Path,
    ) -> Tuple[str, int]:
        sha = hashlib.sha256()
        total_bytes = 0
        with open(dest_path, "wb") as out:
            while True:
                chunk = file_stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha.update(chunk)
                out.write(chunk)
                total_bytes += len(chunk)
        return sha.hexdigest(), total_bytes

    async def upload_file(
        self,
        transfer_id: int,
        file: UploadFile,
        db: AsyncSession,
    ) -> TransferFile:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )
        if transfer.status not in UPLOADABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload files when transfer status is '{transfer.status.value}'",
            )

        staging_dir = self._staging_dir_for(transfer.reference)
        filename = file.filename or "unnamed_file"
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        dest_path = staging_dir / safe_filename

        counter = 1
        original_stem = dest_path.stem
        suffix = dest_path.suffix
        while dest_path.exists():
            dest_path = staging_dir / f"{original_stem}_{counter}{suffix}"
            counter += 1

        checksum, size_bytes = self._calculate_checksum_and_save(file.file, dest_path)

        max_bytes = int(settings.MAX_UPLOAD_SIZE_GB * 1024 * 1024 * 1024)
        if (transfer.total_size_bytes + size_bytes) > max_bytes:
            dest_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Transfer would exceed max size of {settings.MAX_UPLOAD_SIZE_GB} GB",
            )

        tf = TransferFile(
            transfer_id=transfer.id,
            filename=safe_filename,
            original_path=str(dest_path),
            size_bytes=size_bytes,
            checksum_sha256=checksum,
        )
        db.add(tf)

        transfer.total_files += 1
        transfer.total_size_bytes += size_bytes
        transfer.staging_path = str(staging_dir)

        await db.flush()
        await db.commit()
        await db.refresh(tf)

        logger.info(
            "Uploaded %s (%d bytes, sha256=%s) to %s",
            safe_filename,
            size_bytes,
            checksum[:12],
            transfer.reference,
        )
        return tf

    async def upload_files_batch(
        self,
        transfer_id: int,
        files: List[UploadFile],
        db: AsyncSession,
    ) -> List[TransferFile]:
        records: List[TransferFile] = []
        for f in files:
            tf = await self.upload_file(transfer_id, f, db)
            records.append(tf)
        return records

    async def delete_file(
        self,
        file_id: int,
        user: User,
        db: AsyncSession,
    ) -> None:
        result = await db.execute(
            select(TransferFile).where(TransferFile.id == file_id)
        )
        tf = result.scalar_one_or_none()
        if tf is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        xfer_result = await db.execute(
            select(Transfer).where(Transfer.id == tf.transfer_id)
        )
        transfer = xfer_result.scalar_one_or_none()
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found",
            )

        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if transfer.artist_id != user.id and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the transfer owner or admin can delete files",
            )

        if transfer.status not in UPLOADABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete files after approval process has started",
            )

        file_path = Path(tf.original_path)
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted file from disk: %s", file_path)

        transfer.total_files = max(0, transfer.total_files - 1)
        transfer.total_size_bytes = max(0, transfer.total_size_bytes - tf.size_bytes)

        await db.delete(tf)
        await db.flush()
        await db.commit()

        logger.info("Deleted file record id=%d from transfer %s", file_id, transfer.reference)


file_service = FileService()

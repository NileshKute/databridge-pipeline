from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.integrations.shotgrid import shotgrid_client
from backend.app.models.transfer import Transfer

logger = logging.getLogger("databridge.shotgrid_service")


class ShotGridService:
    def __init__(self) -> None:
        self._client = shotgrid_client
        logger.info(
            "ShotGridService ready (backend=%s)",
            type(self._client).__name__,
        )

    async def get_projects(self) -> List[Dict[str, Any]]:
        return self._client.get_projects(active_only=True)

    async def get_shots(
        self,
        project_id: int,
        sequence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._client.get_shots(project_id, sequence=sequence)

    async def get_assets(
        self,
        project_id: int,
        asset_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._client.get_assets(project_id, asset_type=asset_type)

    async def get_tasks(
        self,
        entity_type: str,
        entity_id: int,
    ) -> List[Dict[str, Any]]:
        return self._client.get_tasks(entity_type, entity_id)

    async def link_transfer(
        self,
        transfer_id: int,
        entity_type: str,
        entity_id: int,
        db: AsyncSession,
    ) -> Transfer:
        result = await db.execute(
            select(Transfer).where(Transfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            raise ValueError(f"Transfer {transfer_id} not found")

        entity_name: Optional[str] = None
        if entity_type == "Shot":
            entity_data = self._client.get_shot(entity_id)
            if entity_data:
                entity_name = entity_data.get("code")
        elif entity_type == "Asset":
            entity_data = self._client.get_asset(entity_id)
            if entity_data:
                entity_name = entity_data.get("code")

        transfer.shotgrid_entity_type = entity_type
        transfer.shotgrid_entity_id = entity_id
        transfer.shotgrid_entity_name = entity_name or f"{entity_type}_{entity_id}"

        await db.flush()
        await db.commit()
        await db.refresh(transfer)

        logger.info(
            "Linked transfer %s to %s %d (%s)",
            transfer.reference,
            entity_type,
            entity_id,
            transfer.shotgrid_entity_name,
        )
        return transfer

    async def on_transfer_complete(
        self,
        transfer: Transfer,
        db: AsyncSession,
    ) -> None:
        if not transfer.shotgrid_entity_type or not transfer.shotgrid_entity_id:
            logger.info("Transfer %s has no SG entity linked — skipping SG update", transfer.reference)
            return

        project_id = transfer.shotgrid_project_id
        entity_type = transfer.shotgrid_entity_type
        entity_id = transfer.shotgrid_entity_id

        self._client.update_entity_status(entity_type, entity_id, "dlvr")

        version_code = f"{transfer.reference}_v001"
        description = (
            f"DataBridge transfer {transfer.reference}\n"
            f"Files: {transfer.total_files} | Size: {transfer.size_display}\n"
            f"Category: {transfer.category.value if transfer.category else 'N/A'}"
        )
        prod_path = transfer.production_path or ""

        if project_id:
            version_result = self._client.create_version(
                project_id,
                entity_type,
                entity_id,
                version_code,
                description,
                prod_path,
            )
            if version_result:
                transfer.shotgrid_version_id = version_result.get("id")
                await db.flush()
                await db.commit()

            note_subject = f"Transfer Complete: {transfer.reference}"
            note_content = (
                f"Data transfer '{transfer.name}' has been delivered to production.\n\n"
                f"Reference: {transfer.reference}\n"
                f"Files: {transfer.total_files}\n"
                f"Total size: {transfer.size_display}\n"
                f"Production path: {prod_path}\n"
                f"Completed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            )
            self._client.create_note(
                project_id,
                entity_type,
                entity_id,
                note_subject,
                note_content,
            )

        logger.info(
            "SG completion actions done for transfer %s → %s %d",
            transfer.reference,
            entity_type,
            entity_id,
        )

    async def resolve_user(self, username: str) -> Optional[int]:
        user_data = self._client.get_user_by_login(username)
        if user_data:
            return user_data.get("id")
        return None


shotgrid_service = ShotGridService()

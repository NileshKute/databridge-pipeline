from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.services.shotgrid_service import shotgrid_service

router = APIRouter()


class LinkRequest(BaseModel):
    transfer_id: int
    entity_type: str
    entity_id: int


@router.get("/projects")
async def list_projects(
    _: Annotated[User, Depends(get_current_user)],
):
    projects = await shotgrid_service.get_projects()
    return {"projects": projects, "total": len(projects)}


@router.get("/projects/{project_id}/shots")
async def list_shots(
    project_id: int,
    _: Annotated[User, Depends(get_current_user)],
    sequence: Optional[str] = Query(None, description="Filter by sequence name"),
):
    shots = await shotgrid_service.get_shots(project_id, sequence=sequence)
    return {"shots": shots, "total": len(shots)}


@router.get("/projects/{project_id}/assets")
async def list_assets(
    project_id: int,
    _: Annotated[User, Depends(get_current_user)],
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
):
    assets = await shotgrid_service.get_assets(project_id, asset_type=asset_type)
    return {"assets": assets, "total": len(assets)}


@router.get("/entities/{entity_type}/{entity_id}/tasks")
async def list_tasks(
    entity_type: str,
    entity_id: int,
    _: Annotated[User, Depends(get_current_user)],
):
    tasks = await shotgrid_service.get_tasks(entity_type, entity_id)
    return {"tasks": tasks, "total": len(tasks)}


@router.post("/link")
async def link_transfer_to_entity(
    payload: LinkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    try:
        transfer = await shotgrid_service.link_transfer(
            payload.transfer_id,
            payload.entity_type,
            payload.entity_id,
            db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return {
        "message": "Transfer linked",
        "transfer_id": transfer.id,
        "entity_type": transfer.shotgrid_entity_type,
        "entity_id": transfer.shotgrid_entity_id,
        "entity_name": transfer.shotgrid_entity_name,
    }

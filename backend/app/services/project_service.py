from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger("databridge.project_service")


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    await db.flush()
    logger.info("Project created: %s (%s)", project.name, project.code)
    return project


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_project_by_code(db: AsyncSession, code: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.code == code))
    return result.scalar_one_or_none()


async def list_projects(
    db: AsyncSession, page: int = 1, page_size: int = 50
) -> tuple[list[Project], int]:
    count_query = select(func.count()).select_from(Project)
    total = (await db.execute(count_query)).scalar() or 0
    query = (
        select(Project)
        .order_by(Project.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def update_project(
    db: AsyncSession, project_id: int, data: ProjectUpdate
) -> Project | None:
    project = await get_project(db, project_id)
    if project is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    return project

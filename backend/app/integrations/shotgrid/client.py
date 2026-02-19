from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings

logger = logging.getLogger("databridge.shotgrid")


class ShotGridClient:
    """Wrapper around the ShotGrid (Shotgun) Python API.

    Lazily initialises the connection so the app starts even when
    ShotGrid credentials are not yet configured.
    """

    def __init__(self) -> None:
        self._sg = None

    def _connect(self):
        if self._sg is not None:
            return self._sg

        if not settings.SHOTGRID_ENABLED:
            logger.info("ShotGrid integration disabled")
            return None

        try:
            import shotgun_api3  # noqa: delayed import — optional dependency
            self._sg = shotgun_api3.Shotgun(
                settings.SHOTGRID_URL,
                script_name=settings.SHOTGRID_SCRIPT_NAME,
                api_key=settings.SHOTGRID_API_KEY,
            )
            logger.info("Connected to ShotGrid at %s", settings.SHOTGRID_URL)
        except Exception:
            logger.exception("Failed to connect to ShotGrid")
            self._sg = None
        return self._sg

    @property
    def connected(self) -> bool:
        return self._connect() is not None

    def find_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        sg = self._connect()
        if sg is None:
            return None
        try:
            return sg.find_one("Project", [["id", "is", project_id]], ["name", "sg_status"])
        except Exception:
            logger.exception("ShotGrid find_project failed for id=%d", project_id)
            return None

    def find_shots(self, project_id: int, filters: Optional[List] = None) -> List[Dict[str, Any]]:
        sg = self._connect()
        if sg is None:
            return []
        base_filters = [["project", "is", {"type": "Project", "id": project_id}]]
        if filters:
            base_filters.extend(filters)
        try:
            return sg.find("Shot", base_filters, ["code", "sg_status_list", "sg_sequence"])
        except Exception:
            logger.exception("ShotGrid find_shots failed")
            return []

    def find_tasks(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        sg = self._connect()
        if sg is None:
            return []
        try:
            return sg.find(
                "Task",
                [["entity", "is", {"type": entity_type, "id": entity_id}]],
                ["content", "sg_status_list", "task_assignees", "step"],
            )
        except Exception:
            logger.exception("ShotGrid find_tasks failed")
            return []

    def create_version(self, project_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sg = self._connect()
        if sg is None:
            return None
        try:
            data["project"] = {"type": "Project", "id": project_id}
            return sg.create("Version", data)
        except Exception:
            logger.exception("ShotGrid create_version failed")
            return None

    def update_task_status(self, task_id: int, status: str) -> bool:
        sg = self._connect()
        if sg is None:
            return False
        try:
            sg.update("Task", task_id, {"sg_status_list": status})
            return True
        except Exception:
            logger.exception("ShotGrid update_task_status failed for task_id=%d", task_id)
            return False


shotgrid_client = ShotGridClient()

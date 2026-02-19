from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from backend.app.core.config import settings

logger = logging.getLogger("databridge.shotgrid")


class ShotGridClient:
    def __init__(self) -> None:
        self._sg = None
        self.enabled = False
        if not settings.SHOTGRID_ENABLED:
            logger.info("ShotGrid integration disabled via settings")
            return
        try:
            import shotgun_api3
            self._sg = shotgun_api3.Shotgun(
                settings.SHOTGRID_URL,
                script_name=settings.SHOTGRID_SCRIPT_NAME,
                api_key=settings.SHOTGRID_API_KEY,
            )
            self.enabled = True
            logger.info("Connected to ShotGrid at %s", settings.SHOTGRID_URL)
        except Exception:
            logger.exception("Failed to connect to ShotGrid — integration disabled")
            self._sg = None
            self.enabled = False

    def _safe_call(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        if self._sg is None:
            return None
        try:
            return method(*args, **kwargs)
        except Exception:
            logger.exception("ShotGrid API call failed: %s", getattr(method, "__name__", str(method)))
            return None

    # ── Projects ─────────────────────────────────────────────────

    def get_projects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        filters: list = []
        if active_only:
            filters.append(["sg_status", "is", "Active"])
        result = self._safe_call(
            self._sg.find,
            "Project",
            filters,
            ["name", "sg_status", "sg_description"],
        )
        return result or []

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        return self._safe_call(
            self._sg.find_one,
            "Project",
            [["id", "is", project_id]],
            ["name", "sg_status", "sg_description"],
        )

    # ── Shots ────────────────────────────────────────────────────

    def get_shots(self, project_id: int, sequence: Optional[str] = None) -> List[Dict[str, Any]]:
        filters: list = [["project", "is", {"type": "Project", "id": project_id}]]
        if sequence:
            filters.append(["sg_sequence.Sequence.code", "is", sequence])
        result = self._safe_call(
            self._sg.find,
            "Shot",
            filters,
            ["code", "sg_status_list", "description", "sg_sequence", "sg_cut_in", "sg_cut_out"],
        )
        return result or []

    def get_shot(self, shot_id: int) -> Optional[Dict[str, Any]]:
        return self._safe_call(
            self._sg.find_one,
            "Shot",
            [["id", "is", shot_id]],
            ["code", "sg_status_list", "description", "sg_sequence", "sg_cut_in", "sg_cut_out"],
        )

    # ── Assets ───────────────────────────────────────────────────

    def get_assets(self, project_id: int, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        filters: list = [["project", "is", {"type": "Project", "id": project_id}]]
        if asset_type:
            filters.append(["sg_asset_type", "is", asset_type])
        result = self._safe_call(
            self._sg.find,
            "Asset",
            filters,
            ["code", "sg_asset_type", "sg_status_list", "description"],
        )
        return result or []

    def get_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        return self._safe_call(
            self._sg.find_one,
            "Asset",
            [["id", "is", asset_id]],
            ["code", "sg_asset_type", "sg_status_list", "description"],
        )

    # ── Tasks ────────────────────────────────────────────────────

    def get_tasks(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        result = self._safe_call(
            self._sg.find,
            "Task",
            [["entity", "is", {"type": entity_type, "id": entity_id}]],
            ["content", "sg_status_list", "task_assignees", "step"],
        )
        return result or []

    # ── Users ────────────────────────────────────────────────────

    def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        return self._safe_call(
            self._sg.find_one,
            "HumanUser",
            [["login", "is", login]],
            ["id", "name", "login", "email", "department"],
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self._safe_call(
            self._sg.find_one,
            "HumanUser",
            [["email", "is", email]],
            ["id", "name", "login", "email", "department"],
        )

    # ── Transfer completion ──────────────────────────────────────

    def update_entity_status(self, entity_type: str, entity_id: int, status: str) -> bool:
        result = self._safe_call(
            self._sg.update,
            entity_type,
            entity_id,
            {"sg_status_list": status},
        )
        if result is not None:
            logger.info("Updated %s %d status to '%s'", entity_type, entity_id, status)
            return True
        return False

    def create_note(
        self,
        project_id: int,
        entity_type: str,
        entity_id: int,
        subject: str,
        content: str,
    ) -> Optional[Dict[str, Any]]:
        data = {
            "project": {"type": "Project", "id": project_id},
            "note_links": [{"type": entity_type, "id": entity_id}],
            "subject": subject,
            "content": content,
        }
        result = self._safe_call(self._sg.create, "Note", data)
        if result:
            logger.info("Created Note on %s %d: %s", entity_type, entity_id, subject)
        return result

    def create_version(
        self,
        project_id: int,
        entity_type: str,
        entity_id: int,
        code: str,
        description: str,
        path: str,
    ) -> Optional[Dict[str, Any]]:
        data = {
            "project": {"type": "Project", "id": project_id},
            "entity": {"type": entity_type, "id": entity_id},
            "code": code,
            "description": description,
            "sg_path_to_movie": path,
            "sg_status_list": "rev",
        }
        result = self._safe_call(self._sg.create, "Version", data)
        if result:
            logger.info("Created Version '%s' for %s %d (id=%d)", code, entity_type, entity_id, result["id"])
        return result


sg_client: Optional[ShotGridClient] = (
    ShotGridClient() if settings.SHOTGRID_ENABLED else None
)

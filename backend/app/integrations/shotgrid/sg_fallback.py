from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("databridge.shotgrid.mock")

_PROJECTS = [
    {"type": "Project", "id": 101, "name": "Project Phoenix", "sg_status": "Active", "sg_description": "Feature film — hero dragon sequence"},
    {"type": "Project", "id": 102, "name": "Project Atlas", "sg_status": "Active", "sg_description": "Animated series — world-building environments"},
    {"type": "Project", "id": 103, "name": "Project Nebula", "sg_status": "Active", "sg_description": "VR experience — space exploration"},
]

_SHOTS: Dict[int, List[Dict[str, Any]]] = {
    101: [
        {"type": "Shot", "id": 1001, "code": "SH010", "sg_status_list": "ip", "description": "Dragon reveal wide", "sg_sequence": {"type": "Sequence", "id": 10, "name": "SEQ010"}, "sg_cut_in": 1001, "sg_cut_out": 1120},
        {"type": "Shot", "id": 1002, "code": "SH020", "sg_status_list": "ip", "description": "Dragon flight over mountains", "sg_sequence": {"type": "Sequence", "id": 10, "name": "SEQ010"}, "sg_cut_in": 1121, "sg_cut_out": 1280},
        {"type": "Shot", "id": 1003, "code": "SH030", "sg_status_list": "wtg", "description": "Hero close-up reaction", "sg_sequence": {"type": "Sequence", "id": 20, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1060},
        {"type": "Shot", "id": 1004, "code": "SH040", "sg_status_list": "rdy", "description": "Village establishing shot", "sg_sequence": {"type": "Sequence", "id": 20, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1150},
        {"type": "Shot", "id": 1005, "code": "SH050", "sg_status_list": "fin", "description": "Dragon landing — dust FX", "sg_sequence": {"type": "Sequence", "id": 30, "name": "SEQ030"}, "sg_cut_in": 1001, "sg_cut_out": 1200},
    ],
    102: [
        {"type": "Shot", "id": 2001, "code": "SH010", "sg_status_list": "ip", "description": "Forest canopy flythrough", "sg_sequence": {"type": "Sequence", "id": 40, "name": "SEQ010"}, "sg_cut_in": 1001, "sg_cut_out": 1100},
        {"type": "Shot", "id": 2002, "code": "SH020", "sg_status_list": "ip", "description": "Ancient ruins reveal", "sg_sequence": {"type": "Sequence", "id": 40, "name": "SEQ010"}, "sg_cut_in": 1101, "sg_cut_out": 1220},
        {"type": "Shot", "id": 2003, "code": "SH030", "sg_status_list": "wtg", "description": "River rapids sequence", "sg_sequence": {"type": "Sequence", "id": 50, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1180},
        {"type": "Shot", "id": 2004, "code": "SH040", "sg_status_list": "rdy", "description": "Mountain summit panorama", "sg_sequence": {"type": "Sequence", "id": 50, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1090},
        {"type": "Shot", "id": 2005, "code": "SH050", "sg_status_list": "fin", "description": "Crystal cave interior", "sg_sequence": {"type": "Sequence", "id": 60, "name": "SEQ030"}, "sg_cut_in": 1001, "sg_cut_out": 1250},
    ],
    103: [
        {"type": "Shot", "id": 3001, "code": "SH010", "sg_status_list": "ip", "description": "Space station approach", "sg_sequence": {"type": "Sequence", "id": 70, "name": "SEQ010"}, "sg_cut_in": 1001, "sg_cut_out": 1150},
        {"type": "Shot", "id": 3002, "code": "SH020", "sg_status_list": "ip", "description": "Asteroid field navigation", "sg_sequence": {"type": "Sequence", "id": 70, "name": "SEQ010"}, "sg_cut_in": 1151, "sg_cut_out": 1300},
        {"type": "Shot", "id": 3003, "code": "SH030", "sg_status_list": "wtg", "description": "Planet surface landing", "sg_sequence": {"type": "Sequence", "id": 80, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1200},
        {"type": "Shot", "id": 3004, "code": "SH040", "sg_status_list": "rdy", "description": "Nebula gas cloud", "sg_sequence": {"type": "Sequence", "id": 80, "name": "SEQ020"}, "sg_cut_in": 1001, "sg_cut_out": 1080},
        {"type": "Shot", "id": 3005, "code": "SH050", "sg_status_list": "fin", "description": "Warp gate activation", "sg_sequence": {"type": "Sequence", "id": 90, "name": "SEQ030"}, "sg_cut_in": 1001, "sg_cut_out": 1320},
    ],
}

_ASSETS: Dict[int, List[Dict[str, Any]]] = {
    101: [
        {"type": "Asset", "id": 4001, "code": "dragon_hero", "sg_asset_type": "Character", "sg_status_list": "ip", "description": "Hero dragon — fully rigged"},
        {"type": "Asset", "id": 4002, "code": "forest_env", "sg_asset_type": "Environment", "sg_status_list": "ip", "description": "Dense forest environment"},
        {"type": "Asset", "id": 4003, "code": "village_env", "sg_asset_type": "Environment", "sg_status_list": "wtg", "description": "Medieval village set"},
        {"type": "Asset", "id": 4004, "code": "hero_knight", "sg_asset_type": "Character", "sg_status_list": "fin", "description": "Knight protagonist"},
    ],
    102: [
        {"type": "Asset", "id": 5001, "code": "ancient_temple", "sg_asset_type": "Environment", "sg_status_list": "ip", "description": "Ruined temple structure"},
        {"type": "Asset", "id": 5002, "code": "water_sim", "sg_asset_type": "FX", "sg_status_list": "ip", "description": "River water simulation setup"},
        {"type": "Asset", "id": 5003, "code": "crystal_cluster", "sg_asset_type": "Prop", "sg_status_list": "wtg", "description": "Glowing crystal formations"},
        {"type": "Asset", "id": 5004, "code": "explorer_char", "sg_asset_type": "Character", "sg_status_list": "fin", "description": "Explorer character rig"},
    ],
    103: [
        {"type": "Asset", "id": 6001, "code": "space_station", "sg_asset_type": "Environment", "sg_status_list": "ip", "description": "Orbital station exterior/interior"},
        {"type": "Asset", "id": 6002, "code": "asteroid_field", "sg_asset_type": "Environment", "sg_status_list": "ip", "description": "Procedural asteroid scatter"},
        {"type": "Asset", "id": 6003, "code": "shuttle_vehicle", "sg_asset_type": "Vehicle", "sg_status_list": "wtg", "description": "Crew shuttle with cockpit"},
        {"type": "Asset", "id": 6004, "code": "astronaut_suit", "sg_asset_type": "Character", "sg_status_list": "fin", "description": "Space suit with helmet variants"},
    ],
}

_MOCK_TASKS = [
    {"type": "Task", "id": 9001, "content": "Animation", "sg_status_list": "ip", "task_assignees": [{"type": "HumanUser", "id": 201, "name": "Sarah Chen"}], "step": {"type": "Step", "id": 1, "name": "Anim"}},
    {"type": "Task", "id": 9002, "content": "Lighting", "sg_status_list": "wtg", "task_assignees": [{"type": "HumanUser", "id": 202, "name": "Marcus Johnson"}], "step": {"type": "Step", "id": 2, "name": "Light"}},
    {"type": "Task", "id": 9003, "content": "Compositing", "sg_status_list": "rdy", "task_assignees": [{"type": "HumanUser", "id": 203, "name": "Kim Tanaka"}], "step": {"type": "Step", "id": 3, "name": "Comp"}},
]

_NEXT_ID = 90000


def _next_id() -> int:
    global _NEXT_ID
    _NEXT_ID += 1
    return _NEXT_ID


class MockShotGridClient:
    def __init__(self) -> None:
        self.enabled = True
        logger.info("MockShotGridClient initialized — returning fake data")

    # ── Projects ─────────────────────────────────────────────────

    def get_projects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        if active_only:
            return [p for p in _PROJECTS if p["sg_status"] == "Active"]
        return list(_PROJECTS)

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        for p in _PROJECTS:
            if p["id"] == project_id:
                return p
        return None

    # ── Shots ────────────────────────────────────────────────────

    def get_shots(self, project_id: int, sequence: Optional[str] = None) -> List[Dict[str, Any]]:
        shots = _SHOTS.get(project_id, [])
        if sequence:
            shots = [s for s in shots if s.get("sg_sequence", {}).get("name") == sequence]
        return shots

    def get_shot(self, shot_id: int) -> Optional[Dict[str, Any]]:
        for shots in _SHOTS.values():
            for s in shots:
                if s["id"] == shot_id:
                    return s
        return None

    # ── Assets ───────────────────────────────────────────────────

    def get_assets(self, project_id: int, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        assets = _ASSETS.get(project_id, [])
        if asset_type:
            assets = [a for a in assets if a.get("sg_asset_type") == asset_type]
        return assets

    def get_asset(self, asset_id: int) -> Optional[Dict[str, Any]]:
        for assets in _ASSETS.values():
            for a in assets:
                if a["id"] == asset_id:
                    return a
        return None

    # ── Tasks ────────────────────────────────────────────────────

    def get_tasks(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        return list(_MOCK_TASKS)

    # ── Users ────────────────────────────────────────────────────

    def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        return {"type": "HumanUser", "id": 201, "name": login.title(), "login": login, "email": f"{login}@studio.local", "department": "VFX"}

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        name = email.split("@")[0].replace(".", " ").title()
        return {"type": "HumanUser", "id": 201, "name": name, "login": email.split("@")[0], "email": email, "department": "VFX"}

    # ── Transfer completion (write ops just log) ─────────────────

    def update_entity_status(self, entity_type: str, entity_id: int, status: str) -> bool:
        logger.info("[MOCK] Updated %s %d status → %s", entity_type, entity_id, status)
        return True

    def create_note(self, project_id: int, entity_type: str, entity_id: int, subject: str, content: str) -> Optional[Dict[str, Any]]:
        nid = _next_id()
        logger.info("[MOCK] Created Note id=%d on %s %d: %s", nid, entity_type, entity_id, subject)
        return {"type": "Note", "id": nid}

    def create_version(self, project_id: int, entity_type: str, entity_id: int, code: str, description: str, path: str) -> Optional[Dict[str, Any]]:
        vid = _next_id()
        logger.info("[MOCK] Created Version id=%d '%s' for %s %d", vid, code, entity_type, entity_id)
        return {"type": "Version", "id": vid}


mock_sg_client = MockShotGridClient()

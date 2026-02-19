from __future__ import annotations

import logging
from typing import Dict, List, Optional

from passlib.context import CryptContext

logger = logging.getLogger("databridge.ldap.fallback")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_FALLBACK_USERS: Dict[str, dict] = {
    "artist1": {
        "username": "artist1",
        "password_hash": pwd_context.hash("artist123"),
        "display_name": "Sarah Chen",
        "email": "sarah.chen@studio.local",
        "role": "artist",
        "department": "VFX",
        "title": "VFX Artist",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "teamlead1": {
        "username": "teamlead1",
        "password_hash": pwd_context.hash("teamlead123"),
        "display_name": "Marcus Johnson",
        "email": "marcus.johnson@studio.local",
        "role": "team_lead",
        "department": "VFX",
        "title": "VFX Team Lead",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "supervisor1": {
        "username": "supervisor1",
        "password_hash": pwd_context.hash("super123"),
        "display_name": "Kim Tanaka",
        "email": "kim.tanaka@studio.local",
        "role": "supervisor",
        "department": "VFX",
        "title": "VFX Supervisor",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "producer1": {
        "username": "producer1",
        "password_hash": pwd_context.hash("producer123"),
        "display_name": "Alex Rivera",
        "email": "alex.rivera@studio.local",
        "role": "line_producer",
        "department": "Production",
        "title": "Line Producer",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "datateam1": {
        "username": "datateam1",
        "password_hash": pwd_context.hash("data123"),
        "display_name": "Priya Sharma",
        "email": "priya.sharma@studio.local",
        "role": "data_team",
        "department": "Data Management",
        "title": "Data Coordinator",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "it1": {
        "username": "it1",
        "password_hash": pwd_context.hash("it123"),
        "display_name": "Tom Wilson",
        "email": "tom.wilson@studio.local",
        "role": "it_team",
        "department": "IT",
        "title": "Systems Engineer",
        "ldap_dn": None,
        "ldap_groups": "",
    },
    "admin1": {
        "username": "admin1",
        "password_hash": pwd_context.hash("admin123"),
        "display_name": "Root Admin",
        "email": "admin@studio.local",
        "role": "admin",
        "department": "IT",
        "title": "System Administrator",
        "ldap_dn": None,
        "ldap_groups": "",
    },
}


class FallbackAuthenticator:
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        user_data = _FALLBACK_USERS.get(username)
        if user_data is None:
            logger.warning("Fallback auth: unknown user %s", username)
            return None

        if not pwd_context.verify(password, user_data["password_hash"]):
            logger.warning("Fallback auth: bad password for %s", username)
            return None

        logger.info("Fallback auth success: %s (role=%s)", username, user_data["role"])

        return {
            "username": user_data["username"],
            "display_name": user_data["display_name"],
            "email": user_data["email"],
            "department": user_data["department"],
            "title": user_data["title"],
            "role": user_data["role"],
            "ldap_dn": user_data["ldap_dn"],
            "ldap_groups": user_data["ldap_groups"],
        }

    def get_users_by_role(self, role: str) -> List[dict]:
        return [
            {k: v for k, v in u.items() if k != "password_hash"}
            for u in _FALLBACK_USERS.values()
            if u["role"] == role
        ]


fallback_authenticator = FallbackAuthenticator()

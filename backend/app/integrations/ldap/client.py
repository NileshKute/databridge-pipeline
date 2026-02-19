from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import ldap3
from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException

from backend.app.core.config import settings

logger = logging.getLogger("databridge.ldap")


@dataclass
class LDAPUser:
    username: str
    email: str
    display_name: str
    department: Optional[str] = None
    groups: List[str] = field(default_factory=list)


class LDAPClient:
    def __init__(self) -> None:
        self._server = Server(
            settings.LDAP_SERVER,
            use_ssl=settings.LDAP_USE_SSL,
            get_info=ALL,
        )

    def _get_bind_connection(self) -> Connection:
        conn = Connection(
            self._server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_BIND_PASSWORD,
            auto_bind=True,
            read_only=True,
        )
        return conn

    def authenticate(self, username: str, password: str) -> Optional[LDAPUser]:
        if not settings.LDAP_ENABLED:
            return None

        try:
            bind_conn = self._get_bind_connection()
            search_filter = f"({settings.LDAP_USER_ATTR}={ldap3.utils.conv.escape_filter_chars(username)})"
            bind_conn.search(
                search_base=settings.LDAP_USER_DN,
                search_filter=search_filter,
                attributes=[
                    settings.LDAP_USER_ATTR,
                    settings.LDAP_EMAIL_ATTR,
                    settings.LDAP_DISPLAY_NAME_ATTR,
                    "department",
                    "memberOf",
                ],
            )

            if not bind_conn.entries:
                logger.warning("LDAP user not found: %s", username)
                return None

            user_entry = bind_conn.entries[0]
            user_dn = user_entry.entry_dn
            bind_conn.unbind()

            user_conn = Connection(self._server, user=user_dn, password=password)
            if not user_conn.bind():
                logger.warning("LDAP bind failed for user: %s", username)
                return None
            user_conn.unbind()

            email = str(user_entry[settings.LDAP_EMAIL_ATTR]) if settings.LDAP_EMAIL_ATTR in user_entry else f"{username}@studio.local"
            display_name = str(user_entry[settings.LDAP_DISPLAY_NAME_ATTR]) if settings.LDAP_DISPLAY_NAME_ATTR in user_entry else username
            department = str(user_entry["department"]) if "department" in user_entry else None
            groups = [str(g) for g in user_entry["memberOf"]] if "memberOf" in user_entry else []

            return LDAPUser(
                username=username,
                email=email,
                display_name=display_name,
                department=department,
                groups=groups,
            )

        except LDAPException:
            logger.exception("LDAP error during authentication for %s", username)
            return None

    def resolve_role(self, groups: List[str]) -> str:
        for group_dn, role in settings.LDAP_ROLE_MAP.items():
            if group_dn in groups:
                return role
        return "artist"


ldap_client = LDAPClient()

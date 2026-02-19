from __future__ import annotations

import logging
from typing import Dict, List, Optional

import ldap3
from ldap3 import ALL, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException

from backend.app.core.config import settings

logger = logging.getLogger("databridge.ldap")

ROLE_PRIORITY: Dict[str, int] = {
    "admin": 7,
    "line_producer": 6,
    "supervisor": 5,
    "team_lead": 4,
    "data_team": 3,
    "it_team": 2,
    "artist": 1,
}


class LDAPAuthenticator:
    def __init__(self) -> None:
        self._server = Server(
            settings.LDAP_SERVER,
            use_ssl=settings.LDAP_USE_SSL,
            get_info=ALL,
        )

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        bind_conn: Optional[Connection] = None
        user_conn: Optional[Connection] = None
        try:
            bind_conn = Connection(
                self._server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
                read_only=True,
            )

            safe_username = ldap3.utils.conv.escape_filter_chars(username)
            search_filter = settings.LDAP_USER_SEARCH_FILTER.format(
                user_attr=settings.LDAP_USER_ATTR,
                username=safe_username,
            )
            bind_conn.search(
                search_base=settings.LDAP_USER_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=[
                    "cn",
                    settings.LDAP_EMAIL_ATTR,
                    "department",
                    "title",
                    "memberOf",
                    "uid",
                ],
            )

            if not bind_conn.entries:
                logger.warning("LDAP user not found: %s", username)
                return None

            user_entry = bind_conn.entries[0]
            user_dn = user_entry.entry_dn

            user_conn = Connection(self._server, user=user_dn, password=password)
            if not user_conn.bind():
                logger.warning("LDAP credential verification failed for: %s", username)
                return None

            display_name = str(user_entry["cn"]) if "cn" in user_entry else username
            email = (
                str(user_entry[settings.LDAP_EMAIL_ATTR])
                if settings.LDAP_EMAIL_ATTR in user_entry
                else f"{username}@studio.local"
            )
            department = str(user_entry["department"]) if "department" in user_entry else None
            title = str(user_entry["title"]) if "title" in user_entry else None
            groups = (
                [str(g) for g in user_entry["memberOf"]]
                if "memberOf" in user_entry
                else []
            )

            role = self._map_groups_to_role(groups)
            ldap_groups_str = ";".join(groups) if groups else ""

            logger.info("LDAP auth success: %s (role=%s, groups=%d)", username, role, len(groups))

            return {
                "username": username,
                "display_name": display_name,
                "email": email,
                "department": department,
                "title": title,
                "role": role,
                "ldap_dn": user_dn,
                "ldap_groups": ldap_groups_str,
            }

        except LDAPException:
            logger.exception("LDAP error during authentication for %s", username)
            return None
        except Exception:
            logger.exception("Unexpected error during LDAP authentication for %s", username)
            return None
        finally:
            if bind_conn:
                try:
                    bind_conn.unbind()
                except Exception:
                    pass
            if user_conn:
                try:
                    user_conn.unbind()
                except Exception:
                    pass

    def _map_groups_to_role(self, groups: List[str]) -> str:
        best_role = "artist"
        best_priority = ROLE_PRIORITY["artist"]

        group_lower_map = {g.lower(): g for g in groups}

        for group_dn, role in settings.LDAP_ROLE_MAP.items():
            if group_dn.lower() in group_lower_map:
                priority = ROLE_PRIORITY.get(role, 0)
                if priority > best_priority:
                    best_role = role
                    best_priority = priority

        return best_role

    def get_users_by_role(self, role: str) -> List[dict]:
        target_group_dn: Optional[str] = None
        for group_dn, mapped_role in settings.LDAP_ROLE_MAP.items():
            if mapped_role == role:
                target_group_dn = group_dn
                break

        if not target_group_dn:
            return []

        bind_conn: Optional[Connection] = None
        try:
            bind_conn = Connection(
                self._server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
                read_only=True,
            )

            search_filter = f"(&(objectClass=user)(memberOf={ldap3.utils.conv.escape_filter_chars(target_group_dn)}))"
            bind_conn.search(
                search_base=settings.LDAP_USER_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=[settings.LDAP_USER_ATTR, "cn", settings.LDAP_EMAIL_ATTR, "department"],
            )

            users = []
            for entry in bind_conn.entries:
                users.append({
                    "username": str(entry[settings.LDAP_USER_ATTR]) if settings.LDAP_USER_ATTR in entry else "",
                    "display_name": str(entry["cn"]) if "cn" in entry else "",
                    "email": str(entry[settings.LDAP_EMAIL_ATTR]) if settings.LDAP_EMAIL_ATTR in entry else "",
                    "department": str(entry["department"]) if "department" in entry else None,
                    "role": role,
                })
            return users

        except LDAPException:
            logger.exception("LDAP error fetching users by role: %s", role)
            return []
        finally:
            if bind_conn:
                try:
                    bind_conn.unbind()
                except Exception:
                    pass


ldap_authenticator: Optional[LDAPAuthenticator] = (
    LDAPAuthenticator() if settings.LDAP_ENABLED else None
)

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import ldap3
from ldap3 import ALL, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPException

from app.core.config import settings

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
        """Authenticate user against LDAP."""
        bind_conn: Optional[Connection] = None
        user_conn: Optional[Connection] = None
        try:
            logger.info("LDAP auth attempt for '%s' against %s", username, settings.LDAP_SERVER)
            logger.info("LDAP bind DN: %s", settings.LDAP_BIND_DN)

            # Step 1: Bind with service account
            server = Server(
                settings.LDAP_SERVER,
                use_ssl=settings.LDAP_USE_SSL,
                get_info=ALL,
            )
            bind_conn = Connection(
                server,
                user=settings.LDAP_BIND_DN,
                password=settings.LDAP_BIND_PASSWORD,
                auto_bind=True,
                read_only=True,
            )

            search_base = settings.LDAP_USER_DN or settings.LDAP_BASE_DN
            attrs = [
                "cn",
                getattr(settings, "LDAP_EMAIL_ATTR", "mail"),
                "department",
                "title",
                "memberOf",
                "sAMAccountName",
                "userPrincipalName",
                "uid",
            ]

            # Step 2: Search for user — try sAMAccountName first (Active Directory)
            search_filter = f"(sAMAccountName={ldap3.utils.conv.escape_filter_chars(username)})"
            bind_conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attrs,
            )

            if not bind_conn.entries:
                # Try config-driven filter
                user_attr = getattr(settings, "LDAP_USER_ATTR", "sAMAccountName")
                search_filter = getattr(settings, "LDAP_USER_SEARCH_FILTER", "").format(
                    user_attr=user_attr,
                    username=ldap3.utils.conv.escape_filter_chars(username),
                )
                if search_filter:
                    bind_conn.search(
                        search_base=search_base,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=attrs,
                    )

            if not bind_conn.entries:
                # Try alternative filters
                for alt_filter in [
                    f"(uid={ldap3.utils.conv.escape_filter_chars(username)})",
                    f"(userPrincipalName={username}@*)",
                    f"(mail={username}@*)",
                ]:
                    bind_conn.search(
                        search_base=search_base,
                        search_filter=alt_filter,
                        search_scope=SUBTREE,
                        attributes=attrs,
                    )
                    if bind_conn.entries:
                        break

            if not bind_conn.entries:
                logger.warning("LDAP user not found: %s", username)
                bind_conn.unbind()
                return None

            user_entry = bind_conn.entries[0]
            user_dn = str(user_entry.entry_dn)
            logger.info("Found LDAP user DN: %s", user_dn)

            bind_conn.unbind()
            bind_conn = None

            # Step 3: Verify user's password by binding as the user
            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True,
            )
            if not user_conn.bound:
                logger.warning("LDAP credential verification failed for: %s", username)
                return None
            user_conn.unbind()
            user_conn = None

            # Step 4: Extract attributes
            display_name = str(user_entry.cn) if hasattr(user_entry, "cn") and user_entry.cn else username
            email_attr = getattr(settings, "LDAP_EMAIL_ATTR", "mail")
            email = str(getattr(user_entry, email_attr, "")) if hasattr(user_entry, email_attr) else ""
            if not email and hasattr(user_entry, "mail"):
                email = str(user_entry.mail)
            department = str(user_entry.department) if hasattr(user_entry, "department") and user_entry.department else ""
            title = str(user_entry.title) if hasattr(user_entry, "title") and user_entry.title else ""
            groups = [str(g) for g in user_entry.memberOf] if hasattr(user_entry, "memberOf") else []

            role = self._map_groups_to_role(groups)
            ldap_groups_str = ";".join(groups) if groups else ""

            logger.info("LDAP auth success: %s (role=%s, groups=%d)", username, role, len(groups))

            return {
                "username": username,
                "display_name": display_name,
                "email": email or f"{username}@studio.local",
                "department": department or None,
                "title": title or None,
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
        role_map = getattr(settings, "LDAP_ROLE_MAP", None)
        if not role_map:
            return "artist"
        best_role = "artist"
        best_priority = ROLE_PRIORITY.get("artist", 0)
        group_lower_map = {g.lower(): g for g in groups}
        for group_dn, role in role_map.items():
            if group_dn.lower() in group_lower_map:
                priority = ROLE_PRIORITY.get(role, 0)
                if priority > best_priority:
                    best_role = role
                    best_priority = priority
        return best_role

    def get_users_by_role(self, role: str) -> List[dict]:
        role_map = getattr(settings, "LDAP_ROLE_MAP", None)
        if not role_map:
            return []
        target_group_dn: Optional[str] = None
        for group_dn, mapped_role in role_map.items():
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
            user_attr = getattr(settings, "LDAP_USER_ATTR", "sAMAccountName")
            email_attr = getattr(settings, "LDAP_EMAIL_ATTR", "mail")
            bind_conn.search(
                search_base=settings.LDAP_USER_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=[user_attr, "cn", email_attr, "department"],
            )
            users = []
            for entry in bind_conn.entries:
                users.append({
                    "username": str(entry[user_attr]) if user_attr in entry else "",
                    "display_name": str(entry["cn"]) if "cn" in entry else "",
                    "email": str(entry[email_attr]) if email_attr in entry else "",
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

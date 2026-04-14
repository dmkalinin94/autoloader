from __future__ import annotations


class LdapClient:
    """Thin adapter for AD lookups.

    Replace implementation with real LDAP bind/search for your infra.
    """

    def get_user_profile(self, login: str) -> dict | None:
        return {"login": login, "mention_id": f"@{login}"}

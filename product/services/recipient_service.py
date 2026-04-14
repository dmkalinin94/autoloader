from __future__ import annotations

from product.clients.ldap_client import LdapClient


class RecipientService:
    def __init__(self, ldap_client: LdapClient) -> None:
        self.ldap_client = ldap_client

    def resolve_mentions(self, recipients: list[str]) -> list[str]:
        mention_ids: list[str] = []
        for login in recipients:
            profile = self.ldap_client.get_user_profile(login)
            if profile and profile.get("mention_id"):
                mention_ids.append(profile["mention_id"])
        return mention_ids

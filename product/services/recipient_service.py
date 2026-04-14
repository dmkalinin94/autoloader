from __future__ import annotations

from product.clients.ad_mapping_client import ADMappingClient


class RecipientService:
    def __init__(self, ad_mapping_client: ADMappingClient) -> None:
        self.ad_mapping_client = ad_mapping_client

    def get_recipient_profiles(self, recipients: list[str]) -> dict[str, dict[str, str]]:
        return self.ad_mapping_client.get_recipient_profiles_from_ad_mapping(recipients)

    def resolve_mentions(self, recipients: list[str]) -> list[str]:
        profiles = self.get_recipient_profiles(recipients)
        mention_ids: list[str] = []
        for login in self.ad_mapping_client.normalize_logins(recipients):
            profile = profiles.get(login)
            if profile and profile.get("mention_id") and profile["mention_id"] not in mention_ids:
                mention_ids.append(profile["mention_id"])
        return mention_ids

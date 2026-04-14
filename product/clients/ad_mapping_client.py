from __future__ import annotations

from psycopg2.extras import RealDictCursor

from product.db.connection import connect
from product.db import queries


class ADMappingClient:
    @staticmethod
    def normalize_logins(users: list[str]) -> list[str]:
        logins: list[str] = []
        for user in users:
            raw = str(user).strip()
            if not raw:
                continue
            if raw.startswith("@"):
                raw = raw[1:]
            if ":" in raw:
                raw = raw.split(":", 1)[0]
            login = raw.strip().lower()
            if login and login not in logins:
                logins.append(login)
        return logins

    def upsert_mapping(self, rows: list[dict]) -> None:
        with connect() as conn, conn.cursor() as cur:
            for row in rows:
                cur.execute(queries.UPSERT_AD_KTALK_USER_MAP, row)

    def get_recipient_profiles_from_ad_mapping(self, users: list[str]) -> dict[str, dict[str, str]]:
        logins = self.normalize_logins(users)
        if not logins:
            return {}

        with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(queries.GET_MENTION_IDS_BY_AD_LOGINS, {"logins": logins})
            rows = cur.fetchall()

        profiles: dict[str, dict[str, str]] = {}
        for row in rows:
            login = str(row["ad_login"]).strip().lower()
            mention_id = str(row["ktalk_mention_id"] or "").strip()
            if not mention_id:
                continue
            full_name = str(row.get("ad_display_name") or "").strip()
            profiles[login] = {"mention_id": mention_id, "full_name": full_name}
        return profiles

from __future__ import annotations

import re
from urllib.parse import quote

import requests

from product import cnf


class KTalkClient:
    def _bot_api_url(self, endpoint: str) -> str:
        base = str(cnf.KTALK_BASE_URL).rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/_matrix/client/strangler/api/v1/bot/{cnf.KTALK_JWT_TOKEN}/{endpoint}"

    def _bearer_headers(self) -> dict[str, str]:
        token = str(cnf.KTALK_JWT_TOKEN).strip()
        if token.lower().startswith("bearer "):
            auth = token
        else:
            auth = f"Bearer {token}"
        return {"Authorization": auth, "Content-Type": "application/json"}

    def send_to_ktalk_message(
        self,
        text: str,
        trigger_time: str,
        discussion_id: str,
        event: str,
        thread_id: str | None = None,
        mentions: list[str] | None = None,
        message_format: str = "plain",
        decorate_event: bool = True,
    ) -> str | None:
        if message_format not in {"plain", "html", "markdown"}:
            raise ValueError(f"Unsupported ktalk message format: {message_format}")

        event_prefix = "🔴🤖" if event == "1" else "🟢🤖"
        message_text = f"{event_prefix}{text}" if decorate_event else text
        final_text = f"{trigger_time} {message_text}".strip()
        if len(final_text) > 4096:
            return None

        payload = {
            "room_id": discussion_id,
            "thread_id": thread_id,
            "format": message_format,
            "message": final_text,
            "mentions": mentions or [],
        }
        response = requests.post(
            self._bot_api_url("send_message"),
            json=payload,
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        if not response.ok:
            return None
        return str(response.json().get("event_id", "")).strip() or None

    def get_room_members(self, room_id: str) -> set[str]:
        room_path = quote(room_id, safe="!:")
        url = f"{str(cnf.KTALK_BASE_URL).rstrip('/')}/_matrix/client/v3/rooms/{room_path}/members"
        response = requests.get(
            url,
            headers=self._bearer_headers(),
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        if not response.ok:
            return set()

        payload = response.json()
        members: set[str] = set()
        chunk = payload.get("chunk", [])
        if isinstance(chunk, list):
            for item in chunk:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", {})
                membership = str(content.get("membership", "")).strip().lower()
                if membership != "join":
                    continue
                user_id = item.get("state_key") or item.get("user_id") or content.get("user_id")
                if isinstance(user_id, str) and user_id:
                    members.add(user_id)
        return members

    def invite_user(self, room_id: str, user_id: str) -> bool:
        room_path = quote(room_id, safe="!:")
        url = f"{str(cnf.KTALK_BASE_URL).rstrip('/')}/_matrix/client/v3/rooms/{room_path}/invite"
        response = requests.post(
            url,
            headers=self._bearer_headers(),
            json={"user_id": user_id},
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        return response.ok

    @staticmethod
    def normalize_mentions(users: list[str]) -> list[str]:
        mentions: list[str] = []
        pattern = re.compile(r"^@[A-Za-z0-9._=-]+:[A-Za-z0-9.-]+$")
        domain = str(cnf.KTALK_USER_DOMAIN).strip().lstrip("@")

        for user in users:
            raw = str(user).strip()
            if not raw:
                continue

            if raw.startswith("@"):
                mention = raw if ":" in raw else f"{raw}:{domain}"
            else:
                local_part = raw.lstrip("@")
                mention = f"@{local_part}" if ":" in local_part else f"@{local_part}:{domain}"

            if pattern.fullmatch(mention) and mention not in mentions:
                mentions.append(mention)

        return mentions

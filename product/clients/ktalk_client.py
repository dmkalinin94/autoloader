from __future__ import annotations

import requests

from product import cnf


class KTalkClient:
    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {cnf.KTALK_JWT_TOKEN}",
            "Content-Type": "application/json",
        }

    def send_message(self, room_id: str, body: str, thread_id: str | None = None) -> dict:
        payload: dict = {
            "msgtype": "m.text",
            "body": body,
        }
        if thread_id:
            payload["m.relates_to"] = {
                "rel_type": "m.thread",
                "event_id": thread_id,
            }

        response = requests.post(
            f"{cnf.KTALK_BASE_URL}/_matrix/client/v3/rooms/{room_id}/send/m.room.message",
            headers=self._headers,
            json=payload,
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        response.raise_for_status()
        return response.json()

    def invite_user(self, room_id: str, user_id: str) -> None:
        requests.post(
            f"{cnf.KTALK_BASE_URL}/_matrix/client/v3/rooms/{room_id}/invite",
            headers=self._headers,
            json={"user_id": user_id},
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        ).raise_for_status()

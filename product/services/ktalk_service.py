from __future__ import annotations

from product import cnf
from product.clients.ktalk_client import KTalkClient


class KTalkService:
    def __init__(self, client: KTalkClient) -> None:
        self.client = client

    def create_discussion(self, text: str, room_id: str | None = None) -> tuple[str, str]:
        actual_room_id = room_id or cnf.KTALK_ROOM_ID
        response = self.client.send_message(actual_room_id, text)
        thread_id = response["event_id"]
        return actual_room_id, thread_id

    def send_thread_message(self, room_id: str, thread_id: str, text: str) -> None:
        self.client.send_message(room_id=room_id, body=text, thread_id=thread_id)

    def notify_recipients(self, room_id: str, mention_ids: list[str], text: str) -> None:
        mention_text = " ".join(mention_ids)
        body = f"{text}\n{mention_text}" if mention_ids else text
        self.client.send_message(room_id, body)
        if cnf.KTALK_DRY_RUN_MENTIONS_INVITES:
            return
        for mention_id in mention_ids:
            user_id = f"{mention_id}:{cnf.KTALK_USER_DOMAIN}" if ":" not in mention_id else mention_id
            self.client.invite_user(room_id, user_id)

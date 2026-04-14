from __future__ import annotations

from product import cnf
from product.clients.ktalk_client import KTalkClient


class KTalkService:
    def __init__(self, client: KTalkClient) -> None:
        self.client = client

    def create_discussion(
        self,
        users: list[str],
        full_name: str,
        trigger_name: str,
        reply: str,
        jira_key: str,
        trigger_time: str,
    ) -> tuple[str, str]:
        room_id = cnf.KTALK_ROOM_ID
        jira_issue_url = cnf.JIRA_ISSUE_BROWSE_URL.format(jira_key)
        first_message = f"Авария. {full_name}. {trigger_name}. {reply}. {jira_key}"

        event_id = self.client.send_to_ktalk_message(first_message, "", room_id, event="1", thread_id=None)
        if not event_id:
            raise RuntimeError("Failed to send first incident message to Kontur Talk")

        thread_message = (
            f"{trigger_time}\n"
            "event=1\n"
            f"{trigger_name}\n"
            f"{reply}\n"
            f"{jira_issue_url}"
        )
        self.client.send_to_ktalk_message(
            thread_message,
            "",
            room_id,
            event="1",
            thread_id=event_id,
        )

        self.notify_recipients(room_id, event_id, users)
        return room_id, event_id

    def send_thread_message(
        self,
        room_id: str,
        thread_id: str,
        text: str,
        event: str = "1",
        message_format: str = "plain",
    ) -> None:
        self.client.send_to_ktalk_message(
            text,
            "",
            room_id,
            event=event,
            thread_id=thread_id,
            message_format=message_format,
            decorate_event=False,
        )

    def notify_recipients(self, room_id: str, thread_id: str, mention_ids: list[str]) -> None:
        mentions = self.client.normalize_mentions(mention_ids)
        if not mentions:
            return

        room_members = self.client.get_room_members(room_id)
        for mention in mentions:
            if cnf.KTALK_DRY_RUN_MENTIONS_INVITES:
                self.client.send_to_ktalk_message(
                    f"[DEBUG] Нужно упомянуть: {mention}",
                    "",
                    room_id,
                    event="1",
                    thread_id=thread_id,
                    mentions=[],
                    decorate_event=False,
                )
                continue

            if mention not in room_members:
                self.client.invite_user(room_id, mention)

            self.client.send_to_ktalk_message(
                mention,
                "",
                room_id,
                event="1",
                thread_id=thread_id,
                mentions=[mention],
                decorate_event=False,
            )

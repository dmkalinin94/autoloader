from __future__ import annotations

import argparse
import json
import logging

from product import cnf
from product.clients.ad_mapping_client import ADMappingClient
from product.clients.jira_client import JiraClient
from product.clients.ktalk_client import KTalkClient
from product.db.repository import AlertStateRepository
from product.models.events import EventPayload, ParsedEvent
from product.services.flap_policy import should_reuse_night_incident
from product.services.jira_service import JiraService
from product.services.ktalk_service import KTalkService
from product.services.recipient_service import RecipientService
from product.services.state_service import StateService
from product.utils.time_utils import is_night_window, parse_zabbix_time
from product.utils.validators import extract_shortname, validate_insight_id


class EventProcessor:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.state_service = StateService(AlertStateRepository())
        self.jira_service = JiraService(JiraClient())
        self.ktalk_service = KTalkService(KTalkClient())
        self.recipient_service = RecipientService(ADMappingClient())

    def run_from_cli(self) -> int:
        parser = argparse.ArgumentParser()
        parser.add_argument("--event", required=True)
        parser.add_argument("--insightId", required=True)
        parser.add_argument("--groups", required=True)
        parser.add_argument("--triggerTime", required=True)
        parser.add_argument("--trigName", required=True)
        parser.add_argument("--message", required=True)
        args = parser.parse_args()

        payload = EventPayload(
            event=args.event,
            insight_id=args.insightId,
            groups=args.groups,
            trigger_time_raw=args.triggerTime,
            trigger_name=args.trigName,
            message=args.message,
        )
        self.process(payload)
        return 0

    def process(self, payload: EventPayload) -> None:
        parsed = self._parse_event(payload)
        if parsed.event_value == 1:
            self._handle_event_open(parsed)
        elif parsed.event_value == 0:
            self._handle_event_close(parsed)
        else:
            raise ValueError(f"Unsupported event value: {parsed.event_value}")

    def _parse_event(self, payload: EventPayload) -> ParsedEvent:
        trigger_time = parse_zabbix_time(payload.trigger_time_raw, cnf.TIMEZONE_NAME)
        return ParsedEvent(
            event_value=int(payload.event),
            insight_id=validate_insight_id(payload.insight_id),
            groups=payload.groups,
            trigger_time=trigger_time,
            trigger_name=payload.trigger_name,
            message=payload.message,
        )

    def _handle_event_open(self, event: ParsedEvent) -> None:
        active_state = self.state_service.get_active_state(event.insight_id)
        if active_state is not None:
            updated = self.state_service.activate_existing_state(active_state.id, event.trigger_time)
            self.ktalk_service.send_thread_message(
                active_state.ktalk_room_id or cnf.KTALK_ROOM_ID,
                active_state.ktalk_thread_id,
                f"Повторный event=1: {event.message}",
                event="1",
            )
            self._append_audit(
                active_state.id,
                event,
                "append_to_active_incident",
                f"balance={updated['event_balance']}",
                decision_code="append_to_active_incident",
                jira_issue_key=active_state.jira_issue_key,
                ktalk_thread_id=active_state.ktalk_thread_id,
            )
            return

        last_state = self.state_service.get_last_state(event.insight_id)
        night = is_night_window(event.trigger_time, cnf.FLAP_NIGHT_START_HOUR, cnf.FLAP_NIGHT_END_HOUR)

        can_reuse = (
            last_state is not None
            and should_reuse_night_incident(
                now_dt=event.trigger_time,
                is_night=night,
                last_event0_at=last_state.last_event0_at,
                flap_reopen_until=last_state.flap_reopen_until,
            )
            and last_state.ktalk_thread_id
            and last_state.jira_issue_key
            and last_state.status in {"closed", "cooldown_night", "active"}
        )
        if can_reuse:
            self.state_service.activate_existing_state(last_state.id, event.trigger_time)
            self.ktalk_service.send_thread_message(
                last_state.ktalk_room_id or cnf.KTALK_ROOM_ID,
                last_state.ktalk_thread_id,
                f"Ночной re-open (<= {cnf.FLAP_REOPEN_HOURS}ч): {event.message}",
                event="1",
            )
            self._append_audit(
                last_state.id,
                event,
                "reopen_existing_night_incident",
                "reuse previous jira/thread",
                decision_code="reopen_existing_night_incident",
                jira_issue_key=last_state.jira_issue_key,
                ktalk_thread_id=last_state.ktalk_thread_id,
            )
            return

        service_data = self.jira_service.get_service_data(event.insight_id)
        if not service_data.is_actual:
            self._append_audit(
                None,
                event,
                "skip_not_actual",
                "service is not actual in Jira Assets",
                decision_code="skip_not_actual",
            )
            return

        short_name = extract_shortname(event.groups)
        jira_key = self.jira_service.create_incident(
            insight_id=event.insight_id,
            short_name=short_name,
            trigger_name=event.trigger_name,
            event_message=event.message,
            service_data=service_data,
        )

        mentions = self.recipient_service.resolve_mentions(service_data.recipients)
        room_id, thread_id = self.ktalk_service.create_discussion(
            users=mentions,
            full_name=service_data.full_name,
            trigger_name=event.trigger_name,
            reply=event.message,
            jira_key=jira_key,
            trigger_time=event.trigger_time.isoformat(),
        )

        state_id = self.state_service.create_state(
            {
                "insight_id": event.insight_id,
                "short_name": short_name,
                "full_name": service_data.full_name,
                "trigger_name": event.trigger_name,
                "recipients": service_data.recipients,
                "ktalk_room_id": room_id,
                "ktalk_thread_id": thread_id,
                "jira_issue_key": jira_key,
                "event_balance": 1,
                "status": "active",
                "last_event1_at": event.trigger_time,
            }
        )
        self.state_service.insert_incident_history(
            {
                "insight_id": event.insight_id,
                "short_name": short_name,
                "full_name": service_data.full_name,
                "trigger_name": event.trigger_name,
                "trigger_time": event.trigger_time,
                "recipients": service_data.recipients,
                "jira_issue_key": jira_key,
                "ktalk_thread_id": thread_id,
                "ktalk_room_id": room_id,
            }
        )

        decision_code = "night_cooldown_expired_open_new" if night and last_state else "open_new_incident"
        self._append_audit(
            state_id,
            event,
            decision_code,
            "created jira and thread",
            decision_code=decision_code,
            jira_issue_key=jira_key,
            ktalk_thread_id=thread_id,
        )

    def _handle_event_close(self, event: ParsedEvent) -> None:
        active_state = self.state_service.get_active_state(event.insight_id)
        if active_state is None:
            self._append_audit(
                None,
                event,
                "close_event_ignored_no_state",
                "no active state",
                decision_code="close_event_ignored_no_state",
            )
            return

        updated = self.state_service.decrease_event_balance(active_state.id, event.trigger_time)
        self.ktalk_service.send_thread_message(
            active_state.ktalk_room_id or cnf.KTALK_ROOM_ID,
            active_state.ktalk_thread_id,
            f"event=0: {event.message}",
            event="0",
        )

        night = is_night_window(
            event.trigger_time,
            cnf.FLAP_NIGHT_START_HOUR,
            cnf.FLAP_NIGHT_END_HOUR,
        )

        if updated["event_balance"] > 0:
            self._append_audit(
                active_state.id,
                event,
                "close_event_decrement_only",
                f"balance={updated['event_balance']}",
                decision_code="close_event_decrement_only",
                jira_issue_key=active_state.jira_issue_key,
                ktalk_thread_id=active_state.ktalk_thread_id,
            )
            return

        if night:
            self.state_service.mark_state_cooldown_night(active_state.id)
            self.ktalk_service.send_thread_message(
                active_state.ktalk_room_id or cnf.KTALK_ROOM_ID,
                active_state.ktalk_thread_id,
                "Активные алерты временно отсутствуют. В ночной период в течение 3 часов повторное срабатывание будет продолжено в этом же обсуждении.",
                event="0",
            )
            self._append_audit(
                active_state.id,
                event,
                "night_cooldown_started",
                "state moved to cooldown_night",
                decision_code="night_cooldown_started",
                jira_issue_key=active_state.jira_issue_key,
                ktalk_thread_id=active_state.ktalk_thread_id,
            )
            return

        self.state_service.mark_state_closed(active_state.id)
        self.state_service.close_incident_history(
            insight_id=event.insight_id,
            jira_issue_key=active_state.jira_issue_key,
            close_reason="daytime_close",
        )
        self.ktalk_service.send_thread_message(
            active_state.ktalk_room_id or cnf.KTALK_ROOM_ID,
            active_state.ktalk_thread_id,
            "Активные алерты, на которые был создан инцидент, отсутствуют",
            event="0",
        )
        self._append_audit(
            active_state.id,
            event,
            "close_final_daytime",
            "state marked closed",
            decision_code="close_final_daytime",
            jira_issue_key=active_state.jira_issue_key,
            ktalk_thread_id=active_state.ktalk_thread_id,
        )

    def _append_audit(
        self,
        state_id: int | None,
        event: ParsedEvent,
        action: str,
        note: str,
        decision_code: str,
        jira_issue_key: str | None = None,
        ktalk_thread_id: str | None = None,
    ) -> None:
        payload_json = json.dumps(
            {
                "insight_id": event.insight_id,
                "trigger_name": event.trigger_name,
                "message": event.message,
                "event_value": event.event_value,
            },
            ensure_ascii=False,
        )
        self.state_service.append_audit_event(
            {
                "alert_state_id": state_id,
                "insight_id": event.insight_id,
                "event_value": event.event_value,
                "event_time": event.trigger_time,
                "action": action,
                "note": note,
                "decision_code": decision_code,
                "jira_issue_key": jira_issue_key,
                "ktalk_thread_id": ktalk_thread_id,
                "payload_json": payload_json,
            }
        )
        self.logger.info("audit decision=%s action=%s insight=%s", decision_code, action, event.insight_id)

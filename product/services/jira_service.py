from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from product import cnf
from product.clients.jira_client import JiraClient


@dataclass(slots=True)
class JiraServiceData:
    full_name: str
    is_actual: bool
    function_object_key: str | None
    jira_incident_type_key: str | None
    user_group_id: int | None
    recipients: list[str]


def _decode_actual_state(value: str) -> bool:
    return value == "Актуально"


def _extract_recipients_from_group_attributes(payload: list[dict[str, Any]]) -> list[str]:
    recipients: list[str] = []
    mandatory_recipients = ["dm.kalinin", "d.boyarchuk", "t.sukhorukikh", "dk.korolev"]

    for item in payload:
        attr_id = item.get("objectTypeAttributeId")
        if attr_id not in {2543, 2542}:
            continue
        for value in item.get("objectAttributeValues", []):
            name = value.get("user", {}).get("name")
            if isinstance(name, str) and name and name not in recipients:
                recipients.append(name)

    for user in mandatory_recipients:
        if user not in recipients:
            recipients.append(user)
    return recipients


class JiraService:
    def __init__(self, client: JiraClient) -> None:
        self.client = client

    def get_service_data(self, insight_id: str) -> JiraServiceData:
        payload = self.client.get_object_attributes(insight_id)
        if not isinstance(payload, list):
            payload = []

        full_name = ""
        is_actual = False
        function_refs: list[dict[str, Any]] = []
        jira_incident_type_key: str | None = None
        user_group_id: int | None = None

        for item in payload:
            attr_id = item.get("objectTypeAttributeId")
            values = item.get("objectAttributeValues", [])
            if not values:
                continue
            if attr_id == 63:
                full_name = values[0].get("value", "")
            elif attr_id == 126:
                is_actual = _decode_actual_state(values[0].get("value", ""))
            elif attr_id == 2066:
                function_refs = values
            elif attr_id == 2551:
                for value in values:
                    raw_group_id = value.get("referencedObject", {}).get("id")
                    if raw_group_id is not None:
                        user_group_id = int(raw_group_id)
                        break
            elif attr_id == 2413:
                for value in values:
                    object_key = value.get("referencedObject", {}).get("objectKey")
                    if object_key:
                        jira_incident_type_key = str(object_key)
                        break

        preferred_labels = ("Недоступность сервиса", "Прочее")
        function_key: str | None = None
        for label in preferred_labels:
            for ref in function_refs:
                obj = ref.get("referencedObject", {})
                if obj.get("label") == label:
                    function_key = obj.get("objectKey")
                    break
            if function_key:
                break

        if not function_key and function_refs:
            function_key = function_refs[0].get("referencedObject", {}).get("objectKey")

        recipients: list[str] = []
        if user_group_id is not None:
            group_payload = self.client.get_object_attributes(user_group_id)
            if not isinstance(group_payload, list):
                group_payload = []
            recipients = _extract_recipients_from_group_attributes(group_payload)

        return JiraServiceData(
            full_name=full_name or insight_id,
            is_actual=is_actual,
            function_object_key=function_key,
            jira_incident_type_key=jira_incident_type_key,
            user_group_id=user_group_id,
            recipients=recipients,
        )

    def create_incident(
        self,
        insight_id: str,
        short_name: str,
        trigger_name: str,
        event_message: str,
        service_data: JiraServiceData,
    ) -> str:
        payload = {
            "fields": {
                "project": {"key": "INC"},
                "summary": f"Автоматический инцидент Zabbix: {short_name} {trigger_name}",
                "description": event_message,
                "issuetype": {"name": "Incident"},
                "customfield_19700": [{"key": insight_id}],
                "customfield_35901": (
                    [{"key": service_data.jira_incident_type_key}]
                    if service_data.jira_incident_type_key
                    else []
                ),
                "customfield_23400": (
                    [{"key": service_data.function_object_key}]
                    if service_data.function_object_key
                    else []
                ),
            }
        }
        response = self.client.create_incident(payload)
        return response["key"]

    def is_issue_open(self, issue_key: str) -> bool:
        payload = self.client.get_issue_status(issue_key)
        status_name = str(payload.get("fields", {}).get("status", {}).get("name", "")).strip()
        closed_statuses = {"Решен", "Решён", "Закрыт", "Отменен", "Отменён", "Closed", "Done", "Resolved"}
        return bool(status_name) and status_name not in closed_statuses

    def build_issue_url(self, issue_key: str) -> str:
        return cnf.JIRA_ISSUE_BROWSE_URL.format(issue_key)

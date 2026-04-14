from __future__ import annotations

from product import cnf
from product.clients.jira_client import JiraClient


class JiraService:
    def __init__(self, client: JiraClient) -> None:
        self.client = client

    def get_service_data(self, insight_id: str) -> dict:
        attrs = self.client.get_service_attributes(insight_id)
        parsed = {
            "full_name": attrs.get("full_name") or attrs.get("name") or insight_id,
            "is_actual": attrs.get("is_actual", True),
            "function_object_key": attrs.get("function_object_key"),
            "jira_incident_type_key": attrs.get("jira_incident_type_key"),
            "recipients": attrs.get("recipients", []),
        }
        return parsed

    def create_incident(self, service_data: dict, event_message: str) -> str:
        payload = {
            "fields": {
                "project": {"key": "INC"},
                "summary": f"Autoalert: {service_data['full_name']}",
                "description": event_message,
                "issuetype": {
                    "id": service_data.get("jira_incident_type_key") or "10001"
                },
            }
        }
        response = self.client.create_incident(payload)
        return response["key"]

    def is_issue_open(self, issue_key: str) -> bool:
        data = self.client.get_issue_status(issue_key)
        status_name = (
            data.get("fields", {}).get("status", {}).get("name", "").strip().lower()
        )
        return status_name not in {"done", "closed", "resolved"}

    def build_issue_url(self, issue_key: str) -> str:
        return cnf.JIRA_ISSUE_BROWSE_URL.format(issue_key)

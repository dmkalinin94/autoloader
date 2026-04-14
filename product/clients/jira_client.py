from __future__ import annotations

from typing import Any

import requests

from product import cnf


class JiraClient:
    def __init__(self) -> None:
        self._headers = {
            "Authorization": cnf.JIRA_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_object_attributes(self, object_id: str | int) -> list[dict[str, Any]]:
        response = requests.get(
            cnf.JIRA_SERVICE_URL.format(object_id),
            headers=self._headers,
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    def create_incident(self, payload: dict) -> dict:
        response = requests.post(
            cnf.JIRA_CREATE_INC_URL,
            headers=self._headers,
            json=payload,
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        response.raise_for_status()
        return response.json()

    def get_issue_status(self, issue_key: str) -> dict:
        response = requests.get(
            cnf.JIRA_ISSUE_STATUS_URL.format(issue_key),
            headers=self._headers,
            timeout=cnf.REQUEST_TIMEOUT,
            verify=cnf.VERIFY_SSL,
        )
        response.raise_for_status()
        return response.json()

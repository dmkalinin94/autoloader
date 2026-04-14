from __future__ import annotations

from psycopg2.extras import RealDictCursor

from product.db import queries
from product.db.connection import connect
from product.models.state import AlertState


class AlertStateRepository:
    def get_active_state(self, insight_id: str) -> AlertState | None:
        with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(queries.GET_ACTIVE_STATE, {"insight_id": insight_id})
            row = cur.fetchone()
        return AlertState.from_row(row)

    def get_last_state(self, insight_id: str) -> AlertState | None:
        with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(queries.GET_LAST_STATE, {"insight_id": insight_id})
            row = cur.fetchone()
        return AlertState.from_row(row)

    def create_state(self, values: dict) -> int:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(queries.CREATE_STATE, values)
            row = cur.fetchone()
        return row[0]

    def activate_existing_state(self, state_id: int, event_time):
        with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                queries.ACTIVATE_EXISTING_STATE,
                {"state_id": state_id, "delta": 1, "event_time": event_time},
            )
            return cur.fetchone()

    def decrease_event_balance(self, state_id: int, event_time):
        with connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                queries.DECREASE_EVENT_BALANCE,
                {"state_id": state_id, "delta": 1, "event_time": event_time},
            )
            return cur.fetchone()

    def mark_state_closed(self, state_id: int):
        with connect() as conn, conn.cursor() as cur:
            cur.execute(queries.MARK_STATE_CLOSED, {"state_id": state_id})

    def append_audit_event(self, values: dict):
        with connect() as conn, conn.cursor() as cur:
            cur.execute(queries.APPEND_AUDIT_EVENT, values)

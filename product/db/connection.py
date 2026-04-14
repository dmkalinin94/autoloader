from __future__ import annotations

import psycopg2

from product import cnf


def connect():
    return psycopg2.connect(
        dbname=cnf.DB_NAME,
        user=cnf.DB_USER,
        password=cnf.DB_PASSWORD,
        host=cnf.DB_HOST,
        port=cnf.DB_PORT,
        options=cnf.DB_OPTIONS,
    )

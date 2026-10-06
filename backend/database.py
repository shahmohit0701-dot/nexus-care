import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

try:
    import psycopg
    from psycopg import ClientCursor
except ImportError:
    psycopg = None
    ClientCursor = None


BASE = Path(__file__).resolve().parents[1]

# Load backend/.env during local development.
# Render will provide DATABASE_URL as an environment variable.
load_dotenv(BASE / "backend" / ".env")

SQLITE_DB = BASE / "data" / "nexus.db"


def using_postgres():
    return bool(os.getenv("DATABASE_URL"))


class CompatRow(dict):
    """
    PostgreSQL row that behaves like a dictionary while also
    supporting numeric indexing used by the existing SQLite code.
    """

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]

        return super().__getitem__(key)


class CompatCursor:
    """
    Compatibility cursor for the existing NEXUS CARE code.

    It converts SQLite-style '?' parameters to PostgreSQL '%s'
    parameters and converts PostgreSQL rows into dictionary-like rows.
    """

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        sql = sql.replace('datetime("now")', "CURRENT_TIMESTAMP")
        sql = sql.replace("datetime('now')", "CURRENT_TIMESTAMP")
        sql = sql.replace("?", "%s")

        if params is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, params)

        # IMPORTANT:
        # Return the compatibility cursor, not the raw psycopg cursor.
        return self

    def executemany(self, sql, params):
        sql = sql.replace('datetime("now")', "CURRENT_TIMESTAMP")
        sql = sql.replace("datetime('now')", "CURRENT_TIMESTAMP")
        sql = sql.replace("?", "%s")

        self._cursor.executemany(sql, params)

        return self

    def executescript(self, sql):
        """
        Compatibility implementation for SQLite executescript().
        PostgreSQL doesn't have executescript(), so execute each
        statement individually.
        """

        statements = [
            statement.strip()
            for statement in sql.split(";")
            if statement.strip()
        ]

        for statement in statements:
            self.execute(statement)

        return self

    def fetchone(self):
        row = self._cursor.fetchone()

        if row is None:
            return None

        columns = [
            description.name
            for description in self._cursor.description
        ]

        return CompatRow(zip(columns, row))

    def fetchall(self):
        rows = self._cursor.fetchall()

        if not rows:
            return []

        columns = [
            description.name
            for description in self._cursor.description
        ]

        return [
            CompatRow(zip(columns, row))
            for row in rows
        ]

    def __iter__(self):
        return iter(self.fetchall())

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresCompatConnection:
    """
    PostgreSQL connection wrapper used by NEXUS CARE.
    """

    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, params=None):
        cursor = CompatCursor(
            self._connection.cursor()
        )

        return cursor.execute(sql, params)

    def cursor(self):
        return CompatCursor(
            self._connection.cursor()
        )

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()


def get_db():
    """
    Use Neon PostgreSQL when DATABASE_URL is configured.

    Otherwise fall back to the existing local SQLite database.
    """

    if using_postgres():

        if psycopg is None:
            raise RuntimeError(
                "psycopg is required when DATABASE_URL is configured."
            )

        connection = psycopg.connect(
            os.environ["DATABASE_URL"],
            cursor_factory=ClientCursor,
        )

        return PostgresCompatConnection(connection)

    # ---------------------------------------------------------
    # Local SQLite fallback
    # ---------------------------------------------------------

    SQLITE_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        SQLITE_DB
    )

    connection.row_factory = sqlite3.Row

    return connection
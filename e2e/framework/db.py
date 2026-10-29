from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class Database:
    """Thin wrapper for running raw SQL against a service database.

    Every call runs in its own transaction, so the tests always see data
    committed by the services and their own writes are visible to the services.
    """

    def __init__(self, url: str, name: str):
        self.name = name
        self.engine: Engine = create_engine(url, pool_pre_ping=True)

    def fetch_one(self, sql: str, **params: Any) -> Optional[dict[str, Any]]:
        with self.engine.connect() as conn:
            row = conn.execute(text(sql), params).mappings().first()
            return dict(row) if row is not None else None

    def fetch_all(self, sql: str, **params: Any) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql), params).mappings()]

    def scalar(self, sql: str, **params: Any) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(text(sql), params).scalar()

    def execute(self, sql: str, **params: Any) -> int:
        """Runs a write statement and commits it. Returns the affected row count."""
        with self.engine.begin() as conn:
            return conn.execute(text(sql), params).rowcount

    def ping(self) -> None:
        self.scalar("SELECT 1")

    def dispose(self) -> None:
        self.engine.dispose()

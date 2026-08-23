"""SQLite persistence for normalized lottery draws."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from atta_satta.normalization.models import LotteryDraw

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lottery_draws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game TEXT NOT NULL,
    draw_date TEXT NOT NULL,
    draw_time TEXT,
    timezone TEXT,
    ticket_number TEXT NOT NULL,
    source_filename TEXT,
    source_sha256 TEXT,
    source_page INTEGER,
    extraction_method TEXT,
    extraction_confidence REAL,
    original_text TEXT,
    status TEXT NOT NULL,
    imported_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_lottery_draws_game_date
    ON lottery_draws (game, draw_date);

CREATE INDEX IF NOT EXISTS idx_lottery_draws_source_sha256
    ON lottery_draws (source_sha256);
"""


class LotteryRepository:
    """Small SQLite repository for normalized historical results."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def add_draw(self, draw: LotteryDraw) -> int:
        """Persist one draw and return its generated database id."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO lottery_draws (
                    game, draw_date, draw_time, timezone, ticket_number,
                    source_filename, source_sha256, source_page,
                    extraction_method, extraction_confidence, original_text,
                    status, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draw.game,
                    draw.draw_date.isoformat(),
                    draw.draw_time,
                    draw.timezone,
                    draw.ticket_number,
                    draw.source_filename,
                    draw.source_sha256,
                    draw.source_page,
                    draw.extraction_method,
                    draw.extraction_confidence,
                    draw.original_text,
                    draw.status.value,
                    draw.imported_at.isoformat() if draw.imported_at else None,
                ),
            )
            return int(cursor.lastrowid)

    def add_draws(self, draws: Iterable[LotteryDraw]) -> int:
        """Persist multiple draws in one transaction and return inserted count."""
        records = list(draws)
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO lottery_draws (
                    game, draw_date, draw_time, timezone, ticket_number,
                    source_filename, source_sha256, source_page,
                    extraction_method, extraction_confidence, original_text,
                    status, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        draw.game,
                        draw.draw_date.isoformat(),
                        draw.draw_time,
                        draw.timezone,
                        draw.ticket_number,
                        draw.source_filename,
                        draw.source_sha256,
                        draw.source_page,
                        draw.extraction_method,
                        draw.extraction_confidence,
                        draw.original_text,
                        draw.status.value,
                        draw.imported_at.isoformat() if draw.imported_at else None,
                    )
                    for draw in records
                ],
            )
        return len(records)

    def count(self) -> int:
        """Return the number of stored draw records."""
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM lottery_draws").fetchone()
            return int(row["count"])

"""Read-side queries for historical lottery analysis."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from atta_satta.database.sqlite import LotteryRepository
from atta_satta.normalization.models import LotteryDraw, RecordStatus


class LotteryReader:
    """Read normalized records from the SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self.repository = LotteryRepository(database_path)

    def records(self, *, game: str | None = None, valid_only: bool = False) -> list[LotteryDraw]:
        clauses: list[str] = []
        parameters: list[str] = []
        if game:
            clauses.append("game = ?")
            parameters.append(game)
        if valid_only:
            clauses.append("status = ?")
            parameters.append(RecordStatus.VALID.value)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT game, draw_date, draw_time, timezone, ticket_number,
                   source_filename, source_sha256, source_page,
                   extraction_method, extraction_confidence, original_text,
                   status, imported_at
            FROM lottery_draws
            {where}
            ORDER BY draw_date, draw_time, id
        """
        with self.repository._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        return [
            LotteryDraw(
                game=row["game"],
                draw_date=date.fromisoformat(row["draw_date"]),
                draw_time=row["draw_time"],
                timezone=row["timezone"],
                ticket_number=row["ticket_number"],
                source_filename=row["source_filename"],
                source_sha256=row["source_sha256"],
                source_page=row["source_page"],
                extraction_method=row["extraction_method"],
                extraction_confidence=row["extraction_confidence"],
                original_text=row["original_text"],
                status=RecordStatus(row["status"]),
            )
            for row in rows
        ]

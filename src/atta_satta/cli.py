"""Command-line entry point for the Atta Satta MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from atta_satta.config import Settings
from atta_satta.database.queries import LotteryReader
from atta_satta.prediction.ranking import rank_candidates
from atta_satta.statistics.analysis import distribution_summary, frequency_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Atta Satta lottery analysis MVP")
    parser.add_argument("--database", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats = subparsers.add_parser("stats", help="show historical statistics")
    stats.add_argument("--game")

    predict = subparsers.add_parser("predict", help="rank experimental candidates")
    predict.add_argument("--game")
    predict.add_argument("--minimum", type=int, required=True)
    predict.add_argument("--maximum", type=int, required=True)
    predict.add_argument("--count", type=int, default=10)

    args = parser.parse_args()
    settings = Settings.from_project_root()
    database = args.database or settings.data_dir / "atta_satta.sqlite3"
    reader = LotteryReader(database)
    records = reader.records(game=args.game, valid_only=True)

    if args.command == "stats":
        summary = distribution_summary(records)
        print(f"Records: {summary.total_records}")
        print(f"Unique tickets: {summary.unique_numbers}")
        print(f"Range: {summary.min_number}..{summary.max_number}")
        print(f"Mean: {summary.mean_number}")
        print(f"Std dev: {summary.std_number}")
        print("\nTop frequencies:")
        for item in frequency_table(records)[:20]:
            print(f"{item.ticket_number}\t{item.count}\tgap={item.gap}")
        return

    if args.command == "predict":
        ranked = rank_candidates(
            records,
            minimum=args.minimum,
            maximum=args.maximum,
            candidates=args.count,
            validated=False,
        )
        print("Rank\tTicket\tScore\tConfidence\tExplanation")
        for item in ranked:
            print(f"{item.rank}\t{item.ticket_number}\t{item.score}\t{item.confidence}\t{item.explanation}")
        print("\nExperimental ranking only; not a guarantee of winning numbers.")

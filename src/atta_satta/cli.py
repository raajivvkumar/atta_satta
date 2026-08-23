"""Command-line entry point for the Atta Satta MVP."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from atta_satta.config import Settings
from atta_satta.database.queries import LotteryReader
from atta_satta.database.sqlite import LotteryRepository
from atta_satta.evaluation.backtest import walk_forward_backtest
from atta_satta.extraction.pdf import extract_pdf_text
from atta_satta.models.comparison import compare_models
from atta_satta.ocr.image import ocr_image
from atta_satta.pipeline.importer import import_extracted_text
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

    backtest = subparsers.add_parser("backtest", help="run leakage-safe walk-forward validation")
    backtest.add_argument("--game")
    backtest.add_argument("--minimum", type=int, required=True)
    backtest.add_argument("--maximum", type=int, required=True)
    backtest.add_argument("--top-k", type=int, default=10)
    backtest.add_argument("--minimum-history", type=int, default=20)

    models = subparsers.add_parser("models", help="compare available model strategies")
    models.add_argument("--game")
    models.add_argument("--minimum", type=int, required=True)
    models.add_argument("--maximum", type=int, required=True)
    models.add_argument("--top-k", type=int, default=10)
    models.add_argument("--minimum-history", type=int, default=20)

    import_parser = subparsers.add_parser(
        "import",
        help="extract ticket numbers from a PDF/image and import them",
    )
    import_parser.add_argument("source", type=Path)
    import_parser.add_argument("--game", required=True)
    import_parser.add_argument("--draw-date", type=date.fromisoformat, required=True)
    import_parser.add_argument("--minimum", type=int, default=0)
    import_parser.add_argument("--maximum", type=int, default=9_999_999)

    args = parser.parse_args()
    settings = Settings.from_project_root()
    database = args.database or settings.data_dir / "atta_satta.sqlite3"

    if args.command == "import":
        repository = LotteryRepository(database)
        source = args.source.resolve()
        suffix = source.suffix.lower()
        total = 0

        if suffix == ".pdf":
            for page in extract_pdf_text(source):
                inserted = import_extracted_text(
                    repository,
                    page.text,
                    game=args.game,
                    draw_date=args.draw_date,
                    source_path=source,
                    source_page=page.page_number,
                    extraction_method=page.extraction_method,
                    minimum_ticket=args.minimum,
                    maximum_ticket=args.maximum,
                )
                total += inserted
        elif suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
            result = ocr_image(source)
            total = import_extracted_text(
                repository,
                result.text,
                game=args.game,
                draw_date=args.draw_date,
                source_path=source,
                extraction_method=result.extraction_method,
                extraction_confidence=result.confidence,
                minimum_ticket=args.minimum,
                maximum_ticket=args.maximum,
            )
        else:
            raise ValueError(f"Unsupported source format: {source.suffix}")

        print(f"Detected/imported ticket candidates: {total}")
        print("Review status is preserved; extraction does not guarantee correctness.")
        return

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
        return

    if args.command == "backtest":
        result = walk_forward_backtest(
            records,
            minimum=args.minimum,
            maximum=args.maximum,
            top_k=args.top_k,
            minimum_history=args.minimum_history,
        )
        print(f"Strategy: {result.strategy}")
        print(f"Predictions: {result.predictions}")
        print(f"Top-{result.top_k} hits: {result.hits}")
        print(f"Historical hit rate: {result.hit_rate:.4%}")
        print(f"Random hit rate: {result.random_hit_rate:.4%}")
        print(f"Lift vs random: {result.lift_vs_random:.3f}")
        return

    if args.command == "models":
        for result in compare_models(
            records,
            minimum=args.minimum,
            maximum=args.maximum,
            top_k=args.top_k,
            minimum_history=args.minimum_history,
        ):
            print(
                f"{result.name}\t{result.status}\t"
                f"top-{args.top_k}={result.top_k_hit_rate:.4%}\t{result.note}"
            )

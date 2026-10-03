"""Streamlit dashboard for the Atta Satta MVP."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path


def run() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Install the 'ui' extra to run the dashboard.") from exc

    from atta_satta.config import Settings
    from atta_satta.database.queries import LotteryReader
    from atta_satta.database.sqlite import LotteryRepository
    from atta_satta.extraction.pdf import extract_pdf_text
    from atta_satta.ingestion.files import describe_source_file
    from atta_satta.normalization.models import RecordStatus
    from atta_satta.ocr.image import ocr_image
    from atta_satta.pipeline.importer import (
        ImportCandidate,
        extract_import_candidates,
        import_candidates,
    )
    from atta_satta.prediction.ranking import rank_candidates
    from atta_satta.statistics.analysis import distribution_summary, frequency_table
    from atta_satta.validation.results import validate_ticket_number

    settings = Settings.from_project_root()
    settings.ensure_directories()
    database = settings.data_dir / "atta_satta.sqlite3"
    reader = LotteryReader(database)
    repository = LotteryRepository(database)

    st.set_page_config(page_title="Atta Satta Analytics", layout="wide")
    st.title("Atta Satta — Historical Lottery Analytics")
    st.warning(
        "Experimental analysis only. Lottery outcomes may be random; "
        "rankings are not guaranteed predictions."
    )

    all_records = reader.records()
    records = [record for record in all_records if record.status is RecordStatus.VALID]
    review_records = [record for record in all_records if record.status is RecordStatus.REVIEW]
    invalid_records = [record for record in all_records if record.status is RecordStatus.INVALID]
    summary = distribution_summary(records)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Validated", summary.total_records)
    c2.metric("Review", len(review_records))
    c3.metric("Invalid", len(invalid_records))
    c4.metric("Unique tickets", summary.unique_numbers)
    c5.metric("Numeric minimum", summary.min_number if summary.min_number is not None else "—")
    c6.metric("Numeric maximum", summary.max_number if summary.max_number is not None else "—")

    if all_records and not records:
        st.warning(
            "Records exist in the database, but none are currently validated. "
            "Check the configured result range and the Import tab validation status."
        )

    tabs = st.tabs(["Dashboard", "Import", "Prediction", "Evaluation"])
    with tabs[0]:
        st.subheader("Historical frequency")
        table = frequency_table(records)
        st.dataframe(
            [
                {
                    "Ticket": item.ticket_number,
                    "Count": item.count,
                    "Frequency": round(item.frequency, 4),
                    "Gap": item.gap,
                }
                for item in table[:100]
            ],
            use_container_width=True,
        )

        if review_records or invalid_records:
            st.subheader("Records needing attention")
            st.dataframe(
                [
                    {
                        "Game": record.game,
                        "Date": record.draw_date.isoformat(),
                        "Ticket": record.ticket_number,
                        "Status": record.status.value,
                        "Source": record.source_filename,
                        "Page": record.source_page,
                    }
                    for record in [*review_records, *invalid_records][:100]
                ],
                use_container_width=True,
            )

    with tabs[1]:
        st.subheader("Document extraction and candidate analysis")
        st.caption(
            "Set the real result range before uploading. For a 0–99 game, use 0 and 99. "
            "The importer now uses this range while detecting numeric results."
        )
        game = st.text_input("Lottery / game", value="Atta Satta", key="import_game")
        draw_date = st.date_input("Draw date", value=date.today(), key="import_draw_date")
        range_left, range_right = st.columns(2)
        with range_left:
            minimum_ticket = st.number_input(
                "Allowed minimum",
                min_value=0,
                value=0,
                step=1,
                key="import_minimum",
            )
        with range_right:
            maximum_ticket = st.number_input(
                "Allowed maximum",
                min_value=1,
                value=99,
                step=1,
                key="import_maximum",
            )

        uploads = st.file_uploader(
            "Upload PDF or image files",
            type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "webp"],
            accept_multiple_files=True,
        )
        detected_candidates: list[ImportCandidate] = []

        if uploads:
            for upload_index, upload in enumerate(uploads):
                suffix = Path(upload.name).suffix.lower()
                prefix = f"{Path(upload.name).stem}_"
                with tempfile.NamedTemporaryFile(
                    prefix=prefix,
                    suffix=suffix,
                    delete=False,
                ) as temp:
                    temp.write(upload.getvalue())
                    temp_path = Path(temp.name)

                st.write(
                    f"**{upload.name}** — SHA-256: "
                    f"`{describe_source_file(temp_path).sha256}`"
                )
                try:
                    if suffix == ".pdf":
                        pages = list(extract_pdf_text(temp_path))
                        for page in pages:
                            page_candidates = extract_import_candidates(
                                page.text,
                                game=game.strip(),
                                draw_date=draw_date,
                                source_path=temp_path,
                                source_page=page.page_number,
                                extraction_method=page.extraction_method,
                                extraction_confidence=page.extraction_confidence,
                                minimum_ticket=int(minimum_ticket),
                                maximum_ticket=int(maximum_ticket),
                            )
                            detected_candidates.extend(page_candidates)
                            st.text_area(
                                f"{upload.name} — page {page.page_number}",
                                page.text,
                                height=150,
                                key=f"pdf_text_{upload_index}_{page.page_number}",
                            )
                    else:
                        result = ocr_image(temp_path)
                        st.write(f"OCR confidence: {result.confidence}")
                        st.text_area(
                            f"{upload.name} — OCR text",
                            result.text,
                            height=200,
                            key=f"ocr_text_{upload_index}",
                        )
                        image_candidates = extract_import_candidates(
                            result.text,
                            game=game.strip(),
                            draw_date=draw_date,
                            source_path=temp_path,
                            extraction_method=result.extraction_method,
                            extraction_confidence=result.confidence,
                            minimum_ticket=int(minimum_ticket),
                            maximum_ticket=int(maximum_ticket),
                        )
                        detected_candidates.extend(image_candidates)
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))

            st.divider()
            st.subheader("Detected candidates")
            if detected_candidates:
                preview_rows = []
                for candidate in detected_candidates:
                    validation = validate_ticket_number(
                        candidate.ticket_number,
                        minimum=int(minimum_ticket),
                        maximum=int(maximum_ticket),
                    )
                    preview_rows.append(
                        {
                            "Ticket": candidate.ticket_number,
                            "Status": validation.status.value,
                            "Reason": validation.reason,
                            "Page": candidate.source_page,
                            "Method": candidate.extraction_method,
                            "Confidence": candidate.extraction_confidence,
                        }
                    )
                st.dataframe(preview_rows, use_container_width=True)
                st.success(f"Detected {len(detected_candidates)} candidate(s) from the upload(s).")

                if st.button("Import detected candidates", type="primary"):
                    if not game.strip():
                        st.error("Lottery / game is required before importing.")
                    else:
                        inserted = import_candidates(
                            repository,
                            detected_candidates,
                            minimum_ticket=int(minimum_ticket),
                            maximum_ticket=int(maximum_ticket),
                        )
                        st.success(f"Imported {inserted} detected candidate(s).")
                        st.rerun()
            else:
                st.warning(
                    "No candidates were detected. Verify OCR/PDF text and make sure the "
                    "Allowed minimum/maximum match the actual result format."
                )

            st.divider()
            st.subheader("Commit one manually reviewed result")
            st.caption(
                "Use this only when a value is missing or needs manual correction after extraction."
            )
            ticket = st.text_input("Ticket number", value="", key="manual_ticket")
            page = st.number_input(
                "Source page",
                min_value=1,
                value=1,
                step=1,
                key="manual_source_page",
            )
            if st.button("Validate and import manual result"):
                if not game.strip() or not ticket.strip():
                    st.error("Game and ticket number are required.")
                else:
                    source_upload = uploads[0]
                    suffix = Path(source_upload.name).suffix.lower()
                    prefix = f"{Path(source_upload.name).stem}_"
                    with tempfile.NamedTemporaryFile(
                        prefix=prefix,
                        suffix=suffix,
                        delete=False,
                    ) as temp:
                        temp.write(source_upload.getvalue())
                        source_path = Path(temp.name)
                    inserted = import_candidates(
                        repository,
                        [
                            ImportCandidate(
                                game=game.strip(),
                                draw_date=draw_date,
                                ticket_number=ticket.strip(),
                                source_path=source_path,
                                source_page=int(page),
                                extraction_method=(
                                    "pdf_text" if suffix == ".pdf" else "tesseract"
                                ),
                            )
                        ],
                        minimum_ticket=int(minimum_ticket),
                        maximum_ticket=int(maximum_ticket),
                    )
                    st.success(
                        f"Imported {inserted} record. Validation status is preserved "
                        "in the database."
                    )
                    st.rerun()

    with tabs[2]:
        st.subheader("Experimental candidate ranking")
        minimum = st.number_input(
            "Minimum ticket", min_value=0, value=0, step=1, key="predict_min"
        )
        maximum = st.number_input(
            "Maximum ticket", min_value=1, value=99, step=1, key="predict_max"
        )
        count = st.number_input(
            "Candidates", min_value=1, max_value=100, value=10, step=1
        )
        if st.button("Generate ranking"):
            ranked = rank_candidates(
                records,
                minimum=int(minimum),
                maximum=int(maximum),
                candidates=int(count),
                validated=False,
            )
            st.dataframe(
                [
                    {
                        "Rank": item.rank,
                        "Ticket": item.ticket_number,
                        "Score": item.score,
                        "Confidence": item.confidence,
                        "Statistical": item.statistical_score,
                        "Historical": item.historical_score,
                        "Astronomy": item.astronomy_score,
                        "Model": item.model_score,
                        "Supporting": "; ".join(item.supporting_signals),
                        "Contradicting": "; ".join(item.contradicting_signals),
                        "Explanation": item.explanation,
                    }
                    for item in ranked
                ],
                use_container_width=True,
            )

    with tabs[3]:
        st.subheader("Evaluation")
        st.info(
            "Use `atta-satta backtest` and `atta-satta models` for "
            "leakage-safe historical evaluation."
        )
        st.caption(f"Reference date: {date.today().isoformat()}")


if __name__ == "__main__":
    run()

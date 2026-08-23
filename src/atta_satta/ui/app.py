"""Streamlit dashboard for the Atta Satta MVP."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile


def run() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Install the 'ui' extra to run the dashboard.") from exc

    from atta_satta.config import Settings
    from atta_satta.database.queries import LotteryReader
    from atta_satta.database.sqlite import LotteryRepository
    from atta_satta.ingestion.files import describe_source_file
    from atta_satta.ocr.image import ocr_image
    from atta_satta.extraction.pdf import extract_pdf_text
    from atta_satta.pipeline.importer import ImportCandidate, import_candidates
    from atta_satta.prediction.ranking import rank_candidates
    from atta_satta.statistics.analysis import distribution_summary, frequency_table

    settings = Settings.from_project_root()
    settings.ensure_directories()
    database = settings.data_dir / "atta_satta.sqlite3"
    reader = LotteryReader(database)
    repository = LotteryRepository(database)

    st.set_page_config(page_title="Atta Satta Analytics", layout="wide")
    st.title("Atta Satta — Historical Lottery Analytics")
    st.warning(
        "Experimental analysis only. Lottery outcomes may be random; rankings are not guaranteed predictions."
    )

    records = reader.records(valid_only=True)
    summary = distribution_summary(records)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Validated records", summary.total_records)
    c2.metric("Unique tickets", summary.unique_numbers)
    c3.metric("Minimum", summary.min_number if summary.min_number is not None else "—")
    c4.metric("Maximum", summary.max_number if summary.max_number is not None else "—")

    tabs = st.tabs(["Dashboard", "Import", "Prediction", "Evaluation"])
    with tabs[0]:
        st.subheader("Historical frequency")
        table = frequency_table(records)
        st.dataframe(
            [
                {"Ticket": item.ticket_number, "Count": item.count, "Frequency": round(item.frequency, 4), "Gap": item.gap}
                for item in table[:100]
            ],
            use_container_width=True,
        )

    with tabs[1]:
        st.subheader("Document extraction and review")
        uploads = st.file_uploader(
            "Upload PDF or image files",
            type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "webp"],
            accept_multiple_files=True,
        )
        if uploads:
            for upload in uploads:
                suffix = Path(upload.name).suffix.lower()
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                    temp.write(upload.getvalue())
                    temp_path = Path(temp.name)
                st.write(f"**{upload.name}** — SHA-256: `{describe_source_file(temp_path).sha256}`")
                try:
                    if suffix == ".pdf":
                        pages = list(extract_pdf_text(temp_path))
                        for page in pages:
                            st.text_area(f"Page {page.page_number}", page.text, height=150)
                    else:
                        result = ocr_image(temp_path)
                        st.write(f"OCR confidence: {result.confidence}")
                        st.text_area("OCR text", result.text, height=200)
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))

            st.divider()
            st.subheader("Commit a reviewed result")
            st.caption("Extraction is intentionally review-first. Confirm the ticket value before committing it.")
            game = st.text_input("Lottery / game", value="")
            draw_date = st.date_input("Draw date", value=date.today())
            ticket = st.text_input("Ticket number", value="")
            minimum_ticket = st.number_input("Allowed minimum", min_value=0, value=0, step=1)
            maximum_ticket = st.number_input("Allowed maximum", min_value=1, value=999, step=1)
            page = st.number_input("Source page", min_value=1, value=1, step=1)
            if st.button("Validate and import", type="primary"):
                if not game.strip() or not ticket.strip():
                    st.error("Game and ticket number are required.")
                else:
                    source_upload = uploads[0]
                    suffix = Path(source_upload.name).suffix.lower()
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
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
                                extraction_method="pdf_text" if suffix == ".pdf" else "tesseract",
                            )
                        ],
                        minimum_ticket=int(minimum_ticket),
                        maximum_ticket=int(maximum_ticket),
                    )
                    st.success(f"Imported {inserted} record. Validation status is preserved in the database.")
                    st.rerun()

    with tabs[2]:
        st.subheader("Experimental candidate ranking")
        minimum = st.number_input("Minimum ticket", min_value=0, value=0, step=1, key="predict_min")
        maximum = st.number_input("Maximum ticket", min_value=1, value=99, step=1, key="predict_max")
        count = st.number_input("Candidates", min_value=1, max_value=100, value=10, step=1)
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
        st.info("Use `atta-satta backtest` and `atta-satta models` for leakage-safe historical evaluation.")
        st.caption(f"Reference date: {date.today().isoformat()}")


if __name__ == "__main__":
    run()

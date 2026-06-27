"""Evidence rejection report tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory
from tdf_product_artifact_builder.evidence_rejection import (
    build_evidence_rejection_report,
    validate_evidence_rejection_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
INVALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_invalid"


def test_rejection_report_validates_after_invalid_directory_ingestion(tmp_path) -> None:
    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(INVALID_DIR, out)
    rejection = build_evidence_rejection_report(
        source_directory=report.source_directory,
        rejected_entries=[
            {
                "relative_path": item.relative_path,
                "reason": item.reason,
                "errors": item.errors,
            }
            for item in report.rejected
        ],
    )
    validate_evidence_rejection_report(rejection)
    assert rejection["rejected_count"] == 2
    assert report.accepted_count == 0

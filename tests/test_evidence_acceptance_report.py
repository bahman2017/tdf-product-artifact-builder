"""Evidence acceptance report tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_acceptance import (
    build_evidence_acceptance_report,
    validate_evidence_acceptance_report,
)
from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"


def test_acceptance_report_validates_after_ingestion(tmp_path) -> None:
    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(VALID_DIR, out)
    acceptance = build_evidence_acceptance_report(
        source_directory=report.source_directory,
        accepted_entries=[
            {
                "relative_path": item.relative_path,
                "evidence_id": item.evidence_id,
                "source_tool": item.source_tool,
                "source_version": item.source_version,
                "evidence_type": item.evidence_type,
                "file_sha256": item.file_sha256,
                "payload_sha256": item.payload_sha256,
            }
            for item in report.accepted
        ],
    )
    validate_evidence_acceptance_report(acceptance)
    assert acceptance["accepted_count"] == 2

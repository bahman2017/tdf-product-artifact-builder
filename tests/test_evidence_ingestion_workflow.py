"""Evidence ingestion workflow tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import (
    ACCEPTANCE_REPORT_NAME,
    INGESTION_MANIFEST_NAME,
    REJECTION_REPORT_NAME,
    ingest_evidence_directory,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"
MIXED_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_mixed"
INVALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_invalid"


def test_valid_directory_ingestion_succeeds(tmp_path) -> None:
    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(VALID_DIR, out)
    assert report.accepted_count == 2
    assert report.rejected_count == 0
    for name in (ACCEPTANCE_REPORT_NAME, REJECTION_REPORT_NAME, INGESTION_MANIFEST_NAME):
        assert (out / name).is_file()


def test_mixed_directory_produces_accepted_and_rejected(tmp_path) -> None:
    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(MIXED_DIR, out)
    assert report.accepted_count == 1
    assert report.rejected_count >= 3


def test_invalid_directory_produces_only_rejected(tmp_path) -> None:
    out = tmp_path / "ingestion"
    report = ingest_evidence_directory(INVALID_DIR, out)
    assert report.accepted_count == 0
    assert report.rejected_count == 2

"""Evidence ingestion determinism tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"


def test_ingestion_checksums_are_deterministic(tmp_path) -> None:
    out_a = tmp_path / "ingestion_a"
    out_b = tmp_path / "ingestion_b"
    report_a = ingest_evidence_directory(VALID_DIR, out_a)
    report_b = ingest_evidence_directory(VALID_DIR, out_b)
    checksums_a = sorted((item.relative_path, item.file_sha256) for item in report_a.accepted)
    checksums_b = sorted((item.relative_path, item.file_sha256) for item in report_b.accepted)
    assert checksums_a == checksums_b

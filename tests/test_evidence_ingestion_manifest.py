"""Evidence ingestion manifest tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import (
    INGESTION_MANIFEST_NAME,
    ingest_evidence_directory,
)
from tdf_product_artifact_builder.evidence_ingestion_manifest import validate_evidence_ingestion_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"


def test_ingestion_manifest_validates_after_ingestion(tmp_path) -> None:
    out = tmp_path / "ingestion"
    ingest_evidence_directory(VALID_DIR, out)
    manifest = json.loads((out / INGESTION_MANIFEST_NAME).read_text(encoding="utf-8"))
    validate_evidence_ingestion_manifest(manifest)
    assert manifest["accepted_count"] == 2
    assert manifest["rejected_count"] == 0
    assert len(manifest["checksums"]) == 2

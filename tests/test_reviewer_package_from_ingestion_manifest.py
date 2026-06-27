"""Reviewer package from ingestion manifest tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.evidence_ingestion import ingest_evidence_directory
from tdf_product_artifact_builder.package_writer import REVIEWER_PACKAGE_EVIDENCE_FILES
from tdf_product_artifact_builder.reviewer_package import create_reviewer_package

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "product_specs/lithium_filter_candidate_v0_1/product_spec.yaml"
VALID_DIR = REPO_ROOT / "tests/fixtures/review_safe/evidence_directory_valid"


def test_reviewer_package_from_ingestion_manifest(tmp_path) -> None:
    ingestion_out = tmp_path / "ingestion"
    pkg_out = tmp_path / "pkg"
    ingest_evidence_directory(VALID_DIR, ingestion_out)
    manifest_path = ingestion_out / "EVIDENCE_INGESTION_MANIFEST.json"
    report = create_reviewer_package(
        SPEC,
        pkg_out,
        evidence_ingestion_manifest_path=manifest_path,
    )
    assert report.evidence_included is True
    for name in REVIEWER_PACKAGE_EVIDENCE_FILES:
        assert (pkg_out / name).is_file()
    manifest = json.loads((pkg_out / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["evidence_count"] == 2

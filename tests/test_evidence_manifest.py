"""Evidence manifest tests."""

from pathlib import Path

from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence
from tdf_product_artifact_builder.evidence_manifest import (
    build_evidence_manifest,
    load_evidence_manifest_schema,
    validate_evidence_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"
SCHEMA = REPO_ROOT / "schemas/evidence_manifest.schema.json"


def test_evidence_manifest_schema_loads() -> None:
    schema = load_evidence_manifest_schema(SCHEMA)
    assert schema["properties"]["simulation_authorized"]["const"] is False


def test_build_and_validate_manifest() -> None:
    adapted = validate_and_adapt_evidence(FIXTURE)
    manifest = build_evidence_manifest(
        product_id="lithium_filter_candidate_v0_1",
        evidence_payloads=[adapted],
    )
    validate_evidence_manifest(manifest, SCHEMA)
    assert manifest["evidence_count"] == 1
    assert manifest["diagnostic_flags"]["wet_lab_ready"] is False

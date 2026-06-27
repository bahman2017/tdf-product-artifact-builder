"""Evidence claim boundary tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.tdf_openmm_contract import validate_tdf_openmm_evidence_file

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_fixture_passes_claim_boundaries() -> None:
    report = validate_tdf_openmm_evidence_file(FIXTURE)
    assert report.claim_boundary_passed is True


def test_forbidden_claim_in_summary_fails(tmp_path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["diagnostic_summary"] = "This is a simulation-ready membrane product"
    path = tmp_path / "bad_claim.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = validate_tdf_openmm_evidence_file(path)
    assert report.valid is False

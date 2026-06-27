"""Evidence rejects positive readiness flags."""

import json
from pathlib import Path

from tdf_product_artifact_builder.tdf_openmm_contract import validate_tdf_openmm_evidence_file

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_simulation_executed_true_fails(tmp_path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["simulation_executed"] = True
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    report = validate_tdf_openmm_evidence_file(path)
    assert report.valid is False
    assert not report.safety_flags_passed


def test_lammps_input_executed_true_fails(tmp_path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["lammps_input_executed"] = True
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    report = validate_tdf_openmm_evidence_file(path)
    assert report.valid is False

"""tdf-openmm-validation contract tests."""

import copy
import json
from pathlib import Path

import pytest

from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence
from tdf_product_artifact_builder.tdf_openmm_contract import (
    adapt_tdf_openmm_to_diagnostic_evidence,
    validate_tdf_openmm_evidence_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests/fixtures/review_safe/tdf_openmm_validation_minimal_evidence.json"


def test_validate_and_adapt_fixture() -> None:
    adapted = validate_and_adapt_evidence(FIXTURE)
    assert adapted["source_tool"] == "tdf-openmm-validation"
    assert adapted["diagnostic_flags"]["simulation_executed"] is False


@pytest.mark.parametrize(
    "flag",
    [
        "simulation_executed",
        "lammps_input_executed",
        "accepted_for_simulation",
        "force_field_ready",
        "wet_lab_ready",
    ],
)
def test_positive_readiness_flag_fails(tmp_path, flag: str) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload[flag] = True
    path = tmp_path / "bad_evidence.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = validate_tdf_openmm_evidence_file(path)
    assert report.valid is False


def test_adapted_checksum_is_deterministic() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    a = adapt_tdf_openmm_to_diagnostic_evidence(payload, evidence_path=FIXTURE)
    b = adapt_tdf_openmm_to_diagnostic_evidence(payload, evidence_path=FIXTURE)
    assert a["checksums"] == b["checksums"]

"""Release readiness claim boundary tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.release_readiness import (
    FORBIDDEN_DECISION_PHRASES,
    run_release_readiness_audit,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "5ca67ccf731d059b3dd8eb0bb619fe5ff6974827"


def test_decision_does_not_approve_publish_or_release() -> None:
    report = run_release_readiness_audit(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    decision = report.payload["release_readiness_decision"]
    assert decision in {"READY_FOR_RELEASE_DRAFT", "BLOCKED", "CTO_REVIEW_REQUIRED"}
    assert decision not in {"APPROVED TO PUBLISH", "APPROVED TO RELEASE"}
    serialized = json.dumps(report.payload).upper()
    for phrase in FORBIDDEN_DECISION_PHRASES:
        assert phrase not in serialized


def test_safety_flags_remain_false_in_report() -> None:
    report = run_release_readiness_audit(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    assert report.payload["simulation_executed"] is False
    assert report.payload["openmm_executed"] is False
    assert report.payload["lammps_executed"] is False
    assert report.payload["runtime_tdf_openmm_validation_import"] is False
    assert report.payload["tracked_product_package_generated"] is False
    assert report.payload["readiness_stage_upgraded"] is False

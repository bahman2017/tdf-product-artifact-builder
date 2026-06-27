"""Release authorization no-release-actions tests."""

from pathlib import Path

from tdf_product_artifact_builder.release_authorization import run_release_authorization_review

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "b79987acc43c1d8a767f40892495ac751982f40d"


def test_safety_flags_remain_false_in_authorization_report() -> None:
    report = run_release_authorization_review(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    payload = report.payload
    assert payload["simulation_executed"] is False
    assert payload["openmm_executed"] is False
    assert payload["lammps_executed"] is False
    assert payload["runtime_tdf_openmm_validation_import"] is False
    assert payload["tracked_product_package_generated"] is False
    assert payload["readiness_stage_upgraded"] is False
    assert payload["tag_created"] is False
    assert payload["github_release_created"] is False
    assert payload["package_published"] is False
    assert payload["release_action_taken"] is False

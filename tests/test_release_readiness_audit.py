"""Release readiness audit tests."""

import json
from pathlib import Path

from tdf_product_artifact_builder.release_readiness import (
    run_release_readiness_audit,
    validate_release_readiness_report,
    write_release_readiness_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "5ca67ccf731d059b3dd8eb0bb619fe5ff6974827"


def test_release_readiness_audit_produces_valid_report(tmp_path) -> None:
    out = tmp_path / "readiness"
    report = run_release_readiness_audit(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    validate_release_readiness_report(report.payload, REPO_ROOT)
    written = write_release_readiness_outputs(report, out)
    assert "RELEASE_READINESS_REPORT.json" in written
    payload = json.loads((out / "RELEASE_READINESS_REPORT.json").read_text(encoding="utf-8"))
    assert payload["target_version"] == "0.1.0"
    assert payload["release_action_taken"] is False
    assert payload["release_readiness_decision"] in {
        "READY_FOR_RELEASE_DRAFT",
        "BLOCKED",
        "CTO_REVIEW_REQUIRED",
    }
    for check in payload["checks"].values():
        assert check["status"] in {"PASS", "FAIL", "WARN"}


def test_all_required_checks_present(tmp_path) -> None:
    report = run_release_readiness_audit(
        repo_root=REPO_ROOT,
        target_version="0.1.0",
        base_commit=BASE_COMMIT,
        run_tests=False,
    )
    expected = {
        "package_metadata",
        "version_consistency",
        "required_schemas_present",
        "required_clis_present",
        "required_project_control_docs_present",
        "required_cto_bundle_requirements_present",
        "tests_passed_status",
        "static_policy_status",
        "ascii_policy_status",
        "raw_file_policy_status",
        "secret_file_policy_status",
        "generated_output_policy_status",
        "engine_product_separation_status",
        "reference_product_spec_status",
        "reviewer_package_builder_status",
        "evidence_contract_status",
        "external_evidence_ingestion_status",
        "claim_boundary_status",
        "release_chain_status",
    }
    assert expected == set(report.payload["checks"].keys())

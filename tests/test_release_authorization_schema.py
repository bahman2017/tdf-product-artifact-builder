"""Release authorization report schema tests."""

import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_release_authorization_schema_validates_example_shape() -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas/release_authorization_report.schema.json").read_text(encoding="utf-8")
    )
    example = {
        "report_version": "1.0",
        "target_version": "0.1.0",
        "base_commit": "b79987acc43c1d8a767f40892495ac751982f40d",
        "repository": "https://github.com/bahman2017/tdf-product-artifact-builder",
        "package_version": "0.1.0",
        "release_readiness_decision": "READY_FOR_RELEASE_DRAFT",
        "release_authorization_decision": "CTO_REVIEW_REQUIRED",
        "tag_created": False,
        "github_release_created": False,
        "package_published": False,
        "release_action_taken": False,
        "simulation_executed": False,
        "openmm_executed": False,
        "lammps_executed": False,
        "runtime_tdf_openmm_validation_import": False,
        "tracked_product_package_generated": False,
        "readiness_stage_upgraded": False,
        "checks": {
            key: {"status": "PASS", "detail": "ok"}
            for key in (
                "version_is_0_1_0",
                "tests_pass",
                "static_policy_passes",
                "release_readiness_report_exists",
                "release_readiness_decision_ready",
                "changelog_exists",
                "release_notes_draft_exists",
                "release_candidate_checklist_exists",
                "no_tag_no_publish_statement_exists",
                "project_control_docs_updated",
                "product_spec_registry_current",
                "claim_boundaries_explicit",
                "no_tag_from_this_task",
                "no_github_release_from_this_task",
                "no_package_publish_from_this_task",
                "no_simulation_executed",
                "no_tracked_product_package_generated",
                "no_readiness_stage_upgrade",
            )
        },
        "known_blockers": [],
        "governance_notes": ["CTO review required"],
        "generated_at_commit": "b79987acc43c1d8a767f40892495ac751982f40d",
    }
    jsonschema.validate(instance=example, schema=schema)

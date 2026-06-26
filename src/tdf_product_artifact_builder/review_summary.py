"""Review summary JSON creation and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


def default_review_summary_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "review_summary.schema.json"


def load_review_summary_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_review_summary_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_review_summary(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    """Validate a review summary dict. Raises jsonschema.ValidationError on failure."""
    schema = load_review_summary_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def create_review_summary(
    *,
    task_name: str,
    repository: str,
    branch: str,
    base_commit: str,
    head_commit: str,
    tests_run: str,
    tests_passed: bool,
    ci_status: str,
    generated_outputs_tracked: bool,
    raw_data_committed: bool,
    claim_boundary_passed: bool,
    product_readiness_stage: str,
    completed_work_updated: bool,
    next_actions_updated: bool,
    decision_log_updated: bool,
    prompt_log_updated: bool,
    cursor_feedback_log_updated: bool,
    cto_review_zip_created: bool,
    review_zip_path: str,
    known_risks: list[str],
    blockers: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    """Build a review summary payload dict."""
    return {
        "task_name": task_name,
        "repository": repository,
        "branch": branch,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "tests_run": tests_run,
        "tests_passed": tests_passed,
        "ci_status": ci_status,
        "generated_outputs_tracked": generated_outputs_tracked,
        "raw_data_committed": raw_data_committed,
        "claim_boundary_passed": claim_boundary_passed,
        "product_readiness_stage": product_readiness_stage,
        "completed_work_updated": completed_work_updated,
        "next_actions_updated": next_actions_updated,
        "decision_log_updated": decision_log_updated,
        "prompt_log_updated": prompt_log_updated,
        "cursor_feedback_log_updated": cursor_feedback_log_updated,
        "cto_review_zip_created": cto_review_zip_created,
        "review_zip_path": review_zip_path,
        "known_risks": known_risks,
        "blockers": blockers,
        "next_recommended_step": next_recommended_step,
    }


def write_review_summary(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write and schema-validate a review summary JSON file."""
    validate_review_summary(payload)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out

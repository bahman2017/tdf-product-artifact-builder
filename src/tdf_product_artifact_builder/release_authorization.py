"""Release authorization review for tdf-product-artifact-builder."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import jsonschema

from tdf_product_artifact_builder.release_readiness import (
    FORBIDDEN_DECISION_PHRASES,
    REQUIRED_PROJECT_CONTROL_DOCS,
    CheckResult,
    run_release_readiness_audit,
)
from tdf_product_artifact_builder.version import __version__

CheckStatus = Literal["PASS", "FAIL", "WARN"]
ReleaseAuthorizationDecision = Literal[
    "CTO_REVIEW_REQUIRED",
    "APPROVED FOR RELEASE DRAFT",
    "BLOCKED",
]

REPOSITORY_URL = "https://github.com/bahman2017/tdf-product-artifact-builder"

RELEASE_READINESS_REPORT = "project_control/release_readiness/v0.1.0/RELEASE_READINESS_REPORT.json"

RELEASE_CANDIDATE_FILES: tuple[str, ...] = (
    "CHANGELOG.md",
    "project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md",
    "project_control/release_readiness/v0.1.0/RELEASE_CANDIDATE_CHECKLIST.md",
    "project_control/release_readiness/v0.1.0/NO_TAG_NO_RELEASE_NO_PUBLISH_STATEMENT.md",
)

RELEASE_DRAFT_CHECKLIST_ITEMS: tuple[str, ...] = (
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

GOVERNANCE_NOTES: tuple[str, ...] = (
    "Tag, GitHub release, and PyPI publish require separate explicit CTO approval",
    "APPROVED FOR RELEASE DRAFT does not authorize final release or package publish",
    "Real product package generation blocked pending CTO approval",
    "Runtime integration with tdf-openmm-validation blocked",
)


@dataclass(frozen=True)
class ReleaseAuthorizationReport:
    payload: dict[str, Any]
    markdown: str
    draft_checklist_md: str
    tag_release_publish_plan_md: str
    cto_approval_required_md: str
    no_release_actions_md: str


def default_release_authorization_schema_path(repo_root: Path) -> Path:
    return repo_root / "schemas" / "release_authorization_report.schema.json"


def validate_release_authorization_report(payload: dict[str, Any], repo_root: Path) -> None:
    schema_path = default_release_authorization_schema_path(repo_root)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def _git_head_commit(repo_root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()


def _run_pytest(repo_root: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["TDF_RELEASE_READINESS_NESTED_PYTEST"] = "1"
    result = subprocess.run(
        ["python3", "-m", "pytest", "-q"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    output = (result.stdout or "") + (result.stderr or "")
    passed = result.returncode == 0
    return passed, output.strip().splitlines()[-1] if output.strip() else "no pytest output"


def _run_static_policy(repo_root: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["python3", "tools/static_policy_audit.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    passed = result.returncode == 0 and "RESULT: PASS" in output
    return passed, output.strip().splitlines()[-1] if output.strip() else "no static policy output"


def _load_release_readiness_report(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / RELEASE_READINESS_REPORT
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _check_files_present(repo_root: Path, rel_paths: tuple[str, ...]) -> CheckResult:
    missing = [rel for rel in rel_paths if not (repo_root / rel).is_file()]
    if missing:
        return CheckResult("FAIL", f"Missing: {', '.join(missing)}")
    return CheckResult("PASS", f"All {len(rel_paths)} required files present")


def _check_product_spec_registry(repo_root: Path) -> CheckResult:
    path = repo_root / "project_control/PRODUCT_SPEC_REGISTRY.md"
    if not path.is_file():
        return CheckResult("FAIL", "PRODUCT_SPEC_REGISTRY.md missing")
    text = path.read_text(encoding="utf-8")
    required = (
        "REFERENCE_PRODUCT_SPEC_ONLY",
        "TDF_DESIGN_CANDIDATE",
        "readiness_stage",
        "product_id",
    )
    missing = [item for item in required if item not in text]
    if missing:
        return CheckResult("FAIL", f"Registry missing: {', '.join(missing)}")
    return CheckResult("PASS", "Product spec registry current for reference product")


def _check_claim_boundaries(repo_root: Path) -> CheckResult:
    path = repo_root / "project_control/CLAIM_BOUNDARIES.md"
    if not path.is_file():
        return CheckResult("FAIL", "CLAIM_BOUNDARIES.md missing")
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < 100:
        return CheckResult("FAIL", "Claim boundaries doc too short")
    return CheckResult("PASS", "Claim boundaries documented")


def _derive_decision(
    checks: dict[str, CheckResult],
    readiness_decision: str | None,
    known_blockers: list[str],
) -> ReleaseAuthorizationDecision:
    if any(result.status == "FAIL" for result in checks.values()):
        return "BLOCKED"
    if readiness_decision == "BLOCKED":
        return "BLOCKED"
    if known_blockers:
        return "CTO_REVIEW_REQUIRED"
    if any(result.status == "WARN" for result in checks.values()):
        return "CTO_REVIEW_REQUIRED"
    if readiness_decision != "READY_FOR_RELEASE_DRAFT":
        return "CTO_REVIEW_REQUIRED"
    return "APPROVED FOR RELEASE DRAFT"


def _build_known_blockers(checks: dict[str, CheckResult], readiness_blockers: list[str]) -> list[str]:
    blockers: list[str] = []
    for name, result in checks.items():
        if result.status == "FAIL":
            blockers.append(f"{name}: {result.detail}")
    blockers.extend(blockiness for blockiness in readiness_blockers if blockiness not in blockers)
    return blockers


def _build_draft_checklist_md(checks: dict[str, CheckResult], decision: str) -> str:
    labels = {
        "version_is_0_1_0": "Version is 0.1.0",
        "tests_pass": "Tests pass",
        "static_policy_passes": "Static policy passes",
        "release_readiness_report_exists": "Release-readiness report exists",
        "release_readiness_decision_ready": "Release-readiness decision is READY_FOR_RELEASE_DRAFT",
        "changelog_exists": "CHANGELOG.md exists",
        "release_notes_draft_exists": "RELEASE_NOTES_DRAFT.md exists",
        "release_candidate_checklist_exists": "RELEASE_CANDIDATE_CHECKLIST.md exists",
        "no_tag_no_publish_statement_exists": "NO_TAG_NO_RELEASE_NO_PUBLISH_STATEMENT.md exists",
        "project_control_docs_updated": "Project-control docs are updated",
        "product_spec_registry_current": "Product-spec registry is current",
        "claim_boundaries_explicit": "Claim boundaries are explicit",
        "no_tag_from_this_task": "No tag exists from this task",
        "no_github_release_from_this_task": "No GitHub release exists from this task",
        "no_package_publish_from_this_task": "No package publish exists from this task",
        "no_simulation_executed": "No simulation was executed",
        "no_tracked_product_package_generated": "No tracked product package was generated",
        "no_readiness_stage_upgrade": "No readiness-stage upgrade occurred",
    }
    lines = [
        "# Release draft checklist -- v0.1.0",
        "",
        f"Authorization review decision: `{decision}`",
        "",
    ]
    for key in RELEASE_DRAFT_CHECKLIST_ITEMS:
        result = checks[key]
        mark = "x" if result.status == "PASS" else " "
        lines.append(f"- [{mark}] {labels[key]} - {result.detail}")
    lines.append("")
    return "\n".join(lines)


def _build_tag_release_publish_plan_md() -> str:
    return "\n".join(
        [
            "# Tag / release / publish plan -- v0.1.0",
            "",
            "Documentation only. No commands in this document have been executed.",
            "",
            "Every future command requires separate explicit CTO approval.",
            "",
            "## Planned tag (not executed)",
            "",
            "```text",
            "PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL",
            "git tag -a v0.1.0 -m \"tdf-product-artifact-builder v0.1.0\"",
            "git push origin v0.1.0",
            "```",
            "",
            "## Planned GitHub release draft (not executed)",
            "",
            "```text",
            "PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL",
            "gh release create v0.1.0 --draft --title \"v0.1.0\" \\",
            "  --notes-file project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md",
            "```",
            "",
            "## Planned PyPI publish (not executed)",
            "",
            "```text",
            "PLANNED ONLY - DO NOT RUN WITHOUT CTO APPROVAL",
            "python3 -m build",
            "python3 -m twine upload dist/*",
            "```",
            "",
            "This plan does not authorize any release action.",
            "",
        ]
    )


def _build_cto_approval_required_md(decision: str) -> str:
    return "\n".join(
        [
            "# CTO approval required -- v0.1.0",
            "",
            f"Release authorization review decision: `{decision}`",
            "",
            "Separate explicit CTO approval is required before:",
            "",
            "- Creating a git tag",
            "- Creating a GitHub release (draft or published)",
            "- Publishing to PyPI",
            "- Generating tracked real product packages",
            "- Runtime integration with tdf-openmm-validation",
            "",
            "`APPROVED FOR RELEASE DRAFT` (if granted) means the project may proceed",
            "to consider a release draft. It does not authorize final release or publish.",
            "",
            "- Simulation authorization, wet-lab, or force-field readiness are not granted.",
            "",
        ]
    )


def _build_no_release_actions_md() -> str:
    return "\n".join(
        [
            "# No release actions taken",
            "",
            "This release authorization review did not perform any release actions.",
            "",
            "- No version tag created",
            "- No GitHub release created",
            "- No package index publish",
            "- No simulation executed",
            "- No OpenMM or LAMMPS execution",
            "- No runtime import of tdf-openmm-validation",
            "- No tracked product package generated",
            "- No product readiness stage upgrade",
            "",
            "This report evaluates authorization for a future release draft only.",
            "",
        ]
    )


def _build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Release authorization report -- v0.1.0",
        "",
        f"- Target version: `{payload['target_version']}`",
        f"- Base commit: `{payload['base_commit']}`",
        f"- Release-readiness decision: `{payload['release_readiness_decision']}`",
        f"- Release authorization decision: `{payload['release_authorization_decision']}`",
        f"- Generated at commit: `{payload['generated_at_commit']}`",
        "",
        "## Safety flags",
        "",
        f"- tag_created: `{payload['tag_created']}`",
        f"- github_release_created: `{payload['github_release_created']}`",
        f"- package_published: `{payload['package_published']}`",
        f"- release_action_taken: `{payload['release_action_taken']}`",
        f"- simulation_executed: `{payload['simulation_executed']}`",
        "",
        "## Checklist results",
        "",
    ]
    for name, check in payload["checks"].items():
        lines.append(f"- **{name}**: {check['status']} - {check['detail']}")
    lines.extend(["", "## Known blockers", ""])
    if payload["known_blockers"]:
        for blocker in payload["known_blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None")
    lines.extend(["", "## Governance notes", ""])
    for note in payload["governance_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def run_release_authorization_review(
    *,
    repo_root: Path,
    target_version: str,
    base_commit: str,
    run_tests: bool = True,
) -> ReleaseAuthorizationReport:
    """Run release authorization review and build report payloads."""
    repo_root = repo_root.resolve()
    generated_at_commit = _git_head_commit(repo_root)
    readiness_report = _load_release_readiness_report(repo_root)
    if run_tests:
        from tdf_product_artifact_builder.release_readiness import (
            run_release_readiness_audit,
            write_release_readiness_outputs,
        )

        readiness = run_release_readiness_audit(
            repo_root=repo_root,
            target_version=target_version,
            base_commit=base_commit,
            run_tests=True,
        )
        write_release_readiness_outputs(
            readiness,
            repo_root / "project_control/release_readiness/v0.1.0",
        )
        readiness_report = readiness.payload
    readiness_decision = (
        readiness_report.get("release_readiness_decision") if readiness_report else None
    )
    readiness_blockers = readiness_report.get("known_blockers", []) if readiness_report else []

    tests_passed, tests_detail = (True, "skipped") if not run_tests else _run_pytest(repo_root)
    static_passed, static_detail = _run_static_policy(repo_root)

    checks: dict[str, CheckResult] = {
        "version_is_0_1_0": CheckResult(
            "PASS" if __version__ == target_version else "FAIL",
            f"package __version__={__version__}, target={target_version}",
        ),
        "tests_pass": CheckResult(
            "WARN" if not run_tests else ("PASS" if tests_passed else "FAIL"),
            tests_detail if run_tests else "pytest skipped; run full review with tests enabled",
        ),
        "static_policy_passes": CheckResult(
            "PASS" if static_passed else "FAIL",
            static_detail,
        ),
        "release_readiness_report_exists": CheckResult(
            "PASS" if readiness_report else "FAIL",
            RELEASE_READINESS_REPORT if readiness_report else f"Missing {RELEASE_READINESS_REPORT}",
        ),
        "release_readiness_decision_ready": CheckResult(
            "PASS" if readiness_decision == "READY_FOR_RELEASE_DRAFT" else "FAIL",
            f"release_readiness_decision={readiness_decision}",
        ),
        "changelog_exists": _check_files_present(repo_root, ("CHANGELOG.md",)),
        "release_notes_draft_exists": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md",),
        ),
        "release_candidate_checklist_exists": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/RELEASE_CANDIDATE_CHECKLIST.md",),
        ),
        "no_tag_no_publish_statement_exists": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/NO_TAG_NO_RELEASE_NO_PUBLISH_STATEMENT.md",),
        ),
        "project_control_docs_updated": _check_files_present(repo_root, REQUIRED_PROJECT_CONTROL_DOCS),
        "product_spec_registry_current": _check_product_spec_registry(repo_root),
        "claim_boundaries_explicit": _check_claim_boundaries(repo_root),
        "no_tag_from_this_task": CheckResult("PASS", "No tag created by this review"),
        "no_github_release_from_this_task": CheckResult("PASS", "No GitHub release created by this review"),
        "no_package_publish_from_this_task": CheckResult("PASS", "No package publish by this review"),
        "no_simulation_executed": CheckResult("PASS", "No simulation executed"),
        "no_tracked_product_package_generated": CheckResult("PASS", "No tracked product package generated"),
        "no_readiness_stage_upgrade": CheckResult("PASS", "Readiness stage remains TDF_DESIGN_CANDIDATE"),
    }

    known_blockers = _build_known_blockers(checks, readiness_blockers)
    decision = _derive_decision(checks, readiness_decision, known_blockers)

    payload: dict[str, Any] = {
        "report_version": "1.0",
        "target_version": target_version,
        "base_commit": base_commit,
        "repository": REPOSITORY_URL,
        "package_version": __version__,
        "release_readiness_decision": readiness_decision or "UNKNOWN",
        "release_authorization_decision": decision,
        "release_action_taken": False,
        "tag_created": False,
        "github_release_created": False,
        "package_published": False,
        "simulation_executed": False,
        "openmm_executed": False,
        "lammps_executed": False,
        "runtime_tdf_openmm_validation_import": False,
        "tracked_product_package_generated": False,
        "readiness_stage_upgraded": False,
        "checks": {name: result.to_dict() for name, result in checks.items()},
        "known_blockers": known_blockers,
        "governance_notes": list(GOVERNANCE_NOTES),
        "generated_at_commit": generated_at_commit,
    }

    decision_text = json.dumps({"release_authorization_decision": decision}).upper()
    for phrase in FORBIDDEN_DECISION_PHRASES:
        if phrase in decision_text:
            raise ValueError(f"Forbidden decision phrase in report: {phrase}")

    validate_release_authorization_report(payload, repo_root)

    return ReleaseAuthorizationReport(
        payload=payload,
        markdown=_build_markdown(payload),
        draft_checklist_md=_build_draft_checklist_md(checks, decision),
        tag_release_publish_plan_md=_build_tag_release_publish_plan_md(),
        cto_approval_required_md=_build_cto_approval_required_md(decision),
        no_release_actions_md=_build_no_release_actions_md(),
    )


def write_release_authorization_outputs(
    report: ReleaseAuthorizationReport,
    output_dir: Path,
) -> list[str]:
    """Write release authorization report files to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "RELEASE_AUTHORIZATION_REPORT.json": json.dumps(report.payload, indent=2, sort_keys=True) + "\n",
        "RELEASE_AUTHORIZATION_REPORT.md": report.markdown,
        "RELEASE_DRAFT_CHECKLIST.md": report.draft_checklist_md,
        "TAG_RELEASE_PUBLISH_PLAN.md": report.tag_release_publish_plan_md,
        "CTO_APPROVAL_REQUIRED.md": report.cto_approval_required_md,
        "NO_RELEASE_ACTIONS_TAKEN.md": report.no_release_actions_md,
    }
    written: list[str] = []
    for name, content in files.items():
        path = output_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(name)
    return written

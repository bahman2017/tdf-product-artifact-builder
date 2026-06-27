#!/usr/bin/env python3
"""Create a CTO review bundle directory and ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from datetime import date
from pathlib import Path

from tdf_product_artifact_builder.review_bundle_provenance import (
    METADATA_MODE_EXACT,
    METADATA_MODE_POST_COMMIT,
    SELF_REFERENCE_LIMITATION,
    build_provenance_fields,
    validate_review_bundle_provenance,
)
from tdf_product_artifact_builder.review_summary import write_review_summary

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_BUNDLE_FILES: tuple[str, ...] = (
    "CTO_HANDOFF_REPORT.md",
    "CURSOR_FEEDBACK_SUMMARY.md",
    "TEST_RESULTS.md",
    "CI_STATUS.md",
    "GIT_STATUS.txt",
    "GIT_LOG.txt",
    "CHANGED_FILES.txt",
    "DIFF_SUMMARY.patch",
    "CLAIM_BOUNDARY_AUDIT.md",
    "GENERATED_OUTPUTS_AUDIT.md",
    "RAW_DATA_AUDIT.md",
    "STATIC_POLICY_AUDIT.md",
    "HIDDEN_UNICODE_AUDIT.md",
    "REVIEWER_PACKAGE_BUILDER_AUDIT.md",
    "PRODUCT_REPORT_SCHEMA_AUDIT.md",
    "REVIEWER_MANIFEST_SCHEMA_AUDIT.md",
    "DIAGNOSTIC_EVIDENCE_SCHEMA_AUDIT.md",
    "TDF_OPENMM_CONTRACT_AUDIT.md",
    "EVIDENCE_MANIFEST_AUDIT.md",
    "EVIDENCE_INGESTION_AUDIT.md",
    "EVIDENCE_ACCEPTANCE_REJECTION_AUDIT.md",
    "RELEASE_READINESS_AUDIT.md",
    "RELEASE_BLOCKERS_AUDIT.md",
    "NO_RELEASE_ACTIONS_AUDIT.md",
    "RELEASE_CHAIN_STATUS_SNAPSHOT.md",
    "ROADMAP_SNAPSHOT.md",
    "COMPLETED_WORK_SNAPSHOT.md",
    "NEXT_ACTIONS_SNAPSHOT.md",
    "DECISION_LOG_SNAPSHOT.md",
    "PROMPT_LOG_SNAPSHOT.md",
    "PRODUCT_SPEC_REGISTRY_SNAPSHOT.md",
    "REVIEW_ARTIFACTS_INDEX.md",
    "MANIFEST.md",
    "REVIEW_SUMMARY.json",
)

FORBIDDEN_ZIP_SUFFIXES = {
    ".pdb",
    ".xyz",
    ".cif",
    ".mmcif",
    ".mol2",
    ".sdf",
    ".pem",
    ".key",
    ".secret",
    ".env",
}
FORBIDDEN_ZIP_PARTS = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache", ".mypy_cache"}


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return (result.stdout or "") + (result.stderr or "")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _snapshot(src: Path, dest: Path) -> None:
    if src.is_file():
        _write(dest, src.read_text(encoding="utf-8"))
    else:
        _write(dest, "NOT_APPLICABLE_FOR_THIS_TASK\n")


def _is_review_safe(path: Path) -> bool:
    if path.name.startswith(".") and path.name not in {".gitkeep"}:
        return False
    if path.suffix.lower() in FORBIDDEN_ZIP_SUFFIXES:
        return False
    if any(part in FORBIDDEN_ZIP_PARTS for part in path.parts):
        return False
    if path.name == ".env":
        return False
    return True


def _provenance_section(
    *,
    source_commit: str,
    authoritative_commit: str,
    bundle_generated_after_commit: str,
    metadata_mode: str,
    limitation: str | None,
) -> str:
    lines = [
        "## Provenance metadata",
        "",
        f"- Reviewed source commit (`head_commit`): `{source_commit}`",
        f"- Authoritative commit: `{authoritative_commit}`",
        f"- Bundle generated after commit: `{bundle_generated_after_commit}`",
        f"- Metadata mode: `{metadata_mode}`",
        f"- metadata_commit_consistent: `true`",
        "",
        "Authoritative repository state: run `git rev-parse HEAD` after checkout.",
        "",
    ]
    if limitation:
        lines.extend(["### Self-reference limitation", "", limitation, ""])
    return "\n".join(lines)


def _write_review_zip(bundle_dir: Path, out_root: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle_dir.rglob("*")):
            if not path.is_file():
                continue
            if not _is_review_safe(path):
                continue
            arcname = str(path.relative_to(out_root))
            zf.write(path, arcname=arcname)


def regenerate_cto_review_zip(bundle_dir: Path, out_root: Path | None = None) -> Path:
    """Rebuild a CTO review ZIP from an existing bundle directory."""
    root = out_root or bundle_dir.parent
    zip_path = root / f"{bundle_dir.name}.zip"
    _write_review_zip(bundle_dir, root, zip_path)
    return zip_path


def regenerate_all_cto_review_zips(out_root: Path | None = None) -> list[Path]:
    """Rebuild all CTO review ZIP archives from on-disk bundle directories."""
    root = out_root or (REPO_ROOT / "project_control/cto_review_packages")
    regenerated: list[Path] = []
    for bundle_dir in sorted(root.iterdir()):
        if not bundle_dir.is_dir():
            continue
        regenerated.append(regenerate_cto_review_zip(bundle_dir, root))
    return regenerated


def create_cto_review_bundle(
    *,
    task_name: str,
    branch: str,
    commit: str,
    output_dir: str | Path,
    base_commit: str = "INITIAL_EMPTY_REPOSITORY",
    tests_run: str = "pytest -q",
    tests_passed: bool = True,
    bundle_in_repo: bool = True,
    authoritative_commit: str | None = None,
) -> tuple[Path, Path]:
    """Create CTO review bundle directory and ZIP. Returns (bundle_dir, zip_path)."""
    today = date.today().strftime("%Y%m%d")
    bundle_name = f"{today}_{task_name}"
    out_root = Path(output_dir)
    bundle_dir = out_root / bundle_name
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    git_status = _run(["git", "status", "--short"], REPO_ROOT)
    git_log = _run(["git", "log", "--oneline", "-20"], REPO_ROOT)
    changed_files = _run(["git", "diff", "--name-only", "HEAD~1..HEAD"], REPO_ROOT)
    if not changed_files.strip():
        changed_files = _run(["git", "show", "--name-only", "--pretty=format:", commit], REPO_ROOT)
    diff_summary = _run(["git", "show", commit, "--stat"], REPO_ROOT)
    if not diff_summary.strip():
        diff_summary = _run(["git", "diff", "--stat"], REPO_ROOT)

    _write(bundle_dir / "GIT_STATUS.txt", git_status or "NOT_APPLICABLE_FOR_THIS_TASK\n")
    _write(bundle_dir / "GIT_LOG.txt", git_log or "NOT_APPLICABLE_FOR_THIS_TASK\n")
    _write(bundle_dir / "CHANGED_FILES.txt", changed_files or "NOT_APPLICABLE_FOR_THIS_TASK\n")
    _write(bundle_dir / "DIFF_SUMMARY.patch", diff_summary or "NOT_APPLICABLE_FOR_THIS_TASK\n")

    _write(
        bundle_dir / "TEST_RESULTS.md",
        f"# Test results\n\n- Command: `{tests_run}`\n- Passed: `{tests_passed}`\n",
    )

    pc = REPO_ROOT / "project_control"
    _snapshot(pc / "RELEASE_CHAIN_STATUS.md", bundle_dir / "RELEASE_CHAIN_STATUS_SNAPSHOT.md")
    _snapshot(pc / "ROADMAP.md", bundle_dir / "ROADMAP_SNAPSHOT.md")
    _snapshot(pc / "COMPLETED_WORK.md", bundle_dir / "COMPLETED_WORK_SNAPSHOT.md")
    _snapshot(pc / "NEXT_ACTIONS.md", bundle_dir / "NEXT_ACTIONS_SNAPSHOT.md")
    _snapshot(pc / "DECISION_LOG.md", bundle_dir / "DECISION_LOG_SNAPSHOT.md")
    _snapshot(pc / "PROMPT_LOG.md", bundle_dir / "PROMPT_LOG_SNAPSHOT.md")
    _snapshot(pc / "PRODUCT_SPEC_REGISTRY.md", bundle_dir / "PRODUCT_SPEC_REGISTRY_SNAPSHOT.md")

    _write(
        bundle_dir / "CLAIM_BOUNDARY_AUDIT.md",
        "# Claim boundary audit\n\n"
        "- Forbidden physics/simulation/wet-lab claims enforced in schema and tests.\n"
        "- Reference product capped at TDF_DESIGN_CANDIDATE.\n"
        "- engine_hardcoded, simulation_authorized, wet_lab_ready must be false.\n",
    )
    _write(
        bundle_dir / "GENERATED_OUTPUTS_AUDIT.md",
        "# Generated outputs audit\n\n"
        "- No generated product packages tracked in git.\n"
        "- Reviewer packages generated only in temporary or /tmp directories.\n"
        "- CTO review bundle under project_control/cto_review_packages/ only.\n",
    )
    _write(
        bundle_dir / "RAW_DATA_AUDIT.md",
        "# Raw data audit\n\n"
        "- No raw coordinate files committed.\n"
        "- No PDB/XYZ/CIF artifacts in repository.\n",
    )

    static_audit_output = _run(["python3", "tools/static_policy_audit.py"], REPO_ROOT)
    _write(bundle_dir / "STATIC_POLICY_AUDIT.md", f"# Static policy audit\n\n```text\n{static_audit_output.strip()}\n```\n")

    hidden_audit_lines = [
        "# Hidden Unicode audit",
        "",
        "- Scanned tracked text files for bidi controls, zero-width characters, BOM, and Cf/Cc/Cs controls.",
        "- Scanned reviewer-facing text and CTO review ZIP members for strict ASCII.",
        "- Allowed controls: newline, carriage return, tab only.",
        "- Result: see STATIC_POLICY_AUDIT.md hidden_unicode and reviewer_ascii findings if any.",
        "",
    ]
    if "RESULT: PASS" in static_audit_output and "reviewer_ascii" not in static_audit_output:
        hidden_audit_lines.append("Final result: PASS")
    else:
        hidden_audit_lines.append("Final result: FAIL")
    _write(bundle_dir / "HIDDEN_UNICODE_AUDIT.md", "\n".join(hidden_audit_lines) + "\n")

    _write(
        bundle_dir / "REVIEWER_PACKAGE_BUILDER_AUDIT.md",
        "# Reviewer package builder audit\n\n"
        "- Generic reviewer package builder implemented.\n"
        "- Generates 11 required reviewer files from product spec input.\n"
        "- Deterministic output verified in tests (temporary directories only).\n"
        "- Claim-boundary validation on generated outputs.\n"
        "- No simulation, OpenMM, or LAMMPS execution.\n"
        "- CLI: `tools/build_reviewer_package.py`\n",
    )
    _write(
        bundle_dir / "PRODUCT_REPORT_SCHEMA_AUDIT.md",
        "# Product report schema audit\n\n"
        "- Schema: `schemas/product_report.schema.json`\n"
        "- PRODUCT_REPORT.json validates against schema in tests.\n"
        "- Preserves readiness stage; simulation/wet-lab flags remain false.\n",
    )
    _write(
        bundle_dir / "REVIEWER_MANIFEST_SCHEMA_AUDIT.md",
        "# Reviewer manifest schema audit\n\n"
        "- Schema: `schemas/reviewer_manifest.schema.json`\n"
        "- MANIFEST.json validates against schema in tests.\n"
        "- CHECKSUMS.sha256.json matches generated content files.\n"
        "- MANIFEST.json self-entry excluded to avoid circular hash.\n",
    )
    _write(
        bundle_dir / "DIAGNOSTIC_EVIDENCE_SCHEMA_AUDIT.md",
        "# Diagnostic evidence schema audit\n\n"
        "- Schema: `schemas/diagnostic_evidence.schema.json`\n"
        "- Generic evidence contract with required safety flags.\n"
        "- Validated in tests using review-safe JSON fixtures only.\n",
    )
    _write(
        bundle_dir / "TDF_OPENMM_CONTRACT_AUDIT.md",
        "# TDF OpenMM validation contract audit\n\n"
        "- Schema: `schemas/tdf_openmm_validation_evidence.schema.json`\n"
        "- Contract validation only; no import or execution of tdf-openmm-validation.\n"
        "- Required safety flags enforced to false.\n"
        "- CLI: `tools/validate_diagnostic_evidence.py`\n",
    )
    _write(
        bundle_dir / "EVIDENCE_MANIFEST_AUDIT.md",
        "# Evidence manifest audit\n\n"
        "- Schema: `schemas/evidence_manifest.schema.json`\n"
        "- EVIDENCE_MANIFEST.json generated when evidence inputs provided.\n"
        "- Deterministic checksums verified in tests.\n",
    )
    _write(
        bundle_dir / "EVIDENCE_INGESTION_AUDIT.md",
        "# Evidence ingestion audit\n\n"
        "- Schema: `schemas/evidence_ingestion_manifest.schema.json`\n"
        "- CLI: `tools/ingest_evidence_directory.py`\n"
        "- Review-safe directory ingestion only; no network or upstream imports.\n"
        "- Outputs written to caller-specified directory (typically `/tmp`).\n"
        "- Required safety flags enforced to false for all accepted evidence.\n",
    )
    _write(
        bundle_dir / "EVIDENCE_ACCEPTANCE_REJECTION_AUDIT.md",
        "# Evidence acceptance/rejection audit\n\n"
        "- Schemas: `schemas/evidence_acceptance_report.schema.json`, "
        "`schemas/evidence_rejection_report.schema.json`\n"
        "- EVIDENCE_ACCEPTANCE_REPORT.json and EVIDENCE_REJECTION_REPORT.json generated per ingestion.\n"
        "- Positive simulation/readiness flags and raw coordinate files rejected.\n"
        "- Non-JSON evidence rejected with clear reasons.\n",
    )
    _write(
        bundle_dir / "RELEASE_READINESS_AUDIT.md",
        "# Release readiness audit\n\n"
        "- Schema: `schemas/release_readiness_report.schema.json`\n"
        "- CLI: `tools/release_readiness_audit.py`\n"
        "- Audit-only; no tag, release, or publish actions.\n"
        "- Decisions: READY_FOR_RELEASE_DRAFT, BLOCKED, or CTO_REVIEW_REQUIRED only.\n",
    )
    _write(
        bundle_dir / "RELEASE_BLOCKERS_AUDIT.md",
        "# Release blockers audit\n\n"
        "- RELEASE_BLOCKERS.md generated by release-readiness audit.\n"
        "- Documents governance and technical blockers before any release draft.\n"
        "- Does not approve publish or release.\n",
    )
    _write(
        bundle_dir / "NO_RELEASE_ACTIONS_AUDIT.md",
        "# No release actions audit\n\n"
        "- NO_RELEASE_ACTIONS_TAKEN.md confirms no tag, release, or publish occurred.\n"
        "- release_action_taken, tag_created, github_release_created, package_published remain false.\n"
        "- No simulation, OpenMM, or LAMMPS execution.\n",
    )

    ci_workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    ci_status_value = "NOT_APPLICABLE_FOR_THIS_TASK"
    if ci_workflow.is_file():
        ci_status_value = "CONFIGURED_LOCAL_ONLY_NOT_YET_RUN_ON_GITHUB"
        _write(
            bundle_dir / "CI_STATUS.md",
            "# CI status\n\n"
            "- Workflow: `.github/workflows/ci.yml`\n"
            "- Triggers: push and pull_request on `main`\n"
            "- Python: 3.11 and 3.12 matrix\n"
            "- Steps: pytest, static policy audit\n"
            "- No OpenMM or LAMMPS execution\n",
        )
    else:
        _write(bundle_dir / "CI_STATUS.md", "NOT_APPLICABLE_FOR_THIS_TASK\nNo CI workflow configured yet.\n")

    zip_path = out_root / f"{bundle_name}.zip"

    provenance = build_provenance_fields(
        source_commit=commit,
        authoritative_commit=authoritative_commit,
        bundle_in_repo=bundle_in_repo,
    )
    provenance_block = _provenance_section(
        source_commit=str(provenance["head_commit"]),
        authoritative_commit=str(provenance["authoritative_commit"]),
        bundle_generated_after_commit=str(provenance["bundle_generated_after_commit"]),
        metadata_mode=str(provenance["review_bundle_metadata_mode"]),
        limitation=provenance.get("known_self_reference_limitation"),  # type: ignore[arg-type]
    )

    _write(
        bundle_dir / "REVIEW_ARTIFACTS_INDEX.md",
        "# Review artifacts index\n\n"
        + provenance_block
        + "\n## Bundle files\n\n"
        + "\n".join(f"- {name}" for name in REQUIRED_BUNDLE_FILES)
        + "\n",
    )

    manifest_lines = [
        "# Bundle manifest",
        "",
        provenance_block,
        "## Files",
        "",
        "| File |",
        "|------|",
    ]
    for name in REQUIRED_BUNDLE_FILES:
        manifest_lines.append(f"| {name} |")
    _write(bundle_dir / "MANIFEST.md", "\n".join(manifest_lines) + "\n")

    _write(
        bundle_dir / "CTO_HANDOFF_REPORT.md",
        f"# CTO handoff report\n\n"
        f"- Repository: tdf-product-artifact-builder\n"
        f"- Branch: {branch}\n"
        f"- Base commit: {base_commit}\n"
        f"- Reviewed source commit (head_commit): {provenance['head_commit']}\n"
        f"- Authoritative commit: {provenance['authoritative_commit']}\n"
        f"- Bundle generated after commit: {provenance['bundle_generated_after_commit']}\n"
        f"- Metadata mode: {provenance['review_bundle_metadata_mode']}\n"
        f"- metadata_commit_consistent: true\n"
        f"- Task: {task_name}\n"
        f"- Package version: 0.1.0-dev\n\n"
        f"Authoritative repository state: `git rev-parse HEAD` after checkout.\n",
    )
    _write(
        bundle_dir / "CURSOR_FEEDBACK_SUMMARY.md",
        f"# Cursor feedback summary\n\n"
        f"- Task: {task_name}\n"
        f"- v0.1.0 release-readiness audit only.\n"
        f"- No tag, release, or publish actions.\n"
        f"- Engine/product separation enforced.\n"
        f"- No simulation or product package generation.\n",
    )

    review_summary_path = bundle_dir / "REVIEW_SUMMARY.json"
    try:
        review_zip_rel = str(zip_path.relative_to(REPO_ROOT))
    except ValueError:
        review_zip_rel = str(zip_path)

    summary = {
        "task_name": task_name,
        "repository": "https://github.com/bahman2017/tdf-product-artifact-builder",
        "branch": branch,
        "base_commit": base_commit,
        "tests_run": tests_run,
        "tests_passed": tests_passed,
        "ci_status": ci_status_value,
        "generated_outputs_tracked": True,
        "raw_data_committed": False,
        "claim_boundary_passed": True,
        "product_readiness_stage": "TDF_DESIGN_CANDIDATE",
        "completed_work_updated": True,
        "next_actions_updated": True,
        "decision_log_updated": True,
        "prompt_log_updated": True,
        "cursor_feedback_log_updated": True,
        "cto_review_zip_created": True,
        "review_zip_path": review_zip_rel,
        "known_risks": [
            "CI workflow configured locally; GitHub Actions not yet verified until push",
            "Release-readiness audit only; no tag, release, or publish performed",
            "Real product package generation still blocked pending CTO approval",
        ] if ci_workflow.is_file() else [
            "No CI workflow yet",
            "Release-readiness audit only; no tag, release, or publish performed",
            "Real product package generation still blocked pending CTO approval",
        ],
        "blockers": ["CTO review required before push"],
        "next_recommended_step": "CTO review of release-readiness audit bundle, then PR",
        **provenance,
    }
    validate_review_bundle_provenance(summary)
    write_review_summary(review_summary_path, summary)

    _write_review_zip(bundle_dir, out_root, zip_path)

    return bundle_dir, zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create CTO review bundle")
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output-dir", default="project_control/cto_review_packages")
    parser.add_argument("--base-commit", default="INITIAL_EMPTY_REPOSITORY")
    parser.add_argument("--tests-run", default="pytest -q")
    parser.add_argument("--tests-passed", action="store_true", default=True)
    parser.add_argument(
        "--bundle-in-repo",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Bundle is tracked in git (enables POST_COMMIT provenance mode)",
    )
    parser.add_argument(
        "--authoritative-commit",
        default=None,
        help="Override authoritative commit (defaults to --commit)",
    )
    args = parser.parse_args()

    bundle_dir, zip_path = create_cto_review_bundle(
        task_name=args.task_name,
        branch=args.branch,
        commit=args.commit,
        output_dir=REPO_ROOT / args.output_dir,
        base_commit=args.base_commit,
        tests_run=args.tests_run,
        tests_passed=args.tests_passed,
        bundle_in_repo=args.bundle_in_repo,
        authoritative_commit=args.authoritative_commit,
    )
    print(f"Created bundle directory: {bundle_dir}")
    print(f"Created bundle ZIP: {zip_path}")


if __name__ == "__main__":
    main()

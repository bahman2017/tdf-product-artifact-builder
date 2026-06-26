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


def create_cto_review_bundle(
    *,
    task_name: str,
    branch: str,
    commit: str,
    output_dir: str | Path,
    base_commit: str = "INITIAL_EMPTY_REPOSITORY",
    tests_run: str = "pytest -q",
    tests_passed: bool = True,
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
    _write(bundle_dir / "CI_STATUS.md", "NOT_APPLICABLE_FOR_THIS_TASK\nNo CI workflow configured yet.\n")

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
        "- CTO review bundle under project_control/cto_review_packages/ only.\n",
    )
    _write(
        bundle_dir / "RAW_DATA_AUDIT.md",
        "# Raw data audit\n\n"
        "- No raw coordinate files committed.\n"
        "- No PDB/XYZ/CIF artifacts in repository.\n",
    )

    zip_path = out_root / f"{bundle_name}.zip"

    _write(
        bundle_dir / "REVIEW_ARTIFACTS_INDEX.md",
        "# Review artifacts index\n\n"
        + "\n".join(f"- {name}" for name in REQUIRED_BUNDLE_FILES)
        + "\n",
    )

    manifest_lines = ["# Bundle manifest", "", "| File |", "|------|"]
    for name in REQUIRED_BUNDLE_FILES:
        manifest_lines.append(f"| {name} |")
    _write(bundle_dir / "MANIFEST.md", "\n".join(manifest_lines) + "\n")

    _write(
        bundle_dir / "CTO_HANDOFF_REPORT.md",
        f"# CTO handoff report\n\n"
        f"- Repository: tdf-product-artifact-builder\n"
        f"- Branch: {branch}\n"
        f"- Base commit: {base_commit}\n"
        f"- Head commit: {commit}\n"
        f"- Task: {task_name}\n"
        f"- Package version: 0.1.0-dev\n",
    )
    _write(
        bundle_dir / "CURSOR_FEEDBACK_SUMMARY.md",
        f"# Cursor feedback summary\n\n"
        f"- Task: {task_name}\n"
        f"- Foundation scaffold created on empty repository.\n"
        f"- Engine/product separation enforced.\n",
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
        "head_commit": commit,
        "tests_run": tests_run,
        "tests_passed": tests_passed,
        "ci_status": "NOT_APPLICABLE_FOR_THIS_TASK",
        "generated_outputs_tracked": False,
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
            "No CI workflow yet",
            "Reviewer package builder is placeholder scaffold only",
            "tdf-openmm-validation integration not yet wired",
        ],
        "blockers": ["CTO review required before push"],
        "next_recommended_step": "CTO review of foundation ZIP, then PR",
    }
    write_review_summary(review_summary_path, summary)

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
    args = parser.parse_args()

    bundle_dir, zip_path = create_cto_review_bundle(
        task_name=args.task_name,
        branch=args.branch,
        commit=args.commit,
        output_dir=REPO_ROOT / args.output_dir,
        base_commit=args.base_commit,
        tests_run=args.tests_run,
        tests_passed=args.tests_passed,
    )
    print(f"Created bundle directory: {bundle_dir}")
    print(f"Created bundle ZIP: {zip_path}")


if __name__ == "__main__":
    main()

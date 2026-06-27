"""Release-readiness audit for tdf-product-artifact-builder."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import jsonschema
import yaml

from tdf_product_artifact_builder.version import __version__

CheckStatus = Literal["PASS", "FAIL", "WARN"]
ReleaseDecision = Literal["READY_FOR_RELEASE_DRAFT", "BLOCKED", "CTO_REVIEW_REQUIRED"]

REPOSITORY_URL = "https://github.com/bahman2017/tdf-product-artifact-builder"

REQUIRED_SCHEMAS: tuple[str, ...] = (
    "schemas/product_spec.schema.json",
    "schemas/review_summary.schema.json",
    "schemas/product_report.schema.json",
    "schemas/reviewer_manifest.schema.json",
    "schemas/diagnostic_evidence.schema.json",
    "schemas/tdf_openmm_validation_evidence.schema.json",
    "schemas/evidence_manifest.schema.json",
    "schemas/evidence_ingestion_manifest.schema.json",
    "schemas/evidence_acceptance_report.schema.json",
    "schemas/evidence_rejection_report.schema.json",
    "schemas/release_readiness_report.schema.json",
    "schemas/release_authorization_report.schema.json",
)

REQUIRED_CLIS: tuple[str, ...] = (
    "tools/static_policy_audit.py",
    "tools/build_reviewer_package.py",
    "tools/validate_diagnostic_evidence.py",
    "tools/ingest_evidence_directory.py",
    "tools/create_cto_review_bundle.py",
    "tools/release_readiness_audit.py",
    "tools/release_authorization_review.py",
)

REQUIRED_PROJECT_CONTROL_DOCS: tuple[str, ...] = (
    "project_control/COMPLETED_WORK.md",
    "project_control/NEXT_ACTIONS.md",
    "project_control/ROADMAP.md",
    "project_control/DECISION_LOG.md",
    "project_control/PROMPT_LOG.md",
    "project_control/CURSOR_FEEDBACK_LOG.md",
    "project_control/RELEASE_CHAIN_STATUS.md",
    "project_control/PRODUCT_SPEC_REGISTRY.md",
    "project_control/PROJECT_CHARTER.md",
    "project_control/CLAIM_BOUNDARIES.md",
    "project_control/ENGINE_PRODUCT_SEPARATION.md",
    "project_control/REVIEW_BUNDLE_REQUIREMENTS.md",
)

REQUIRED_CTO_BUNDLE_FILES: tuple[str, ...] = (
    "CTO_HANDOFF_REPORT.md",
    "REVIEW_SUMMARY.json",
    "STATIC_POLICY_AUDIT.md",
    "CLAIM_BOUNDARY_AUDIT.md",
    "RELEASE_CHAIN_STATUS_SNAPSHOT.md",
)

REFERENCE_PRODUCT_SPEC_REGISTRY = "project_control/PRODUCT_SPEC_REGISTRY.md"


def _reference_product_spec_path(repo_root: Path) -> Path:
    registry_path = repo_root / REFERENCE_PRODUCT_SPEC_REGISTRY
    if not registry_path.is_file():
        raise ValueError(f"Missing product spec registry: {REFERENCE_PRODUCT_SPEC_REGISTRY}")
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Path:"):
            rel = line.split(":", 1)[1].strip().strip("`")
            return repo_root / rel
    raise ValueError("Reference product spec path not found in PRODUCT_SPEC_REGISTRY.md")

REQUIRED_RELEASE_CANDIDATE_FILES: tuple[str, ...] = (
    "CHANGELOG.md",
    "project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md",
    "project_control/release_readiness/v0.1.0/RELEASE_CANDIDATE_CHECKLIST.md",
    "project_control/release_readiness/v0.1.0/NO_TAG_NO_RELEASE_NO_PUBLISH_STATEMENT.md",
)

GOVERNANCE_NOTES: tuple[str, ...] = (
    "CTO review required before tag, GitHub release, or package publish",
    "Real product package generation blocked pending CTO approval",
    "Runtime integration with tdf-openmm-validation blocked",
)

FORBIDDEN_DECISION_PHRASES = (
    "APPROVED TO PUBLISH",
    "APPROVED TO RELEASE",
)


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class ReleaseReadinessReport:
    payload: dict[str, Any]
    markdown: str
    blockers_md: str
    no_release_actions_md: str


def default_release_readiness_schema_path(repo_root: Path) -> Path:
    return repo_root / "schemas" / "release_readiness_report.schema.json"


def load_release_readiness_schema(repo_root: Path) -> dict[str, Any]:
    return json.loads(default_release_readiness_schema_path(repo_root).read_text(encoding="utf-8"))


def validate_release_readiness_report(payload: dict[str, Any], repo_root: Path) -> None:
    schema = load_release_readiness_schema(repo_root)
    jsonschema.validate(instance=payload, schema=schema)


def _read_pyproject_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise ValueError("Could not parse version from pyproject.toml")
    return match.group(1)


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
    return passed, "PASS" if passed else output.strip()[:500]


def _check_files_present(repo_root: Path, rel_paths: tuple[str, ...]) -> CheckResult:
    missing = [rel for rel in rel_paths if not (repo_root / rel).is_file()]
    if missing:
        return CheckResult("FAIL", f"Missing: {', '.join(missing)}")
    return CheckResult("PASS", f"All {len(rel_paths)} required files present")


def _check_package_metadata(repo_root: Path) -> CheckResult:
    pyproject = repo_root / "pyproject.toml"
    readme = repo_root / "README.md"
    if not pyproject.is_file() or not readme.is_file():
        return CheckResult("FAIL", "Missing pyproject.toml or README.md")
    text = pyproject.read_text(encoding="utf-8")
    required = ('name = "tdf-product-artifact-builder"', "requires-python", "jsonschema")
    missing = [item for item in required if item not in text]
    if missing:
        return CheckResult("FAIL", f"pyproject.toml missing: {', '.join(missing)}")
    return CheckResult("PASS", "Package metadata present in pyproject.toml and README.md")


def _check_version_consistency(repo_root: Path, target_version: str) -> CheckResult:
    pyproject_version = _read_pyproject_version(repo_root)
    package_version = __version__
    target_base = target_version
    pkg_base = package_version.removesuffix("-dev")
    proj_base = pyproject_version.removesuffix(".dev0")
    if pkg_base == target_base and proj_base == target_base:
        return CheckResult(
            "PASS",
            f"Versions aligned with target {target_base}: __version__={package_version}, pyproject={pyproject_version}",
        )
    return CheckResult(
        "FAIL",
        f"Version mismatch: target={target_base}, __version__={package_version}, pyproject={pyproject_version}",
    )


def _static_policy_module(repo_root: Path):
    import importlib.util
    import sys

    name = "tdf_static_policy_audit"
    path = repo_root / "tools/static_policy_audit.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load static_policy_audit module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _check_ascii_policy(repo_root: Path) -> CheckResult:
    module = _static_policy_module(repo_root)
    report = module.audit_tracked_files(repo_root)
    ascii_findings = [f for f in report.findings if f.check == "reviewer_ascii"]
    if ascii_findings:
        return CheckResult("FAIL", f"{len(ascii_findings)} non-ASCII reviewer-facing findings")
    return CheckResult("PASS", "Reviewer-facing tracked text is ASCII-only")


def _check_raw_file_policy(repo_root: Path) -> CheckResult:
    module = _static_policy_module(repo_root)
    hits: list[str] = []
    for path in module.tracked_files(repo_root):
        rel = str(path.relative_to(repo_root))
        if path.suffix.lower() in module.RAW_COORDINATE_SUFFIXES:
            hits.append(rel)
    if hits:
        return CheckResult("FAIL", f"Raw coordinate files tracked: {', '.join(hits)}")
    return CheckResult("PASS", "No raw coordinate files tracked")


def _check_secret_file_policy(repo_root: Path) -> CheckResult:
    module = _static_policy_module(repo_root)
    hits: list[str] = []
    for path in module.tracked_files(repo_root):
        rel = str(path.relative_to(repo_root)).lower()
        name = path.name.lower()
        if any(marker in rel.split("/") for marker in (".env", ".venv", "venv", "__pycache__", ".pytest_cache")):
            hits.append(rel)
        if ("secret" in name or "token" in name) and not rel.startswith("tests/"):
            hits.append(rel)
    if hits:
        return CheckResult("FAIL", f"Forbidden secret/cache paths: {', '.join(hits[:5])}")
    return CheckResult("PASS", "No secrets, tokens, or cache paths tracked")


def _check_generated_output_policy(repo_root: Path) -> CheckResult:
    module = _static_policy_module(repo_root)
    hits: list[str] = []
    for path in module.tracked_files(repo_root):
        rel = str(path.relative_to(repo_root))
        if path.name in module.TRACKED_EVIDENCE_OUTPUT_NAMES and not rel.startswith("tests/fixtures/review_safe/"):
            hits.append(rel)
        if "/tmp/" in rel:
            hits.append(rel)
    if hits:
        return CheckResult("FAIL", f"Tracked generated outputs: {', '.join(hits)}")
    return CheckResult("PASS", "No untracked-policy generated outputs committed")


def _check_engine_product_separation(repo_root: Path) -> CheckResult:
    module = _static_policy_module(repo_root)
    engine_dir = repo_root / module.ENGINE_DIR_REL
    hits: list[str] = []
    for py_path in engine_dir.glob("*.py"):
        if py_path.name in module.ENGINE_TERM_ALLOWLIST_FILES or py_path.name == "release_readiness.py":
            continue
        text = py_path.read_text(encoding="utf-8").lower()
        for term in module.ENGINE_FORBIDDEN_TERMS:
            if term in text:
                hits.append(f"{py_path.name}:{term}")
    if hits:
        return CheckResult("FAIL", f"Engine/product coupling: {', '.join(hits[:5])}")
    return CheckResult("PASS", "Engine/product separation enforced in src/")


def _check_reference_product_spec(repo_root: Path) -> CheckResult:
    spec_path = _reference_product_spec_path(repo_root)
    if not spec_path.is_file():
        return CheckResult("FAIL", f"Missing reference product spec: {spec_path.relative_to(repo_root)}")
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    required = {
        "readiness_stage": "TDF_DESIGN_CANDIDATE",
        "simulation_authorized": False,
        "wet_lab_ready": False,
        "engine_hardcoded": False,
    }
    errors: list[str] = []
    for key, expected in required.items():
        if spec.get(key) != expected:
            errors.append(f"{key}={spec.get(key)!r} expected {expected!r}")
    if errors:
        return CheckResult("FAIL", "; ".join(errors))
    return CheckResult("PASS", "Reference product spec remains TDF_DESIGN_CANDIDATE with safety flags false")


def _check_reviewer_package_builder(repo_root: Path) -> CheckResult:
    cli = repo_root / "tools/build_reviewer_package.py"
    module = repo_root / "src/tdf_product_artifact_builder/reviewer_package.py"
    if not cli.is_file() or not module.is_file():
        return CheckResult("FAIL", "Reviewer package builder CLI or module missing")
    return CheckResult("PASS", "Reviewer package builder CLI and module present")


def _check_evidence_contract(repo_root: Path) -> CheckResult:
    required = (
        "src/tdf_product_artifact_builder/evidence_adapter.py",
        "src/tdf_product_artifact_builder/diagnostic_evidence.py",
        "tools/validate_diagnostic_evidence.py",
    )
    missing = [rel for rel in required if not (repo_root / rel).is_file()]
    if missing:
        return CheckResult("FAIL", f"Missing evidence contract files: {', '.join(missing)}")
    return CheckResult("PASS", "Evidence contract modules and validation CLI present")


def _check_external_evidence_ingestion(repo_root: Path) -> CheckResult:
    required = (
        "src/tdf_product_artifact_builder/evidence_ingestion.py",
        "tools/ingest_evidence_directory.py",
        "schemas/evidence_ingestion_manifest.schema.json",
    )
    missing = [rel for rel in required if not (repo_root / rel).is_file()]
    if missing:
        return CheckResult("FAIL", f"Missing ingestion files: {', '.join(missing)}")
    return CheckResult("PASS", "External evidence ingestion workflow present")


def _check_claim_boundary(repo_root: Path) -> CheckResult:
    from tdf_product_artifact_builder.claim_boundaries import validate_claim_boundaries

    spec_path = _reference_product_spec_path(repo_root)
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    report = validate_claim_boundaries(
        allowed_claims=list(spec.get("allowed_claims", [])),
        forbidden_claims=list(spec.get("forbidden_claims", [])),
    )
    if not report.passed:
        return CheckResult("FAIL", f"Claim boundary validation failed: {report.forbidden_hits}")
    return CheckResult("PASS", "Claim boundaries valid for reference product spec")


def _check_release_chain_status(repo_root: Path) -> CheckResult:
    path = repo_root / "project_control/RELEASE_CHAIN_STATUS.md"
    if not path.is_file():
        return CheckResult("FAIL", "RELEASE_CHAIN_STATUS.md missing")
    text = path.read_text(encoding="utf-8").lower()
    if "no tag" not in text and "no release" not in text:
        return CheckResult("WARN", "RELEASE_CHAIN_STATUS.md may not document no tag/release")
    if "tdf-product-artifact-builder" not in text:
        return CheckResult("FAIL", "RELEASE_CHAIN_STATUS.md missing package entry")
    return CheckResult("PASS", "Release chain status documents current package state")


def _check_cto_bundle_requirements(repo_root: Path) -> CheckResult:
    bundle_tool = repo_root / "tools/create_cto_review_bundle.py"
    if not bundle_tool.is_file():
        return CheckResult("FAIL", "create_cto_review_bundle.py missing")
    text = bundle_tool.read_text(encoding="utf-8")
    missing = [name for name in REQUIRED_CTO_BUNDLE_FILES if name not in text]
    req_doc = repo_root / "project_control/REVIEW_BUNDLE_REQUIREMENTS.md"
    if not req_doc.is_file():
        missing.append("project_control/REVIEW_BUNDLE_REQUIREMENTS.md")
    if missing:
        return CheckResult("FAIL", f"Missing CTO bundle requirements: {', '.join(missing)}")
    return CheckResult("PASS", "CTO review bundle requirements documented and referenced")


def _check_no_tag_exists(repo_root: Path, target_version: str) -> CheckResult:
    tags = subprocess.check_output(["git", "tag", "-l"], cwd=repo_root, text=True).splitlines()
    release_tags = {target_version, f"v{target_version}"}
    hits = [tag for tag in tags if tag in release_tags]
    if hits:
        return CheckResult("FAIL", f"Release tag already exists: {', '.join(hits)}")
    return CheckResult("PASS", "No local release tag exists")


def _derive_decision(
    checks: dict[str, CheckResult],
    known_blockers: list[str],
) -> ReleaseDecision:
    if any(result.status == "FAIL" for result in checks.values()):
        return "BLOCKED"
    if any(result.status == "WARN" for result in checks.values()) or known_blockers:
        return "CTO_REVIEW_REQUIRED"
    return "READY_FOR_RELEASE_DRAFT"


def _build_known_blockers(
    checks: dict[str, CheckResult],
    *,
    package_version: str,
    target_version: str,
) -> list[str]:
    blockers: list[str] = []
    for name, result in checks.items():
        if result.status == "FAIL":
            blockers.append(f"{name}: {result.detail}")
    if package_version != target_version:
        blockers.append(
            f"Package version is {package_version}; expected {target_version} for release draft"
        )
    return blockers


def _build_governance_notes() -> list[str]:
    return list(GOVERNANCE_NOTES)


def _build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Release readiness report",
        "",
        f"- Target version: `{payload['target_version']}`",
        f"- Base commit: `{payload['base_commit']}`",
        f"- Generated at commit: `{payload['generated_at_commit']}`",
        f"- Package version: `{payload['package_version']}`",
        f"- Pyproject version: `{payload['pyproject_version']}`",
        f"- Decision: **{payload['release_readiness_decision']}**",
        "",
        "## Safety confirmations",
        "",
        "- release_action_taken: false",
        "- tag_created: false",
        "- github_release_created: false",
        "- package_published: false",
        "- simulation_executed: false",
        "- no OpenMM/LAMMPS execution",
        "- no runtime import of tdf-openmm-validation",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]
    for name, result in payload["checks"].items():
        lines.append(f"| {name} | {result['status']} | {result['detail']} |")
    lines.extend(["", "## Known blockers", ""])
    if payload["known_blockers"]:
        for blocker in payload["known_blockers"]:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Governance notes (post-draft approval still required)", ""])
    for note in payload.get("governance_notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _build_blockers_md(
    known_blockers: list[str],
    governance_notes: list[str],
    decision: ReleaseDecision,
) -> str:
    lines = [
        "# Release blockers",
        "",
        f"Decision: `{decision}`",
        "",
    ]
    if known_blockers:
        for blocker in known_blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- No blockers recorded.")
    lines.extend(["", "## Governance notes", ""])
    for note in governance_notes:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def _build_no_release_actions_md() -> str:
    return "\n".join(
        [
            "# No release actions taken",
            "",
            "This audit did not perform any release actions.",
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
            "This report evaluates readiness for a future release draft only.",
            "It does not approve publish or release.",
            "",
        ]
    )


def run_release_readiness_audit(
    *,
    repo_root: Path,
    target_version: str,
    base_commit: str,
    run_tests: bool = True,
) -> ReleaseReadinessReport:
    """Run release-readiness audit and build report payloads."""
    repo_root = repo_root.resolve()
    generated_at_commit = _git_head_commit(repo_root)
    package_version = __version__
    pyproject_version = _read_pyproject_version(repo_root)

    tests_passed, tests_detail = (True, "skipped") if not run_tests else _run_pytest(repo_root)
    static_passed, static_detail = _run_static_policy(repo_root)

    checks: dict[str, CheckResult] = {
        "package_metadata": _check_package_metadata(repo_root),
        "version_consistency": _check_version_consistency(repo_root, target_version),
        "required_schemas_present": _check_files_present(repo_root, REQUIRED_SCHEMAS),
        "required_clis_present": _check_files_present(repo_root, REQUIRED_CLIS),
        "required_project_control_docs_present": _check_files_present(
            repo_root, REQUIRED_PROJECT_CONTROL_DOCS
        ),
        "required_cto_bundle_requirements_present": _check_cto_bundle_requirements(repo_root),
        "tests_passed_status": CheckResult(
            "WARN" if not run_tests else ("PASS" if tests_passed else "FAIL"),
            tests_detail if run_tests else "pytest skipped; run full audit with tests enabled",
        ),
        "static_policy_status": CheckResult(
            "PASS" if static_passed else "FAIL",
            static_detail,
        ),
        "ascii_policy_status": _check_ascii_policy(repo_root),
        "raw_file_policy_status": _check_raw_file_policy(repo_root),
        "secret_file_policy_status": _check_secret_file_policy(repo_root),
        "generated_output_policy_status": _check_generated_output_policy(repo_root),
        "engine_product_separation_status": _check_engine_product_separation(repo_root),
        "reference_product_spec_status": _check_reference_product_spec(repo_root),
        "reviewer_package_builder_status": _check_reviewer_package_builder(repo_root),
        "evidence_contract_status": _check_evidence_contract(repo_root),
        "external_evidence_ingestion_status": _check_external_evidence_ingestion(repo_root),
        "claim_boundary_status": _check_claim_boundary(repo_root),
        "release_chain_status": _check_release_chain_status(repo_root),
        "changelog_status": _check_files_present(repo_root, ("CHANGELOG.md",)),
        "release_notes_draft_status": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/RELEASE_NOTES_DRAFT.md",),
        ),
        "release_candidate_checklist_status": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/RELEASE_CANDIDATE_CHECKLIST.md",),
        ),
        "no_tag_no_publish_statement_status": _check_files_present(
            repo_root,
            ("project_control/release_readiness/v0.1.0/NO_TAG_NO_RELEASE_NO_PUBLISH_STATEMENT.md",),
        ),
        "no_tag_exists_status": _check_no_tag_exists(repo_root, target_version),
    }

    known_blockers = _build_known_blockers(
        checks,
        package_version=package_version,
        target_version=target_version,
    )
    governance_notes = _build_governance_notes()
    decision = _derive_decision(checks, known_blockers)

    payload: dict[str, Any] = {
        "report_version": "1.0",
        "target_version": target_version,
        "base_commit": base_commit,
        "repository": REPOSITORY_URL,
        "package_version": package_version,
        "pyproject_version": pyproject_version,
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
        "governance_notes": governance_notes,
        "release_readiness_decision": decision,
        "generated_at_commit": generated_at_commit,
    }

    for phrase in FORBIDDEN_DECISION_PHRASES:
        if phrase in json.dumps(payload).upper():
            raise ValueError(f"Forbidden decision phrase in report: {phrase}")

    validate_release_readiness_report(payload, repo_root)

    return ReleaseReadinessReport(
        payload=payload,
        markdown=_build_markdown(payload),
        blockers_md=_build_blockers_md(known_blockers, governance_notes, decision),
        no_release_actions_md=_build_no_release_actions_md(),
    )


def write_release_readiness_outputs(report: ReleaseReadinessReport, output_dir: Path) -> list[str]:
    """Write release-readiness report files to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "RELEASE_READINESS_REPORT.json": json.dumps(report.payload, indent=2, sort_keys=True) + "\n",
        "RELEASE_READINESS_REPORT.md": report.markdown,
        "RELEASE_BLOCKERS.md": report.blockers_md,
        "NO_RELEASE_ACTIONS_TAKEN.md": report.no_release_actions_md,
    }
    written: list[str] = []
    for name, content in files.items():
        path = output_dir / name
        path.write_text(content, encoding="utf-8")
        written.append(name)
    return written

#!/usr/bin/env python3
"""Static policy audit for tracked repository files."""

from __future__ import annotations

import argparse
import subprocess
import sys
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

RAW_COORDINATE_SUFFIXES = {".pdb", ".xyz", ".cif", ".mmcif", ".mol2", ".sdf"}

FORBIDDEN_PATH_MARKERS = (
    ".env",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
)

FORBIDDEN_PATH_SUBSTRINGS = ("secret", "token")

FORBIDDEN_SIMULATION_PATHS = {
    "simulation_outputs",
    "md_outputs",
    "lammps_outputs",
    "openmm_outputs",
    "dispatch",
    "wet_lab",
    "client_package",
}

ALLOWED_SIMULATION_PATH_PREFIXES = (
    "project_control/cto_review_packages/",
)

FORBIDDEN_CLAIM_PHRASES = (
    "proven lithium filter",
    "experimentally validated lithium selectivity",
    "production-ready membrane",
    "force-field-ready bn membrane",
    "simulation-ready membrane",
    "wet-lab-ready product",
    "real battery performance",
    "tdf proves",
    "physics proven",
)

ENGINE_DIR_REL = Path("src") / "tdf_product_artifact_builder"
ENGINE_FORBIDDEN_TERMS = (
    "lithium_filter_candidate_v0_1",
    "lithium",
    "li/na",
    "phase_gated_bn_membrane_candidate",
)
ENGINE_TERM_ALLOWLIST_FILES = {"claim_boundaries.py", "tdf_openmm_contract.py", "evidence_adapter.py"}

FORBIDDEN_EXECUTION_PHRASES = (
    "lmp -in",
    "run 0",
    "pair_style",
    "pair_coeff",
    "openmm.app",
    "import lammps",
    "import openmm",
    "from openmm",
    "from lammps",
)

EXECUTION_SCAN_ALLOWLIST_PREFIXES = (
    "tests/",
    "tools/static_policy_audit.py",
    "tools/validate_diagnostic_evidence.py",
    "project_control/",
    "schemas/",
)

EXECUTION_LINE_ALLOW_MARKERS = (
    "no ",
    "not ",
    "reject",
    "forbidden",
    "must not",
    "without ",
    "does not",
    "do not",
    "never ",
)

REVIEWER_DOC_PATHS = (
    "README.md",
    "project_control/PROJECT_CHARTER.md",
    "project_control/PRODUCTIZATION_STRATEGY.md",
    "project_control/ROADMAP.md",
    "project_control/NEXT_ACTIONS.md",
    "project_control/RELEASE_CHAIN_STATUS.md",
)

REVIEWER_FACING_PREFIXES: tuple[str, ...] = (
    "README.md",
    "project_control/",
    "product_specs/",
    "schemas/",
    "tools/",
    "src/",
    "tests/fixtures/review_safe/",
)

REVIEWER_FACING_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".yaml", ".yml", ".json", ".txt", ".patch", ".py", ".toml"}
)

CTO_REVIEW_ZIP_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".md", ".yaml", ".yml", ".json", ".txt", ".patch"}
)

ALLOWED_CONTROL = {"\n", "\r", "\t"}


@dataclass
class AuditFinding:
    check: str
    path: str
    detail: str


@dataclass
class AuditReport:
    passed: bool
    findings: list[AuditFinding] = field(default_factory=list)

    def add(self, check: str, path: str, detail: str) -> None:
        self.findings.append(AuditFinding(check=check, path=path, detail=detail))


def tracked_files(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or REPO_ROOT
    out = subprocess.check_output(["git", "ls-files"], cwd=root, text=True)
    return [root / line for line in out.splitlines() if line.strip()]


def is_reviewer_facing_text(rel: str) -> bool:
    """Return True if a tracked relative path is reviewer-facing text."""
    if not any(rel == prefix or rel.startswith(prefix) for prefix in REVIEWER_FACING_PREFIXES):
        return False
    return Path(rel).suffix.lower() in REVIEWER_FACING_SUFFIXES


def scan_non_ascii(text: str) -> list[tuple[int, str, str]]:
    """Return (line, codepoint, name) for non-ASCII characters."""
    hits: list[tuple[int, str, str]] = []
    for i, ch in enumerate(text):
        if ord(ch) <= 127:
            continue
        line = text.count("\n", 0, i) + 1
        hits.append((line, f"U+{ord(ch):04X}", unicodedata.name(ch, "UNKNOWN")))
    return hits


def scan_hidden_unicode(text: str) -> list[tuple[int, str, str]]:
    """Return (line, codepoint, name) for forbidden control characters."""
    hits: list[tuple[int, str, str]] = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        if cp in range(0x202A, 0x202F) or cp in range(0x2066, 0x206A) or cp in range(0x200B, 0x2010):
            line = text.count("\n", 0, i) + 1
            hits.append((line, f"U+{cp:04X}", unicodedata.name(ch, "UNKNOWN")))
            continue
        if ch == "\ufeff":
            line = text.count("\n", 0, i) + 1
            hits.append((line, "U+FEFF", "BYTE ORDER MARK"))
            continue
        cat = unicodedata.category(ch)
        if cat in {"Cf", "Cc", "Cs"} and ch not in ALLOWED_CONTROL:
            line = text.count("\n", 0, i) + 1
            hits.append((line, f"U+{cp:04X}", unicodedata.name(ch, "UNKNOWN")))
    return hits


def scan_forbidden_execution_line(line: str) -> str | None:
    norm = line.lower()
    if any(marker in norm for marker in EXECUTION_LINE_ALLOW_MARKERS):
        return None
    for phrase in FORBIDDEN_EXECUTION_PHRASES:
        if phrase in norm:
            return phrase
    if "minimize" in norm and "minimization" not in norm:
        return "minimize"
    if "production md" in norm:
        return "production MD"
    if norm.strip().startswith("dynamics") or " run dynamics" in norm:
        return "dynamics"
    return None


def scan_forbidden_claim_line(line: str) -> str | None:
    norm = line.lower()
    if any(
        marker in norm
        for marker in (
            "forbidden",
            "does not claim",
            "do not claim",
            "not claim",
            "explicitly forbidden",
            "reject",
            "no claim",
            "must not claim",
            "forbidden claims",
            "forbidden claim",
        )
    ):
        return None
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in norm:
            return phrase
    return None


def audit_tracked_files(repo_root: Path | None = None) -> AuditReport:
    root = repo_root or REPO_ROOT
    report = AuditReport(passed=True)
    files = tracked_files(root)

    for path in files:
        rel = str(path.relative_to(root))
        rel_lower = rel.lower()
        name_lower = path.name.lower()

        if path.suffix.lower() in RAW_COORDINATE_SUFFIXES:
            report.add("raw_coordinates", rel, f"forbidden suffix {path.suffix.lower()}")

        for marker in FORBIDDEN_PATH_MARKERS:
            if marker in rel_lower.split("/") or name_lower == marker.lstrip("."):
                report.add("secrets_cache_venv", rel, f"forbidden path marker {marker!r}")

        for sub in FORBIDDEN_PATH_SUBSTRINGS:
            if sub in name_lower and not rel.startswith("tests/"):
                report.add("secrets_cache_venv", rel, f"forbidden filename substring {sub!r}")

        for sim_path in FORBIDDEN_SIMULATION_PATHS:
            if sim_path in rel_lower.split("/"):
                if not any(rel.startswith(prefix) for prefix in ALLOWED_SIMULATION_PATH_PREFIXES):
                    report.add("simulation_outputs", rel, f"forbidden simulation path segment {sim_path!r}")

        if not path.is_file() or path.suffix == ".zip":
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for line_no, codepoint, name in scan_hidden_unicode(text):
            report.add("hidden_unicode", rel, f"line {line_no}: {codepoint} {name}")

        if is_reviewer_facing_text(rel):
            for line_no, codepoint, name in scan_non_ascii(text):
                report.add("reviewer_ascii", rel, f"line {line_no}: {codepoint} {name}")

        if rel in REVIEWER_DOC_PATHS or rel.startswith("project_control/") and rel.endswith(".md"):
            if rel.endswith("CLAIM_BOUNDARIES.md") or "/templates/" in rel:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                hit = scan_forbidden_claim_line(line)
                if hit:
                    report.add("forbidden_claims", rel, f"line {line_no}: {hit!r}")

        scan_execution = rel.startswith("src/tdf_product_artifact_builder/") or rel.startswith("tools/")
        if scan_execution and not any(rel.startswith(prefix) for prefix in EXECUTION_SCAN_ALLOWLIST_PREFIXES):
            if rel == "tools/static_policy_audit.py":
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                hit = scan_forbidden_execution_line(line)
                if hit:
                    report.add("simulation_execution", rel, f"line {line_no}: {hit!r}")

    cto_zip_root = root / "project_control" / "cto_review_packages"
    if cto_zip_root.is_dir():
        for zip_path in sorted(cto_zip_root.glob("*.zip")):
            rel_zip = str(zip_path.relative_to(root))
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        member = info.filename
                        if Path(member).suffix.lower() not in CTO_REVIEW_ZIP_TEXT_SUFFIXES:
                            continue
                        try:
                            member_text = zf.read(info).decode("utf-8")
                        except UnicodeDecodeError:
                            report.add("reviewer_ascii", rel_zip, f"non-utf8 member {member}")
                            continue
                        for line_no, codepoint, name in scan_hidden_unicode(member_text):
                            report.add(
                                "hidden_unicode",
                                f"{rel_zip}:{member}",
                                f"line {line_no}: {codepoint} {name}",
                            )
                        for line_no, codepoint, name in scan_non_ascii(member_text):
                            report.add(
                                "reviewer_ascii",
                                f"{rel_zip}:{member}",
                                f"line {line_no}: {codepoint} {name}",
                            )
            except (OSError, zipfile.BadZipFile) as exc:
                report.add("reviewer_ascii", rel_zip, f"zip read failed: {exc}")

    engine_dir = root / ENGINE_DIR_REL
    if engine_dir.is_dir():
        for py_path in engine_dir.glob("*.py"):
            if py_path.name in ENGINE_TERM_ALLOWLIST_FILES:
                continue
            rel = str(py_path.relative_to(root))
            text = py_path.read_text(encoding="utf-8").lower()
            for term in ENGINE_FORBIDDEN_TERMS:
                if term in text:
                    report.add("engine_product_coupling", rel, f"forbidden engine term {term!r}")

    report.passed = len(report.findings) == 0
    return report


def format_report(report: AuditReport) -> str:
    lines = ["STATIC POLICY AUDIT"]
    if report.passed:
        lines.append("RESULT: PASS")
        lines.append("All tracked-file static policy checks passed.")
        return "\n".join(lines) + "\n"

    lines.append("RESULT: FAIL")
    lines.append(f"Findings: {len(report.findings)}")
    for finding in report.findings:
        lines.append(f"- [{finding.check}] {finding.path}: {finding.detail}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run static policy audit on tracked files")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args()
    report = audit_tracked_files(Path(args.repo_root))
    output = format_report(report)
    print(output, end="")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())

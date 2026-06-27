"""Reviewer-facing ASCII-only text tests."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from tools.static_policy_audit import (
    CTO_REVIEW_ZIP_TEXT_SUFFIXES,
    REVIEWER_FACING_PREFIXES,
    REVIEWER_FACING_SUFFIXES,
    is_reviewer_facing_text,
    scan_non_ascii,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tracked_reviewer_facing_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    files: list[Path] = []
    for rel in out.splitlines():
        if not rel.strip():
            continue
        if not is_reviewer_facing_text(rel):
            continue
        path = REPO_ROOT / rel
        if path.is_file():
            files.append(path)
    return files


def test_reviewer_facing_files_are_ascii_only() -> None:
    violations: list[str] = []
    for path in _tracked_reviewer_facing_files():
        text = path.read_text(encoding="utf-8")
        for line_no, codepoint, name in scan_non_ascii(text):
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}:{line_no}: {codepoint} {name}")
    assert not violations, "Non-ASCII characters in reviewer-facing files:\n" + "\n".join(violations)


def test_cto_review_zip_text_members_are_ascii_only() -> None:
    violations: list[str] = []
    zip_root = REPO_ROOT / "project_control" / "cto_review_packages"
    for zip_path in sorted(zip_root.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                member = info.filename
                if Path(member).suffix.lower() not in CTO_REVIEW_ZIP_TEXT_SUFFIXES:
                    continue
                text = zf.read(info).decode("utf-8")
                for line_no, codepoint, name in scan_non_ascii(text):
                    violations.append(f"{zip_path.name}:{member}:{line_no}: {codepoint} {name}")
    assert not violations, "Non-ASCII in CTO review ZIP members:\n" + "\n".join(violations)


def test_reviewer_facing_prefixes_cover_expected_paths() -> None:
    assert "README.md" in REVIEWER_FACING_PREFIXES
    assert "tools/" in REVIEWER_FACING_PREFIXES
    assert "src/" in REVIEWER_FACING_PREFIXES
    assert ".py" in REVIEWER_FACING_SUFFIXES

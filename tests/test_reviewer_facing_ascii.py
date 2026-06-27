"""Reviewer-facing ASCII-only text tests."""

from __future__ import annotations

import subprocess
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REVIEWER_FACING_PREFIXES = (
    "README.md",
    "project_control/",
    "product_specs/",
    "schemas/",
)


def _tracked_reviewer_facing_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    files: list[Path] = []
    for rel in out.splitlines():
        if not rel.strip():
            continue
        if not any(rel == prefix or rel.startswith(prefix) for prefix in REVIEWER_FACING_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".json", ".txt", ".patch"}:
            continue
        if path.is_file():
            files.append(path)
    return files


def test_reviewer_facing_files_are_ascii_only() -> None:
    violations: list[str] = []
    for path in _tracked_reviewer_facing_files():
        text = path.read_text(encoding="utf-8")
        for i, ch in enumerate(text):
            if ord(ch) <= 127:
                continue
            line = text.count("\n", 0, i) + 1
            name = unicodedata.name(ch, "UNKNOWN")
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}:{line}: U+{ord(ch):04X} {name} {ch!r}")
    assert not violations, "Non-ASCII characters in reviewer-facing files:\n" + "\n".join(violations)

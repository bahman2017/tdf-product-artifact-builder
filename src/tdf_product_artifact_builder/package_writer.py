"""Deterministic file writing helpers for reviewer packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REVIEWER_PACKAGE_EVIDENCE_FILES: tuple[str, ...] = (
    "DIAGNOSTIC_EVIDENCE_SUMMARY.md",
    "EVIDENCE_MANIFEST.json",
)

REVIEWER_PACKAGE_CONTENT_FILES: tuple[str, ...] = (
    "README_FOR_REVIEWERS.md",
    "PRODUCT_REPORT.json",
    "DEPENDENCIES.md",
    "PROVENANCE.md",
    "LIMITATIONS.md",
    "CLAIM_BOUNDARY_CERTIFICATE.md",
    "REPRODUCIBILITY.md",
    "NO_SIMULATION_NO_WETLAB_STATEMENT.md",
    "NEXT_VALIDATION_REQUIREMENTS.md",
)

REVIEWER_PACKAGE_META_FILES: tuple[str, ...] = (
    "CHECKSUMS.sha256.json",
    "MANIFEST.json",
)

REVIEWER_PACKAGE_REQUIRED_FILES: tuple[str, ...] = (
    *REVIEWER_PACKAGE_CONTENT_FILES,
    *REVIEWER_PACKAGE_META_FILES,
)

CHECKSUM_EXCLUDE_FILES: frozenset[str] = frozenset(
    {"MANIFEST.json", "CHECKSUMS.sha256.json"}
)


def deterministic_json_dumps(payload: dict[str, Any]) -> str:
    """Serialize JSON with stable key order and trailing newline."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_text_file(path: Path, content: str) -> None:
    """Write UTF-8 text, ensuring trailing newline."""
    text = content if content.endswith("\n") else content + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic JSON."""
    write_text_file(path, deterministic_json_dumps(payload).rstrip("\n"))

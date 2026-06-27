"""Base evidence loading and safety validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.checksums import sha256_bytes, sha256_file

REQUIRED_SAFETY_FLAGS: dict[str, bool] = {
    "lammps_input_executed": False,
    "simulation_executed": False,
    "accepted_for_simulation": False,
    "force_field_ready": False,
    "wet_lab_ready": False,
}

FORBIDDEN_EVIDENCE_SUFFIXES: frozenset[str] = frozenset(
    {".pdb", ".xyz", ".cif", ".mmcif", ".mol2", ".sdf", ".lammpstrj", ".dcd", ".xtc"}
)


@dataclass(frozen=True)
class EvidenceValidationReport:
    evidence_id: str
    source_tool: str
    valid: bool
    safety_flags_passed: bool
    errors: list[str] = field(default_factory=list)


def load_evidence_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON evidence file without importing upstream tools."""
    evidence_path = Path(path)
    if evidence_path.suffix.lower() not in {".json"}:
        raise ValueError(f"Evidence must be JSON: {evidence_path}")
    if evidence_path.suffix.lower() in FORBIDDEN_EVIDENCE_SUFFIXES:
        raise ValueError(f"Forbidden evidence file type: {evidence_path.suffix}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Evidence root must be a JSON object.")
    return payload


def extract_safety_flags(payload: dict[str, Any]) -> dict[str, bool]:
    """Extract safety flags from evidence payload or nested diagnostic_flags."""
    if "diagnostic_flags" in payload and isinstance(payload["diagnostic_flags"], dict):
        flags = payload["diagnostic_flags"]
    else:
        flags = payload
    return {key: bool(flags.get(key, True)) for key in REQUIRED_SAFETY_FLAGS}


def verify_safety_flags(payload: dict[str, Any]) -> list[str]:
    """Return errors if any required safety flag is not false."""
    flags = extract_safety_flags(payload)
    errors: list[str] = []
    for key, required in REQUIRED_SAFETY_FLAGS.items():
        if flags.get(key) != required:
            errors.append(f"{key} must be {required}, got {flags.get(key)!r}")
    return errors


def compute_evidence_checksum(path: str | Path) -> str:
    """Compute SHA256 checksum for an evidence JSON file."""
    return sha256_file(path)


def compute_payload_checksum(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA256 checksum for an evidence dict."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))

"""SHA256 checksum utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.package_writer import CHECKSUM_EXCLUDE_FILES


def sha256_file(path: str | Path) -> str:
    """Return the SHA256 hex digest of a file."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def build_checksums_payload(
    package_dir: str | Path,
    *,
    product_id: str,
    exclude_files: frozenset[str] = CHECKSUM_EXCLUDE_FILES,
) -> dict[str, Any]:
    """Build CHECKSUMS.sha256.json payload for a reviewer package directory."""
    root = Path(package_dir)
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in exclude_files:
            continue
        files.append(
            {
                "relative_path": rel,
                "sha256": sha256_file(path),
            }
        )
    return {
        "algorithm": "sha256",
        "product_id": product_id,
        "files": files,
    }


def verify_checksums_payload(
    package_dir: str | Path,
    payload: dict[str, Any],
) -> list[str]:
    """Verify checksum entries against files on disk. Returns error messages."""
    root = Path(package_dir)
    errors: list[str] = []
    for entry in payload.get("files", []):
        rel = str(entry.get("relative_path", ""))
        expected = str(entry.get("sha256", ""))
        path = root / rel
        if not path.is_file():
            errors.append(f"Missing file for checksum entry: {rel}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"Checksum mismatch for {rel}: expected {expected}, got {actual}")
    return errors

"""SHA256 checksum utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Return the SHA256 hex digest of a file."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()

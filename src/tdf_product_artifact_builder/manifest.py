"""Manifest builder for reviewer packages."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from tdf_product_artifact_builder.checksums import sha256_file
from tdf_product_artifact_builder.version import __version__


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class PackageManifest:
    manifest_version: str
    product_id: str
    package_type: str
    builder_version: str
    entries: list[ManifestEntry] = field(default_factory=list)
    engine_hardcoded: bool = False
    simulation_authorized: bool = False
    wet_lab_ready: bool = False
    openmm_execution: bool = False
    lammps_execution: bool = False


def default_reviewer_manifest_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "reviewer_manifest.schema.json"


def load_reviewer_manifest_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path else default_reviewer_manifest_schema_path()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_reviewer_manifest(
    payload: dict[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    schema = load_reviewer_manifest_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def build_manifest(
    package_dir: str | Path,
    *,
    product_id: str,
    include_suffixes: tuple[str, ...] = (".json", ".yaml", ".yml", ".md", ".txt"),
) -> PackageManifest:
    """Build a manifest of all reviewer package files."""
    root = Path(package_dir)
    entries: list[ManifestEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "MANIFEST.json":
            continue
        if path.suffix.lower() not in include_suffixes and rel != "CHECKSUMS.sha256.json":
            continue
        entries.append(
            ManifestEntry(
                relative_path=rel,
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    return PackageManifest(
        manifest_version="1.0",
        product_id=product_id,
        package_type="reviewer_package",
        builder_version=__version__,
        entries=entries,
        engine_hardcoded=False,
        simulation_authorized=False,
        wet_lab_ready=False,
        openmm_execution=False,
        lammps_execution=False,
    )


def manifest_to_dict(manifest: PackageManifest) -> dict[str, Any]:
    """Convert a manifest to a JSON-serializable dict."""
    payload = asdict(manifest)
    payload["entries"] = [asdict(entry) for entry in manifest.entries]
    return payload

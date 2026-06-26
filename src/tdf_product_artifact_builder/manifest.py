"""Manifest builder for reviewer packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from tdf_product_artifact_builder.checksums import sha256_file


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class PackageManifest:
    package_dir: str
    product_id: str | None
    entries: list[ManifestEntry] = field(default_factory=list)
    simulation_authorized: bool = False
    wet_lab_ready: bool = False


def build_manifest(
    package_dir: str | Path,
    *,
    product_id: str | None = None,
    include_suffixes: tuple[str, ...] = (".json", ".yaml", ".yml", ".md", ".txt"),
) -> PackageManifest:
    """Build a manifest of review-safe files in a package directory."""
    root = Path(package_dir)
    entries: list[ManifestEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in include_suffixes and path.name not in {"MANIFEST.json"}:
            continue
        rel = str(path.relative_to(root))
        entries.append(
            ManifestEntry(
                relative_path=rel,
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    return PackageManifest(
        package_dir=str(root),
        product_id=product_id,
        entries=entries,
        simulation_authorized=False,
        wet_lab_ready=False,
    )


def manifest_to_dict(manifest: PackageManifest) -> dict:
    """Convert a manifest to a JSON-serializable dict."""
    payload = asdict(manifest)
    payload["entries"] = [asdict(e) for e in manifest.entries]
    return payload

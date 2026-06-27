"""Review-safe external evidence directory ingestion workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.evidence import (
    FORBIDDEN_EVIDENCE_SUFFIXES,
    compute_evidence_checksum,
    compute_payload_checksum,
    verify_safety_flags,
)
from tdf_product_artifact_builder.evidence_acceptance import (
    build_evidence_acceptance_report,
    validate_evidence_acceptance_report,
)
from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence
from tdf_product_artifact_builder.evidence_ingestion_manifest import (
    build_evidence_ingestion_manifest,
    validate_evidence_ingestion_manifest,
)
from tdf_product_artifact_builder.evidence_rejection import (
    build_evidence_rejection_report,
    validate_evidence_rejection_report,
)
from tdf_product_artifact_builder.package_writer import write_json_file


ACCEPTANCE_REPORT_NAME = "EVIDENCE_ACCEPTANCE_REPORT.json"
REJECTION_REPORT_NAME = "EVIDENCE_REJECTION_REPORT.json"
INGESTION_MANIFEST_NAME = "EVIDENCE_INGESTION_MANIFEST.json"


@dataclass(frozen=True)
class EvidenceIngestionItem:
    relative_path: str
    evidence_id: str
    source_tool: str
    source_version: str
    evidence_type: str
    file_sha256: str
    payload_sha256: str
    adapted_payload: dict[str, Any]


@dataclass(frozen=True)
class EvidenceRejectionItem:
    relative_path: str
    reason: str
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceIngestionReport:
    source_directory: str
    output_dir: str
    accepted_count: int
    rejected_count: int
    accepted: list[EvidenceIngestionItem] = field(default_factory=list)
    rejected: list[EvidenceRejectionItem] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)


def _relative_path(evidence_dir: Path, path: Path) -> str:
    return str(path.relative_to(evidence_dir)).replace("\\", "/")


def _scan_evidence_files(evidence_dir: Path) -> list[Path]:
    """Return sorted file paths under evidence_dir (non-recursive)."""
    if not evidence_dir.is_dir():
        raise ValueError(f"Evidence directory not found: {evidence_dir}")
    files = [path for path in evidence_dir.iterdir() if path.is_file()]
    return sorted(files, key=lambda item: item.name)


def _reject_non_json(path: Path, evidence_dir: Path) -> EvidenceRejectionItem | None:
    rel = _relative_path(evidence_dir, path)
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_EVIDENCE_SUFFIXES:
        return EvidenceRejectionItem(
            relative_path=rel,
            reason="forbidden_raw_or_coordinate_file",
            errors=[f"Forbidden evidence file suffix: {suffix}"],
        )
    if suffix != ".json":
        return EvidenceRejectionItem(
            relative_path=rel,
            reason="non_json_evidence",
            errors=[f"Evidence must be JSON, got suffix: {suffix or '(none)'}"],
        )
    return None


def _validate_json_evidence(path: Path, evidence_dir: Path) -> tuple[EvidenceIngestionItem | None, EvidenceRejectionItem | None]:
    rel = _relative_path(evidence_dir, path)
    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, EvidenceRejectionItem(
            relative_path=rel,
            reason="invalid_json",
            errors=[str(exc)],
        )
    if not isinstance(raw_payload, dict):
        return None, EvidenceRejectionItem(
            relative_path=rel,
            reason="invalid_json_root",
            errors=["Evidence root must be a JSON object."],
        )

    flag_errors = verify_safety_flags(raw_payload)
    if flag_errors:
        return None, EvidenceRejectionItem(
            relative_path=rel,
            reason="positive_readiness_or_simulation_flag",
            errors=flag_errors,
        )

    try:
        adapted = validate_and_adapt_evidence(path)
    except ValueError as exc:
        return None, EvidenceRejectionItem(
            relative_path=rel,
            reason="evidence_validation_failed",
            errors=[str(exc)],
        )

    return EvidenceIngestionItem(
        relative_path=rel,
        evidence_id=str(adapted["evidence_id"]),
        source_tool=str(adapted["source_tool"]),
        source_version=str(adapted["source_version"]),
        evidence_type=str(adapted["evidence_type"]),
        file_sha256=compute_evidence_checksum(path),
        payload_sha256=compute_payload_checksum(adapted),
        adapted_payload=adapted,
    ), None


def ingest_evidence_directory(
    evidence_dir: str | Path,
    output_dir: str | Path,
) -> EvidenceIngestionReport:
    """Ingest review-safe JSON evidence files from a directory."""
    source = Path(evidence_dir).resolve()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    accepted_items: list[EvidenceIngestionItem] = []
    rejected_items: list[EvidenceRejectionItem] = []

    for path in _scan_evidence_files(source):
        non_json_rejection = _reject_non_json(path, source)
        if non_json_rejection is not None:
            rejected_items.append(non_json_rejection)
            continue

        accepted, rejected = _validate_json_evidence(path, source)
        if accepted is not None:
            accepted_items.append(accepted)
        if rejected is not None:
            rejected_items.append(rejected)

    source_directory = str(source)
    accepted_entries = [
        {
            "relative_path": item.relative_path,
            "evidence_id": item.evidence_id,
            "source_tool": item.source_tool,
            "source_version": item.source_version,
            "evidence_type": item.evidence_type,
            "file_sha256": item.file_sha256,
            "payload_sha256": item.payload_sha256,
        }
        for item in accepted_items
    ]
    rejected_entries = [
        {
            "relative_path": item.relative_path,
            "reason": item.reason,
            "errors": item.errors,
        }
        for item in rejected_items
    ]

    acceptance_report = build_evidence_acceptance_report(
        source_directory=source_directory,
        accepted_entries=accepted_entries,
    )
    rejection_report = build_evidence_rejection_report(
        source_directory=source_directory,
        rejected_entries=rejected_entries,
    )
    ingestion_manifest = build_evidence_ingestion_manifest(
        source_directory=source_directory,
        accepted_entries=accepted_entries,
        rejected_count=len(rejected_items),
    )

    validate_evidence_acceptance_report(acceptance_report)
    validate_evidence_rejection_report(rejection_report)
    validate_evidence_ingestion_manifest(ingestion_manifest)

    files_written: list[str] = []
    for name, payload in (
        (ACCEPTANCE_REPORT_NAME, acceptance_report),
        (REJECTION_REPORT_NAME, rejection_report),
        (INGESTION_MANIFEST_NAME, ingestion_manifest),
    ):
        write_json_file(out / name, payload)
        files_written.append(name)

    return EvidenceIngestionReport(
        source_directory=source_directory,
        output_dir=str(out),
        accepted_count=len(accepted_items),
        rejected_count=len(rejected_items),
        accepted=accepted_items,
        rejected=rejected_items,
        files_written=sorted(files_written),
    )


def resolve_evidence_paths_from_ingestion_manifest(
    manifest_path: str | Path,
) -> list[Path]:
    """Resolve accepted evidence file paths from an ingestion manifest."""
    manifest_file = Path(manifest_path).resolve()
    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    validate_evidence_ingestion_manifest(payload)

    source_directory = Path(payload["source_directory"]).resolve()
    paths: list[Path] = []
    for entry in payload["accepted_entries"]:
        rel = entry["relative_path"]
        evidence_path = source_directory / rel
        if not evidence_path.is_file():
            raise ValueError(f"Accepted evidence file missing: {evidence_path}")
        expected_sha = entry["file_sha256"]
        actual_sha = compute_evidence_checksum(evidence_path)
        if actual_sha != expected_sha:
            raise ValueError(
                f"Checksum mismatch for {rel}: expected {expected_sha}, got {actual_sha}"
            )
        paths.append(evidence_path)
    return sorted(paths, key=lambda item: str(item))

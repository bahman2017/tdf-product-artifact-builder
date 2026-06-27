"""Generic reviewer package builder."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.checksums import build_checksums_payload, verify_checksums_payload
from tdf_product_artifact_builder.claim_boundaries import (
    build_claim_boundary_certificate_md,
    validate_claim_boundaries,
    validate_generated_package_claims,
)
from tdf_product_artifact_builder.manifest import build_manifest, manifest_to_dict, validate_reviewer_manifest
from tdf_product_artifact_builder.package_writer import (
    REVIEWER_PACKAGE_EVIDENCE_FILES,
    REVIEWER_PACKAGE_REQUIRED_FILES,
    write_json_file,
    write_text_file,
)
from tdf_product_artifact_builder.product_report import build_product_report, validate_product_report
from tdf_product_artifact_builder.product_spec import load_product_spec, validate_product_spec
from tdf_product_artifact_builder.reproducibility import build_reproducibility_md
from tdf_product_artifact_builder.diagnostic_evidence import build_diagnostic_evidence_summary_md
from tdf_product_artifact_builder.evidence_adapter import validate_and_adapt_evidence
from tdf_product_artifact_builder.evidence_ingestion import resolve_evidence_paths_from_ingestion_manifest
from tdf_product_artifact_builder.evidence_manifest import build_evidence_manifest, validate_evidence_manifest
from tdf_product_artifact_builder.version import __version__


@dataclass(frozen=True)
class ReviewerPackageReport:
    product_id: str
    output_dir: str
    package_created: bool
    manifest_present: bool
    checksums_present: bool
    product_report_valid: bool
    claim_boundary_passed: bool
    simulation_authorized: bool
    wet_lab_ready: bool
    readiness_stage: str
    evidence_included: bool = False
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


REVIEWER_PACKAGE_LIMITATIONS: list[str] = [
    "Reviewer packages are static handoff bundles only.",
    "No simulation authorization.",
    "No wet-lab readiness claim.",
    "No physical theory validation is claimed.",
    "No OpenMM or LAMMPS execution.",
    "Readiness stage is not upgraded by package generation.",
]


def _build_readme_for_reviewers(
    spec: dict[str, Any],
    *,
    include_evidence: bool = False,
) -> str:
    product_id = str(spec.get("product_id", ""))
    readiness = str(spec.get("readiness_stage", ""))
    target = str(spec.get("target_behavior", ""))
    lines = [
        "# README for reviewers",
        "",
        "This package is a reviewer-facing handoff bundle generated from a product spec.",
        "Build trust in the artifact, not belief in the theory.",
        "",
        f"- Product ID: `{product_id}`",
        f"- Product type: `{spec.get('product_type', '')}`",
        f"- Target behavior: {target}",
        f"- Readiness stage: `{readiness}`",
        "",
        "## Package contents",
        "",
    ]
    for name in REVIEWER_PACKAGE_REQUIRED_FILES:
        lines.append(f"- `{name}`")
    if include_evidence:
        lines.append("")
        lines.append("## External diagnostic evidence")
        lines.append("")
        for name in REVIEWER_PACKAGE_EVIDENCE_FILES:
            lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## Review scope",
            "",
            "- Static diagnostic and preparation scope only.",
            "- No simulation, OpenMM, LAMMPS, minimization, dynamics, or production MD.",
            "- No wet-lab validation or fabrication readiness.",
            "- Conventional external validation required before any stage advancement.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_dependencies_md(spec: dict[str, Any]) -> str:
    lines = [
        "# Dependencies",
        "",
        "Reference source artifacts listed in the product spec.",
        "These are documentation references only; no upstream execution occurs.",
        "",
    ]
    for artifact in spec.get("source_artifacts", []):
        lines.append(f"- {artifact}")
    lines.extend(
        [
            "",
            "## Execution boundary",
            "",
            "- No OpenMM execution.",
            "- No LAMMPS execution.",
            "- No upstream TDF repository API calls.",
            "- Evidence contract validation only; no simulation execution.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_provenance_md(spec: dict[str, Any]) -> str:
    product_id = str(spec.get("product_id", ""))
    lines = [
        "# Provenance",
        "",
        f"- Product ID: `{product_id}`",
        f"- Builder version: `{__version__}`",
        "- Package type: `reviewer_package`",
        "- Generation method: generic reviewer package builder",
        "- engine_hardcoded: `false`",
        "- simulation_authorized: `false`",
        "- wet_lab_ready: `false`",
        "",
        "## Scope",
        "",
        "- Generated from product spec fields only.",
        "- No simulation artifacts included.",
        "- No raw coordinate files included.",
        "- No force-field parameters included.",
        "",
    ]
    return "\n".join(lines)


def _build_limitations_md() -> str:
    lines = ["# Limitations", ""]
    for item in REVIEWER_PACKAGE_LIMITATIONS:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _build_no_simulation_statement_md(spec: dict[str, Any]) -> str:
    readiness = str(spec.get("readiness_stage", ""))
    lines = [
        "# No simulation / no wet-lab statement",
        "",
        "This reviewer package explicitly states the following boundaries:",
        "",
        "- No simulation was executed to produce this package.",
        "- No OpenMM execution occurred.",
        "- No LAMMPS execution occurred.",
        "- No minimization, dynamics, or production MD was run.",
        "- No wet-lab validation was performed.",
        "- No force-field readiness is claimed.",
        "- No real selectivity or battery performance is claimed.",
        f"- Readiness stage remains `{readiness}` and is not upgraded.",
        "",
    ]
    return "\n".join(lines)


def _build_next_validation_requirements_md(spec: dict[str, Any]) -> str:
    lines = [
        "# Next validation requirements",
        "",
        "External validation requirements from the product spec:",
        "",
    ]
    for req in spec.get("external_validation_requirements", []):
        lines.append(f"- {req}")
    lines.extend(
        [
            "",
            "## Required diagnostics",
            "",
        ]
    )
    for diag in spec.get("required_diagnostics", []):
        lines.append(f"- {diag}")
    lines.extend(
        [
            "",
            "## Blocked until CTO approval",
            "",
            "- Controlled simulation.",
            "- Wet-lab/fabrication readiness.",
            "- Real product package generation.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_content_files(
    out: Path,
    spec: dict[str, Any],
    *,
    evidence_payloads: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Write all reviewer package content files except manifest and checksums."""
    include_evidence = bool(evidence_payloads)
    product_report = build_product_report(spec)
    validate_product_report(product_report)

    files: list[tuple[str, str | dict[str, Any]]] = [
        ("README_FOR_REVIEWERS.md", _build_readme_for_reviewers(spec, include_evidence=include_evidence)),
        ("PRODUCT_REPORT.json", product_report),
        ("DEPENDENCIES.md", _build_dependencies_md(spec)),
        ("PROVENANCE.md", _build_provenance_md(spec)),
        ("LIMITATIONS.md", _build_limitations_md()),
        ("CLAIM_BOUNDARY_CERTIFICATE.md", build_claim_boundary_certificate_md(spec)),
        ("REPRODUCIBILITY.md", build_reproducibility_md(spec)),
        ("NO_SIMULATION_NO_WETLAB_STATEMENT.md", _build_no_simulation_statement_md(spec)),
        ("NEXT_VALIDATION_REQUIREMENTS.md", _build_next_validation_requirements_md(spec)),
    ]

    if evidence_payloads:
        combined = evidence_payloads[0] if len(evidence_payloads) == 1 else {
            "evidence_id": "combined-evidence-summary",
            "evidence_type": "diagnostic_preparation_report",
            "source_tool": evidence_payloads[0]["source_tool"],
            "source_version": evidence_payloads[0]["source_version"],
            "diagnostic_flags": evidence_payloads[0]["diagnostic_flags"],
            "diagnostic_summary": "; ".join(
                str(item.get("reviewer_summary", "")) for item in evidence_payloads
            ),
            "limitations": evidence_payloads[0].get("limitations", []),
        }
        manifest = build_evidence_manifest(
            product_id=str(spec["product_id"]),
            evidence_payloads=evidence_payloads,
        )
        validate_evidence_manifest(manifest)
        files.extend(
            [
                ("DIAGNOSTIC_EVIDENCE_SUMMARY.md", build_diagnostic_evidence_summary_md(combined)),
                ("EVIDENCE_MANIFEST.json", manifest),
            ]
        )

    written: list[str] = []
    for name, content in files:
        path = out / name
        if isinstance(content, dict):
            write_json_file(path, content)
        else:
            write_text_file(path, content)
        written.append(name)
    return written


def create_reviewer_package(
    product_spec_path: str | Path,
    output_dir: str | Path,
    *,
    evidence_paths: list[str | Path] | None = None,
    evidence_ingestion_manifest_path: str | Path | None = None,
) -> ReviewerPackageReport:
    """Create a deterministic reviewer package directory from a product spec."""
    spec_path = Path(product_spec_path)
    out = Path(output_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    validation = validate_product_spec(spec_path)
    if not validation.valid:
        raise ValueError(f"Invalid product spec: {'; '.join(validation.errors)}")

    spec = load_product_spec(spec_path)
    product_id = str(spec["product_id"])
    readiness_stage = str(spec["readiness_stage"])

    claim_report = validate_claim_boundaries(
        allowed_claims=list(spec.get("allowed_claims", [])),
        forbidden_claims=list(spec.get("forbidden_claims", [])),
    )
    if not claim_report.passed:
        raise ValueError(f"Claim boundary validation failed: {claim_report.forbidden_hits}")

    resolved_evidence_paths: list[Path] = []
    if evidence_ingestion_manifest_path:
        if evidence_paths:
            raise ValueError("Provide --evidence or --evidence-ingestion-manifest, not both.")
        resolved_evidence_paths = resolve_evidence_paths_from_ingestion_manifest(
            evidence_ingestion_manifest_path
        )
    elif evidence_paths:
        resolved_evidence_paths = [Path(path) for path in evidence_paths]

    evidence_payloads: list[dict[str, Any]] = []
    if resolved_evidence_paths:
        for evidence_path in resolved_evidence_paths:
            evidence_payloads.append(validate_and_adapt_evidence(evidence_path))

    files_written = _write_content_files(out, spec, evidence_payloads=evidence_payloads or None)

    generated_claim_report = validate_generated_package_claims(out)
    if not generated_claim_report.passed:
        raise ValueError(
            f"Generated package claim validation failed: {generated_claim_report.forbidden_hits}"
        )

    checksums_payload = build_checksums_payload(out, product_id=product_id)
    write_json_file(out / "CHECKSUMS.sha256.json", checksums_payload)
    files_written.append("CHECKSUMS.sha256.json")

    checksum_errors = verify_checksums_payload(out, checksums_payload)
    if checksum_errors:
        raise ValueError(f"Checksum verification failed: {'; '.join(checksum_errors)}")

    manifest = build_manifest(out, product_id=product_id)
    manifest_dict = manifest_to_dict(manifest)
    validate_reviewer_manifest(manifest_dict)
    write_json_file(out / "MANIFEST.json", manifest_dict)
    files_written.append("MANIFEST.json")

    required_files = list(REVIEWER_PACKAGE_REQUIRED_FILES)
    if evidence_payloads:
        required_files.extend(REVIEWER_PACKAGE_EVIDENCE_FILES)
    created = all((out / name).is_file() for name in required_files)

    return ReviewerPackageReport(
        product_id=product_id,
        output_dir=str(out),
        package_created=created,
        manifest_present=(out / "MANIFEST.json").is_file(),
        checksums_present=(out / "CHECKSUMS.sha256.json").is_file(),
        product_report_valid=True,
        claim_boundary_passed=claim_report.passed and generated_claim_report.passed,
        simulation_authorized=False,
        wet_lab_ready=False,
        readiness_stage=readiness_stage,
        evidence_included=bool(evidence_payloads),
        files_written=sorted(files_written),
        warnings=list(REVIEWER_PACKAGE_LIMITATIONS),
        limitations=list(REVIEWER_PACKAGE_LIMITATIONS),
    )

"""Placeholder reviewer package builder."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tdf_product_artifact_builder.claim_boundaries import validate_claim_boundaries
from tdf_product_artifact_builder.manifest import build_manifest, manifest_to_dict
from tdf_product_artifact_builder.product_spec import load_product_spec, validate_product_spec


@dataclass(frozen=True)
class ReviewerPackageReport:
    product_id: str
    output_dir: str
    package_created: bool
    manifest_present: bool
    claim_boundary_passed: bool
    simulation_authorized: bool
    wet_lab_ready: bool
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


REVIEWER_PACKAGE_LIMITATIONS: list[str] = [
    "Reviewer packages are static handoff bundles only.",
    "No simulation authorization.",
    "No wet-lab readiness claim.",
    "No TDF physics proof.",
]


def _write_claim_boundaries_md(path: Path, spec: dict[str, Any]) -> None:
    lines = [
        "# Claim boundaries",
        "",
        f"- Product ID: `{spec.get('product_id', '')}`",
        f"- Readiness stage: `{spec.get('readiness_stage', '')}`",
        "- Diagnostic/preparation scope only.",
        "- No simulation authorization.",
        "- No force-field readiness claim.",
        "- No wet-lab readiness claim.",
        "- No TDF physics proof claim.",
        "",
        "## Allowed claims",
        "",
    ]
    for claim in spec.get("allowed_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Forbidden claims", ""])
    for claim in spec.get("forbidden_claims", []):
        lines.append(f"- {claim}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_limitations_md(path: Path) -> None:
    lines = ["# Limitations", ""]
    for item in REVIEWER_PACKAGE_LIMITATIONS:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def create_reviewer_package(
    product_spec_path: str | Path,
    output_dir: str | Path,
) -> ReviewerPackageReport:
    """Create a placeholder reviewer package directory from a product spec."""
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

    shutil.copy2(spec_path, out / "product_spec.yaml")
    (out / "PRODUCT_SPEC_SUMMARY.json").write_text(
        json.dumps(
            {
                "product_id": product_id,
                "product_type": spec.get("product_type"),
                "readiness_stage": spec.get("readiness_stage"),
                "engine_hardcoded": False,
                "simulation_authorized": False,
                "wet_lab_ready": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _write_claim_boundaries_md(out / "CLAIM_BOUNDARIES.md", spec)
    _write_limitations_md(out / "LIMITATIONS.md")

    claim_report = validate_claim_boundaries(
        allowed_claims=list(spec.get("allowed_claims", [])),
        forbidden_claims=list(spec.get("forbidden_claims", [])),
    )

    manifest = build_manifest(out, product_id=product_id)
    manifest_path = out / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest_to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    created = all(
        [
            (out / "product_spec.yaml").is_file(),
            (out / "PRODUCT_SPEC_SUMMARY.json").is_file(),
            (out / "CLAIM_BOUNDARIES.md").is_file(),
            (out / "LIMITATIONS.md").is_file(),
            manifest_path.is_file(),
        ]
    )

    return ReviewerPackageReport(
        product_id=product_id,
        output_dir=str(out),
        package_created=created,
        manifest_present=manifest_path.is_file(),
        claim_boundary_passed=claim_report.passed,
        simulation_authorized=False,
        wet_lab_ready=False,
        warnings=list(REVIEWER_PACKAGE_LIMITATIONS),
        limitations=list(REVIEWER_PACKAGE_LIMITATIONS),
    )

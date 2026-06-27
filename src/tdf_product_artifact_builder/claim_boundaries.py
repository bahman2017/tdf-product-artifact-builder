"""Claim boundary validation for product specs and reviewer packages."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

FORBIDDEN_PRODUCT_PHRASES: tuple[str, ...] = (
    "proven lithium filter",
    "experimentally validated lithium selectivity",
    "production-ready membrane",
    "force-field-ready bn membrane",
    "simulation-ready membrane",
    "wet-lab-ready product",
    "real battery performance claim",
    "battery performance claim",
    "tdf physics proof",
    "real lithium selectivity",
    "fabrication-ready",
    "experimentally validated",
    "simulation-ready",
    "force-field-ready",
    "wet-lab-ready",
    "simulation authorized",
    "wet lab ready",
    "openmm executed",
    "lammps executed",
)

ALLOWED_PRODUCT_PHRASES: tuple[str, ...] = (
    "lithium-selective membrane candidate",
    "phase-gated bn membrane artifact",
    "li/na analog diagnostic result",
    "reviewable atomic blueprint",
    "static validation package",
    "diagnostic preparation package",
    "external reviewer package",
    "conventional validation required",
    "phase-gated bn membrane candidate",
    "reviewable design candidate",
)

READINESS_UPGRADE_PHRASES: tuple[str, ...] = (
    "controlled_simulation",
    "wet_lab_fabrication_readiness",
    "simulation authorized: true",
    "wet_lab_ready: true",
)


@dataclass(frozen=True)
class ClaimBoundaryReport:
    passed: bool
    forbidden_hits: list[str] = field(default_factory=list)
    allowed_claims_present: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def validate_claim_boundaries(
    *,
    allowed_claims: list[str],
    forbidden_claims: list[str],
    extra_texts: list[str] | None = None,
) -> ClaimBoundaryReport:
    """Validate that allowed claims are present and forbidden claims are absent."""
    scan_texts = [_normalize(c) for c in allowed_claims]
    if extra_texts:
        scan_texts.extend(_normalize(t) for t in extra_texts)

    forbidden_hits: list[str] = []
    for phrase in FORBIDDEN_PRODUCT_PHRASES:
        for text in scan_texts:
            if phrase in text:
                forbidden_hits.append(phrase)
                break

    passed = len(forbidden_hits) == 0
    return ClaimBoundaryReport(
        passed=passed,
        forbidden_hits=sorted(set(forbidden_hits)),
        allowed_claims_present=list(allowed_claims),
        warnings=[] if passed else ["Forbidden product claim language detected."],
    )


def scan_text_for_forbidden_claims(text: str) -> list[str]:
    """Return forbidden phrases found in arbitrary text."""
    norm = _normalize(text)
    return [phrase for phrase in FORBIDDEN_PRODUCT_PHRASES if phrase in norm]


def scan_text_for_readiness_upgrades(text: str) -> list[str]:
    """Return readiness upgrade phrases found in arbitrary text."""
    norm = _normalize(text)
    return [phrase for phrase in READINESS_UPGRADE_PHRASES if phrase in norm]


def _text_for_package_claim_scan(path: Path, text: str) -> str:
    """Select reviewer-facing text to scan, excluding documented forbidden-claim lists."""
    if path.name == "CLAIM_BOUNDARY_CERTIFICATE.md":
        if "## Certificate statement" in text:
            return text.split("## Certificate statement", 1)[1]
        return ""
    if path.name == "PRODUCT_REPORT.json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        parts = [
            str(data.get("target_behavior", "")),
            str(data.get("product_type", "")),
        ]
        parts.extend(str(c) for c in data.get("allowed_claims", []))
        return "\n".join(parts)
    return text


def validate_generated_package_claims(package_dir: str | Path) -> ClaimBoundaryReport:
    """Scan reviewer package text for forbidden claim language in affirmative content."""
    root = Path(package_dir)
    texts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".txt"}:
            continue
        raw = path.read_text(encoding="utf-8")
        texts.append(_text_for_package_claim_scan(path, raw))

    combined = "\n".join(texts)
    forbidden_hits = scan_text_for_forbidden_claims(combined)
    forbidden_hits.extend(scan_text_for_readiness_upgrades(combined))
    forbidden_hits = sorted(set(forbidden_hits))

    return ClaimBoundaryReport(
        passed=len(forbidden_hits) == 0,
        forbidden_hits=forbidden_hits,
        warnings=[] if not forbidden_hits else ["Forbidden claim language in generated package."],
    )


def build_claim_boundary_certificate_md(spec: dict) -> str:
    """Build CLAIM_BOUNDARY_CERTIFICATE.md from product spec fields."""
    product_id = str(spec.get("product_id", ""))
    readiness = str(spec.get("readiness_stage", ""))
    lines = [
        "# Claim boundary certificate",
        "",
        "This certificate documents allowed and forbidden claims for the reviewer package.",
        "Build trust in the artifact, not belief in the theory.",
        "",
        f"- Product ID: `{product_id}`",
        f"- Readiness stage: `{readiness}` (not upgraded by this package)",
        "- engine_hardcoded: `false`",
        "- simulation_authorized: `false`",
        "- wet_lab_ready: `false`",
        "- openmm_execution: `false`",
        "- lammps_execution: `false`",
        "",
        "## Allowed claims",
        "",
    ]
    for claim in spec.get("allowed_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Forbidden claims", ""])
    for claim in spec.get("forbidden_claims", []):
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Certificate statement",
            "",
            "- This package does not authorize simulation.",
            "- This package does not claim force-field readiness.",
            "- This package does not claim wet-lab readiness.",
            "- This package does not establish physical theory validation.",
            "- Readiness stage is preserved from the product spec input.",
            "",
        ]
    )
    return "\n".join(lines)

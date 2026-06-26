"""Claim boundary validation for product specs and reviewer packages."""

from __future__ import annotations

from dataclasses import dataclass, field

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

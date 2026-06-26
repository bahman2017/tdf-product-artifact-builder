"""Claim boundary tests."""

from tdf_product_artifact_builder import scan_text_for_forbidden_claims, validate_claim_boundaries


def test_forbidden_claims_detected() -> None:
    report = validate_claim_boundaries(
        allowed_claims=["proven lithium filter"],
        forbidden_claims=["simulation-ready membrane"],
    )
    assert report.passed is False
    assert report.forbidden_hits


def test_clean_claims_pass() -> None:
    report = validate_claim_boundaries(
        allowed_claims=[
            "phase-gated BN membrane candidate",
            "conventional validation required",
        ],
        forbidden_claims=[
            "proven lithium filter",
            "simulation-ready membrane",
        ],
    )
    assert report.passed is True


def test_scan_text_for_simulation_ready() -> None:
    hits = scan_text_for_forbidden_claims("This is simulation-ready membrane product")
    assert "simulation-ready" in hits

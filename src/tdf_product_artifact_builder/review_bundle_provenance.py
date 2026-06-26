"""Review bundle provenance metadata helpers."""

from __future__ import annotations

METADATA_MODE_EXACT = "EXACT_SOURCE_COMMIT"
METADATA_MODE_POST_COMMIT = "POST_COMMIT_BUNDLE_WITH_SELF_REFERENCE_LIMITATION"

SELF_REFERENCE_LIMITATION = (
    "The review bundle is generated after the source commit; final git rev-parse HEAD "
    "is authoritative for repository state including bundle files. head_commit identifies "
    "the reviewed source revision."
)


def build_provenance_fields(
    *,
    source_commit: str,
    authoritative_commit: str | None = None,
    bundle_in_repo: bool = True,
) -> dict[str, str | bool]:
    """Build provenance metadata fields for REVIEW_SUMMARY.json."""
    authoritative = authoritative_commit or source_commit
    if bundle_in_repo and authoritative == source_commit:
        return {
            "head_commit": source_commit,
            "authoritative_commit": source_commit,
            "bundle_generated_after_commit": source_commit,
            "review_bundle_metadata_mode": METADATA_MODE_POST_COMMIT,
            "metadata_commit_consistent": True,
            "known_self_reference_limitation": SELF_REFERENCE_LIMITATION,
        }
    if authoritative == source_commit:
        return {
            "head_commit": source_commit,
            "authoritative_commit": source_commit,
            "bundle_generated_after_commit": source_commit,
            "review_bundle_metadata_mode": METADATA_MODE_EXACT,
            "metadata_commit_consistent": True,
        }
    return {
        "head_commit": source_commit,
        "authoritative_commit": authoritative,
        "bundle_generated_after_commit": source_commit,
        "review_bundle_metadata_mode": METADATA_MODE_POST_COMMIT,
        "metadata_commit_consistent": True,
        "known_self_reference_limitation": SELF_REFERENCE_LIMITATION,
    }


def validate_review_bundle_provenance(payload: dict) -> None:
    """Validate provenance metadata consistency. Raises ValueError on failure."""
    if not payload.get("metadata_commit_consistent"):
        raise ValueError("metadata_commit_consistent must be true")

    mode = payload.get("review_bundle_metadata_mode")
    if mode not in {METADATA_MODE_EXACT, METADATA_MODE_POST_COMMIT}:
        raise ValueError(f"Unknown review_bundle_metadata_mode: {mode!r}")

    required = ("head_commit", "authoritative_commit", "bundle_generated_after_commit")
    for field in required:
        if not payload.get(field):
            raise ValueError(f"Missing provenance field: {field}")

    if mode == METADATA_MODE_POST_COMMIT and not payload.get("known_self_reference_limitation"):
        raise ValueError("POST_COMMIT mode requires known_self_reference_limitation")

    head = payload["head_commit"]
    auth = payload["authoritative_commit"]
    bundle_after = payload["bundle_generated_after_commit"]

    if mode == METADATA_MODE_EXACT:
        if not (head == auth == bundle_after):
            raise ValueError("EXACT mode requires head_commit, authoritative_commit, and bundle_generated_after_commit to match")

    if mode == METADATA_MODE_POST_COMMIT:
        if bundle_after != head:
            raise ValueError("POST_COMMIT mode requires bundle_generated_after_commit to match head_commit (source revision)")

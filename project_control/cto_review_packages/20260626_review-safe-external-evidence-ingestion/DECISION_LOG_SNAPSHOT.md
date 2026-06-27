# Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-25 | Initialize `tdf-product-artifact-builder` as generic engine separate from product specs | Prevents lithium-specific logic in builder; enables multiple products |
| 2026-06-25 | Reference product `lithium_filter_candidate_v0_1` capped at `TDF_DESIGN_CANDIDATE` | Foundation must not imply simulation or wet-lab readiness |
| 2026-06-25 | No push/tag/release until CTO review | Controlled release chain per TDF governance |
| 2026-06-26 | PR #1 approved and merged into `main` | Foundation scope accepted; merge commit `0a67db9` |
| 2026-06-26 | Next task is CI/static policy foundation | Governance checks required before integration and product packages |
| 2026-06-27 | PR #2 approved and merged into `main` | CI/static policy scope accepted; merge commit `5076071` |
| 2026-06-27 | Next task is generic reviewer package builder hardening | Builder must be deterministic and claim-boundary safe before integration |
| 2026-06-27 | PR #3 approved and merged into `main` | Reviewer package builder scope accepted; merge commit `6976a32` |
| 2026-06-27 | Next task is tdf-openmm-validation integration contract layer only | Schemas and validators first; no execution integration or upstream imports |
| 2026-06-27 | PR #4 approved and merged into `main` | Evidence contract scope accepted; merge commit `6f726b9`; Unicode cleanup included |
| 2026-06-27 | Next task is review-safe external evidence ingestion workflow only | File-based ingestion of review-safe JSON; no runtime integration or simulation |

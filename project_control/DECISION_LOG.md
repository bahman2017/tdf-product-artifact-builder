# Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-25 | Initialize `tdf-product-artifact-builder` as generic engine separate from product specs | Prevents lithium-specific logic in builder; enables multiple products |
| 2026-06-25 | Reference product `lithium_filter_candidate_v0_1` capped at `TDF_DESIGN_CANDIDATE` | Foundation must not imply simulation or wet-lab readiness |
| 2026-06-25 | No push/tag/release until CTO review | Controlled release chain per TDF governance |

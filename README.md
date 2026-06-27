# tdf-product-artifact-builder

Public **productization and reviewer-package builder** for the TDF toolchain.

## What this is

This repository turns TDF-chain design artifacts into **reproducible, auditable, conventional product review packages**. It separates generic artifact-building logic from product-specific inputs represented as **product specs**.

**Motto:** Build trust in the artifact, not belief in the theory.

## What this is NOT

- Not a TDF physics proof repository
- Not a simulation repository
- Not a force-field validation repository
- Not a wet-lab or fabrication readiness package

## Architecture

| Layer | Role |
|-------|------|
| **Engine** | Generic artifact builder (`src/tdf_product_artifact_builder/`) |
| **Product specs** | Product-specific inputs under `product_specs/` |
| **Reviewer packages** | Static audit handoff outputs for external review |

The engine must remain **generic**. Product-specific behavior belongs only in product spec files -- never hard-coded in builder logic.

## First reference product

`lithium_filter_candidate_v0_1` is a **reference product spec only**, used to test the generic productization chain. It does not authorize simulation, wet-lab work, or physics claims.

## Install

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

## Project control

See `project_control/` for charter, roadmap, claim boundaries, and release chain status.

## License

MIT

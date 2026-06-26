# Project charter

## Final project goal

Build a **generic, reviewer-facing product artifact builder** that turns TDF-chain design outputs into reproducible, auditable, conventional product review packages — without proving TDF physics or authorizing simulation.

## Non-goals

- TDF physics proof or defense of new physics
- Simulation, MD, minimization, or dynamics
- LAMMPS or OpenMM execution
- Wet-lab, fabrication, or client dispatch packages
- Battery performance claims
- Real lithium selectivity claims

## Reviewer-native language

Products are described as **candidates**, **artifacts**, and **diagnostic preparation packages** requiring **conventional validation**. Reviewers receive static handoff bundles with manifests, claim boundaries, and explicit non-claims.

## Artifact trust model

Trust is built in **artifact integrity** (manifests, checksums, claim boundaries, reproducible structure) — not in theoretical belief. The motto: **Build trust in the artifact, not belief in the theory.**

## Product-readiness ladder

See `PRODUCT_READINESS_LADDER.md`. Foundation work must not exceed `TDF_DESIGN_CANDIDATE` for reference products.

## Explicit non-claims

This repository never claims:

- TDF physics validation
- Real ion selectivity or battery performance
- Simulation readiness or force-field readiness
- Wet-lab or fabrication readiness
- Experimental validation

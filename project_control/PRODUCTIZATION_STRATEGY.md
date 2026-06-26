# Productization strategy

## TDF chain as source of design artifacts

Upstream TDF packages (`tdf-core`, `tdf-iongate`, `tdf-atomic-blueprint`, `tdf-benchmark`, `tdf-openmm-validation`) produce **design and diagnostic artifacts**. They do not, by themselves, constitute product readiness.

## This repo as product artifact builder

`tdf-product-artifact-builder` is the **public productization layer**. It consumes artifact metadata and product specs to produce reviewer packages.

## Product specs as inputs

Each product is defined by a **product spec YAML** under `product_specs/`. Product-specific claims, readiness stage, and validation requirements live in the spec — not in engine code.

## Reviewer packages as outputs

Outputs are **static reviewer packages**: manifests, claim boundaries, limitations, and indexed artifacts suitable for external audit.

## Conventional validation path

Advancement on the readiness ladder requires **conventional independent validation** and explicit CTO approval. Simulation and wet-lab stages are gated and not authorized in foundation work.

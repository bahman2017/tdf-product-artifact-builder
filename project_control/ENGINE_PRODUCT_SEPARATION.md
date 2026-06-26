# Engine / product separation

## Rules

1. **Engine code must remain generic.** Builder logic in `src/tdf_product_artifact_builder/` must not branch on specific product IDs (e.g. lithium filter).
2. **No lithium-specific branching inside builder logic.** The string `lithium_filter` must not appear in engine Python modules.
3. **Product-specific behavior belongs only in product spec files** under `product_specs/`.
4. **Tests must detect forbidden hard-coded product coupling** via static scans of engine source.

## Allowed locations for product names

- `product_specs/` YAML files
- `project_control/` documentation and registry
- Tests that validate reference specs (not engine branching)
- README examples naming the reference product

## Forbidden locations

- Conditional logic in engine modules keyed on product ID
- Hard-coded lithium filter parameters in builder code
- Product-specific claim injection in generic manifest/checksum logic

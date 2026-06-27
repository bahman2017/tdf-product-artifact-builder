# Reviewer manifest schema audit

- Schema: `schemas/reviewer_manifest.schema.json`
- MANIFEST.json validates against schema in tests.
- CHECKSUMS.sha256.json matches generated content files.
- MANIFEST.json self-entry excluded to avoid circular hash.

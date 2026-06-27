# Evidence ingestion audit

- Schema: `schemas/evidence_ingestion_manifest.schema.json`
- CLI: `tools/ingest_evidence_directory.py`
- Review-safe directory ingestion only; no network or upstream imports.
- Outputs written to caller-specified directory (typically `/tmp`).
- Required safety flags enforced to false for all accepted evidence.

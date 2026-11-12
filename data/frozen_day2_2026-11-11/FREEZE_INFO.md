# Day 2 Frozen Dataset

**Freeze date:** 2026-11-11  
**Project:** Customer Support AI  
**Assistant:** Averse — the Customer Support AI

This directory is a dated, read-only-by-convention snapshot of the Day 2 knowledge-base disposition. The snapshot preserves approved, review, excluded and rejected passage records, the materialized retrieval set, source register, passage-level verification report, knowledge-base README, Day 2 report, supervisor review notes, validator and retrieval builder.

## Snapshot counts

- 23 `APPROVED`
- 2 `NEEDS_REVIEW` (KB027–KB028)
- 4 `EXCLUDED` (KB010, KB020–KB022; independent researcher scope decisions, not supervisor approvals)
- 0 `REJECTED`
- 18 retrieval-enabled records in `data/retrieval_passages.json`
- 29 total passage records and 15 registered sources
- All original IDs KB001–KB026 accounted for

## Reproducibility and integrity

- Run `python validate_knowledge_base.py` from this directory to reproduce the structural dataset validation.
- Run `python build_retrieval_dataset.py --check` to confirm the retrieval file equals the approved-and-enabled subset.
- Run `python create_freeze_manifest.py --verify` to validate the complete file set, sizes and SHA-256 values in `SHA256SUMS.csv`.
- Run `python create_freeze_manifest.py --create` to deterministically regenerate the sorted manifest after a deliberate snapshot change. Recreating the manifest does not itself validate factual accuracy.

`SHA256SUMS.csv` lists every payload file in this directory except itself. Any deliberate change to a frozen payload requires regenerating and rechecking the manifest; preserve the original snapshot when creating a new version.

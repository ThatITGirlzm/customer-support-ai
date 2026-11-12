# Customer Support AI

**Assistant name:** Averse — the Customer Support AI  
**Project scope:** English-language consumer information for Zambia, based only on approved passages from public Bank of Zambia sources.

Averse answers from the project’s approved, source-backed knowledge only. If supported information is missing, it says “not in the sources.” It does not generate free-form factual answers, access accounts, move money, or handle individual cases. Scam/fraud and human-help requests require a human referral with a reference number; the runtime referral workflow is not implemented yet.

## Current project state

- Day 2 knowledge-base audit is **partially complete**.
- Only `APPROVED` records with `retrieval_enabled: true` belong in retrieval. The checked materialized set is `data/retrieval_passages.json`.
- `NEEDS_REVIEW`, `EXCLUDED`, and `REJECTED` records are retained for audit and are not retrievable.
- The intent set is fixed at ten labels; details and Day 3 dataset rules are in the dataset specification.
- Day 3 datasets are generated: 250 training, 50 validation, and 110 held-out records. Their documented coverage limits mean retrieval-ranker evaluation still needs answerable validation/test queries.
- The classifier has not been trained or evaluated, and no backend routing behavior is implemented yet.

## Key files

- [Day 2 completion report](docs/DAY_2_COMPLETION_REPORT.md)
- [Knowledge-base README](docs/KNOWLEDGE_BASE_README.md)
- [Supervisor review items and evidence gaps](docs/SUPERVISOR_REVIEW_ITEMS.md)
- [Day 3 dataset specification](docs/DAY_3_DATASET_SPECIFICATION.md)
- [Day 3 readiness report](docs/DAY_3_READINESS_REPORT.md)
- [Day 3 dataset completion report](docs/DAY_3_DATASET_COMPLETION_REPORT.md)
- [Training dataset validator](scripts/validate_training_dataset.py)
- [Day 3 dataset builder](scripts/build_day3_datasets.py)
- [Knowledge-base validator](validate_knowledge_base.py)
- [Retrieval dataset builder](build_retrieval_dataset.py)

## Dataset checks

From the project root:

```powershell
python build_retrieval_dataset.py --check
python validate_knowledge_base.py
python scripts/validate_training_dataset.py
```

The validator checks structure, references, statuses, original passage ID coverage, sensitive-intent retrieval flags, and exact membership of the materialized retrieval set. It does not establish legal currentness or factual truth; those require source inspection.

# Customer Support AI

**Assistant name:** Averse — the Customer Support AI  
**Project scope:** English-language consumer information for Zambia, based only on approved passages from public Bank of Zambia sources.

Averse answers from the project’s approved, source-backed knowledge only. If supported information is missing, it says “not in the sources.” It does not generate free-form factual answers, access accounts, move money, or handle individual cases. Scam/fraud and human-help requests require a human referral with a reference number; the runtime referral workflow is not implemented yet.

## Current project state

- Day 2 knowledge-base audit is **partially complete**.
- Only `APPROVED` records with `retrieval_enabled: true` belong in retrieval. The checked materialized set is `data/retrieval_passages.json`.
- `NEEDS_REVIEW`, `EXCLUDED`, and `REJECTED` records are retained for audit and are not retrievable.
- The intent set is fixed at ten labels; details and Day 3 dataset rules are in the dataset specification.
- The frozen Day 3 v1.0.0 datasets remain at 250 training, 50 validation, and 110 held-out records. Current v1.1.0 data is isolated in `data/day3-v1.1.0/` with 275 training, 56 validation, and 120 held-out records.
- v1.1.0 includes separate retrieval-only sets at `data/answerable_validation.json` (15) and `data/answerable_test.json` (30). These were not used to train the classifier.
- From-scratch Naive Bayes and softmax classifiers have been fitted on v1.1.0 training questions and intent labels only. They have not been evaluated, and no backend routing behavior is implemented yet.

## Key files

- [Day 2 completion report](docs/DAY_2_COMPLETION_REPORT.md)
- [Knowledge-base README](docs/KNOWLEDGE_BASE_README.md)
- [Supervisor review items and evidence gaps](docs/SUPERVISOR_REVIEW_ITEMS.md)
- [Day 3 dataset specification](docs/DAY_3_DATASET_SPECIFICATION.md)
- [Day 3 readiness report](docs/DAY_3_READINESS_REPORT.md)
- [Day 3 dataset completion report](docs/DAY_3_DATASET_COMPLETION_REPORT.md)
- [Day 3 v1.1.0 dataset completion report](docs/DAY_3_DATASET_COMPLETION_REPORT_v1.1.0.md)
- [Training dataset validator](scripts/validate_training_dataset.py)
- [Day 3 v1.1.0 validator](scripts/validate_day3_v1_1.py)
- [Day 3 v1.1.0 classifier trainer](scripts/train_day3_v1_1_classifier.py)
- [Day 3 dataset builder](scripts/build_day3_datasets.py)
- [Knowledge-base validator](validate_knowledge_base.py)
- [Retrieval dataset builder](build_retrieval_dataset.py)

## Dataset checks

From the project root:

```powershell
python build_retrieval_dataset.py --check
python validate_knowledge_base.py
python scripts/validate_training_dataset.py
python scripts/validate_day3_v1_1.py
```

The validator checks structure, references, statuses, original passage ID coverage, sensitive-intent retrieval flags, and exact membership of the materialized retrieval set. It does not establish legal currentness or factual truth; those require source inspection.

# Customer Support AI

**Assistant name:** Averse — the Customer Support AI  
**Project scope:** English-language consumer information for Zambia, based only on approved passages from public Bank of Zambia sources.

Averse is a source-limited prototype. Until an approved answerability catalogue exists, ordinary requests abstain rather than produce factual banking answers. It does not access accounts, move money, submit complaints, or create official case references. Scam/fraud and human-help requests are routed to a safe human-assistance response; no external referral workflow is implemented.

## Current project state

- Day 2 knowledge-base audit is **partially complete**.
- Only `APPROVED` records with `retrieval_enabled: true` belong in retrieval. The checked materialized set is `data/retrieval_passages.json`.
- `NEEDS_REVIEW`, `EXCLUDED`, and `REJECTED` records are retained for audit and are not retrievable.
- The intent set is fixed at ten labels; details and Day 3 dataset rules are in the dataset specification.
- The frozen Day 3 v1.0.0 datasets remain at 250 training, 50 validation, and 110 held-out records. Current v1.1.0 data is isolated in `data/day3-v1.1.0/` with 275 training, 56 validation, and 120 held-out records.
- v1.1.0 includes separate retrieval-only sets at `data/answerable_validation.json` (15) and `data/answerable_test.json` (30). These were not used to train the classifier.
- Day 4 validation-only evaluation on the 56-record v1.1.0 validation split produced 51/56 correct for Naive Bayes and 11/56 for softmax; softmax predicted `out_of_scope` for every record. Naive Bayes is the leading experimental candidate, not production-ready. The softmax artifact is unsuitable for routing or safety decisions.
- The corrected preprocessing and classifiers are covered by the Day 4 test suite. The separately versioned artifact `data/models/day4-text-processing-v2/intent_models.json` is preserved unchanged after evaluation; the original v1.1.0 artifact is also preserved.
- The local FastAPI prototype under `app/` validates requests, runs safety preflight before classification/retrieval, blocks recognised injection attempts, isolates sensitive requests, and always abstains when no approved answer rule exists.
- The React Native/Expo client under `mobile/` calls only the ordinary request endpoint. It does not expose the local demonstration route, factual-answer actions, external referrals, or message history.

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
- [Day 4 Phase 1 completion report](docs/DAY_4_PHASE_1_COMPLETION_REPORT.md)
- [Day 4 Phase 2 classifier evaluation](docs/DAY_4_PHASE_2_CLASSIFIER_EVALUATION.md)
- [Day 4 closure report](docs/DAY_4_CLOSURE_REPORT.md)
- [Day 5 retrieval-engine completion report](docs/DAY_5_RETRIEVAL_ENGINE_COMPLETION_REPORT.md)
- [Day 6 local API and mobile-integration guide](docs/DAY_6_LOCAL_API_AND_DEPLOYMENT_GUIDE.md)
- [Mobile-app setup guide](mobile/README.md)
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

## Safe local prototype run

Install the pinned Python dependencies, then start the API on loopback only:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`GET /health` is available locally. The general request endpoint is `POST /api/v1/requests`. Keep the demonstration workflow disabled unless running an explicitly synthetic, local-only demonstration. Do not bind the API to a public interface or use it with real customer data.

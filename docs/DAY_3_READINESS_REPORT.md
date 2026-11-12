# Day 3 Dataset Readiness Report

**Project:** Customer Support AI  
**Assistant:** Averse — the Customer Support AI  
**Assessment date:** 2026-11-11

## Decision

**Ready to begin classifier development with the generated Day 3 datasets, subject to the coverage limits below.** The datasets are not a trained or evaluated classifier, and they do not yet support held-out retrieval-ranker evaluation. Day 2 remains **PARTIALLY COMPLETE**. The fixed ten intents and source gaps are preserved; review-only or excluded passages are not used as answer evidence.

## Day 3 dataset snapshot

The specification was finalized and the datasets were generated as UTF-8 JSON arrays:

- `data/training_examples.json`: 250 records (25 per fixed intent).
- `data/validation_examples.json`: 50 records (5 per fixed intent; an independent researcher planning decision).
- `data/test_examples.json`: 110 records: 80 baseline cases (8 per intent), 20 additional out-of-scope cases, and 10 separate prompt-injection cases.
- `data/dataset_metadata.json`: records dataset version, schema version, date, fixed intents, counts, seed, split method, evidence hashes and untrained/unevaluated model status.

`python scripts/validate_training_dataset.py` passed. It confirmed exact schemas and counts, fixed labels, unique IDs/questions, split and family separation, action rules, active passage/source references, metadata hashes, and safety collection rules. It checked 83,845 question pairs and found no suspicious near-duplicate pair at the specified 0.88 threshold. This is structural validation; the script does not prove semantic passage support or execute application routing.

Only 27 training records have source-backed answers. All in-scope validation and baseline test records without evidence use `ABSTAIN_NOT_IN_SOURCES`; there are no answerable validation or held-out baseline cases. The current splits can support initial intent-classifier development, but they cannot measure retrieval Recall@1/Recall@3 or test whether an answerability threshold preserves supported answers. Add separately curated, source-backed held-out retrieval examples before evaluating the ranker. No unsupported answer text was created.

## Day 2 snapshot and checks

The dated Day 2 freeze is `data/frozen_day2_2026-11-11/`. It contains the approved, review, excluded and rejected datasets; source register; passage verification report; knowledge-base README; Day 2 report; validator; and SHA-256 manifest. Use the freeze manifest’s `--verify` mode to check integrity and the frozen validator to reproduce the structural check.

The manifest covers 17 payload files; two consecutive `--create` runs generated the same bytes. `python create_freeze_manifest.py --verify` returned `PASS: verified 17 frozen files against SHA256SUMS.csv.` The frozen validator and retrieval dataset check also passed.

Workspace validation passed with this exact output:

```text
Knowledge-base structural validation
Records: 23 approved, 2 needing review, 4 excluded, 0 rejected; 18 retrieval-enabled.
Retrieval dataset records: 18.
Sources registered: 15; passage audit rows: 29.
Factual accuracy is not automatically verified by this script; it requires manual source inspection.
WARNING: Payment retrieval includes EFT/RTGS context; no approved current mobile-money how-to guidance is available (KB027 and KB028 remain review-only).
PASS: required files, schemas, original and unique IDs, source links, dispositions, retrieval dataset eligibility, sensitive-intent exclusions, dates, and audit coverage are structurally valid.
```

Current disposition counts: 23 `APPROVED`, 2 `NEEDS_REVIEW`, 4 `EXCLUDED`, 0 `REJECTED`; 18 records are retrieval-enabled. The separate `data/retrieval_passages.json` contains only approved and retrieval-enabled passages, and the validator checks exact equality with that eligible subset. All 26 original IDs remain accounted for; total passage records are 29 and source records are 15.

## Coverage available to ground future examples

| Fixed intent | Active retrieval passages | Coverage note |
|---|---:|---|
| `complaints_process` | 4 | Three-step Path to Justice passages plus one source-backed complaint/contact clarification. Does not establish current mobile-money complaint timelines. |
| `scam_fraud_warning` | 0 | Four source-backed passages exist but are deliberately disabled. Every such request must refer to a person before retrieval. |
| `consumer_rights` | 3 | Limited article-level consumer-protection material, not a comprehensive rights guide. |
| `payments_mobile_money` | 3 | KB012–KB013 describe EFT/RTGS context and KB029 gives a narrow oversight statement. No mobile-money how-to, fees, reversals, failed-transaction remedies or current complaint timeline. |
| `licensed_institutions` | 2 | Limited directory and commercial-bank supervision/licensing information. Directory presence is not a safety guarantee. |
| `financial_education` | 4 | Includes survey, campaign/event and historical information; keep dates and historical framing explicit. |
| `regulations_directives` | 0 | KB020–KB022 are excluded as applicant/operator requirements; no approved consumer-facing directive passage is active. |
| `contact_regulator` | 2 | General regulator contact information; not a formal complaint route. |
| `human_help_request` | 0 | Referral is an application workflow requirement, not a sourced knowledge claim. Runtime workflow is not implemented. |
| `out_of_scope` | 0 | Classification/decline behavior; no knowledge passage expected. |

The active retrieval set has 18 passages across six intents. This is evidence coverage, not a requirement that training examples use only those six labels. Examples for all ten intents may train classification, but unsupported in-scope requests must abstain rather than invent an answer.

## Open constraints before evaluation

- KB027–KB028 remain `NEEDS_REVIEW` because the current legal force of the July 2023 directives could not be established from the checked official BoZ evidence. Keep both outside training answer targets and retrieval.
- The remote SRC004 March 2025 PDF URL and contents remain unverified; do not use it for a new supported claim.
- The Day 2 schedule’s minimum of eight official sources is met, but the separate target of 25 distinct source items is not demonstrated. Do not count passages as sources.
- Sensitive referral-before-retrieval and reference-number creation are not implemented in `app/`. Day 3 tests can specify these required behaviors, but they cannot be reported as runtime-passed until the application exists.
- No decision in this report is supervisor approval. KB010 and KB020–KB022 are independent researcher exclusions and remain preserved for audit.

## Next Day 3 steps

1. Develop the from-scratch intent classifier using the training file; use validation for any threshold choices and keep all 110 held-out cases sealed until choices are frozen.
2. Before retrieval-ranker evaluation, curate source-backed validation and held-out queries with active passage references; do not change existing labels or invent answers to fill the gap.
3. Implement and separately test referral-before-retrieval, out-of-scope decline and injection blocking when the application exists. Dataset labels do not demonstrate runtime behavior.
4. Record model configuration and evaluation results only after the classifier and application are built and evaluated. Keep Day 2 marked partially complete until its open evidence issues are resolved through the approved review process.

# Day 3 Dataset Completion Report

**Formal project:** Customer Support AI  
**Assistant:** Averse  
**Dataset version:** `day3-v1.0.0`  
**Completion date:** 2026-11-11  
**Day 2 status:** **PARTIALLY COMPLETE** (unchanged)

## Outcome

The Day 3 specification was finalized, and the training, validation, and held-out test datasets were generated. Structural validation passed. The datasets are ready for initial classifier development; no classifier has been trained or evaluated. Dataset validation does not establish runtime routing, retrieval quality, or factual correctness beyond the manually checked passage links.

## Counts by intent and split

| Intent | Train | Validation | Test baseline | Additional OOS | Test total for intent |
|---|---:|---:|---:|---:|---:|
| `complaints_process` | 25 | 5 | 8 | 0 | 8 |
| `scam_fraud_warning` | 25 | 5 | 8 | 0 | 8 |
| `consumer_rights` | 25 | 5 | 8 | 0 | 8 |
| `payments_mobile_money` | 25 | 5 | 8 | 0 | 8 |
| `licensed_institutions` | 25 | 5 | 8 | 0 | 8 |
| `financial_education` | 25 | 5 | 8 | 0 | 8 |
| `regulations_directives` | 25 | 5 | 8 | 0 | 8 |
| `contact_regulator` | 25 | 5 | 8 | 0 | 8 |
| `human_help_request` | 25 | 5 | 8 | 0 | 8 |
| `out_of_scope` | 25 | 5 | 8 | 20 | 28 |
| **Intent-labelled total** | **250** | **50** | **80** | **20** | **100** |

The test file also contains 10 prompt-injection/adversarial safety cases with `intent: null`. Therefore `data/test_examples.json` has 110 records total: 80 baseline + 20 additional out-of-scope + 10 injection cases. The additional collections are separate from the baseline 80.

## Routing and evidence labels

| Dataset | `ANSWER_FROM_SOURCE` | `ABSTAIN_NOT_IN_SOURCES` | `REFER_HUMAN` | `DECLINE_OUT_OF_SCOPE` | `BLOCK_INJECTION` | Total |
|---|---:|---:|---:|---:|---:|---:|
| Training | 27 | 148 | 50 | 25 | 0 | 250 |
| Validation | 0 | 35 | 10 | 5 | 0 | 50 |
| Held-out test | 0 | 56 | 16 | 28 | 10 | 110 |

The two sensitive intents (`scam_fraud_warning` and `human_help_request`) always use `REFER_HUMAN` and carry no retrieval references. All `out_of_scope` examples use `DECLINE_OUT_OF_SCOPE`. Injection cases have null intent, use `BLOCK_INJECTION`, and have no passage/source references. In-scope questions without active supporting evidence retain their domain intent and use `ABSTAIN_NOT_IN_SOURCES`. Examples carry no generated factual answer text.

The 27 source-backed training questions were manually checked against their cited active retrieval passage text. Every referenced passage is `APPROVED` and retrieval-enabled; source IDs match the source register. The structural validator also confirms that no review-only, excluded, or rejected passage is used.

During final curation, three repeated complaint-path questions that asked for the same supported step were replaced with distinct questions whose answers are absent from active passages. Several cross-split prompts on complaints, consumer rights, financial education and regulator contacts were also reworded to remove same-question paraphrases. The expected routing actions were regenerated from the evidence references; no facts were added to fill missing coverage.

## Leakage and reproducibility controls

- Training, validation, and test are separate files with no duplicate example IDs or normalized exact duplicate questions across files.
- Question-family keys are stored in `annotation_note`; the validator confirms no family key crosses a split.
- A deterministic seed of `20261111` is recorded. Split membership is curated and stratified by intent/family before dataset generation; seeds `20261111`, `20261112`, and `20261113` only shuffle order within train, validation, and test, respectively. The held-out test has not been used for model fitting or threshold tuning.
- A normalized token-sequence near-duplicate scan at threshold `0.88` checked **83,845 pairs** and found **0 suspicious pairs**.
- The freeze-manifest SHA-256 for the Day 2 snapshot is `6e44f72d565f694cec47eb05fbec2d1726de88fba2aa49d011a708058a30a506`.
- Active retrieval dataset SHA-256: `be6e2104182827fb5065dadab82295007886695964a920183a895db467c7a193`.
- Source register SHA-256: `e4206b98835fb8f28ef272023554cd27f33068c86b12d5ccb9588b3d94e77d54`.
- Dataset file SHA-256 values and the source snapshot hashes are recorded in `data/dataset_metadata.json`.

## Validation result

Command: `python scripts/validate_training_dataset.py`

```text
Day 3 training, validation and test dataset validation
train: 250 total
  complaints_process: 25
  consumer_rights: 25
  contact_regulator: 25
  financial_education: 25
  human_help_request: 25
  licensed_institutions: 25
  out_of_scope: 25
  payments_mobile_money: 25
  regulations_directives: 25
  scam_fraud_warning: 25
validation: 50 total
  complaints_process: 5
  consumer_rights: 5
  contact_regulator: 5
  financial_education: 5
  human_help_request: 5
  licensed_institutions: 5
  out_of_scope: 5
  payments_mobile_money: 5
  regulations_directives: 5
  scam_fraud_warning: 5
test: 110 total
  complaints_process: 8
  consumer_rights: 8
  contact_regulator: 8
  financial_education: 8
  human_help_request: 8
  licensed_institutions: 8
  out_of_scope: 28
  payments_mobile_money: 8
  regulations_directives: 8
  scam_fraud_warning: 8
  collections: baseline=80, additional_out_of_scope=20, prompt_injection=10
Duplicate scan: 83845 pairs checked; 0 suspicious near-duplicate pairs (threshold 0.88).
PASS: exact schemas and counts, fixed intents, unique IDs/questions, split/family separation, actions, active passage/source references, metadata hashes, and safety collection rules are valid.
This validates dataset integrity and routing labels only; it does not train/evaluate a classifier or verify that cited passage text semantically answers every question.
```

## Coverage limits and readiness

- The 27 answerable examples are all in training. No validation or held-out baseline record currently tests retrieval of an answerable passage. Retrieval Recall@1/Recall@3, citation selection, and answerability-threshold performance therefore cannot be evaluated from these splits yet.
- Current approved retrieval coverage remains narrow: mobile-money instructions, current failed-transaction timelines, current e-money remedies, and consumer-facing directive guidance are not established in active passages. Related in-scope examples correctly abstain.
- All ten fixed intents are represented in every classifier split; training has 25 examples per intent and validation has 5 per intent. This supports initial classifier development, but classifier accuracy, thresholds, and generalization remain unmeasured.
- The validator checks structural and routing-label consistency. A curator must continue reviewing semantic fit of intents and passage support; application-level referral-before-retrieval and injection interception must be tested when implemented.

**Decision:** Ready for initial classifier development only. Not ready to claim classifier evaluation, retrieval-ranker evaluation, end-to-end safety, or Day 2 completion. Day 2 remains **PARTIALLY COMPLETE**.

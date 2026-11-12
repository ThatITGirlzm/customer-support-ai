# Day 3 Dataset Specification

**Project:** Customer Support AI  
**Assistant:** Averse — the Customer Support AI  
**Status:** Finalized for the Day 3 dataset build. Counts and split rules below are independent researcher decisions where the development schedule is silent.

## Purpose and fixed labels

The dataset will train and evaluate the from-scratch intent classifier. Labels are fixed to these ten values for the whole project:

1. `complaints_process`
2. `scam_fraud_warning`
3. `consumer_rights`
4. `payments_mobile_money`
5. `licensed_institutions`
6. `financial_education`
7. `regulations_directives`
8. `contact_regulator`
9. `human_help_request`
10. `out_of_scope`

Do not add synonyms as new labels. Preserve the English-only scope. Classification examples teach intent only; they do not authorize unsupported answers.

## Split targets

| Split | Planned size | Basis |
|---|---:|---|
| Train | Exactly 25 examples per intent; 250 total | Ten fixed intents × 25. Examples should vary meaningfully in wording while preserving intent. |
| Validation | Exactly 5 examples per intent; 50 total | Independent researcher planning decision because the schedule requires validation-based threshold selection but gives no validation count. |
| Held-out baseline test | At least 8 examples per intent; 80 baseline examples | Ten fixed intents × 8. These 80 include 8 `out_of_scope` examples. |
| Additional held-out out-of-scope collection | 20 examples | Separate from the baseline 80; all have `out_of_scope` and `DECLINE_OUT_OF_SCOPE`. |
| Additional prompt-injection/adversarial safety collection | 10 examples | Separate from the baseline 80 and the additional 20 OOS cases; all use `intent: null` and `BLOCK_INJECTION`, not an eleventh label. |
| Total held-out test | 110 examples | 80 baseline + 20 additional out-of-scope + 10 prompt-injection/adversarial safety cases. |

The 20 additional out-of-scope cases and 10 injection cases are distinct records outside the baseline 80. In the test file, identify them with `scenario_type: "additional_out_of_scope"` and `scenario_type: "prompt_injection"`; the baseline 80 use `scenario_type: "baseline_classification"`. Keep the held-out test untouched during vocabulary construction, feature selection, model fitting, threshold selection and rule tuning. Use validation data for thresholds. Never duplicate questions to inflate counts.

## Example record schema

The requested dataset files are UTF-8 JSON arrays. Each example has exactly these fields:

| Field | Type | Rule |
|---|---|---|
| `example_id` | string | Stable unique ID within a dataset version. |
| `question` | string | One English user request; no real personal, account, card or transaction data. |
| `split` | string | Exactly `train`, `validation` or `test`. |
| `intent` | string or null | One of the ten fixed labels. Null only for safety-only injection cases that are intercepted before classification. |
| `scenario_type` | string | Exactly one of `ordinary`, `sensitive_referral`, `out_of_scope`, `baseline_classification`, `additional_out_of_scope`, `prompt_injection`; controlled vocabulary to be versioned. |
| `expected_action` | string | One of `ANSWER_FROM_SOURCE`, `ABSTAIN_NOT_IN_SOURCES`, `REFER_HUMAN`, `DECLINE_OUT_OF_SCOPE`, `BLOCK_INJECTION`. |
| `supporting_passage_ids` | array of strings | Empty when no sourced answer is expected; otherwise IDs must exist in `data/retrieval_passages.json`. |
| `source_ids` | array of strings | BoZ source IDs corresponding to the cited supporting passages; must match the source register. |
| `annotation_note` | string | Short rationale for ambiguous labels or edge cases; never a substitute for source evidence. |

No example may contain an answer that is not already supported by its referenced approved passage. Training examples do not contain free-form gold answers. The eventual answer builder must select approved passage text and use fixed, reviewed response templates for routing and abstention.

## Annotation and safety rules

- Intent classification, answer retrieval and the final action are separate decisions. A valid in-scope intent does not imply that answer evidence exists. Retrieval may use only active approved passages; if none supports the request, preserve its domain intent and use `ABSTAIN_NOT_IN_SOURCES`.
- Do not invent factual answers, policies, contacts, numbers or advice to compensate for missing passages. The dataset contains requests and expected actions, not generated answers.
- Requests about scams or fraud receive `scam_fraud_warning` and `REFER_HUMAN` regardless of whether a knowledge passage exists. They must not use ordinary knowledge retrieval.
- Requests explicitly asking for a person or human assistance receive `human_help_request` and `REFER_HUMAN`.
- An injection attempt is intercepted by the pre-classification safety check and gets `BLOCK_INJECTION`. It is not an extra classifier label and must not reach the classifier or retrieval or override the approved-source-only rule. In the test file, its separate safety collection is identified by `scenario_type: "prompt_injection"` and `intent: null`.
- Requests outside the project scope receive `out_of_scope` and `DECLINE_OUT_OF_SCOPE`.
- An in-scope question whose answer is absent from approved retrieval passages retains its domain intent and gets `ABSTAIN_NOT_IN_SOURCES`; do not relabel missing evidence as out of scope.
- Only `ANSWER_FROM_SOURCE` examples may reference passage IDs, and every referenced ID must be in the active retrieval dataset. Never reference `NEEDS_REVIEW`, `EXCLUDED`, `REJECTED`, disabled or backup records.
- Do not include actual names, phone numbers, account identifiers, card numbers, credentials, one-time codes or identifiable case narratives. Use synthetic, non-sensitive wording for routing tests.

## Quality checks before splitting and training

1. Validate the schema, exact intent vocabulary, expected action and field types.
2. Verify unique IDs, non-empty questions, valid passage/source references and active approval/retrieval status.
3. Normalize case, punctuation and whitespace for exact duplicate detection. The validator flags suspicious near-duplicates when normalized token-sequence similarity is at least 0.88; inspect and resolve every flag. Keep paraphrases of the same underlying question in one split; record family keys in `annotation_note` so split leakage can be checked without adding schema fields.
4. Check intent counts and action/intent consistency, especially referral and injection cases.
5. Group examples derived from the same base question or source scenario before splitting. Do not place paraphrases of the same request in different splits.
6. Record annotation changes and dataset versions; do not silently overwrite an evaluated dataset.

## From-scratch constraints

Implement tokenization, features, Naive Bayes, softmax regression, confidence thresholds, retrieval scoring and evaluation in project code using Python’s standard library and NumPy only. Do not use scikit-learn, PyTorch, transformers, pretrained models or AI APIs in model code. Keep evaluation deterministic with a recorded random seed. The held-out set must not influence vocabulary, feature weights, thresholds or model choices.

## Evaluation plan

Report, at minimum:

- Per-intent precision, recall and F1; macro-F1; confusion matrix; and overall accuracy.
- Out-of-scope precision/recall and false-acceptance rate.
- Sensitive referral recall and false-negative count for both sensitive intents; target zero sensitive requests reaching retrieval.
- Injection block rate and count of injection cases that reach classifier or retrieval; target zero bypasses.
- Retrieval Recall@1 and Recall@3, plus top-result relevance for answerable source-backed queries.
- Citation/source match correctness and the rate of unsupported answers; target zero unsupported factual claims.
- Correct abstention rate for in-scope questions with no eligible passage.

Use validation results to select confidence/abstention thresholds. Report held-out metrics only after all choices are frozen. Do not claim that high intent accuracy establishes factual correctness or current legal status.

## Version record to keep with the dataset

Record the dataset version, schema version, collection date, split method and random seed, per-intent counts, annotation rules version, frozen Day 2 dataset/manifest hash, active passage snapshot hash, source register hash, tokenizer version, model configuration, thresholds and evaluation command. Changing sources, labels, text normalization, examples, splits or safety logic creates a new version and requires reevaluation.

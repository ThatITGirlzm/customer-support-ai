# Day 4 Closure Report — Classifier Error Analysis

**Project:** Customer Support AI  
**Assistant:** Averse  
**Closure review date:** 2026-11-14  
**Scope:** Verification, validation-result analysis, and documentation only.

## 1. Objective and scope

This report closes the Day 4 classifier evaluation/documentation milestone by checking the recorded validation results against the current pinned evaluator, reviewing the five Naive Bayes mistakes, examining the softmax failure, and verifying stored hashes. No classifier code, preprocessing, weights, priors, datasets, metadata, or knowledge-base files were changed. No held-out test questions were opened or inspected, and no test-set evaluation was run.

## 2. Evaluation setup and artifacts

The evaluated classifier dataset is `day3-v1.1.0`. The evaluator entry point, `scripts/evaluate_day4_validation.py`, pins `data/day3-v1.1.0/validation_examples.json` and the Day 4 model artifact by SHA-256. It passes only those two file paths to `ml.evaluation.evaluate_files`; it does not refer to the training file, classifier test file, or retrieval evaluation collections. The model artifact's embedded training-file fingerprint is checked as a JSON field; the trainer input file is not opened by evaluation.

| Artifact | SHA-256 |
|---|---|
| Validation records (`data/day3-v1.1.0/validation_examples.json`) | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` |
| Day 4 model (`data/models/day4-text-processing-v2/intent_models.json`) | `728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12` |

The fresh evaluator run verified 56 validation records and reproduced 51 correct Naive Bayes predictions, 11 correct softmax predictions, and the same learned-prior/equal-prior Naive Bayes predictions and metrics recorded in the Phase 2 report. Evaluation outputs are deterministic; the Phase 2 report records identical output hashes from two successive runs.

The model uses the saved 725-term vocabulary and `TEXT_PROCESSING_VERSION` 2.0.0. Error feature evidence below was computed from the five validation questions, the shared preprocessing pipeline, and frozen Naive Bayes log-likelihoods. It does not inspect training question text or alter any model parameter.

## 3. Naive Bayes results and five errors

Naive Bayes classified **51/56** records correctly: accuracy **91.07%**, macro precision **93.06%**, macro recall **90.00%**, and macro F1 **90.20%**. All five mistakes are between related consumer-support topics; none is an out-of-scope or safety-intent error.

| Validation ID | Actual → predicted | Adjacent? | P(predicted) / P(actual) | Model/record evidence and likely weakness | Safety implication |
|---|---|---|---:|---|---|
| `VAL-CO-002` | `contact_regulator` → `complaints_process` | Yes | 0.6873 / 0.2805 | The question asks about a visitor appointment at BoZ Head Office. `appointment` and `going` are outside the saved vocabulary. In the frozen NB score, `before`, stemmed `requir`, and `head` favor the predicted class; `visitor`, `office`, and `regulator` favor the actual class. This suggests a vocabulary/cue coverage and class-overlap weakness. | None directly; not a scam/fraud or human-help record. |
| `VAL-CR-005` | `consumer_rights` → `complaints_process` | Yes | 0.3950 / 0.0057 | The question asks for a copy of an investigation report. `investigation` is outside the vocabulary. Among retained terms, `i`, `provider`, `can`, and `ask` favor complaints; `copy`, `its`, and `report` provide little score separation for consumer rights. This points to weak distinguishing evidence and retained generic terms, not a proven dataset-label issue. | None directly. |
| `VAL-CO-004` | `contact_regulator` → `complaints_process` | Yes | 0.8182 / 0.1125 | The question asks whether the website has an after-hours emergency contact for financial complaints. `website` and `emergency` are outside the vocabulary, while `complaint` strongly favors the predicted class. `contact`, `doe`, and `hour` favor the actual class but do not overcome it. This is direct lexical overlap plus missing distinguishing vocabulary. | None directly. |
| `VAL-LI-005` | `licensed_institutions` → `contact_regulator` | Yes | 0.4451 / 0.4243 | The question concerns correcting a firm's address in the public register. `correct` is outside the vocabulary. The learned prior favors `contact_regulator` over `licensed_institutions` by only 0.0408 log units; the total NB score margin is 0.0478, so the likelihood difference is also small. `regulator`, `public`, and `address` favor contact; `register` and `firm` favor licensed institutions. This is a near-boundary class/vocabulary distinction. Equal priors still produce the same incorrect class. | None directly. |
| `VAL-CR-004` | `consumer_rights` → `complaints_process` | Yes | 0.6141 / 0.0382 | No question token is out of vocabulary. The retained terms `it`, `must`, `why`, and the one-letter token `s` from the possessive form favor complaints in the saved NB likelihoods; `account` favors consumer rights but is insufficient. This indicates a possible feature-weight/stop-word and possessive-token limitation, as well as adjacent class overlap. | None directly. |

The token evidence identifies which saved lexical likelihoods distinguish the winning and true classes; it does not prove which training examples created those likelihoods. No training-text review or causal feature attribution was performed. The errors show complaints were over-predicted: nine questions were assigned that class despite five true complaint-process records.

### Safety-focused error analysis

- None of the five Naive Bayes mistakes has actual intent `scam_fraud_warning` or `human_help_request`.
- Naive Bayes correctly classified all five validation records in each of those two classes.
- No record from another intent was incorrectly predicted as either `scam_fraud_warning` or `human_help_request` by Naive Bayes.
- These are small samples of five examples per intent. Zero observed errors do **not** establish reliable safety performance.
- Softmax has a different and serious result: all five scam/fraud and all five human-help records were assigned `out_of_scope`. If a runtime relied on softmax alone, those records would not receive their intended classifier labels. The independent pre-classifier safety/referral check remains essential and was not evaluated here.

## 4. Softmax regression failure

The current softmax artifact predicted `out_of_scope` for **all 56/56** validation questions: the 11 actual out-of-scope records were correct and all 45 records from the other nine intents were incorrect. It produced zero predictions for each of those nine classes.

Its probability outputs were valid: all values were finite and in `[0, 1]`, with maximum absolute row-sum error `2.22e-16`. The output is nevertheless weakly separated. Maximum-class confidence ranged from **0.1795** to **0.2334** (median **0.1917**); 41 records were below 0.20 and the remaining 15 were below 0.40. Thus the repeated OOS decision is not a high-confidence rejection.

Observed parameter and data facts:

- Training class counts stored in the artifact are 54 for `out_of_scope` and 23–25 for each other class.
- The fitted softmax OOS bias is `+0.6937`; other class biases range from `-0.1375` to `-0.0553`.
- Validation feature coverage is not empty: all 56 questions have at least one in-vocabulary token. Across 511 preprocessed validation tokens, 428 (83.6%) occur in the saved vocabulary; 83 (16.4%) do not.

The out-of-scope intercept dominating every decision is an observed scoring behavior. Its association with the larger OOS training class is plausible, and weak feature evidence/coverage may contribute. The available evidence does not establish a single root cause or distinguish class imbalance from optimization/convergence, parameter learning, or feature representation. No training-loss trace or controlled diagnostic experiment was available. The current softmax artifact must therefore **not** be used for intent routing or safety decisions. It is preserved unchanged; no repair or retraining was attempted.

## 5. Learned-prior comparison

The learned-prior and equal-prior Naive Bayes variants produced identical predictions for **56/56** validation records, identical confusion matrices, and identical accuracy and macro metrics. Mean maximum confidence was 0.8237 with learned priors and 0.8119 with equal priors. This only describes this validation set; it does not establish that priors never affect predictions on other inputs.

Softmax has no separate prior term that can be cleanly replaced while leaving its learned discriminative weights/intercepts interpretable as unchanged. No artificial equal-prior softmax variant was evaluated.

## 6. Current classifier position and limitations

- **Naive Bayes** is the leading experimental candidate on this validation collection. It is not production-ready or fully validated. Its five mistakes, small per-intent sample sizes, and limited evidence of safety performance preclude a reliability claim. It may not authorize an answer or bypass approved-passage retrieval/evidence checks.
- **Softmax regression** is unsuitable for current intent routing and safety decisions based on the all-OOS validation result. Preserve the artifact and its hash; do not silently replace it.
- The validation set has only five examples for each non-OOS intent and eleven OOS examples. One error changes recall by 20 percentage points for a five-record class. The curated validation result is not a population estimate. Probability normalization is not calibration.
- The observed NB lexical contributions suggest testable preprocessing/vocabulary and class-boundary weaknesses, but this analysis does not establish a corrected feature set or label change.

## 7. Dataset, test-set, and artifact integrity

The following current SHA-256 values match the hashes recorded before Day 4 Phase 1 changes. For both v1.0.0 and v1.1.0, the training, validation, and test file hashes also match the respective dataset metadata `file_sha256` entries. Hash verification read files as bytes only; no held-out question text was displayed or inspected.

| Artifact | SHA-256 | Result |
|---|---|---|
| v1.0.0 training `data/training_examples.json` | `e753ffdeea81d81665dc8423ca8dbe1ff206c7f68b0808840567c7b468fd372c` | Match |
| v1.0.0 validation `data/validation_examples.json` | `50b3b4cb1f05f8e03d1043a9b2a90fd9b15f6c331c98d609495a813b7b21caa6` | Match |
| v1.0.0 test `data/test_examples.json` | `b26ef4d157936a00063e07d419f4f32f581c4219f892410296c8f535c24804aa` | Match |
| v1.0.0 metadata `data/dataset_metadata.json` | `0fe81ff65295f1d7684c7bce14fa3e5382cf3ec20d3e725dd34abf473c4227d6` | Match |
| v1.1.0 training | `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a` | Match |
| v1.1.0 validation | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` | Match |
| v1.1.0 classifier test | `b32b616019e1fed5041d7d8cb868f5a4b678f7c866d18cb533b7ac8ef9d32c2c` | Match |
| v1.1.0 metadata | `16c724aa089c9ce7d74709a0bb47644d6349df03ac560c38f6a0ae04133979ca` | Match |
| Retrieval validation `data/answerable_validation.json` | `2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd` | Match |
| Retrieval test `data/answerable_test.json` | `25f928c28c62df98be87c8c0bc17fd69d0ee94eedc3e53ad5fe32fc526dcb56c` | Match |
| Original v1.1.0 model `data/day3-v1.1.0/intent_models.json` | `372235355b4df7c45c95a5f3b856dafcb61447a104c99ce4b12c5612186b0cc7` | Match |
| Day 4 model `data/models/day4-text-processing-v2/intent_models.json` | `728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12` | Match |

The current trainer's production entry point reads only the v1.1.0 training file and selects `question` and `intent`; its synthetic isolation tests reject access to validation, test, and metadata fixtures. Phase 1 records the training command output and the artifact's matching training-data fingerprint. The trainer records no validation/test file hashes and performs no validation-based tuning. The evaluation CLI pins the validation path/hash and contains no path to the classifier test file or retrieval test collection; the evaluator's synthetic access test confirms only its supplied model and validation files are read. No retrieval dataset is referenced by evaluation.

These repository records support that the documented training/evaluation workflow did not use the held-out classifier or retrieval test sets. Matching baseline hashes establish that their current bytes are unchanged since the recorded baseline. No operating-system-level file-access logs were supplied for this review, so it cannot prove that no manual or external process accessed those files outside the recorded workflow. No test-set predictions, metrics, or model-selection decisions were made.

## 8. Outstanding risks and unresolved questions

- Why the softmax OOS intercept dominates every validation decision remains unresolved. A separate controlled diagnostic phase would be needed; this closure did not tune or test candidate fixes.
- Naive Bayes's perfect observed recall on scam and human-help has only five examples per class and is not a safety guarantee.
- The examples show that unseen terms and retained generic/possessive tokens can affect NB scores. No preprocessing or vocabulary changes were made; any future change requires a separately approved training/evaluation plan.
- No real-world, retrieval-answer, threshold, calibration, or held-out test performance is established.
- No historical OS-level audit trail is available to prove non-access beyond the recorded code/configuration and executions.

## 9. Day 4 closure decision and next milestone

**Day 4's classifier-evaluation and documentation milestone is closed.** The validation-only comparison, complete five-error analysis, softmax failure documentation, prior comparison, tests, and byte-integrity checks are recorded. This closure does not mean the classifier subsystem is production-ready: softmax remains unsuitable, Naive Bayes remains experimental, and safety performance is not proven.

The next project milestone is **Day 5: retrieval engine development**. It has not been started in this task. Any future retrieval answer must remain limited to approved passages, with abstention and independent sensitive-case referral controls.

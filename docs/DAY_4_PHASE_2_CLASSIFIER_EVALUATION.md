# Day 4 Phase 2 — Classifier Evaluation

**Project:** Customer Support AI  
**Assistant:** Averse  
**Evaluation date:** 2026-11-14  
**Status:** Validation-only evaluation complete; no model or dataset changes made.

## Executive result

The evaluation used the pinned 56-record v1.1.0 validation collection and the frozen Day 4 model artifact. Naive Bayes classified 51/56 records correctly (91.07% accuracy; 0.9020 macro F1). Softmax regression classified 11/56 correctly (19.64% accuracy; 0.0328 macro F1) and predicted `out_of_scope` for every validation question. Its output probabilities were normalized but low-confidence and close to uniform. This is a serious performance failure; softmax should not route intents or sensitive referrals in its current form.

Naive Bayes with learned and equal priors made the same prediction on all 56 records. The validation set is small and curated, so these results are descriptive for this dataset, not a production-readiness claim or a population performance estimate.

## 1. Inspection and frozen inputs

At the start of this phase, `HEAD` was `732faf3a301006f6dc1e788dae1127013845b898` on `main`. The working tree already contained the unstaged Day 4 Phase 1 changes reported in `DAY_4_PHASE_1_COMPLETION_REPORT.md`; they were preserved. No commit, tag, dataset edit, metadata edit, retraining, or model edit was performed in this phase.

The Phase 1 report, `ml/intent_classifier.py`, `ml/text_processing.py`, `scripts/train_day3_v1_1_classifier.py`, the model artifact, v1.1.0 metadata, and `scripts/validate_day3_v1_1.py` were inspected. The existing configuration was recorded without changing it:

- Dataset: `day3-v1.1.0`; 275 training records, 56 validation records, 120 held-out test records.
- Preprocessing: shared `preprocess_text`, version `2.0.0`.
- Naive Bayes: multinomial, Laplace `alpha=1.0`.
- Softmax: batch gradient descent, learning rate `0.2`, 400 epochs, L2 `0.0001`, seed `20261112`; seeded normal initialization (mean 0, standard deviation 0.01), zero bias initialization.
- Training-data fingerprint embedded in the model: `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a`.

The evaluated model is `data/models/day4-text-processing-v2/intent_models.json`, SHA-256:

`728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12`

The validation input is `data/day3-v1.1.0/validation_examples.json`, SHA-256:

`75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89`

The validation hash matches `file_sha256.validation_examples.json` in the frozen v1.1.0 metadata. It has exactly 56 records and the v1.1.0 schema: `example_id`, `question`, `split`, `intent`, `scenario_type`, `expected_action`, `supporting_passage_ids`, `source_ids`, `annotation_note`, with `rewritten_from` present where applicable. Intent support is five records each for nine intents and eleven for `out_of_scope`.

The evaluator reads only the explicitly supplied validation file and model artifact. Its CLI pins both file paths and their expected SHA-256 values; it also checks the training fingerprint stored inside the model without opening the training file. There is no training or held-out-test dataset path in the CLI. A synthetic file-access test denies access to decoy training and test files and confirms that evaluation reads only the supplied model and validation fixture. The real held-out test file was not opened or inspected.

`TextVectorizer.transform` uses `ml.text_processing.preprocess_text`, the same versioned pipeline used to construct the saved vocabulary during training. The evaluator restores the serialized vocabulary and fitted classifier parameters, validates their dimensions/configuration, and calls prediction methods; it does not call `fit` or alter the artifact. `expected_action` and other annotation fields are not used as model inputs or labels.

## 2. Evaluation methodology

The fixed class and matrix order is:

`complaints_process`, `scam_fraud_warning`, `consumer_rights`, `payments_mobile_money`, `licensed_institutions`, `financial_education`, `regulations_directives`, `contact_regulator`, `human_help_request`, `out_of_scope`.

The NumPy-only metrics implementation calculates accuracy, per-intent precision/recall/F1, fixed-label macro averages, and a confusion matrix with actual classes as rows and predicted classes as columns. All ten fixed intents are included in macro averages. If a class has no predicted records, precision is reported as `0.0` with `precision_defined=false`; if it has no true support, recall is reported as `0.0` with `recall_defined=false`. Undefined F1 is also `0.0` with `f1_defined=false`. Thus undefined values are explicit and do not silently remove a class from a macro average. In this validation set every class has true support; softmax predicts zero records for nine classes.

Probability matrices are checked for finite values in `[0, 1]`, the expected 56-by-10 shape, and row sums within absolute tolerance `1e-9`. Confidence is the maximum class probability per record. Its distribution is summarized by min, quartiles, median, mean, max, and fixed 0.20-wide bins. These confidence figures are descriptive; no calibration or threshold analysis was performed.

For the prior comparison, the evaluator scores the same Naive Bayes feature matrix and frozen log-likelihoods twice: once with serialized learned log priors and once with equal log priors `-log(10)`. It does not mutate the saved model. Softmax has no separately identifiable prior parameter: its learned bias/intercepts and weights jointly define class scores. Therefore no artificial equal-prior softmax variant was created.

## 3. Overall results

| Model/scoring variant | Correct / total | Incorrect | Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Naive Bayes, learned priors | 51 / 56 | 5 | 91.07% | 93.06% | 90.00% | 90.20% |
| Naive Bayes, equal priors | 51 / 56 | 5 | 91.07% | 93.06% | 90.00% | 90.20% |
| Softmax regression, saved parameters | 11 / 56 | 45 | 19.64% | 1.96% | 10.00% | 3.28% |

The two Naive Bayes variants produced exactly the same predicted intent for all 56 records and have identical confusion matrices and classification metrics. The learned-prior setting changed probability values and confidence, not the winning class decisions.

### Per-intent results

`P`, `R`, and `F1` are percentages. Softmax's precision and F1 are marked `0.00*` for classes it never predicted; these zero values are included in the ten-class macro averages.

| Intent | Support | NB P | NB R | NB F1 | Softmax P | Softmax R | Softmax F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| complaints_process | 5 | 55.56 | 100.00 | 71.43 | 0.00* | 0.00 | 0.00* |
| scam_fraud_warning | 5 | 100.00 | 100.00 | 100.00 | 0.00* | 0.00 | 0.00* |
| consumer_rights | 5 | 100.00 | 60.00 | 75.00 | 0.00* | 0.00 | 0.00* |
| payments_mobile_money | 5 | 100.00 | 100.00 | 100.00 | 0.00* | 0.00 | 0.00* |
| licensed_institutions | 5 | 100.00 | 80.00 | 88.89 | 0.00* | 0.00 | 0.00* |
| financial_education | 5 | 100.00 | 100.00 | 100.00 | 0.00* | 0.00 | 0.00* |
| regulations_directives | 5 | 100.00 | 100.00 | 100.00 | 0.00* | 0.00 | 0.00* |
| contact_regulator | 5 | 75.00 | 60.00 | 66.67 | 0.00* | 0.00 | 0.00* |
| human_help_request | 5 | 100.00 | 100.00 | 100.00 | 0.00* | 0.00 | 0.00* |
| out_of_scope | 11 | 100.00 | 100.00 | 100.00 | 19.64 | 100.00 | 32.84 |

## 4. Confusion matrices

Abbreviations: CP=`complaints_process`, SF=`scam_fraud_warning`, CR=`consumer_rights`, PM=`payments_mobile_money`, LI=`licensed_institutions`, FE=`financial_education`, RD=`regulations_directives`, CO=`contact_regulator`, HH=`human_help_request`, OOS=`out_of_scope`. Each row below is an actual intent; vector entries are predicted counts in column order `[CP, SF, CR, PM, LI, FE, RD, CO, HH, OOS]`.

### Naive Bayes, learned priors

The equal-prior matrix is identical.

| Actual | Predicted-count vector |
|---|---|
| CP | `[5, 0, 0, 0, 0, 0, 0, 0, 0, 0]` |
| SF | `[0, 5, 0, 0, 0, 0, 0, 0, 0, 0]` |
| CR | `[2, 0, 3, 0, 0, 0, 0, 0, 0, 0]` |
| PM | `[0, 0, 0, 5, 0, 0, 0, 0, 0, 0]` |
| LI | `[0, 0, 0, 0, 4, 0, 0, 1, 0, 0]` |
| FE | `[0, 0, 0, 0, 0, 5, 0, 0, 0, 0]` |
| RD | `[0, 0, 0, 0, 0, 0, 5, 0, 0, 0]` |
| CO | `[2, 0, 0, 0, 0, 0, 0, 3, 0, 0]` |
| HH | `[0, 0, 0, 0, 0, 0, 0, 0, 5, 0]` |
| OOS | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 11]` |

### Softmax regression

| Actual | Predicted-count vector |
|---|---|
| CP | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| SF | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| CR | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| PM | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| LI | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| FE | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| RD | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| CO | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| HH | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 5]` |
| OOS | `[0, 0, 0, 0, 0, 0, 0, 0, 0, 11]` |

## 5. Probability validity and confidence

All three evaluated probability matrices were finite, within `[0, 1]`, and normalized to one per row. Maximum absolute row-sum errors were `6.88e-15` for learned-prior Naive Bayes, `4.44e-16` for equal-prior Naive Bayes, and `2.22e-16` for softmax.

| Variant | Min | Q25 | Median | Mean | Q75 | Max | Counts in bins `[0,.2)`, `[.2,.4)`, `[.4,.6)`, `[.6,.8)`, `[.8,1]` |
|---|---:|---:|---:|---:|---:|---:|---|
| NB, learned priors | 0.3950 | 0.7345 | 0.8857 | 0.8237 | 0.9757 | 0.9998 | 0, 1, 10, 8, 37 |
| NB, equal priors | 0.2965 | 0.6789 | 0.8654 | 0.8119 | 0.9770 | 0.9998 | 0, 1, 10, 10, 35 |
| Softmax | 0.1795 | 0.1875 | 0.1917 | 0.1969 | 0.2012 | 0.2334 | 41, 15, 0, 0, 0 |

Softmax's class probabilities are valid mathematically but provide little separation: its maximum confidence is only 0.2334, and 41/56 predictions have maximum probability below 0.20. Choosing OOS every time should not be mistaken for confident rejection.

## 6. Misclassification analysis

### Naive Bayes errors

| ID | Actual → predicted | Confidence / P(predicted) | P(actual) | Other leading class | Likely explanation |
|---|---|---:|---:|---|---|
| VAL-CO-002 | contact_regulator → complaints_process | 0.6873 | 0.2805 | consumer_rights 0.0226 | A general regulator visit/appointment enquiry may overlap broad public-help and complaint language; no exact appointment cue wins. |
| VAL-CR-005 | consumer_rights → complaints_process | 0.3950 | 0.0057 | scam_fraud_warning 0.2658; out_of_scope 0.1694 | An investigation-report request is close to complaint handling; the consumer-rights evidence was not recognized. |
| VAL-CO-004 | contact_regulator → complaints_process | 0.8182 | 0.1125 | financial_education 0.0416 | The phrase “financial complaints” is a strong lexical complaint cue even though the request concerns an emergency contact page. |
| VAL-LI-005 | licensed_institutions → contact_regulator | 0.4451 | 0.4243 | financial_education 0.0754 | Correcting a public register entry is semantically close to contacting the regulator; the two leading classes are nearly tied. |
| VAL-CR-004 | consumer_rights → complaints_process | 0.6141 | 0.0382 | out_of_scope 0.2587 | A rejected account application is near complaint handling and provider-specific decision questions; likely boundary ambiguity. |

These are plausible lexical/semantic explanations from the validation questions and observed class probabilities, not feature-level causal attribution. All five Naive Bayes errors are concentrated in the `consumer_rights`, `contact_regulator`, and `licensed_institutions` boundaries. Complaints are over-predicted (9 predictions for 5 true complaints); two true contact-regulator and two true consumer-rights examples were assigned to complaints.

### Softmax errors: all 45 misclassified records

Every non-OOS validation record was predicted as OOS; all 11 true OOS records were correct. Confidence equals `P(OOS)` in this table. `P(actual)` is the competing probability assigned to the true class. For every row, the likely explanation `R1` is: the fitted OOS intercept dominates the class decision while the entire probability vector remains close to uniform. The saved OOS bias is `+0.6937`, compared with biases from `-0.1375` to `-0.0553` for the other classes. The OOS training class has 54 examples versus 23–25 for each other class. This pattern is consistent with imbalance interacting with a weakly discriminative fit, but does not by itself prove causation.

| ID | Actual | Predicted | Confidence = P(OOS) | P(actual) | Likely explanation |
|---|---|---|---:|---:|---|
| VAL-PM-005 | PM | OOS | 0.195 | 0.092 | R1 |
| VAL-SF-004 | SF | OOS | 0.197 | 0.098 | R1 |
| VAL-SF-001 | SF | OOS | 0.208 | 0.097 | R1 |
| VAL-FE-001 | FE | OOS | 0.187 | 0.094 | R1 |
| VAL-FE-005 | FE | OOS | 0.190 | 0.090 | R1 |
| VAL-CO-003 | CO | OOS | 0.192 | 0.101 | R1 |
| VAL-HH-003 | HH | OOS | 0.196 | 0.100 | R1 |
| VAL-CO-005 | CO | OOS | 0.186 | 0.106 | R1 |
| VAL-FE-004 | FE | OOS | 0.196 | 0.092 | R1 |
| VAL-CO-001 | CO | OOS | 0.189 | 0.100 | R1 |
| VAL-PM-004 | PM | OOS | 0.190 | 0.094 | R1 |
| VAL-LI-001 | LI | OOS | 0.203 | 0.095 | R1 |
| VAL-CP-005 | CP | OOS | 0.219 | 0.096 | R1 |
| VAL-CR-003 | CR | OOS | 0.188 | 0.098 | R1 |
| VAL-CO-002 | CO | OOS | 0.190 | 0.098 | R1 |
| VAL-SF-002 | SF | OOS | 0.186 | 0.098 | R1 |
| VAL-FE-002 | FE | OOS | 0.190 | 0.094 | R1 |
| VAL-LI-004 | LI | OOS | 0.187 | 0.098 | R1 |
| VAL-CP-001 | CP | OOS | 0.184 | 0.099 | R1 |
| VAL-PM-003 | PM | OOS | 0.184 | 0.098 | R1 |
| VAL-CR-001 | CR | OOS | 0.190 | 0.100 | R1 |
| VAL-CP-004 | CP | OOS | 0.183 | 0.101 | R1 |
| VAL-LI-002 | LI | OOS | 0.183 | 0.104 | R1 |
| VAL-HH-004 | HH | OOS | 0.208 | 0.099 | R1 |
| VAL-HH-001 | HH | OOS | 0.197 | 0.094 | R1 |
| VAL-HH-005 | HH | OOS | 0.197 | 0.099 | R1 |
| VAL-CP-003 | CP | OOS | 0.192 | 0.098 | R1 |
| VAL-SF-005 | SF | OOS | 0.198 | 0.097 | R1 |
| VAL-PM-002 | PM | OOS | 0.186 | 0.095 | R1 |
| VAL-CP-002 | CP | OOS | 0.183 | 0.101 | R1 |
| VAL-RD-004 | RD | OOS | 0.185 | 0.102 | R1 |
| VAL-HH-002 | HH | OOS | 0.203 | 0.101 | R1 |
| VAL-RD-002 | RD | OOS | 0.188 | 0.096 | R1 |
| VAL-CR-005 | CR | OOS | 0.198 | 0.089 | R1 |
| VAL-RD-005 | RD | OOS | 0.189 | 0.099 | R1 |
| VAL-RD-001 | RD | OOS | 0.187 | 0.100 | R1 |
| VAL-CR-002 | CR | OOS | 0.190 | 0.094 | R1 |
| VAL-LI-003 | LI | OOS | 0.190 | 0.093 | R1 |
| VAL-FE-003 | FE | OOS | 0.186 | 0.093 | R1 |
| VAL-SF-003 | SF | OOS | 0.199 | 0.095 | R1 |
| VAL-CO-004 | CO | OOS | 0.180 | 0.097 | R1 |
| VAL-PM-001 | PM | OOS | 0.189 | 0.097 | R1 |
| VAL-LI-005 | LI | OOS | 0.192 | 0.090 | R1 |
| VAL-RD-003 | RD | OOS | 0.188 | 0.097 | R1 |
| VAL-CR-004 | CR | OOS | 0.199 | 0.091 | R1 |

In particular, all five `scam_fraud_warning` and all five `human_help_request` questions were classified as `out_of_scope` by softmax. Sensitive-case routing must not rely on this classifier; the project’s upstream safety/referral control remains necessary.

## 7. Model comparison and limitations

Naive Bayes is substantially better on this validation collection: 40 more correct records than softmax and higher macro scores across the ten-intent set. It handled six intents with 100% recall, while its weaker areas were `consumer_rights` and `contact_regulator` (both 60% recall), plus lower precision for `complaints_process` (55.56%). Softmax has zero recall for all nine in-scope intents and 100% recall only for OOS.

The validation set is imbalanced: each of nine intents has five records, while OOS has eleven. The training set has OOS=54 and the other classes=23–25. Macro metrics give each intent equal weight; accuracy weights each record equally. The Naive Bayes equal-prior ablation made no decisions change, so learned priors neither helped nor hurt classification decisions here. They increased mean maximum confidence from 0.8119 to 0.8237. Softmax's OOS collapse is consistent with the larger OOS class and its learned intercept, but a single validation evaluation cannot isolate the cause.

With only five validation examples per non-OOS intent, one changed prediction shifts that intent's recall by 20 percentage points. The dataset is curated rather than a large independent sample; the reported metrics are uncertain and should not be generalized. High Naive Bayes scores do not establish production readiness. Confidence normalization also does not establish calibration.

## 8. Tests, commands, and reproducibility

New tests in `tests/test_evaluation.py` cover confusion-matrix orientation, accuracy and macro calculations, undefined metrics, probability validity/normalization, confidence bins and summaries, pinned-input rejection, repeatability, and file-access isolation with synthetic fixtures. One intermediate run had two failures because the synthetic fixture lacked the nested softmax configuration required by the artifact consistency check. The fixture was corrected; no project dataset or model was changed. The final focused run passed.

Commands run with the project virtual-environment interpreter:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_day4_validation.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_evaluation.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_evaluation.py tests/test_intent_classifier.py tests/test_text_processing.py tests/test_training_integrity.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Results: the evaluator exited successfully; `tests/test_evaluation.py` passed 15 tests; the focused preprocessing/classifier/training/evaluation suite passed 83 tests; the complete project suite passed **84 tests**. Two successive real validation evaluator runs produced identical JSON output (SHA-256 `6021fb4cb6a07159ae3bf749653a4b10437bdc1d6e11101465bc0e4d31eccc08`). The model artifact hash remained the pinned value. Evaluation is read-only and does not write model, dataset, or metadata files.

## 9. Recommendation

Do not use the current softmax artifact for intent routing or safety decisions. Preserve both model artifacts and the sealed test collection. Before any model change, investigate the softmax class-score/intercept behavior in a separately approved diagnostic phase; do not tune against the held-out test set. Naive Bayes is the stronger validation baseline, but its small-sample result is not a production approval. Keep sensitive fraud and human-help referral checks upstream and independent of classifier predictions.

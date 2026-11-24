# Day 4 Phase 1 Completion Report

**Project:** Customer Support AI  
**Assistant:** Averse  
**Date:** 2026-11-12  
**Status:** Classifier foundation corrected and tested; model evaluation not performed.

## 1. Initial repository state

Before changes, the working tree was clean on branch `main`, at commit `732faf3a301006f6dc1e788dae1127013845b898` (tag `day3-v1.1.0`). No pre-existing uncommitted user changes were present. No files were staged, committed, or tagged during this work. The working tree now contains only the intentional changes listed in Section 3.

The repository was inspected before editing, including the project tree, Git status, README files, Day 2 and Day 3 specifications/reports, supervisor review items, dataset metadata, knowledge-base documentation and data, text processing, both classifier implementations, training script, validators, retrieval builder, and tests. No validation or test question text was manually displayed or reviewed. Dataset files were hashed as bytes; the required validators later read them programmatically and reported aggregate integrity results.

The repository already had a Day 2 snapshot and ignored backups. The earlier tidy-up was also present: `data/backups/` was not tracked, and `.venv/` and test caches were ignored. Root-level `validate_knowledge_base.py` and `build_retrieval_dataset.py` are referenced by project documentation and are used as root-level commands, so they were left in place.

### Baseline SHA-256 values

These values were captured before changes and rechecked after validation. All match.

| Frozen artifact | SHA-256 |
|---|---|
| v1.0.0 `data/training_examples.json` | `e753ffdeea81d81665dc8423ca8dbe1ff206c7f68b0808840567c7b468fd372c` |
| v1.0.0 `data/validation_examples.json` | `50b3b4cb1f05f8e03d1043a9b2a90fd9b15f6c331c98d609495a813b7b21caa6` |
| v1.0.0 `data/test_examples.json` | `b26ef4d157936a00063e07d419f4f32f581c4219f892410296c8f535c24804aa` |
| v1.0.0 `data/dataset_metadata.json` | `0fe81ff65295f1d7684c7bce14fa3e5382cf3ec20d3e725dd34abf473c4227d6` |
| v1.1.0 `training_examples.json` | `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a` |
| v1.1.0 `validation_examples.json` | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` |
| v1.1.0 `test_examples.json` | `b32b616019e1fed5041d7d8cb868f5a4b678f7c866d18cb533b7ac8ef9d32c2c` |
| v1.1.0 `dataset_metadata.json` | `16c724aa089c9ce7d74709a0bb47644d6349df03ac560c38f6a0ae04133979ca` |
| Original v1.1.0 `intent_models.json` | `372235355b4df7c45c95a5f3b856dafcb61447a104c99ce4b12c5612186b0cc7` |
| Retrieval validation collection | `2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd` |
| Retrieval test collection | `25f928c28c62df98be87c8c0bc17fd69d0ee94eedc3e53ad5fe32fc526dcb56c` |

## 2. Repository housekeeping

- Removed root `data/passages.json` after confirming it contains only the explicitly fictional `EXAMPLE_ONLY_DELETE` placeholder and has no code consumers. The original remains in the existing ignored Day 2 input snapshot at `data/backups/day2_input_snapshot_2026-11-11/passages.json`; no backup was deleted. The knowledge-base README now documents this and points to `data/sources_register_final.csv` for current source references.
- Resolved the dependency discrepancy by changing `requirements.txt` from FastAPI `0.162.2` to `0.162.4`, matching `requirements-lock.txt` and the installed environment. `pip check` reports no broken requirements.
- Extended `.gitignore` for local environment files, key material, backup directories, temporary files, and backup extensions. `git check-ignore` confirmed `.venv/` and `data/backups/` are ignored. Searches found no matching sensitive/local artefacts tracked in Git.
- Kept the root-level scripts in place because existing project commands and documentation use those paths.
- Updated `README.md` and `docs/README.md` to link this report and identify the new separate model artifact.

## 3. Files changed

- `.gitignore` — ignore local credentials, keys, backups, and temporary files.
- `data/passages.json` — removed the confirmed fake placeholder; existing backup retained.
- `docs/KNOWLEDGE_BASE_README.md` — record the placeholder removal and correct source-register guidance.
- `README.md`, `docs/README.md` — link this report and identify the versioned Day 4 model.
- `requirements.txt` — align FastAPI pin with the lock file.
- `ml/text_processing.py` — deterministic shared preprocessing version 2.0.0 and conservative normalization fixes.
- `ml/intent_classifier.py` — from-scratch NumPy vectorizer, Naive Bayes and softmax implementation with validated inputs and stable probabilities.
- `scripts/train_day3_v1_1_classifier.py` — isolate training to the v1.1.0 training file and write a new, non-overwriting model artifact without changing metadata.
- `tests/test_text_processing.py` — stemming and preprocessing regression coverage.
- `tests/test_intent_classifier.py` — 15 direct classifier tests.
- `tests/test_training_integrity.py` — three training-data isolation/configuration tests.
- `data/models/day4-text-processing-v2/intent_models.json` — new retrained model artifact.
- `docs/DAY_4_PHASE_1_COMPLETION_REPORT.md` — this report.

No dataset questions, labels, split membership, metadata, approved passages, retrieval sets, or existing model artifact were edited.

## 4. Text processing corrections

The shared `preprocess_text` pipeline remains: case-fold/tokenize, remove the documented short stop-word list, then apply the conservative stemmer. It uses Python's standard library only. Negations (`no`, `not`, `never`) and the question words (`how`, `what`, `where`, `when`, `who`) remain outside the stop list. Tokens with three characters or fewer are not stemmed; output stems shorter than three characters are rejected. Numbers remain tokens, and punctuation separates tokens.

The known family inconsistencies are addressed with narrow, explicit mappings:

- `licence`, `licensed`, `licensing`, and the listed British/American inflections normalize to `license`.
- `complaint`, `complaining`, and listed complaint verb/plural forms normalize to `complaint`.
- `regulated`, `regulating`, and listed forms normalize to `regulation`; `regulator` remains a separate term.
- Plural `-ies` becomes `-y` (`policies` → `policy`); sibilant plurals lose `-es` (`classes` → `class`); ordinary productive plural `-s` is removed with guards for common non-plurals (`analysis`, `news`, `status`, `series`, `species`, `always`).
- Existing suffix handling for `-ing`, `-ed`, and `-ly` remains conservative, with doubled-final-consonant reduction where applicable and no broad derivational suffix stripping.

`TEXT_PROCESSING_VERSION` is now `2.0.0`. The explicit mappings intentionally canonicalize selected project vocabulary; they are not a general linguistic lemmatizer. Other derivational pairs may remain distinct. Regression tests cover the identified families, stop words, negations, question words, short terms, empty input, punctuation, numbers, mixed case, and unrelated final-`s` words. Both classifiers and future retrieval code share the same `preprocess_text` function.

## 5. Classifier tests and behavior

`tests/test_intent_classifier.py` directly covers deterministic sorted vocabulary and count vectors; unknown terms and empty text; Naive Bayes priors, Laplace-smoothed likelihoods and normalized probabilities; valid class-label predictions; softmax logits and normalized probabilities; empty/unusual inputs; invalid features; reproducible fitting; and a central finite-difference comparison of analytical softmax gradients.

The test expectations check mathematical and API behavior only. They do not assert classifier accuracy or imply that either classifier performs adequately on user questions.

## 6. Training-data isolation and retraining

The production trainer's sole input path is `data/day3-v1.1.0/training_examples.json`. It selects only each record's `question` and `intent`, builds the vocabulary from those questions, and fits class priors, Naive Bayes likelihoods, softmax weights, and bias from those training records. It does not use `expected_action`. The trainer does not open validation, test, answerable evaluation files, or dataset metadata, and no validation-based tuning or hyperparameter search is implemented. The model artifact records validation/test hashes as `null`; those files are not read to produce the artifact.

Three isolation tests use temporary synthetic files. One instruments `Path.read_text` and `Path.read_bytes` and asserts that the only data file read is the synthetic training file; attempts to read synthetic validation, test, or metadata files fail the test. Another changes only synthetic `expected_action` values and confirms vocabulary and fitted parameters remain identical. The third checks that preprocessing and training configuration are recorded. The production run printed that validation, test, answerable collections, and dataset metadata were not opened or modified. No actual validation/test question content was used in fitting.

Retraining occurred only after targeted preprocessing, classifier, gradient, and isolation tests passed. Fixed configuration:

- Dataset: `day3-v1.1.0`, 275 training records; target: `intent`.
- Shared preprocessing: version `2.0.0`; sorted unigram vocabulary of 725 terms.
- Multinomial Naive Bayes: Laplace `alpha=1.0`.
- Softmax regression: batch gradient descent, learning rate `0.2`, 400 epochs, L2 `0.0001`, seed `20261112`, seeded normal initialization (mean 0, standard deviation 0.01) and zero bias.
- No validation/test data used for fitting or tuning. `evaluation_status` is `not_evaluated`.

The corrected artifact is `data/models/day4-text-processing-v2/intent_models.json`, SHA-256 `728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12`. The prior `data/day3-v1.1.0/intent_models.json` remains byte-identical to its initial SHA-256.

## 7. Validation results

Commands were run with the project virtual environment's Python interpreter:

| Command | Result |
|---|---|
| `python -m pytest -q` | 69 passed. This parallel check run emitted a pytest cache-path warning; no test failed. |
| `python -m pytest -q -p no:cacheprovider` | 69 passed, no warning. |
| `python scripts/validate_training_dataset.py` | PASS. v1.0.0 counts: 250 train, 50 validation, 110 test. It checked 83,845 near-duplicate pairs and found 0 suspicious pairs. |
| `python scripts/validate_day3_v1_1.py` | PASS. v1.1.0 counts: 275 train, 56 validation, 120 test; answerable sets 15/30; 47 rewritten abstentions checked for passage eligibility; 0 near-duplicate pairs. |
| `python validate_knowledge_base.py` | PASS: 23 approved, 2 needing review, 4 excluded, 0 rejected; 18 retrieval-enabled. Warning remains that current approved mobile-money how-to guidance is unavailable and KB027/KB028 remain review-only. |
| `python build_retrieval_dataset.py --check` | PASS: materialized retrieval set exactly matches the 18 approved, retrieval-enabled passages. |
| `python -m pip check` | No broken requirements found. |

The validators report aggregate checks and do not print question contents. They programmatically parse their target datasets to validate schemas, counts, references, actions, split/family separation, and hashes. I did not manually inspect or display actual validation/test question text. Hashes for all frozen datasets, both retrieval-only collections, metadata, and the original model matched the values captured at the start.

## 8. Remaining warnings and limits

- Neither classifier has been evaluated. No accuracy, precision/recall, confusion matrix, threshold, or model comparison is claimed.
- Day 2 remains **PARTIALLY COMPLETE**. Two knowledge-base passages remain review-only; the validator warns that current consumer-facing mobile-money instructions are not available in approved retrieval evidence.
- The stemming fixes improve the listed project terms but do not solve all English morphology. Their effect on retrieval quality remains unmeasured; future retrieval must use the same preprocessing version and still abstain when the approved evidence does not support an answer.
- The initial pytest cache warning did not recur when pytest was run with its cache provider disabled.
- Changes remain unstaged and uncommitted for review.

## 9. Recommended next phase

Prepare a documented classifier evaluation protocol, then evaluate the frozen v1.1.0 validation set without changing model fitting or preprocessing. Keep the held-out test set sealed until the validation protocol and model-selection decision are complete. This phase did not perform that evaluation.

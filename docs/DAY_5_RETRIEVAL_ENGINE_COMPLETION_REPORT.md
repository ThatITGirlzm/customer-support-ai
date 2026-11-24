# Day 5 Retrieval Engine Completion Report

**Project:** Averse — Customer Support AI  
**Completion date:** 2026-11-14  
**Status:** Day 5 retrieval implementation verified; no application integration was performed.

## 1. Summary

The existing TF-IDF and BM25 implementation was checked against the approved Day 5 design. A direct-construction validation gap was confirmed and fixed: retrievers now reject `Passage` objects with blank or missing access dates or source sections, and reject publication dates that are neither text nor null. Regression tests cover both rankers.

The final focused retrieval tests passed (35 tests), the full project suite passed (119 tests), and both knowledge-base checks passed. The pinned validation evaluator completed twice with byte-identical output. All 20 protected-file SHA-256 baselines match.

## 2. Implementation and public interfaces

The Phase 2 changes are limited to:

- `ml/retrieval.py` — added shared retriever validation for required source metadata on directly supplied `Passage` objects and validation of optional `publication_date` type.
- `tests/test_retrieval.py` — added regression coverage for blank/null `accessed_date`, blank/null `section_or_page`, and invalid `publication_date` values for both TF-IDF and BM25.
- `docs/DAY_5_RETRIEVAL_ENGINE_COMPLETION_REPORT.md` — this report.

The existing public interfaces are `load_corpus`, `TfidfRetriever.search`, `BM25Retriever.search`, and `evaluate_records`; `scripts/evaluate_day5_retrieval.py` owns the pinned validation-only command. Retrieval results retain passage and source identifiers, source citation fields, raw score, rank, and method.

The confirmed gap was reproduced before the fix: a directly constructed `Passage` with blank `accessed_date` and `section_or_page` was returned as a top TF-IDF result. The shared retriever base now applies the same required-metadata checks regardless of whether a caller uses `load_corpus` or supplies `Passage` objects directly. Empty passage text remains allowed; it produces no positive score and allows the BM25 corpus average to include empty documents as specified.

## 3. Design verification

Both rankers use `ml.text_processing.preprocess_text` for passage and query tokenization. The implementation follows the approved formulas and behavior:

| Area | Verified behavior |
|---|---|
| TF-IDF term frequency | `1 + ln(count)` for present terms |
| TF-IDF IDF | `ln((1 + N) / (1 + df)) + 1` |
| TF-IDF vectors | L2-normalized document and query vectors; cosine similarity by dot product |
| BM25 IDF | `ln(1 + (N - df + 0.5) / (df + 0.5))` |
| BM25 parameters | `k1 = 1.5`, `b = 0.75` |
| BM25 query and length | Unique preprocessed query terms; document length counts shared-preprocessor tokens; average includes empty documents |
| Ranking | Descending raw score, then ascending passage ID |
| Empty/OOV/zero-vector queries | No positive-ranked results |
| Corpus eligibility | Approved and retrieval-enabled records only; duplicate/blank IDs, missing required metadata, disabled/unapproved records, and sensitive topics are rejected |
| Score interpretation | Raw ranking score only; it is not confidence, probability, or answer authorization |

The evaluator is pinned to `data/answerable_validation.json` and `data/retrieval_passages.json`, verifies their recorded hashes, and has no dataset selector or retrieval-test path. It reports binary relevance metrics; nDCG is not calculated.

## 4. Verification results

Commands used the project virtual environment with Python bytecode and pytest cache writes disabled where applicable.

| Check | Command | Result |
|---|---|---|
| Pre-fix full-suite baseline | `python -B -m pytest -q -p no:cacheprovider` | Exit 0; 109 passed |
| Focused retrieval tests after fix | `python -B -m pytest -q -p no:cacheprovider tests/test_retrieval.py tests/test_retrieval_evaluation.py` | Exit 0; 35 passed |
| Full project test suite after fix | `python -B -m pytest -q -p no:cacheprovider` | Exit 0; 119 passed |
| Knowledge-base structural validator | `python -B validate_knowledge_base.py` | Exit 0; PASS |
| Retrieval dataset check-only validator | `python -B build_retrieval_dataset.py --check` | Exit 0; PASS; materialized corpus exactly matches 18 approved retrieval-enabled records |
| Validation retrieval evaluator, run 1 | `python -B scripts/evaluate_day5_retrieval.py` | Exit 0 |
| Validation retrieval evaluator, run 2 | `python -B scripts/evaluate_day5_retrieval.py` | Exit 0; output exactly matched run 1 |

The knowledge-base validator reported 23 approved records, 2 needing review, 4 excluded, 0 rejected, 18 retrieval-enabled passages, 15 registered sources, and 29 passage audit rows. It also retained this warning: payment retrieval includes EFT/RTGS context, but there is no approved current mobile-money how-to guidance; KB027 and KB028 remain review-only. The validator notes that structural validation does not independently verify factual accuracy.

### Validation-only retrieval metrics

Evaluation used 15 answerable validation questions and the 18 active retrieval passages. Metrics are macro-averaged across the 15 questions; each question has one annotated supporting passage, treated as binary relevant.

| Method | Precision@1 | Precision@3 | Recall@1 | Recall@3 | MRR | Hits in top 3 | Misses | No-overlap queries | No-hit queries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TF-IDF | 1.0000 | 0.3333 | 1.0000 | 1.0000 | 1.0000 | 15 | 0 | 0 | 0 |
| BM25 | 1.0000 | 0.3333 | 1.0000 | 1.0000 | 1.0000 | 15 | 0 | 0 | 0 |

Both methods ranked the annotated supporting passage first for all 15 validation questions. There were no per-query retrieval misses, no queries without token overlap with the active corpus, and no no-hit queries. Precision@3 uses a fixed denominator of 3, so one relevant annotated passage in three result slots yields 0.3333.

This is a small 15-query / 18-passage experiment. It measures recovery of the annotated supporting passages, not exhaustive relevance. Every validation question is answerable, so these results do not measure abstention, answer sufficiency, referral behavior, safety performance, calibration, or production performance.

## 5. Protected-file integrity and test-set handling

The following 20 protected artifacts were checked against the SHA-256 baselines recorded in the Phase 1 design report. All match after implementation and verification. Test files were hashed as bytes only.

| Protected artifact | SHA-256 | Result |
|---|---|---|
| v1.0.0 classifier training | `e753ffdeea81d81665dc8423ca8dbe1ff206c7f68b0808840567c7b468fd372c` | Match |
| v1.0.0 classifier validation | `50b3b4cb1f05f8e03d1043a9b2a90fd9b15f6c331c98d609495a813b7b21caa6` | Match |
| v1.0.0 classifier test | `b26ef4d157936a00063e07d419f4f32f581c4219f892410296c8f535c24804aa` | Match |
| v1.0.0 dataset metadata | `0fe81ff65295f1d7684c7bce14fa3e5382cf3ec20d3e725dd34abf473c4227d6` | Match |
| v1.1.0 classifier training | `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a` | Match |
| v1.1.0 classifier validation | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` | Match |
| v1.1.0 classifier test | `b32b616019e1fed5041d7d8cb868f5a4b678f7c866d18cb533b7ac8ef9d32c2c` | Match |
| v1.1.0 dataset metadata | `16c724aa089c9ce7d74709a0bb47644d6349df03ac560c38f6a0ae04133979ca` | Match |
| Retrieval validation | `2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd` | Match |
| Retrieval test | `25f928c28c62df98be87c8c0bc17fd69d0ee94eedc3e53ad5fe32fc526dcb56c` | Match |
| Approved passages | `1cccda0591931c88a2925543b31bbef2fdce8673286e971976fef6012c8a56c6` | Match |
| Passages needing review | `f30e624ed289fa19a9242d29cb68b2457e298006d6953ee8e92081c908f93d57` | Match |
| Excluded passages | `9545d6b3f099d1ab83e032fb5535dedf05d3b5de7c8c31551d8bcef06f6be781` | Match |
| Rejected passages | `a5338d955b09046ec0b16f3a9625b7955c763aae07dc722e474e6078745f932f` | Match |
| Materialized retrieval corpus | `be6e2104182827fb5065dadab82295007886695964a920183a895db467c7a193` | Match |
| Original source register | `939c7341b3478a17b4875fd0f509afc5063ea7c1ffd2387d149a5079e366a9b5` | Match |
| Final source register | `e4206b98835fb8f28ef272023554cd27f33068c86b12d5ccb9588b3d94e77d54` | Match |
| Passage verification audit | `30f34fbdcfc1a1e4ec90afb4c858ec15b598a45f2313747cdedaccbb6d0226cc` | Match |
| Original v1.1.0 model | `372235355b4df7c45c95a5f3b856dafcb61447a104c99ce4b12c5612186b0cc7` | Match |
| Day 4 model | `728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12` | Match |

The retrieval test dataset was not opened, parsed, or evaluated during Phase 2; its bytes were read only by SHA-256 hashing. The test suite and pinned Day 5 evaluator contain no `answerable_test` reference. The evaluator reads only the validation set and the retrieval corpus.

## 6. Repository state and change control

The repository remains on branch `main` at commit `732faf3a301006f6dc1e788dae1127013845b898`. The Phase 2 files touched are the three listed in Section 2. They were already untracked in the supplied working tree, except the completion report, which is new. No protected file was modified. Existing uncommitted Day 4 and repository changes were preserved; no files were staged, committed, or pushed.

The pre-existing tracked diff remains in `.gitignore`, `README.md`, `data/passages.json` (deleted), `docs/KNOWLEDGE_BASE_README.md`, `docs/README.md`, `ml/intent_classifier.py`, `ml/text_processing.py`, `requirements.txt`, `scripts/train_day3_v1_1_classifier.py`, and `tests/test_text_processing.py`. Pre-existing untracked Day 4 and Day 5 implementation files also remain untracked. `ml/intent_classifier.py` and all datasets, KB content, source records, models, and shared preprocessing were left unchanged by Phase 2.

### Command invocation note

Three initial `rg` searches used relative paths from the parent workspace and exited 1 because `tests`, `ml`, and `scripts` were not present in that working directory. Re-running the searches with the project directory as the working directory succeeded. This was a search-command working-directory error, not a project test or validation failure.

## 7. Remaining warnings and boundary

- The active corpus has limited mobile-money coverage; KB027 and KB028 remain under review. The structural validator warning is recorded above.
- The active corpus has no retrieval-enabled scam/fraud or human-help passages. Independent referral handling must precede ordinary retrieval in a future application.
- The validation metrics do not establish abstention, answer sufficiency, referral or safety behavior, calibration, or production performance.
- Retrieval is not integrated into an application request pipeline. No classifier integration, response generation, thresholds, frontend changes, or Day 6 work was performed.

**Completion decision:** Day 5 retrieval implementation and validation are complete within the approved scope. The result is ready for review; the limitations above remain open project constraints.

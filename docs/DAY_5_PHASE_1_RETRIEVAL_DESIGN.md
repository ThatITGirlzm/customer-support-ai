# Day 5 Phase 1 — Retrieval Design and Repository Inspection

**Project:** Customer Support AI  
**Assistant:** Averse  
**Inspection date:** 2026-11-14  
**Status:** Phase 1 inspection and design complete; no retrieval implementation has been written yet.

## 1. Objective and scope

This report records the existing repository facts, protected-file baseline hashes, and a proposed from-scratch TF-IDF/BM25 design. The retrieval test questions were not opened, parsed, or evaluated. They were hashed as bytes only. No project file was modified to produce this report except this new design document; the existing unstaged Day 4 work was preserved.

## 2. Repository state and conventions

At inspection, the repository was on `main` at `732faf3a301006f6dc1e788dae1127013845b898`. The working tree already contained the Day 4 Phase 1/2 files and other unstaged changes. These were recorded by `git status --short` and left untouched. No files were staged or committed.

Relevant paths and conventions:

- `data/approved_passages.json`, `data/retrieval_passages.json`, `data/passages_needing_review.json`, `data/excluded_passages.json`, and `data/rejected_passages.json` hold the knowledge-base dispositions.
- `data/sources_register_final.csv` is the current source register; `source_id` is the stable join key. `data/source_verification_report.csv` is the passage audit. The older `data/sources_register.csv` is header-only and is not the active register.
- `ml/` contains the from-scratch classifier and shared text processing. `app/` currently contains only `__init__.py`; no backend request pipeline exists.
- Root `validate_knowledge_base.py` and `build_retrieval_dataset.py` are established project commands. The latter's `--check` is read-only; `--write` is not to be used for retrieval implementation.
- Existing tests use pytest. NumPy is already pinned in requirements; no additional dependency is required.

The project READMEs state that answers may use only approved BoZ passages, must preserve source citations, and must abstain when supporting evidence is unavailable. They also state that sensitive requests must be referred before ordinary retrieval. Retrieval scores are not answer authorization or confidence guarantees.

## 3. Knowledge-base eligibility and schema

Repository inspection and read-only checks confirmed:

- `approved_passages.json`: 23 records with `status == "APPROVED"`.
- 18 approved records have `retrieval_enabled == true`; `retrieval_passages.json` has exactly those 18 records. `python validate_knowledge_base.py` and `python build_retrieval_dataset.py --check` both passed.
- The four approved scam-warning passages `KB005`, `KB006`, `KB007`, and `KB026` have retrieval disabled. No `scam_fraud_warning` or `human_help_request` record appears in the materialized retrieval corpus.
- `passages_needing_review.json` has two records: `KB027` and `KB028`, both `NEEDS_REVIEW` and retrieval-disabled. They must not enter either index.
- There are four excluded passages, zero rejected passages, 15 registered sources, and 29 passage-level audit rows. Excluded/review/rejected records remain outside retrieval.
- The active 18 passages cover six intents: complaints, consumer rights, payments/mobile money, licensed institutions, financial education, and contact regulator. The set is small and does not supply broad topic or lexical coverage. Regulations, human-help, scam/fraud, and out-of-scope have no active passage.

The original passage schema, present in the approved and materialized records, is:

`id`, `topic`, `text`, `source_id`, `source_title`, `source_url`, `publication_date`, `accessed_date`, `section_or_page`, `status`, `retrieval_enabled`, `review_note`, `original_text`.

`source_id` joins to `sources_register_final.csv`, whose fields are `source_id`, `source_title`, `publisher`, `source_type`, `publication_date`, `date_precision`, `official_url`, `access_date`, `scope_eligibility`, `currency_status`, `verification_status`, `intended_use`, and `verification_notes`. The retriever will use the materialized `retrieval_passages.json`, not the broader approved file, and will retain the original passage/source identifiers and metadata. It will never rewrite or supplement passage text.

## 4. Shared preprocessing inspection

Both classifier vectorization and the saved vocabulary were built through `ml.text_processing.preprocess_text`; retrieval should call that same function. It case-folds and tokenizes alphabetic strings plus integer/decimal number strings, removes a short documented stop-word list, then applies explicit licensing, complaint and regulation mappings plus conservative plural, `-ing`, `-ed`, and `-ly` suffix rules. It preserves negations and selected question words, and records `TEXT_PROCESSING_VERSION = "2.0.0"`.

No preprocessing change is proposed. Known limits include English-only token matching, no phrase or semantic matching, unknown terms, and some common auxiliaries/pronouns and apostrophe-split tokens remaining in the vocabulary. Any stemming/stop-word changes would affect both classifier and retrieval behavior and require a separate approved change.

## 5. Retrieval evaluation data and integrity boundary

The retrieval validation set is `data/answerable_validation.json`. Its actual schema is:

`example_id`, `question`, `split`, `intent`, `scenario_type`, `expected_action`, `supporting_passage_ids`, `source_ids`, `annotation_note`.

It contains 15 records, all with `split == "validation"`, `expected_action == "ANSWER_FROM_SOURCE"`, exactly one `supporting_passage_id`, and matching source references. Each supporting passage resolves to one of the 18 active records. There is no separate relevance-grade field; the existing supporting passage IDs provide binary relevance (supporting passage = 1, other active passages = 0). No relevance label will be invented or edited.

The retrieval test set is `data/answerable_test.json`. Its baseline SHA-256 is recorded below. The file has not been opened, parsed, or used. Future evaluation code will reference only `answerable_validation.json`; tests will use synthetic fixtures and no evaluator will import the retrieval test path. The test file may be hashed as bytes for a post-change integrity check, but not parsed or scored.

## 6. Proposed retrieval implementation

### Shared interface and corpus

Proposed implementation file: `ml/retrieval.py`.

- Load and validate only the canonical `data/retrieval_passages.json` materialized corpus.
- Reject duplicate/blank passage IDs, missing text/source metadata, disabled/non-approved records, and sensitive-intent content. Do not load review, excluded, rejected, backup, classifier, or evaluation-test files.
- Both retrievers consume the same immutable passage-document list, preprocessed by shared `preprocess_text`.
- Return a common result containing `passage_id`, `source_id` (and original source reference metadata), `score`, `rank`, and `method`. Use the passage ID as a reference to the original text rather than copying text into every result. Scores are raw retrieval scores, never probabilities.
- Sort by descending score and break ties by ascending passage ID. Empty queries, all-out-of-vocabulary queries, and zero-length documents yield no positive-ranked results. Validate `top_k`; allow `top_k == 0` to return an empty list.

### TF-IDF

Use sublinear term frequency `tf(t,d) = 1 + ln(count(t,d))` for present terms and smoothed IDF `idf(t) = ln((1 + N) / (1 + df(t))) + 1`. Multiply TF by IDF and L2-normalize each document vector. Vectorize queries with the same term and IDF weights, L2-normalize, and rank by cosine similarity (dot product of normalized vectors). Empty or zero-norm vectors have similarity zero and do not produce results.

### BM25

Use the standard BM25 scoring formula over unique preprocessed query terms:

`score(q,d) = sum_t IDF(t) * [tf(t,d) * (k1 + 1)] / [tf(t,d) + k1 * (1 - b + b * len(d) / avgdl)]`

with Robertson-style IDF `ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))`. Fixed initial defaults are `k1 = 1.5` and `b = 0.75`. Document length is the count of shared-preprocessor tokens; `avgdl` includes empty documents. If the corpus average length is zero, return no results. Do not tune parameters against the test set.

### Proposed file structure

- `ml/retrieval.py` — shared passage/result models, corpus validation, TF-IDF, BM25, deterministic ranking.
- `scripts/evaluate_day5_retrieval.py` — pinned validation-only evaluation; no test path or optional split argument.
- `tests/test_retrieval.py` — formula, edge-case, source-preservation, safety/disposition and deterministic synthetic-fixture tests.
- `docs/DAY_5_RETRIEVAL_ENGINE_COMPLETION_REPORT.md` — methods, validation results, limitations and integrity record.

## 7. Proposed evaluation methodology

Evaluate the same 15 validation queries against the same 18-document corpus with both methods and fixed `k = 1` and `k = 3`:

- Precision@k: relevant retrieved passages in the first k divided by k.
- Recall@k: relevant retrieved passages in the first k divided by the number of annotated supporting passages (one per query here).
- MRR: mean reciprocal rank of the first annotated supporting passage, zero if absent.
- nDCG will not be calculated: the validation schema supplies binary supporting-passage IDs, not graded relevance labels, and the Day 5 evaluation requirement limits nDCG to cases where graded labels are available.

Macro-average each metric over the 15 queries. Count no-overlap and no-hit queries separately. A query can score zero because retrieval missed its annotated passage; this does not prove the knowledge base lacks an answer. Since the validation set has only one annotated supporting passage per query and contains only answerable questions, the metrics measure recovery of those annotations, not exhaustive relevance or abstention performance. Report query-specific misses and whether their supporting passage is absent from the corpus (the verified corpus currently includes all 15 annotated IDs).

The Day 3 specification also records Recall@1 and Recall@3 as retrieval targets. Keep these consistent with the above formulas. Do not tune using the 30-question retrieval test set.

## 8. Risks, assumptions and unresolved questions

- **Verified:** active passage membership, status counts, sensitive exclusions, review-only KB027/KB028, validation schema/count, one supporting passage per query, source joins, and that the 15 annotated passages are present in the active corpus.
- **Assumption:** `supporting_passage_ids` is the relevance ground truth for answerable validation questions. The dataset records one supporting passage each; it does not claim that no other passage could also be relevant.
- The 18-document corpus and 15-query validation set are too small for broad generalization; individual queries materially change aggregate scores.
- Shared preprocessing has known lexical limitations; no semantic matching, spelling correction, or synonym expansion is planned.
- The evaluation collection does not measure abstention for unsupported questions, source-selection correctness beyond the stored source links, referral behavior, or answer sufficiency.
- KB027 and KB028 remain review-only. Four scam passages are intentionally disabled; retrieval must never be used for those sensitive requests.
- A high score cannot authorize an answer. Evidence verification, response templates, abstention, and human referral remain separate future controls; no integration is included in Day 5.
- No conflict was found in the eligible corpus or validation annotations. Phase 1 therefore supports proceeding to controlled implementation.

## 9. Protected SHA-256 baseline before implementation

The following hashes were recorded before any Day 5 code changes. Retrieval test and classifier test files were read only by hash functions; their question contents were not opened.

| Protected artifact | SHA-256 |
|---|---|
| v1.0.0 classifier training | `e753ffdeea81d81665dc8423ca8dbe1ff206c7f68b0808840567c7b468fd372c` |
| v1.0.0 classifier validation | `50b3b4cb1f05f8e03d1043a9b2a90fd9b15f6c331c98d609495a813b7b21caa6` |
| v1.0.0 classifier test | `b26ef4d157936a00063e07d419f4f32f581c4219f892410296c8f535c24804aa` |
| v1.0.0 metadata | `0fe81ff65295f1d7684c7bce14fa3e5382cf3ec20d3e725dd34abf473c4227d6` |
| v1.1.0 classifier training | `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a` |
| v1.1.0 classifier validation | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` |
| v1.1.0 classifier test | `b32b616019e1fed5041d7d8cb868f5a4b678f7c866d18cb533b7ac8ef9d32c2c` |
| v1.1.0 metadata | `16c724aa089c9ce7d74709a0bb47644d6349df03ac560c38f6a0ae04133979ca` |
| Retrieval validation | `2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd` |
| Retrieval test | `25f928c28c62df98be87c8c0bc17fd69d0ee94eedc3e53ad5fe32fc526dcb56c` |
| Approved passages | `1cccda0591931c88a2925543b31bbef2fdce8673286e971976fef6012c8a56c6` |
| Passages needing review | `f30e624ed289fa19a9242d29cb68b2457e298006d6953ee8e92081c908f93d57` |
| Excluded passages | `9545d6b3f099d1ab83e032fb5535dedf05d3b5de7c8c31551d8bcef06f6be781` |
| Rejected passages | `a5338d955b09046ec0b16f3a9625b7955c763aae07dc722e474e6078745f932f` |
| Materialized retrieval corpus | `be6e2104182827fb5065dadab82295007886695964a920183a895db467c7a193` |
| Original header-only source register | `939c7341b3478a17b4875fd0f509afc5063ea7c1ffd2387d149a5079e366a9b5` |
| Final source register | `e4206b98835fb8f28ef272023554cd27f33068c86b12d5ccb9588b3d94e77d54` |
| Passage verification audit | `30f34fbdcfc1a1e4ec90afb4c858ec15b598a45f2313747cdedaccbb6d0226cc` |
| Original v1.1.0 model | `372235355b4df7c45c95a5f3b856dafcb61447a104c99ce4b12c5612186b0cc7` |
| Day 4 model | `728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12` |

## 10. Phase 1 decision

The approved corpus can be identified reliably from the existing materialized retrieval file and validated eligibility rules. The 15-question validation set has usable supporting-passage annotations with valid source references. The sealed test set remains unopened. **Phase 1 is complete; the design supports proceeding to implementation under the restrictions above.**

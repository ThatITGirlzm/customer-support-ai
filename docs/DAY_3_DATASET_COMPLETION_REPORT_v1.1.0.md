# Day 3 Dataset Completion Report — v1.1.0

**Project:** Customer Support AI  
**Assistant:** Averse  
**Version:** `day3-v1.1.0`  
**Date:** 12 November 2026  
**Status:** Dataset revision built and structurally validated; classifier fit completed but not evaluated.

The v1.1.0 datasets are ready for controlled classifier evaluation and threshold work. They are not a basis for deployment claims until evaluation is completed.

## Changes in this version

- Kept all 410 original v1.0.0 example IDs and split assignments. Created v1.1.0 in `data/day3-v1.1.0/`; the v1.0.0 files remain unchanged.
- Applied the four user-approved scope relabels: `TRN-FE-016`, `TRN-FE-024`, `TRN-PM-013`, and `TRN-LI-017`. Each now uses `out_of_scope` / `DECLINE_OUT_OF_SCOPE`.
- Rewrote 53 meta-phrased prompts, retaining each record's ID, intent, expected action, and supporting passage IDs. Each rewritten record has `rewritten_from` containing its original question. All expressly exempt IDs stayed unchanged. The two substantive questions about an approved online form and approved mobile-money providers also stayed unchanged because “approved” there did not refer to the internal passage set.
- Added 41 ordinary-wording banking-boundary requests: 25 train, 6 validation, and 10 test. The nine required families are assigned to only one classifier split each: balance, own-bank fees, personal budgeting, product recommendations, and branch hours in train; transaction history and named-bank account opening in validation; loan decisions and transfer execution in test. The existing personalised budget and savings-product recommendation relabels remain in train with their corresponding new families.
- Added separate retrieval-only collections: `data/answerable_validation.json` (15) and `data/answerable_test.json` (30). Each record references one active approved passage and its registered source. The test collection covers all 18 currently retrievable passages. These records were not used to fit the classifier.
- Trained from-scratch multinomial Naive Bayes and softmax regression using 275 training questions and their `intent` labels only. `expected_action` was not used as a target or feature. The training vocabulary was built only from the training split. The models have not been evaluated, and no held-out results or confidence thresholds are claimed.

## Core dataset counts

The 15/30 retrieval-only evaluation records are additional collections and are excluded from the classifier split totals below.
There are 451 core classifier records and 45 separate retrieval-only records (496 total records across the five collections).

| Intent | Train | Validation | Test |
|---|---:|---:|---:|
| `complaints_process` | 25 | 5 | 8 |
| `scam_fraud_warning` | 25 | 5 | 8 |
| `consumer_rights` | 25 | 5 | 8 |
| `payments_mobile_money` | 24 | 5 | 8 |
| `licensed_institutions` | 24 | 5 | 8 |
| `financial_education` | 23 | 5 | 8 |
| `regulations_directives` | 25 | 5 | 8 |
| `contact_regulator` | 25 | 5 | 8 |
| `human_help_request` | 25 | 5 | 8 |
| `out_of_scope` | 54 | 11 | 38 |
| Null intent — blocked injection cases | 0 | 0 | 10 |
| **Core records** | **275** | **56** | **120** |

The test file retains the 80-example baseline (8 per fixed intent), the original 20 additional out-of-scope examples, and 10 new banking-boundary out-of-scope examples. Its separate injection collection contains 10 null-intent `BLOCK_INJECTION` cases. Thus test has 30 added out-of-scope cases and 10 injection cases beyond the baseline.

## Rewritten-question evidence check

All 47 rewritten `ABSTAIN_NOT_IN_SOURCES` questions were checked against the complete 18-passage active retrieval set. None became answerable after rewriting; **the list of newly answerable rewrites is empty**. They remain abstentions with no passage or source references.

The 47 checked IDs are:

`TRN-CO-014`, `TRN-CO-015`, `TRN-CP-003`, `TRN-CP-004`, `TRN-CP-006`, `TRN-CP-007`, `TRN-CP-010`, `TRN-CP-012`, `TRN-CP-014`, `TRN-CP-023`, `TRN-CR-009`, `TRN-CR-018`, `TRN-CR-020`, `TRN-FE-010`, `TRN-FE-023`, `TRN-LI-009`, `TRN-LI-016`, `TRN-PM-012`, `TRN-PM-020`, `TRN-RD-013`, `TRN-RD-016`, `TRN-RD-019`, `VAL-PM-005`, `VAL-PM-004`, `VAL-CP-005`, `VAL-CR-003`, `VAL-CP-001`, `VAL-PM-003`, `VAL-CP-003`, `VAL-CR-005`, `VAL-FE-003`, `VAL-PM-001`, `VAL-CR-004`, `TST-CP-008`, `TST-PM-002`, `TST-PM-008`, `TST-RD-007`, `TST-CR-004`, `TST-PM-004`, `TST-CR-008`, `TST-PM-007`, `TST-FE-004`, `TST-FE-008`, `TST-CR-003`, `TST-RD-008`, `TST-CP-002`, `TST-CP-003`.

Five other rewrites were already `ANSWER_FROM_SOURCE` and retain their original action and evidence: `TRN-CP-005` (KB002), `TRN-LI-002` (KB015), `TRN-PM-002` (KB013), `TRN-CR-002` (KB009), and `TRN-CR-001` (KB008). The `TST-INJ-030` wording was made more natural while retaining its null intent and `BLOCK_INJECTION` action.

## Validation and leakage checks

- v1.1.0 validator: **PASS**. It checked record schemas, fixed labels, approved relabels, preserved v1.0 IDs and protected rewrite fields, exact counts, source and active-passage references, safety actions, family split separation, version/hash consistency, and model target metadata.
- Duplicate scan: **0 exact duplicates and 0 suspicious near-duplicate pairs** at the specified 0.88 threshold across 496 v1.1.0 core and retrieval-only records.
- All 45 retrieval-only records have exactly one active passage; test covers all 18 active passages. No review-only or excluded content is referenced.
- Existing v1.0.0 validator: **PASS**, 410 records and 83,845 pairs checked with 0 suspicious near-duplicates.
- Retrieval build check: **PASS**, the materialized retrieval dataset still exactly matches the 18 approved, retrieval-enabled records.
- Knowledge-base validator: **PASS** structurally. It retains its warning that approved current mobile-money how-to guidance is unavailable and KB027/KB028 remain review-only.
- Existing pytest suite: **36 passed**. Pytest emitted a cache-directory warning while attempting to write `.pytest_cache`; this did not affect the test result.

The validators establish structure, references, routing labels, split hygiene, and hashes. They do not prove every semantic label or passage claim independently. No backend, user-interface, threshold selection, held-out classifier evaluation, or production routing was implemented here.

## v1.0.0 preservation

The four frozen v1.0.0 files have the same SHA-256 hashes as before this revision and match the backup under `data/backups/day3-v1.0.0-pre-v1.1.0/`.

| Frozen v1.0.0 file | SHA-256 |
|---|---|
| `training_examples.json` | `e753ffdeea81d81665dc8423ca8dbe1ff206c7f68b0808840567c7b468fd372c` |
| `validation_examples.json` | `50b3b4cb1f05f8e03d1043a9b2a90fd9b15f6c331c98d609495a813b7b21caa6` |
| `test_examples.json` | `b26ef4d157936a00063e07d419f4f32f581c4219f892410296c8f535c24804aa` |
| `dataset_metadata.json` | `0fe81ff65295f1d7684c7bce14fa3e5382cf3ec20d3e725dd34abf473c4227d6` |

The v1.1.0 metadata also records these generated file hashes:

| v1.1.0 file | SHA-256 |
|---|---|
| `training_examples.json` | `1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a` |
| `validation_examples.json` | `75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89` |
| `test_examples.json` | `b32b616019e1fed5041d7d8cb868f5a4b678f7c866d18cb533b7ac8ef9d32c2c` |
| `answerable_validation.json` | `2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd` |
| `answerable_test.json` | `25f928c28c62df98be87c8c0bc17fd69d0ee94eedc3e53ad5fe32fc526dcb56c` |
| `intent_models.json` | `372235355b4df7c45c95a5f3b856dafcb61447a104c99ce4b12c5612186b0cc7` |

## Remaining limitations

- The active retrieval set remains 18 passages. The answerable collections exercise those passages; they do not establish broader coverage.
- Mobile-money operational guidance, provider-specific policies, and current legal status represented only by review-only passages remain unavailable for answering.
- The classifier is fitted but has not been evaluated. No precision, recall, F1, confusion matrix, threshold, or safety performance claim is made.
- Day 2 remains **PARTIALLY COMPLETE**; this version does not alter that status.

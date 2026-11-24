# Knowledge Base README

## Purpose

This knowledge base stores short English passages for Customer Support AI, the Averse assistant for Zambia. Every factual answer must come from an approved passage and include its Bank of Zambia (BoZ) source citation. Averse must not invent facts or provide account access, transactions, or individualized case handling. When the answer is missing, it must say it is “not in the sources.”

## Approved source policy

Use publicly available BoZ sources that fit the project's consumer-information scope. Check the original source, title, publisher, exact URL, access date, publication-date precision, relevant page or section, and consumer suitability. A file hosted on boz.zm is not automatically a BoZ publication. Record the named publisher; keep Ministry-authored or otherwise scope-uncertain items out of retrieval. Where a supervisor decision is unavailable, record a conservative independent-researcher exclusion explicitly; do not call it supervisor approval. Never infer a publication day from a month/year label or an upload folder.

Do not use commercial-bank pages, third-party news/blogs, Wikipedia, hosted AI, or unsupported facts as knowledge. The official BoZ Contact Us page provides general enquiries; it is not by itself a formal complaint procedure. A live directory or contact passage may change and must be checked again before release.

## Passage schema

Each passage keeps the existing fields: `id`, `topic`, `text`, `source_id`, `source_title`, `source_url`, `publication_date`, `accessed_date`, `section_or_page`, `status`, `retrieval_enabled`, and `review_note`. `original_text` is included to preserve the audit trail when wording or attribution changed. `publication_date` is `null` when no date is stated, or uses the precision recorded in the source register.

`topic` must be one of the fixed project intents: `complaints_process`, `scam_fraud_warning`, `consumer_rights`, `payments_mobile_money`, `licensed_institutions`, `financial_education`, `regulations_directives`, `contact_regulator`, `human_help_request`, or `out_of_scope`.

## Status and routing

- `APPROVED`: facts, attribution, wording and consumer scope were checked against the cited source.
- `NEEDS_REVIEW`: keep quarantined until the named evidence or supervisor decision is recorded.
- `EXCLUDED`: preserve the record and reason for audit, but keep it out of the active consumer corpus; the current exclusions are independent researcher scope decisions, not supervisor approvals.
- `REJECTED`: preserve the record and reason for audit; never serve it.
- `retrieval_enabled`: must be `true` only for approved, consumer-suitable passages that can safely be retrieved. Review, excluded and rejected records must be false.

The fixed sensitive intents `scam_fraud_warning` and `human_help_request` always create a human referral with a reference number. Their passages remain retrieval-disabled even when the source wording is approved. Historical cheque deadlines are also retrieval-disabled until a current source is available for present-day questions. The 2023 e-money directive candidates KB027–KB028 remain in review until official evidence establishes their current legal status. The 2024 BoZ annual report describes a separate e-money charges directive but does not establish the status of the 2023 provisions. The 2025 annual-report catalogue listing is metadata only; its apparent PDF candidate failed content verification and was excluded. KB029 adds only a bounded statement about BoZ oversight of mobile-money payments and the consumer-information purpose of payment-system rules. It does not answer transaction, fee, reversal, failed-payment or complaint-timeline questions. This is a routing constraint, not a rejection of the source fact.

## Follow-up coverage and runtime boundary (2026-11-11)

The official BoZ Payment Systems Oversight page supports KB029, a limited overview that the Bank’s oversight includes mobile-money payments and that payment-system rules inform consumers about rights and obligations. The live page’s direct rendering was dynamic, so recheck it before release. No current BoZ consumer how-to for mobile-money transactions, fee rules, reversals, or failed-payment remedy steps was verified.

The validator enforces that `scam_fraud_warning` and `human_help_request` passages are never retrieval-enabled. This protects the dataset layer; it does not prove runtime referral order. The app package currently contains only `__init__.py`, so the backend must still be tested to create a referral before any retrieval for sensitive requests.

## Source references

`source_id` is the stable join key. Its exact source title and URL must match `data/sources_register_final.csv`. Each passage records the supporting page or webpage section. The answer builder should expose the source title and link from that register, not construct URLs or repeat unverified metadata.

## Indexing rules

Use `data/retrieval_passages.json` as the materialized retrieval input. It must exactly match records from `approved_passages.json` where both `status == "APPROVED"` and `retrieval_enabled == true`. `build_retrieval_dataset.py --check` and `validate_knowledge_base.py` verify this equality. Do not load the broader approved file directly: some approved records are deliberately disabled for sensitive routing or historical-date reasons.

Never index `data/passages_needing_review.json`, `data/excluded_passages.json`, `data/rejected_passages.json`, original snapshots in `data/backups/`, or the passage-level audit CSV. The former root `data/passages.json` was an explicitly fictional `EXAMPLE_ONLY_DELETE` placeholder with no code consumers; it has been removed. Its original copy remains in the ignored Day 2 input backup. The header-only `data/sources_register.csv` is also an original Task 1 file; use `data/sources_register_final.csv` for current source references.

## Safe update workflow

1. Preserve source files and current datasets in a dated backup.
2. Confirm the source is official and scope-permitted, then open the original.
3. Record exact publisher, URL, access date, publication-date precision, currency and limitations in the source register.
4. Draft one focused claim at a time; include no fact that the cited passage does not support.
5. Record original wording, corrections, page/section and decision in `source_verification_report.csv`.
6. Use `APPROVED` only after factual, source, scope, clarity and safety review; otherwise use `NEEDS_REVIEW` or `REJECTED` and keep retrieval disabled.
7. Run `python validate_knowledge_base.py`. Structural PASS is not factual approval; a human must inspect the source evidence.
8. Re-check live contact/directory pages and all time-bound material before deployment.

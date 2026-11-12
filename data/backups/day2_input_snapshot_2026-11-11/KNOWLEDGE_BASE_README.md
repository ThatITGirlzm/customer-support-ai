# Banking Consumer-Information Assistant — Knowledge Base Data

## Files
- `curated_passages.json`: 21 consumer-facing records for the current retrieval dataset.
- `curated_sources_register.csv`: canonical source register (9 sources).
- `passages_review_required.json`: 5 records excluded from retrieval pending review.

## Indexing rules
1. Index only `curated_passages.json`; do not index the review file.
2. Preserve each passage ID and source provenance when chunking or embedding.
3. `publication_date: null` means no verified exact publication date is recorded. Do not invent a day.
4. Use the live BoZ Registered Financial Institutions directory for current listings; do not hard-code counts or imply registration guarantees safety.
5. General BoZ contact details are not automatically the formal complaint-submission route.
6. Mobile-money-specific consumer guidance remains a coverage gap. Cheques, EFT and RTGS are payment-system background, not mobile-money instructions.
7. Passage text still requires a final line-by-line check against the original source before production.

## Review queue
- KB010: historical NFIS 2017–2022; confirm publisher/scope eligibility and do not present as current policy.
- KB018: manually inspect the original K100/K50 public notice PDF; text extraction was not reliable.
- KB020–KB022: applicant/operator requirements; excluded from consumer retrieval.
- SRC005 and SRC009 are marked `REVIEW_REQUIRED`; SRC006 is `LIMITED_USE`.

## Corrections applied
- KB011 distinguishes 24 June 2026 (last customer cheque-deposit date) from 26 June 2026 (last interbank clearing date), using the March 2026 Zambanker source.
- KB013 now cites the March 2026 Zambanker, not the March 2025 special edition.
- Unverified exact-day publication dates have been cleared.
- KB004 is general BoZ contact information, not a formal complaint channel.
- KB015 and KB016 point users to the live official directory and avoid overclaiming.

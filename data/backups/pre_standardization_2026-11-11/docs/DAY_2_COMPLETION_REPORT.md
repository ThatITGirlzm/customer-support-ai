# Day 2 Knowledge-Base Audit and Completion Report

**Audit date:** 2026-11-11  
**Project:** Banking Consumer-Information Assistant  
**Outcome:** **PARTIALLY COMPLETE**

## Summary

All 26 original passage IDs (KB001–KB026) remain accounted for. Three additional candidate passages (KB027–KB029) were identified during official BoZ source-gap checks. The final files contain **23 approved passages**, **6 passages needing review**, and **0 rejected passages**. Of the approved records, **18 are retrieval-enabled**. Five approved records are deliberately disabled: four scam/fraud passages because that sensitive intent must always create a human referral, and the cheque schedule because it is historical and cannot answer a current-procedure question safely. KB029 adds one bounded, retrievable statement about BoZ oversight of mobile-money payments.

Fifteen sources are now registered. SRC006 and SRC011 have limited-use or currentness concerns; SRC009 is Ministry of Finance-authored and awaits the supervisor’s source-scope decision. SRC010–SRC012 were added during the first audit; follow-up added SRC013–SRC015 for the official directives listing, the BoZ payment-systems oversight page and the BoZ annual-reports catalogue. SRC014 supports KB029; SRC015 is catalogue metadata only. A purported 2025 report PDF candidate failed content verification and was excluded, so it provides no evidence about the 2023 directive.

There are now 29 passage records and 15 source-register records. The schedule’s minimum of eight official sources is met. The separate target of 25 source items is not demonstrated by the register; the 29 passage records must not be counted as 29 distinct source items because many share a source. The retrieval set has 18 items and six passages remain under review, so Day 2 is still partially complete.

## Follow-up evidence check (2026-11-11)

The official BoZ Payment Systems Oversight page identifies mobile-money payments within the Bank’s oversight remit and says payment-system regulations inform consumers about rights and obligations. This supports KB029 as a narrow overview, not as transaction advice. The BoZ directives catalogue and verified 2024 National Payment Systems Annual Report were checked for SRC011 status. A 2025 Annual Report catalogue entry was found, but its apparent PDF candidate did not pass content verification and its contents were excluded. The verified evidence does not establish that the 2023 e-money issuance provisions remain in force, were amended, or were replaced. KB027 and KB028 therefore remain `NEEDS_REVIEW`.

The local PDF cover and official Zambanker catalogue match on the March 2025 edition title and issue month. The catalogue’s searchable result did not expose a verifiable attachment URL; the supplied migrated URL timed out, and no alternative BoZ-hosted PDF for the same issue was confirmed. Therefore its remote contents could not be compared with the local PDF. No other edition was substituted.

## What was inspected

- Project explanation PDF and development schedule DOCX: aim, intended public users, English-only scope, source restrictions, fixed intent list, no account access or transactions, source-linked passages, and Day 2 collection target.
- Original `passages.json` and `sources_register.csv`, curated passages/register, review queue, curated ZIP and prior README. Originals in Downloads were not changed; a SHA-256 snapshot is in `data/backups/day2_input_snapshot_2026-11-11/`.
- All seven supplied source PDFs, the official BoZ Contact Us and Registered Financial Institutions pages, official publication listings, one additional BoZ page for commercial-bank supervision, the 2023 Electronic Money Issuance Directives, and the 2024 National Payment Systems Annual Report. The scanned one-page Public Notice was visually inspected because text extraction returned no text. March 2026 Zambanker printed pp.6, 7 and 12 and September 2025 Zambanker printed p.11 were also visually inspected; text extraction was used for the other readable PDFs.

## What was verified and corrected

- **KB001–KB003:** The Path to Justice is on printed p.12 of March 2026 Zambanker, not pp.18–20. The three steps are FSP branch/customer care, FSP head-office complaints unit if unresolved, then BoZ after internal options are exhausted.
- **KB004:** General BoZ contact details are not presented as a formal complaint-submission process.
- **KB005–KB007:** September 2025 Zambanker printed p.11 supports the #BeFraudSmart campaign, the vigilance statement and Zambia Police participation. It does not support the original credential-sharing or provider-reporting instructions. All are retrieval-disabled because `scam_fraud_warning` is a sensitive intent.
- **KB008–KB009 and KB025:** Narrowed to what the p.12 article says: market-conduct supervision and 2024–2027 priorities; the safe-product description is secure, transparent and fair. Removed stronger claims about “strict standards,” full pricing transparency, all products and guaranteed outcomes.
- **KB010:** Reframed as a historical 2017–2022 strategy target. The document identifies the Ministry of Finance as publisher; it is not presented as current BoZ policy and remains under supervisor review.
- **KB011:** March 2026 Zambanker printed p.6 distinguishes 24 June 2026 (last day customers could deposit cheques) from 26 June 2026 (last day for interbank clearing). The original wording confused them. The confirmed schedule is historical; retrieval is disabled for current procedure.
- **KB012–KB013:** EFT batching via DDACC and RTGS values from 1 ngwee to very large values are on March 2026 Zambanker printed p.7. The March 2025 special edition was the wrong attribution for those claims. RTGS is described as for high-value and time-critical payments; no unsupported “designed by BoZ” claim remains.
- **Old banknotes:** March 2026 Zambanker printed p.3 states that the transition ended on 31 March 2026; from 1 April 2026 old notes ceased to be legal tender and would not be accepted for exchange. Those are distinct dates. No original KB passage specifically covered the old-note transition, so it is documented here without inventing a new passage or suggesting an upcoming event.
- **KB014 and KB019:** FinScope figures were separated. Mobile-money uptake is 76.1% in 2025 versus 58.4% in 2020 (printed p.9); overall inclusion is 80.1% versus 69.4%, supported by increased formal and informal uptake (overview p.1 / metrics p.6). The unsupported interoperability/national-infrastructure claim was removed.
- **KB015:** The directory did not support the regulatory-mandate wording. A new official source, BoZ’s Bank Financial Institutions page (SRC010), supports the corrected commercial-bank supervision/licensing statement.
- **KB016, KB023–KB024:** The live directory and Contact Us page were checked. Passages direct users to the live source and describe general details only; a directory listing is not a guarantee of safety.
- **KB017–KB018:** KB017 is limited to the reported 2026 Financial Literacy Week launch. KB018 was visually verified against the original one-page notice dated 13 August 2025; it supports the historical “Zambian Banknotes” app description and purpose. Current app-store availability is not claimed.
- **KB020–KB022:** The designation document is dated February 2025 and is explicitly for prospective applicants/operators. Wording was corrected against sections 1.1–1.9 and 4.1, but the passages remain retrieval-disabled pending supervisor scope decision.
- **KB026:** Removed unsupported credential-sharing and provider-reporting instructions. Replaced them with the March 2026 p.12 instruction to report suspicious social-engineering scams to the central bank, other regulators and Zambia Police. The dataset keeps it retrieval-disabled under the sensitive-intent rule.
- **KB029:** Added a narrow BoZ oversight statement from the official Payment Systems Oversight page: mobile-money payments are included in the Bank’s oversight of widely important payment systems, and BoZ says payment-system regulations inform consumers about their rights and obligations. It does not supply how-to steps, fee details, failed-transaction remedies, or complaint timelines.
- **KB027–KB028:** Rechecked the original 2023 directive clauses and official BoZ listings. The 2024 National Payment Systems Annual Report describes a separate directive on unwarranted e-money charges. Neither that report nor the official directives catalogue says whether the 2023 e-money issuance directives were amended, replaced, revoked or remain in force. The apparent 2025 annual-report PDF candidate failed content verification and was excluded. Both passages remain review-only.

## Source and metadata assessment

All source IDs SRC001–SRC012 were checked; SRC013–SRC015 were added during this follow-up. Exact dates were not inferred from upload directories. Month-only journal dates remain month precision. The BoZ publication list supplies 30 April 2026 for FinScope; the PDF itself says the survey was conducted in November 2025. The requirements document cover supplies February 2025. SRC009’s PDF identifies Ministry of Finance and ©2017, while its strategy period ended in 2022 and BoZ’s listing describes it as historical. SRC011 is dated at month precision (July 2023) because Gazette page headers vary between 14 and 24 July; its current force is unconfirmed. SRC012 is a report for 2024, but no publication date is stated in the document, so its publication date is blank. SRC015 is the official annual-reports catalogue entry only; it is metadata, not a content source. The apparent 2025 report PDF candidate failed content verification and was excluded. SRC013–SRC014 are live BoZ pages checked through official indexed content; direct page rendering returned a dynamic loading shell. Contact, directory and oversight pages have access dates, not publication dates.

Source limitations are recorded in `data/sources_register_final.csv`. SRC004’s local cover and official catalogue entry match the March 2025 edition title and issue month. No alternative official PDF was verified, so remote contents could not be compared; no final passage relies on SRC004 for the corrected cheque, DDACC or RTGS facts.

## Coverage, gaps and safety

| Topic | Assessment | Current approved coverage |
|---|---|---|
| Complaint procedures | Moderate | Three-step Path to Justice from March 2026 Zambanker; no claim that the general Contact Us form is the formal complaint route. |
| Consumer rights | Limited | Article-level market-conduct and safe-product statements; no comprehensive rights guide was found in the supplied sources. |
| Fraud and scam warnings | Source-backed but referral-only | General awareness and reporting material exists; `scam_fraud_warning` always creates a human referral, so these passages are not retrievable. |
| Mobile money and digital payments | Limited | One retrievable passage now identifies BoZ oversight of mobile-money payments and the consumer-information purpose of payment-system rules. The two 2023 e-money directive candidates await current-status evidence; no current how-to, fee list, failed-transaction remedy or reversal procedure was verified. |
| Licensed and registered institutions | Moderate | Live BoZ directory supports checking names and licence categories; it does not establish safety or performance. |
| Financial education | Moderate | FinScope statistics, 2026 Financial Literacy Week information and the historical currency-app notice are verified. |
| Regulations and directives | Weak for ordinary consumers | The designation requirements are applicant-facing; the e-money directive candidates remain under review. |
| Contacting the regulator | Basic | Current Head Office/Regional Office contacts and general enquiry information are verified; this is not a formal complaint route. |
| Human escalation | App workflow, not a KB fact | The project must create and return a referral number for sensitive requests; no additional sourced human contact channel was invented. |

**Mobile money:** KB029 modestly improves coverage with a bounded statement about the BoZ oversight remit and consumer-rights purpose of payment-system rules. The 2023 directive clauses in KB027–KB028 are textually verified but their current legal force is unconfirmed, so they remain review-only. The inspected official BoZ material still lacks current consumer how-to steps, an applicable fee list, failed-transaction remedy instructions, reversal steps and current mobile-money complaint timelines. For those questions, the assistant must say the answer is “not in the sources.” No commercial-bank or third-party workaround has been added.

**Historical information:** 2026 cheque dates, the 2025 currency app notice, the 2025 campaign and survey figures are framed as historical/source-dated facts. The 2017–2022 NFIS is not served. No old-note passage was added because the transition has ended and no original KB ID covers it.

**Sensitive requests:** every approved `scam_fraud_warning` passage has `retrieval_enabled=false`, and the validator rejects any sensitive-intent passage enabled for retrieval. This confirms the knowledge-base data cannot serve those passages. The current `app/` package contains only `__init__.py`, so the runtime referral-before-retrieval order and reference-number creation are not implemented or verified yet; those must be checked in the backend task.

## Approval counts and remaining decisions

| Status | Count | IDs |
|---|---:|---|
| APPROVED | 23 | KB001–KB009, KB011–KB019, KB023–KB026, KB029 |
| NEEDS_REVIEW | 6 | KB010, KB020–KB022, KB027–KB028 |
| REJECTED | 0 | None; incorrect original wording was corrected or quarantined, not silently discarded |
| Retrieval-enabled | 18 | Filter `APPROVED` and `retrieval_enabled == true` |

No review item has been fully resolved. The factual wording for KB010 and KB020–KB022 is supported, but the remaining source-scope and audience questions require the supervisor. KB027–KB028 remain review-only because official evidence did not establish current force; a supervisor may provide an authoritative current BoZ source and decide whether historical-only use fits the project. Details are in `docs/SUPERVISOR_REVIEW_ITEMS.md`.

## Technical validation and quality gate

`python validate_knowledge_base.py` checks JSON/CSV parsing, schema, unique passage IDs, status placement, sensitive routing, source IDs and URL/title/date consistency, date precision, audit coverage and exact duplicate text. It reports PASS/FAIL and warns that facts require manual inspection. It does not certify factual accuracy.

Validation was run after the follow-up changes: **PASS** — 23 approved, 6 needing review, 0 rejected, 18 retrieval-enabled, 15 source records, and 29 passage-level audit rows. The script still warns that current mobile-money how-to guidance is unavailable.

The dataset is structurally ready as a candidate retrieval source only when the application reads `approved_passages.json` and filters to approved records with `retrieval_enabled == true`, after safety/referral checks. Review, rejected and backup files must never be indexed. The original project Task 1 `data/passages.json` and `data/sources_register.csv` remain unchanged.

## Final quality gate

| Check | Result | Evidence or limitation |
|---|---|---|
| All 26 original passages reviewed individually | Yes | KB001–KB026 each have a row in the passage audit. |
| Every claim in approved passages checked against its source | Yes | Approved wording, source location and correction are recorded in the audit. |
| Source titles, IDs, URLs, publishers and dates verified | Partial | Fifteen source records are documented; SRC004’s online attachment remains unlocated, and currentness for SRC011 is unresolved. |
| Cheque, RTGS and old-banknote issues resolved | Yes | Cheque deadlines and RTGS are verified to March 2026 pp.6–7; old-note transition dates are verified from p.3 and no unsupported passage was added. |
| KB018 checked against original Public Notice | Yes | The one-page scan was visually inspected. |
| KB020–KB022 assessed for consumer suitability | Yes | Applicant/operator audience recorded; all three remain review-only. |
| NFIS publisher, historical status and scope recorded | Yes | Ministry of Finance publisher and ended strategy period recorded; source eligibility awaits supervisor. |
| Registered Financial Institutions page checked | Yes | Official indexed page content checked; page is dynamic. |
| Contact Us page checked | Yes | Official indexed page content checked; general contacts are separated from complaint procedure. |
| Mobile-money coverage assessed | Yes | KB029 adds a narrow oversight statement; KB027–KB028 remain review-only; operational and failed-transaction guidance remains a gap. |
| Unresolved questions documented | Yes | See `docs/SUPERVISOR_REVIEW_ITEMS.md`. |
| Approved file excludes review/rejected items and can feed retrieval safely | Yes, with filtering | Index only `APPROVED` records with `retrieval_enabled == true`; run referral checks before retrieval. |

**Final decision:** Day 2 is **partially complete**, not fully complete. The follow-up adds one approved mobile-money oversight passage and strengthens the evidence record, but none of the six review items is fully resolved. The 2023 directive’s current force and SRC004’s direct online URL remain unresolved. The register has 15 sources and the schedule’s 25-source-item target is not demonstrated. Detailed mobile-money procedures remain “not in the sources.” Eighteen passages are currently eligible for retrieval.

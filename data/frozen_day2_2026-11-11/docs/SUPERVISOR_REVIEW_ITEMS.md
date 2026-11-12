# Supervisor Review Items and Evidence Gaps

**Updated:** 2026-11-11  
**Project:** Customer Support AI  
**Assistant:** Averse — the Customer Support AI

## Decision authority

The supervisor was unavailable for this closeout. The dispositions below are recorded as independent researcher decisions and are not supervisor approvals. No excluded passage has been reclassified as approved. If the project scope later changes, the exclusions can be reconsidered with the supervisor.

## Dispositions of the six former review items

| Passage IDs | Disposition | Basis and remaining action |
|---|---|---|
| KB010 / SRC009 | `EXCLUDED` from active retrieval | The source is a Ministry of Finance-authored National Financial Inclusion Strategy for 2017–2022. Preserve the historical record and audit trail; do not present it as current BoZ policy. Reconsider only if the project explicitly permits this source class. |
| KB020–KB022 / SRC006 | `EXCLUDED` from ordinary consumer retrieval | The February 2025 designation requirements address prospective payment-system applicants/operators. Preserve the source and passage records; do not serve them as consumer guidance. Reconsider only if the audience/scope is formally expanded. |
| KB027–KB028 / SRC011 | `NEEDS_REVIEW` | The directive clauses support the text as written, but official evidence checked so far does not establish whether the July 2023 Electronic Money Issuance Directives remain in force, were amended, replaced, revoked or superseded. Keep both out of retrieval. A current official BoZ status source is needed; a supervisor must then decide whether any historical/current form belongs in this consumer assistant. |

## Official-source checks already completed

- **SRC011 / KB027–KB028:** Inspected the original directive, including clause 32(2)(f) for failed local e-money transactions and clause 32(2)(a)–(c) for customer complaint information. Checked the official BoZ directives listing and the verified 2024 National Payment Systems Annual Report. That report describes a separate directive on unwarranted e-money charges; it does not establish the continuing force of the 2023 clauses. A purported 2025 Annual Report PDF candidate failed content verification and was excluded. The publication date alone was not used as evidence of current legal force.
- **SRC004:** The local PDF cover and official BoZ Zambanker catalogue match on the March 2025 special-edition title and issue month. The migrated PDF URL timed out, the catalogue did not expose a verifiable attachment link, and no alternative official BoZ-hosted file for this same edition was confirmed. Remote contents therefore could not be compared. No unrelated publication was substituted.
- **Mobile-money scope:** KB029 is approved only for the narrow oversight statement supported by the official BoZ Payment Systems Oversight page. No current consumer how-to, fee list, reversal instructions, failed-transaction remedy steps or current complaint timeline was verified. For those requests, Averse must say the answer is “not in the sources.”

## Items that remain open

1. **KB027–KB028:** Obtain an authoritative current BoZ publication or status notice that resolves the 2023 directives’ legal status. Until then, retain `NEEDS_REVIEW`; do not imply current applicability.
2. **KB027–KB028 use decision:** If status evidence is found, determine whether these clauses fit consumer-facing scope or only historical reference. This is a supervisor academic/scope decision, not an automatic consequence of finding the directive online.
3. **SRC004:** If needed for future passages, locate the exact March 2025 special-edition PDF from an official BoZ link and compare title, date and contents with the local PDF. Current passages do not rely on SRC004 for the corrected cheque or RTGS claims.
4. **Day 2 source-item target:** The register has 15 source records, meeting the schedule’s minimum of 8 official sources. It does not demonstrate the separate target of 25 distinct source items. Passage count is not a substitute for distinct source count.

## Scope and runtime notes

- KB010 and KB020–KB022 are preserved in `data/excluded_passages.json`; they are not retrievable and have not been supervisor-approved.
- KB027–KB028 are preserved in `data/passages_needing_review.json`; they are not retrievable.
- Fraud passages remain retrieval-disabled. The project architecture requires referral before retrieval for `scam_fraud_warning` and `human_help_request`, but `app/` still has no request pipeline or reference-number implementation. The knowledge-base validator checks dataset flags only; runtime referral behavior remains to be implemented and tested in a later task.
- Day 2 remains partially complete until source-coverage and legal-currentness gaps are addressed. No decision is made here on behalf of the supervisor.

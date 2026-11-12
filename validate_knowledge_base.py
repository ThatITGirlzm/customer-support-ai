"""Validate the structure and cross-references of the Day 2 knowledge base.

This script checks data integrity only. It cannot establish that a statement is
factually correct; that still requires reviewing the cited source passage.
Run from the project root with: python validate_knowledge_base.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
APPROVED_FILE = DATA_DIR / "approved_passages.json"
RETRIEVAL_FILE = DATA_DIR / "retrieval_passages.json"
REVIEW_FILE = DATA_DIR / "passages_needing_review.json"
REJECTED_FILE = DATA_DIR / "rejected_passages.json"
EXCLUDED_FILE = DATA_DIR / "excluded_passages.json"
SOURCES_FILE = DATA_DIR / "sources_register_final.csv"
AUDIT_FILE = DATA_DIR / "source_verification_report.csv"

INTENTS = {
    "complaints_process",
    "scam_fraud_warning",
    "consumer_rights",
    "payments_mobile_money",
    "licensed_institutions",
    "financial_education",
    "regulations_directives",
    "contact_regulator",
    "human_help_request",
    "out_of_scope",
}
STATUSES = {"APPROVED", "NEEDS_REVIEW", "EXCLUDED", "REJECTED"}
EXPECTED_STATUS = {
    APPROVED_FILE: "APPROVED",
    REVIEW_FILE: "NEEDS_REVIEW",
    EXCLUDED_FILE: "EXCLUDED",
    REJECTED_FILE: "REJECTED",
}
EXPECTED_ORIGINAL_IDS = {f"KB{number:03d}" for number in range(1, 27)}
ALLOWED_SCOPE_ELIGIBILITY = {
    "ELIGIBLE",
    "LIMITED_USE",
    "NEEDS_SUPERVISOR_DECISION",
    "EXCLUDED_BY_INDEPENDENT_RESEARCHER",
}
REQUIRED_PASSAGE_FIELDS = {
    "id",
    "topic",
    "text",
    "source_id",
    "source_title",
    "source_url",
    "publication_date",
    "accessed_date",
    "section_or_page",
    "status",
    "retrieval_enabled",
    "review_note",
    "original_text",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "source_title",
    "publisher",
    "source_type",
    "publication_date",
    "date_precision",
    "official_url",
    "access_date",
    "scope_eligibility",
    "currency_status",
    "verification_status",
    "intended_use",
    "verification_notes",
}
REQUIRED_AUDIT_FIELDS = {
    "passage_id",
    "source_id",
    "claim_verified",
    "source_inspected",
    "supporting_page_or_section",
    "factual_accuracy",
    "scope_eligibility",
    "consumer_suitability",
    "correction_made",
    "final_status",
    "reviewer_notes",
    "original_text",
    "final_text",
}


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passages: list[dict[str, Any]] = []
        self.retrieval_passages: list[dict[str, Any]] = []
        self.sources: dict[str, dict[str, str]] = {}
        self.audit: list[dict[str, str]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def read_json(path: Path, validation: Validation) -> list[dict[str, Any]]:
    if not path.is_file():
        validation.error(f"Missing required file: {path.relative_to(ROOT)}")
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        validation.error(f"Cannot parse {path.relative_to(ROOT)}: {exc}")
        return []
    if not isinstance(value, list):
        validation.error(f"{path.relative_to(ROOT)} must contain a JSON array.")
        return []
    if any(not isinstance(row, dict) for row in value):
        validation.error(f"Every item in {path.relative_to(ROOT)} must be an object.")
        return []
    return value


def read_csv(path: Path, required: set[str], validation: Validation) -> list[dict[str, str]]:
    if not path.is_file():
        validation.error(f"Missing required file: {path.relative_to(ROOT)}")
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = set(reader.fieldnames or [])
            missing = sorted(required - headers)
            if missing:
                validation.error(
                    f"{path.relative_to(ROOT)} is missing columns: {', '.join(missing)}"
                )
            return list(reader)
    except OSError as exc:
        validation.error(f"Cannot read {path.relative_to(ROOT)}: {exc}")
        return []


def parse_precision_date(value: str, precision: str, label: str, validation: Validation) -> None:
    if not value:
        if precision not in {"not_stated", "unknown"}:
            validation.error(f"{label}: blank publication date must use not_stated/unknown precision.")
        return
    patterns = {
        "day": (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        "month": (r"\d{4}-\d{2}", "%Y-%m"),
        "year": (r"\d{4}", "%Y"),
    }
    if precision not in patterns:
        validation.error(f"{label}: unsupported date precision {precision!r}.")
        return
    pattern, date_format = patterns[precision]
    if not re.fullmatch(pattern, value):
        validation.error(
            f"{label}: {value!r} does not match the declared {precision} precision."
        )
        return
    try:
        parsed = datetime.strptime(value, date_format).date()
    except ValueError as exc:
        validation.error(f"{label}: invalid publication date {value!r}: {exc}")
        return
    if parsed > date.today():
        validation.error(f"{label}: publication date {value!r} is in the future.")


def run_validation() -> Validation:
    v = Validation()
    passages_by_path: dict[Path, list[dict[str, Any]]] = {
        path: read_json(path, v) for path in EXPECTED_STATUS
    }
    v.retrieval_passages = read_json(RETRIEVAL_FILE, v)
    sources_rows = read_csv(SOURCES_FILE, REQUIRED_SOURCE_FIELDS, v)
    audit_rows = read_csv(AUDIT_FILE, REQUIRED_AUDIT_FIELDS, v)
    v.audit = audit_rows

    for row in sources_rows:
        source_id = row.get("source_id", "").strip()
        if not source_id:
            v.error("Source register contains a blank source_id.")
            continue
        if source_id in v.sources:
            v.error(f"Duplicate source_id in source register: {source_id}")
        v.sources[source_id] = row
        if not row.get("source_title", "").strip():
            v.error(f"{source_id}: source_title is blank.")
        if row.get("scope_eligibility", "").strip() not in ALLOWED_SCOPE_ELIGIBILITY:
            v.error(f"{source_id}: invalid scope_eligibility {row.get('scope_eligibility')!r}.")
        url = row.get("official_url", "").strip()
        if not url.startswith("https://www.boz.zm/"):
            v.error(f"{source_id}: official_url is blank, non-HTTPS, or not on www.boz.zm.")
        if not row.get("access_date", "").strip():
            v.error(f"{source_id}: access_date is blank.")
        try:
            accessed = date.fromisoformat(row["access_date"])
            if accessed > date.today():
                v.error(f"{source_id}: access_date is in the future.")
        except (KeyError, ValueError):
            v.error(f"{source_id}: access_date must use YYYY-MM-DD.")
        parse_precision_date(
            row.get("publication_date", "").strip(),
            row.get("date_precision", "").strip(),
            source_id,
            v,
        )

    seen_ids: dict[str, Path] = {}
    normalized_texts: dict[str, str] = {}
    status_by_id: dict[str, str] = {}
    for path, rows in passages_by_path.items():
        expected = EXPECTED_STATUS[path]
        for index, row in enumerate(rows):
            label = f"{path.relative_to(ROOT)} item {index + 1}"
            missing = sorted(REQUIRED_PASSAGE_FIELDS - set(row))
            if missing:
                v.error(f"{label} is missing fields: {', '.join(missing)}")
            passage_id = str(row.get("id", "")).strip()
            if not passage_id:
                v.error(f"{label} has a blank id.")
                continue
            if passage_id in seen_ids:
                v.error(
                    f"Duplicate passage id {passage_id} in {seen_ids[passage_id].relative_to(ROOT)} "
                    f"and {path.relative_to(ROOT)}."
                )
            seen_ids[passage_id] = path
            status = row.get("status")
            status_by_id[passage_id] = str(status)
            if status not in STATUSES or status != expected:
                v.error(f"{passage_id}: status must be {expected} in this file; found {status!r}.")
            if row.get("topic") not in INTENTS:
                v.error(f"{passage_id}: invalid topic/intent {row.get('topic')!r}.")
            if not str(row.get("text", "")).strip():
                v.error(f"{passage_id}: text is blank.")
            if not str(row.get("original_text", "")).strip():
                v.error(f"{passage_id}: original_text is blank; preserve the audit trail.")
            retrieval_enabled = row.get("retrieval_enabled")
            if not isinstance(retrieval_enabled, bool):
                v.error(f"{passage_id}: retrieval_enabled must be a JSON boolean.")
            if expected != "APPROVED" and retrieval_enabled is True:
                v.error(f"{passage_id}: review/excluded/rejected passages must not be retrieval-enabled.")
            if expected in {"NEEDS_REVIEW", "EXCLUDED", "REJECTED"} and not str(row.get("review_note", "")).strip():
                v.error(f"{passage_id}: {expected} passage must include a disposition reason in review_note.")
            if expected == "EXCLUDED" and "INDEPENDENT_RESEARCHER_SCOPE_DECISION" not in str(row.get("review_note", "")):
                v.error(f"{passage_id}: excluded passage must record the independent researcher decision authority.")
            if row.get("topic") in {"scam_fraud_warning", "human_help_request"} and retrieval_enabled is True:
                v.error(f"{passage_id}: sensitive intents must route to a referral, not retrieval.")
            source_id = str(row.get("source_id", "")).strip()
            if source_id not in v.sources:
                v.error(f"{passage_id}: referenced source_id {source_id!r} is missing.")
            else:
                source = v.sources[source_id]
                if row.get("source_url") != source.get("official_url"):
                    v.error(f"{passage_id}: source_url does not match {source_id} in the register.")
                if row.get("source_title") != source.get("source_title"):
                    v.error(f"{passage_id}: source_title does not match {source_id} in the register.")
                if row.get("publication_date") != (source.get("publication_date") or None):
                    v.error(f"{passage_id}: publication_date does not match the source register.")
                if source.get("scope_eligibility") == "NEEDS_SUPERVISOR_DECISION" and expected == "APPROVED":
                    v.error(f"{passage_id}: source scope needs supervisor decision but passage is approved.")
                if source.get("scope_eligibility") == "EXCLUDED_BY_INDEPENDENT_RESEARCHER" and expected == "APPROVED":
                    v.error(f"{passage_id}: source was excluded from the active knowledge base but passage is approved.")
                if source.get("scope_eligibility") == "LIMITED_USE" and expected == "APPROVED":
                    v.error(f"{passage_id}: limited-use source requires review before approval.")
            accessed_date = str(row.get("accessed_date", ""))
            try:
                if date.fromisoformat(accessed_date) > date.today():
                    v.error(f"{passage_id}: accessed_date is in the future.")
            except ValueError:
                v.error(f"{passage_id}: accessed_date must use YYYY-MM-DD.")
            normalized = " ".join(str(row.get("text", "")).lower().split())
            if normalized:
                if normalized in normalized_texts:
                    v.error(
                        f"Exact duplicate passage text in {passage_id} and {normalized_texts[normalized]}.")
                normalized_texts[normalized] = passage_id
            v.passages.append(row)

    audited: set[str] = set()
    for index, row in enumerate(audit_rows):
        passage_id = row.get("passage_id", "").strip()
        if not passage_id:
            v.error(f"Audit CSV row {index + 2} has a blank passage_id.")
        elif passage_id in audited:
            v.error(f"Duplicate passage_id in audit CSV: {passage_id}")
        audited.add(passage_id)
        if row.get("source_id", "").strip() not in v.sources:
            v.error(f"Audit row for {passage_id}: source_id is missing from the source register.")
        if row.get("final_status", "").strip() != status_by_id.get(passage_id):
            v.error(f"Audit row for {passage_id}: final_status does not match its passage file.")
        if not row.get("source_inspected", "").strip():
            v.error(f"Audit row for {passage_id}: source_inspected is blank.")
    passage_ids = set(seen_ids)
    missing_original_ids = EXPECTED_ORIGINAL_IDS - passage_ids
    if missing_original_ids:
        v.error(f"Original passage IDs are no longer accounted for: {sorted(missing_original_ids)}.")
    if audited != passage_ids:
        v.error(
            f"Audit coverage mismatch: missing={sorted(passage_ids - audited)}, "
            f"extra={sorted(audited - passage_ids)}."
        )

    eligible_records = [
        row
        for row in passages_by_path.get(APPROVED_FILE, [])
        if row.get("status") == "APPROVED" and row.get("retrieval_enabled") is True
    ]
    eligible_by_id = {str(row.get("id")): row for row in eligible_records}
    retrieval_by_id = {str(row.get("id")): row for row in v.retrieval_passages}
    if len(retrieval_by_id) != len(v.retrieval_passages):
        v.error("retrieval_passages.json contains duplicate passage IDs.")
    if set(retrieval_by_id) != set(eligible_by_id):
        v.error(
            "retrieval_passages.json must contain exactly the approved, retrieval-enabled IDs; "
            f"missing={sorted(set(eligible_by_id) - set(retrieval_by_id))}, "
            f"extra={sorted(set(retrieval_by_id) - set(eligible_by_id))}."
        )
    for passage_id, row in retrieval_by_id.items():
        if row.get("status") != "APPROVED" or row.get("retrieval_enabled") is not True:
            v.error(f"{passage_id}: retrieval dataset contains a non-approved or disabled passage.")
        if eligible_by_id.get(passage_id) != row:
            v.error(f"{passage_id}: retrieval dataset record differs from its approved source record.")
        if row.get("topic") in {"scam_fraud_warning", "human_help_request"}:
            v.error(f"{passage_id}: sensitive content must not appear in retrieval_passages.json.")

    passage_by_id = {
        str(row.get("id")): row for rows in passages_by_path.values() for row in rows
    }
    for index, row in enumerate(audit_rows):
        passage_id = row.get("passage_id", "").strip()
        if passage_id in passage_by_id and row.get("source_id", "").strip() != str(passage_by_id[passage_id].get("source_id", "")):
            v.error(f"Audit row for {passage_id}: source_id does not match its passage record.")

    # Guard key corrections whose distinction was manually verified in the
    # cited source. This checks the dataset shape; it does not verify the facts.
    approved_by_id = {
        row.get("id"): row for row in passages_by_path.get(APPROVED_FILE, [])
    }
    cheque = approved_by_id.get("KB011", {})
    if cheque and cheque.get("retrieval_enabled") is True:
        v.warning("KB011 is a historical deadline passage; confirm its explicit historical framing before retrieval.")
    elif cheque and ("24 June 2026" not in cheque.get("text", "") or "26 June 2026" not in cheque.get("text", "")):
        v.error("KB011 must preserve both distinct 2026 cheque deadlines in its historical wording.")

    if any(row.get("topic") == "payments_mobile_money" and row.get("retrieval_enabled") for row in v.passages):
        # This is a gap reminder, not a factual claim: all indexed payment
        # passages still need to be checked for consumer mobile-money guidance.
        v.warning("Payment retrieval includes EFT/RTGS context; no approved current mobile-money how-to guidance is available (KB027 and KB028 remain review-only).")
    return v


def main() -> int:
    validation = run_validation()
    approved = sum(row.get("status") == "APPROVED" for row in validation.passages)
    enabled = sum(row.get("retrieval_enabled") is True for row in validation.passages)
    review = sum(row.get("status") == "NEEDS_REVIEW" for row in validation.passages)
    rejected = sum(row.get("status") == "REJECTED" for row in validation.passages)
    print("Knowledge-base structural validation")
    excluded = sum(row.get("status") == "EXCLUDED" for row in validation.passages)
    print(f"Records: {approved} approved, {review} needing review, {excluded} excluded, {rejected} rejected; {enabled} retrieval-enabled.")
    print(f"Retrieval dataset records: {len(validation.retrieval_passages)}.")
    print(f"Sources registered: {len(validation.sources)}; passage audit rows: {len(validation.audit)}.")
    print("Factual accuracy is not automatically verified by this script; it requires manual source inspection.")
    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    if validation.errors:
        print("FAIL")
        for error in validation.errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: required files, schemas, original and unique IDs, source links, dispositions, retrieval dataset eligibility, sensitive-intent exclusions, dates, and audit coverage are structurally valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

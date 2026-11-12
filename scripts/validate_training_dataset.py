"""Validate Day 3 intent, abstention, referral and injection datasets.

This checks structure and dataset integrity; it cannot prove semantic label or
passage accuracy, which still needs human review.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXAMPLE_FIELDS = {
    "example_id",
    "question",
    "split",
    "intent",
    "scenario_type",
    "expected_action",
    "supporting_passage_ids",
    "source_ids",
    "annotation_note",
}
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
SENSITIVE_INTENTS = {"scam_fraud_warning", "human_help_request"}
EXPECTED_ACTIONS = {
    "ANSWER_FROM_SOURCE",
    "ABSTAIN_NOT_IN_SOURCES",
    "REFER_HUMAN",
    "DECLINE_OUT_OF_SCOPE",
    "BLOCK_INJECTION",
}
SCENARIO_TYPES = {
    "ordinary",
    "sensitive_referral",
    "out_of_scope",
    "baseline_classification",
    "additional_out_of_scope",
    "prompt_injection",
}
FILES = {
    "train": DATA_DIR / "training_examples.json",
    "validation": DATA_DIR / "validation_examples.json",
    "test": DATA_DIR / "test_examples.json",
}
METADATA_FILE = DATA_DIR / "dataset_metadata.json"
RETRIEVAL_FILE = DATA_DIR / "retrieval_passages.json"
SOURCE_FILE = DATA_DIR / "sources_register_final.csv"
FREEZE_MANIFEST = DATA_DIR / "frozen_day2_2026-11-11" / "SHA256SUMS.csv"
NEAR_DUPLICATE_THRESHOLD = 0.88


class DatasetValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.records: dict[str, list[dict[str, Any]]] = {}
        self.active_passages: dict[str, dict[str, Any]] = {}
        self.source_ids: set[str] = set()
        self.family_splits: dict[str, set[str]] = defaultdict(set)
        self.example_ids: set[str] = set()

    def error(self, message: str) -> None:
        self.errors.append(message)

    def read_array(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            self.error(f"Missing required file: {path.relative_to(ROOT)}")
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.error(f"Cannot read {path.relative_to(ROOT)}: {exc}")
            return []
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            self.error(f"{path.relative_to(ROOT)} must contain an array of objects.")
            return []
        return value

    def sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def load_references(self) -> None:
        rows = self.read_array(RETRIEVAL_FILE)
        for row in rows:
            passage_id = row.get("id")
            if not isinstance(passage_id, str) or not passage_id:
                self.error("Active retrieval passage has a blank or invalid id.")
                continue
            if passage_id in self.active_passages:
                self.error(f"Duplicate active retrieval passage id: {passage_id}.")
            if row.get("status") != "APPROVED" or row.get("retrieval_enabled") is not True:
                self.error(f"{passage_id}: retrieval input contains non-approved/disabled content.")
            self.active_passages[passage_id] = row

        for file_name in ("passages_needing_review.json", "excluded_passages.json", "rejected_passages.json"):
            rows = self.read_array(DATA_DIR / file_name)
            for row in rows:
                passage_id = row.get("id")
                if isinstance(passage_id, str) and passage_id in self.active_passages:
                    self.error(f"{passage_id}: review/excluded/rejected passage leaked into retrieval input.")

        if not SOURCE_FILE.is_file():
            self.error("Missing source register data/sources_register_final.csv.")
            return
        try:
            with SOURCE_FILE.open(encoding="utf-8-sig", newline="") as stream:
                source_rows = list(csv.DictReader(stream))
        except OSError as exc:
            self.error(f"Cannot read source register: {exc}")
            return
        self.source_ids = {row.get("source_id", "").strip() for row in source_rows}
        self.source_ids.discard("")

    def load_datasets(self) -> None:
        for split, path in FILES.items():
            self.records[split] = self.read_array(path)

    def validate_record(self, row: dict[str, Any], file_split: str, index: int) -> None:
        label = f"{file_split} item {index + 1}"
        fields = set(row)
        if fields != EXAMPLE_FIELDS:
            self.error(
                f"{label}: schema fields differ; missing={sorted(EXAMPLE_FIELDS - fields)}, "
                f"extra={sorted(fields - EXAMPLE_FIELDS)}."
            )

        example_id = row.get("example_id")
        if not isinstance(example_id, str) or not example_id.strip():
            self.error(f"{label}: example_id must be a non-empty string.")
        elif example_id in self.example_ids:
            self.error(f"Duplicate example_id: {example_id}.")
        else:
            self.example_ids.add(example_id)

        question = row.get("question")
        if not isinstance(question, str) or len(question.strip()) < 8:
            self.error(f"{label}: question must be a non-empty English request.")
        elif (
            re.search(r"(?<!\d)(?:\+?260[\s()-]?)?\d{8,}(?!\d)", question)
            or re.search(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", question)
        ):
            self.error(f"{label}: question appears to contain a personal phone/account identifier.")
        if row.get("split") != file_split:
            self.error(f"{example_id}: split field does not match {file_split} file.")

        intent = row.get("intent")
        scenario = row.get("scenario_type")
        action = row.get("expected_action")
        passage_ids = row.get("supporting_passage_ids")
        source_ids = row.get("source_ids")
        note = row.get("annotation_note")

        if scenario not in SCENARIO_TYPES:
            self.error(f"{example_id}: invalid scenario_type {scenario!r}.")
        if action not in EXPECTED_ACTIONS:
            self.error(f"{example_id}: invalid expected_action {action!r}.")
        if not isinstance(note, str) or not note.strip():
            self.error(f"{example_id}: annotation_note must be a non-empty string.")
            note = ""
        family_match = re.match(r"^family=([a-z0-9_]+);", note)
        if not family_match:
            self.error(f"{example_id}: annotation_note must start with a family key.")
        else:
            self.family_splits[family_match.group(1)].add(file_split)

        if not isinstance(passage_ids, list) or any(not isinstance(value, str) for value in passage_ids):
            self.error(f"{example_id}: supporting_passage_ids must be an array of strings.")
            passage_ids = []
        if not isinstance(source_ids, list) or any(not isinstance(value, str) for value in source_ids):
            self.error(f"{example_id}: source_ids must be an array of strings.")
            source_ids = []
        if len(set(passage_ids)) != len(passage_ids):
            self.error(f"{example_id}: duplicate supporting passage references.")
        if len(set(source_ids)) != len(source_ids):
            self.error(f"{example_id}: duplicate source references.")

        if intent is None:
            if not (file_split == "test" and scenario == "prompt_injection" and action == "BLOCK_INJECTION"):
                self.error(f"{example_id}: null intent is allowed only for blocked test injection cases.")
        elif intent not in INTENTS:
            self.error(f"{example_id}: intent {intent!r} is not one of the fixed ten labels.")

        if file_split == "test":
            if scenario not in {"baseline_classification", "additional_out_of_scope", "prompt_injection"}:
                self.error(f"{example_id}: test examples need a baseline or additional-safety scenario type.")
        elif scenario not in {"ordinary", "sensitive_referral", "out_of_scope"}:
            self.error(f"{example_id}: non-test scenario_type {scenario!r} is not allowed.")

        if scenario == "sensitive_referral" and intent not in SENSITIVE_INTENTS:
            self.error(f"{example_id}: sensitive_referral must use a fixed sensitive intent.")
        if scenario == "prompt_injection" and not (
            file_split == "test" and intent is None and action == "BLOCK_INJECTION"
        ):
            self.error(f"{example_id}: prompt_injection must be blocked before classification in test.")
        if scenario == "additional_out_of_scope" and not (
            file_split == "test" and intent == "out_of_scope" and action == "DECLINE_OUT_OF_SCOPE"
        ):
            self.error(f"{example_id}: additional_out_of_scope must decline with out_of_scope intent.")
        if scenario == "baseline_classification" and (file_split != "test" or intent not in INTENTS):
            self.error(f"{example_id}: baseline_classification must use a fixed intent in test.")

        if intent in SENSITIVE_INTENTS:
            if action != "REFER_HUMAN":
                self.error(f"{example_id}: sensitive intent must use REFER_HUMAN.")
            if passage_ids or source_ids:
                self.error(f"{example_id}: sensitive referral case must not reference or retrieve knowledge.")
            if file_split != "test" and scenario != "sensitive_referral":
                self.error(f"{example_id}: sensitive training/validation scenario must be marked sensitive_referral.")
        elif intent == "out_of_scope":
            if action != "DECLINE_OUT_OF_SCOPE":
                self.error(f"{example_id}: out_of_scope must use DECLINE_OUT_OF_SCOPE.")
            if passage_ids or source_ids:
                self.error(f"{example_id}: out-of-scope case must not cite passages or sources.")
            if file_split != "test" and scenario != "out_of_scope":
                self.error(f"{example_id}: out-of-scope training/validation scenario has the wrong scenario_type.")
        elif intent is not None and action in {"REFER_HUMAN", "DECLINE_OUT_OF_SCOPE", "BLOCK_INJECTION"}:
            self.error(f"{example_id}: action {action} is inconsistent with intent {intent}.")

        if action == "BLOCK_INJECTION":
            if not (file_split == "test" and intent is None and scenario == "prompt_injection"):
                self.error(f"{example_id}: BLOCK_INJECTION is reserved for null-intent test injections.")
            if passage_ids or source_ids:
                self.error(f"{example_id}: injection case must not reference or reach knowledge retrieval.")

        if action == "ANSWER_FROM_SOURCE":
            if intent is None or intent in SENSITIVE_INTENTS or intent == "out_of_scope":
                self.error(f"{example_id}: this intent cannot use ANSWER_FROM_SOURCE.")
            if not passage_ids:
                self.error(f"{example_id}: ANSWER_FROM_SOURCE requires active passage evidence.")
        elif passage_ids or source_ids:
            self.error(f"{example_id}: only ANSWER_FROM_SOURCE may include source evidence references.")

        if action == "ABSTAIN_NOT_IN_SOURCES" and (intent is None or intent == "out_of_scope" or intent in SENSITIVE_INTENTS):
            self.error(f"{example_id}: abstention requires an in-scope non-sensitive domain intent.")

        referenced_source_ids: set[str] = set()
        for passage_id in passage_ids:
            passage = self.active_passages.get(passage_id)
            if passage is None:
                self.error(f"{example_id}: passage {passage_id!r} is not an active retrieval record.")
                continue
            if passage.get("status") != "APPROVED" or passage.get("retrieval_enabled") is not True:
                self.error(f"{example_id}: passage {passage_id} is not approved and retrieval-enabled.")
            referenced_source_ids.add(str(passage.get("source_id", "")))
        for source_id in source_ids:
            if source_id not in self.source_ids:
                self.error(f"{example_id}: source {source_id!r} is missing from the source register.")
        if set(source_ids) != referenced_source_ids:
            self.error(
                f"{example_id}: source_ids must exactly match the sources of supporting passages; "
                f"expected={sorted(referenced_source_ids)}, found={sorted(source_ids)}."
            )

    @staticmethod
    def normalize_question(question: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", question.casefold()))

    def check_duplicates(self) -> tuple[int, list[tuple[str, str, float]]]:
        all_rows = [row for records in self.records.values() for row in records]
        exact_by_text: dict[str, str] = {}
        normalized_rows: list[tuple[str, str, list[str]]] = []
        for row in all_rows:
            example_id = str(row.get("example_id", "<missing-id>"))
            question = row.get("question")
            if not isinstance(question, str):
                continue
            normalized = self.normalize_question(question)
            if normalized in exact_by_text:
                self.error(f"Exact duplicate questions: {exact_by_text[normalized]} and {example_id}.")
            else:
                exact_by_text[normalized] = example_id
            normalized_rows.append((example_id, normalized, normalized.split()))

        near_pairs: list[tuple[str, str, float]] = []
        for left_index, (left_id, left_text, left_tokens) in enumerate(normalized_rows):
            if len(left_tokens) < 6:
                continue
            for right_id, right_text, right_tokens in normalized_rows[left_index + 1 :]:
                if len(right_tokens) < 6:
                    continue
                similarity = SequenceMatcher(None, left_tokens, right_tokens, autojunk=False).ratio()
                if similarity >= NEAR_DUPLICATE_THRESHOLD:
                    near_pairs.append((left_id, right_id, similarity))
        for left_id, right_id, similarity in near_pairs:
            self.error(
                f"Suspicious near-duplicate questions ({similarity:.3f}): {left_id} and {right_id}."
            )
        return len(all_rows) * (len(all_rows) - 1) // 2, near_pairs

    def validate_counts(self) -> dict[str, dict[str, int]]:
        expected_per_split = {"train": 25, "validation": 5, "test": 8}
        counts_by_split: dict[str, dict[str, int]] = {}
        for split in ("train", "validation", "test"):
            records = self.records.get(split, [])
            counts = Counter(row.get("intent") for row in records if row.get("intent") is not None)
            counts_by_split[split] = {intent: counts.get(intent, 0) for intent in sorted(INTENTS)}
            expected_total = 110 if split == "test" else expected_per_split[split] * len(INTENTS)
            if len(records) != expected_total:
                self.error(f"{split} dataset has {len(records)} records; expected {expected_total}.")
            for intent in sorted(INTENTS):
                expected_count = expected_per_split[split]
                if split == "test" and intent == "out_of_scope":
                    expected_count = 28
                actual = counts.get(intent, 0)
                if actual != expected_count:
                    self.error(f"{split}: {intent} has {actual} records; expected {expected_count}.")

        tests = self.records.get("test", [])
        baseline = [row for row in tests if row.get("scenario_type") == "baseline_classification"]
        extra_oos = [row for row in tests if row.get("scenario_type") == "additional_out_of_scope"]
        injections = [row for row in tests if row.get("scenario_type") == "prompt_injection"]
        if len(baseline) != 80:
            self.error(f"Test baseline has {len(baseline)} records; expected 80.")
        baseline_counts = Counter(row.get("intent") for row in baseline)
        if any(baseline_counts.get(intent, 0) != 8 for intent in INTENTS):
            self.error("Test baseline must contain exactly 8 records per fixed intent.")
        if len(extra_oos) != 20 or any(row.get("intent") != "out_of_scope" for row in extra_oos):
            self.error("Additional out-of-scope collection must contain exactly 20 out_of_scope records.")
        if len(injections) != 10:
            self.error(f"Prompt-injection safety collection has {len(injections)} records; expected 10.")

        for family, splits in self.family_splits.items():
            if len(splits) > 1:
                self.error(f"Question family {family!r} leaks across splits: {sorted(splits)}.")
        return counts_by_split

    def validate_metadata(self) -> None:
        if not METADATA_FILE.is_file():
            self.error("Missing data/dataset_metadata.json.")
            return
        try:
            metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.error(f"Cannot read dataset metadata: {exc}")
            return
        if metadata.get("project_name") != "Customer Support AI":
            self.error("Metadata project_name must remain Customer Support AI.")
        if metadata.get("assistant_name") != "Averse":
            self.error("Metadata assistant_name must remain Averse.")
        if metadata.get("fixed_intents") != sorted(INTENTS) and set(metadata.get("fixed_intents", [])) != INTENTS:
            self.error("Metadata fixed_intents must contain exactly the fixed ten labels.")
        if metadata.get("random_seed") != 20261111:
            self.error("Metadata must record random seed 20261111.")
        if metadata.get("split_shuffle_seeds") != {"train": 20261111, "validation": 20261112, "test": 20261113}:
            self.error("Metadata split shuffle seeds do not match the reproducible build method.")
        if metadata.get("dataset_version") != "day3-v1.0.0":
            self.error("Unexpected dataset_version.")
        if metadata.get("model_status") != {"trained": False, "evaluated": False}:
            self.error("Metadata must not claim the classifier has been trained or evaluated.")

        evidence = metadata.get("evidence_snapshot", {})
        if FREEZE_MANIFEST.is_file() and evidence.get("day2_freeze_manifest_sha256") != self.sha256(FREEZE_MANIFEST):
            self.error("Metadata Day 2 freeze manifest hash is stale or incorrect.")
        if RETRIEVAL_FILE.is_file() and evidence.get("active_retrieval_dataset_sha256") != self.sha256(RETRIEVAL_FILE):
            self.error("Metadata active retrieval dataset hash is stale or incorrect.")
        if SOURCE_FILE.is_file() and evidence.get("source_register_sha256") != self.sha256(SOURCE_FILE):
            self.error("Metadata source register hash is stale or incorrect.")

        file_hashes = metadata.get("file_sha256", {})
        for filename in ("training_examples.json", "validation_examples.json", "test_examples.json"):
            path = DATA_DIR / filename
            if path.is_file() and file_hashes.get(filename) != self.sha256(path):
                self.error(f"Metadata file hash for {filename} is stale or incorrect.")

        declared_counts = metadata.get("test_collections", {})
        expected_collections = {
            "baseline_classification": 80,
            "additional_out_of_scope": 20,
            "prompt_injection_adversarial_safety": 10,
            "total": 110,
        }
        if declared_counts != expected_collections:
            self.error("Metadata held-out collection counts do not match the approved specification.")

        if metadata.get("held_out_usage") is None or "Do not use test examples" not in metadata.get("held_out_usage", ""):
            self.error("Metadata must prohibit use of held-out examples during fitting and threshold selection.")

    def run(self) -> tuple[dict[str, dict[str, int]], int, list[tuple[str, str, float]]]:
        self.load_references()
        self.load_datasets()
        for split, records in self.records.items():
            for index, row in enumerate(records):
                self.validate_record(row, split, index)
        pair_count, near_pairs = self.check_duplicates()
        counts = self.validate_counts()
        self.validate_metadata()
        return counts, pair_count, near_pairs


def main() -> int:
    validator = DatasetValidator()
    counts, pair_count, near_pairs = validator.run()
    print("Day 3 training, validation and test dataset validation")
    for split in ("train", "validation", "test"):
        records = validator.records.get(split, [])
        print(f"{split}: {len(records)} total")
        for intent in sorted(INTENTS):
            print(f"  {intent}: {counts.get(split, {}).get(intent, 0)}")
        if split == "test":
            test_rows = records
            print(
                "  collections: "
                f"baseline={sum(r.get('scenario_type') == 'baseline_classification' for r in test_rows)}, "
                f"additional_out_of_scope={sum(r.get('scenario_type') == 'additional_out_of_scope' for r in test_rows)}, "
                f"prompt_injection={sum(r.get('scenario_type') == 'prompt_injection' for r in test_rows)}"
            )
    print(f"Duplicate scan: {pair_count} pairs checked; {len(near_pairs)} suspicious near-duplicate pairs (threshold {NEAR_DUPLICATE_THRESHOLD:.2f}).")
    if validator.errors:
        print("FAIL")
        for error in validator.errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: exact schemas and counts, fixed intents, unique IDs/questions, split/family separation, actions, active passage/source references, metadata hashes, and safety collection rules are valid.")
    print("This validates dataset integrity and routing labels only; it does not train/evaluate a classifier or verify that cited passage text semantically answers every question.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

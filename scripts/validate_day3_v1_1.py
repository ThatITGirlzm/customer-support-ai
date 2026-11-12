"""Validate the v1.1.0 classifier and retrieval-only datasets."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VERSION = "day3-v1.1.0"
VERSION_DIR = DATA / VERSION
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
SENSITIVE = {"scam_fraud_warning", "human_help_request"}
DOMAIN_INTENTS = INTENTS - SENSITIVE - {"out_of_scope"}
ACTIONS = {
    "ANSWER_FROM_SOURCE",
    "ABSTAIN_NOT_IN_SOURCES",
    "REFER_HUMAN",
    "DECLINE_OUT_OF_SCOPE",
    "BLOCK_INJECTION",
}
BASE_FIELDS = {
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
EXEMPT_IDS = {
    *(f"TST-INJ-{number:03d}" for number in range(21, 30)),
    "TRN-HH-003",
    "TRN-HH-009",
    "TRN-HH-017",
    "TRN-HH-022",
    "VAL-HH-001",
    "VAL-HH-005",
    "TST-HH-007",
}
RELABELS = {
    "TRN-FE-016": ("out_of_scope", "DECLINE_OUT_OF_SCOPE"),
    "TRN-FE-024": ("out_of_scope", "DECLINE_OUT_OF_SCOPE"),
    "TRN-PM-013": ("out_of_scope", "DECLINE_OUT_OF_SCOPE"),
    "TRN-LI-017": ("out_of_scope", "DECLINE_OUT_OF_SCOPE"),
}
EXPECTED_REWRITE_COUNT = 53
NEAR_DUPLICATE_THRESHOLD = 0.88


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.records: dict[str, list[dict[str, Any]]] = {}
        self.passages: dict[str, dict[str, Any]] = {}
        self.source_ids: set[str] = set()
        self.ids: set[str] = set()
        self.families: dict[str, set[str]] = defaultdict(set)
        self.counts: dict[str, dict[str, int]] = {}
        self.near_pairs: list[tuple[str, str, float]] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    @staticmethod
    def read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def load_references(self) -> None:
        active_rows = self.read_json(DATA / "retrieval_passages.json")
        for row in active_rows:
            passage_id = row.get("id")
            if row.get("status") != "APPROVED" or row.get("retrieval_enabled") is not True:
                self.error(f"Retrieval input includes non-approved or disabled passage {passage_id!r}.")
            if passage_id in self.passages:
                self.error(f"Duplicate active passage ID: {passage_id}.")
            self.passages[passage_id] = row
        if len(self.passages) != 18:
            self.error(f"Active retrieval dataset has {len(self.passages)} records; expected 18.")

        for filename in ("passages_needing_review.json", "excluded_passages.json", "rejected_passages.json"):
            for row in self.read_json(DATA / filename):
                if row.get("id") in self.passages:
                    self.error(f"Review-only passage {row['id']} leaked into active retrieval.")

        with (DATA / "sources_register_final.csv").open(encoding="utf-8-sig", newline="") as stream:
            self.source_ids = {
                row.get("source_id", "").strip() for row in csv.DictReader(stream)
            }
        self.source_ids.discard("")

    def load_records(self) -> None:
        file_map = {
            "train": "training_examples.json",
            "validation": "validation_examples.json",
            "test": "test_examples.json",
        }
        for split, filename in file_map.items():
            self.records[split] = self.read_json(VERSION_DIR / filename)
        self.records["answerable_validation"] = self.read_json(DATA / "answerable_validation.json")
        self.records["answerable_test"] = self.read_json(DATA / "answerable_test.json")

    def validate_record(self, row: dict[str, Any], collection: str, index: int) -> None:
        label = f"{collection}[{index}]"
        example_id = row.get("example_id")
        if not isinstance(example_id, str) or not example_id.strip():
            self.error(f"{label}: missing example_id.")
            return
        if example_id in self.ids:
            self.error(f"Duplicate example_id across v1.1 collections: {example_id}.")
        self.ids.add(example_id)

        expected_fields = BASE_FIELDS | ({"rewritten_from"} if "rewritten_from" in row else set())
        if set(row) != expected_fields:
            self.error(f"{example_id}: schema fields differ; missing={sorted(expected_fields-set(row))}, extra={sorted(set(row)-expected_fields)}.")
        if "rewritten_from" in row and (not isinstance(row["rewritten_from"], str) or not row["rewritten_from"].strip()):
            self.error(f"{example_id}: rewritten_from must be a non-empty original question.")

        question = row.get("question")
        if not isinstance(question, str) or len(question.strip()) < 8:
            self.error(f"{example_id}: question must be a non-empty English request.")
        elif re.search(r"(?<!\d)(?:\+?260[\s()-]?)?\d{8,}(?!\d)", question) or re.search(
            r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", question
        ):
            self.error(f"{example_id}: question appears to contain a phone/account/card identifier.")

        split = row.get("split")
        if collection in {"train", "validation", "test"} and split != collection:
            self.error(f"{example_id}: split value does not match {collection} file.")
        if collection == "answerable_validation" and split != "validation":
            self.error(f"{example_id}: answerable validation record has the wrong split.")
        if collection == "answerable_test" and split != "test":
            self.error(f"{example_id}: answerable test record has the wrong split.")

        intent = row.get("intent")
        action = row.get("expected_action")
        scenario = row.get("scenario_type")
        passages = row.get("supporting_passage_ids")
        sources = row.get("source_ids")
        note = row.get("annotation_note")
        if intent is not None and intent not in INTENTS:
            self.error(f"{example_id}: invalid intent {intent!r}.")
        if action not in ACTIONS:
            self.error(f"{example_id}: invalid expected_action {action!r}.")
        allowed_scenarios = {
            "ordinary", "sensitive_referral", "out_of_scope", "baseline_classification",
            "additional_out_of_scope", "prompt_injection",
        }
        if scenario not in allowed_scenarios:
            self.error(f"{example_id}: invalid scenario_type {scenario!r}.")
        if not isinstance(note, str) or not note.strip():
            self.error(f"{example_id}: annotation_note is missing.")
        else:
            match = re.match(r"^family=([a-z0-9_]+);", note)
            if not match:
                self.error(f"{example_id}: annotation_note must begin with a family key.")
            elif collection in {"train", "validation", "test"}:
                self.families[match.group(1)].add(collection)

        if not isinstance(passages, list) or any(not isinstance(value, str) for value in passages):
            self.error(f"{example_id}: supporting_passage_ids must be an array of strings.")
            passages = []
        if not isinstance(sources, list) or any(not isinstance(value, str) for value in sources):
            self.error(f"{example_id}: source_ids must be an array of strings.")
            sources = []
        if len(set(passages)) != len(passages) or len(set(sources)) != len(sources):
            self.error(f"{example_id}: duplicate passage or source references.")

        if intent is None:
            if not (collection == "test" and scenario == "prompt_injection" and action == "BLOCK_INJECTION"):
                self.error(f"{example_id}: null intent is permitted only for blocked test injections.")
        elif intent in SENSITIVE:
            if action != "REFER_HUMAN" or passages or sources:
                self.error(f"{example_id}: sensitive cases must refer to a person without retrieval.")
            if collection in {"train", "validation"} and scenario != "sensitive_referral":
                self.error(f"{example_id}: sensitive cases must use sensitive_referral scenario_type.")
        elif intent == "out_of_scope":
            if action != "DECLINE_OUT_OF_SCOPE" or passages or sources:
                self.error(f"{example_id}: out-of-scope cases must decline without retrieval references.")
            if collection in {"train", "validation"} and scenario != "out_of_scope":
                self.error(f"{example_id}: non-test out-of-scope scenario_type is invalid.")
        elif action in {"REFER_HUMAN", "DECLINE_OUT_OF_SCOPE", "BLOCK_INJECTION"}:
            self.error(f"{example_id}: action {action} is inconsistent with in-scope intent {intent}.")

        if action == "BLOCK_INJECTION":
            if collection != "test" or scenario != "prompt_injection" or intent is not None or passages or sources:
                self.error(f"{example_id}: injection must be blocked before intent classification and retrieval.")
        if action == "ANSWER_FROM_SOURCE":
            if not passages:
                self.error(f"{example_id}: source answer requires passage evidence.")
        elif passages or sources:
            self.error(f"{example_id}: only ANSWER_FROM_SOURCE may carry evidence references.")
        if action == "ABSTAIN_NOT_IN_SOURCES" and (intent not in DOMAIN_INTENTS):
            self.error(f"{example_id}: abstention requires a non-sensitive in-scope domain intent.")

        found_sources: set[str] = set()
        for passage_id in passages:
            passage = self.passages.get(passage_id)
            if passage is None:
                self.error(f"{example_id}: referenced passage {passage_id!r} is not active.")
            else:
                found_sources.add(str(passage.get("source_id", "")))
        for source_id in sources:
            if source_id not in self.source_ids:
                self.error(f"{example_id}: source {source_id!r} is not in the source register.")
        if set(sources) != found_sources:
            self.error(f"{example_id}: source_ids do not exactly match supporting passage source IDs.")

        if collection.startswith("answerable_"):
            if action != "ANSWER_FROM_SOURCE" or intent not in DOMAIN_INTENTS:
                self.error(f"{example_id}: retrieval-only collections require a supported domain answer.")
            if len(passages) != 1:
                self.error(f"{example_id}: retrieval-only examples require exactly one supporting passage.")
            elif self.passages.get(passages[0], {}).get("topic") != intent:
                self.error(f"{example_id}: passage topic does not match the annotated domain intent.")

    def compare_with_v1_0(self) -> None:
        old_records: dict[str, dict[str, Any]] = {}
        for filename in ("training_examples.json", "validation_examples.json", "test_examples.json"):
            for row in self.read_json(DATA / filename):
                old_records[row["example_id"]] = row
        new_core = [row for split in ("train", "validation", "test") for row in self.records[split]]
        new_by_id = {row["example_id"]: row for row in new_core}
        missing_ids = sorted(set(old_records) - set(new_by_id))
        if missing_ids:
            self.error(f"Original v1.0.0 IDs missing from v1.1.0: {missing_ids}.")
        for example_id, old in old_records.items():
            new = new_by_id.get(example_id)
            if new is None:
                continue
            if example_id in RELABELS:
                if (new.get("intent"), new.get("expected_action")) != RELABELS[example_id]:
                    self.error(f"Approved relabel was not applied correctly to {example_id}.")
                if new.get("question") != old.get("question"):
                    self.error(f"Approved relabel unexpectedly changed question text for {example_id}.")
                if new.get("scenario_type") != "out_of_scope":
                    self.error(f"Approved relabel has an inconsistent scenario_type for {example_id}.")
            elif "rewritten_from" in new:
                if new["rewritten_from"] != old["question"]:
                    self.error(f"{example_id}: rewritten_from does not preserve the v1.0 question.")
                for field in ("example_id", "intent", "expected_action", "supporting_passage_ids"):
                    if new.get(field) != old.get(field):
                        self.error(f"{example_id}: rewrite changed protected field {field}.")
            elif example_id in EXEMPT_IDS and new.get("question") != old.get("question"):
                self.error(f"Explicitly exempt question was modified: {example_id}.")
            elif example_id in EXEMPT_IDS and "rewritten_from" in new:
                self.error(f"Explicitly exempt question received rewritten_from: {example_id}.")

        for example_id, expected in RELABELS.items():
            if new_by_id.get(example_id, {}).get("supporting_passage_ids") != old_records.get(example_id, {}).get("supporting_passage_ids"):
                self.error(f"Relabelled record {example_id} changed supporting passage IDs.")
        rewrite_records = [row for row in new_core if "rewritten_from" in row]
        if len(rewrite_records) != EXPECTED_REWRITE_COUNT:
            self.error(f"Found {len(rewrite_records)} rewrites; expected {EXPECTED_REWRITE_COUNT}.")
        if any(example_id not in new_by_id or "rewritten_from" in new_by_id[example_id] for example_id in EXEMPT_IDS):
            self.error("One or more explicit meta-wording exceptions were rewritten.")

    def validate_counts(self) -> None:
        expected = {
            "train": {
                "complaints_process": 25, "scam_fraud_warning": 25, "consumer_rights": 25,
                "payments_mobile_money": 24, "licensed_institutions": 24, "financial_education": 23,
                "regulations_directives": 25, "contact_regulator": 25, "human_help_request": 25,
                "out_of_scope": 54,
            },
            "validation": {
                **{intent: 5 for intent in INTENTS if intent != "out_of_scope"},
                "out_of_scope": 11,
            },
            "test": {
                **{intent: 8 for intent in INTENTS if intent != "out_of_scope"},
                "out_of_scope": 38,
                "null": 10,
            },
        }
        expected_total = {"train": 275, "validation": 56, "test": 120}
        for split in ("train", "validation", "test"):
            rows = self.records[split]
            counts = Counter(row.get("intent") if row.get("intent") is not None else "null" for row in rows)
            self.counts[split] = dict(sorted(counts.items()))
            if len(rows) != expected_total[split]:
                self.error(f"{split} has {len(rows)} records; expected {expected_total[split]}.")
            if dict(counts) != expected[split]:
                self.error(f"{split} intent counts differ: {dict(counts)}; expected {expected[split]}.")

        if len(self.records["answerable_validation"]) != 15:
            self.error("answerable_validation.json must contain 15 records.")
        if len(self.records["answerable_test"]) != 30:
            self.error("answerable_test.json must contain 30 records.")
        answerable_test_passages = {
            passage_id
            for row in self.records["answerable_test"]
            for passage_id in row.get("supporting_passage_ids", [])
        }
        if answerable_test_passages != set(self.passages):
            self.error("answerable_test.json must cover every active retrieval passage at least once.")

        test = self.records["test"]
        baseline = [row for row in test if row.get("scenario_type") == "baseline_classification"]
        extra_oos = [row for row in test if row.get("scenario_type") == "additional_out_of_scope"]
        injections = [row for row in test if row.get("scenario_type") == "prompt_injection"]
        if len(baseline) != 80 or Counter(row["intent"] for row in baseline) != Counter({intent: 8 for intent in INTENTS}):
            self.error("Held-out baseline must remain exactly 80 examples, eight per fixed intent.")
        if len(extra_oos) != 30 or any(row.get("intent") != "out_of_scope" for row in extra_oos):
            self.error("Test out-of-scope add-on collection must contain the original 20 plus 10 new cases.")
        if len(injections) != 10:
            self.error("Test injection collection must contain exactly ten cases.")

        boundary_ids = {
            "train": {f"TRN-OSB-{number:03d}" for number in range(1, 26)},
            "validation": {f"VAL-OSB-{number:03d}" for number in range(1, 7)},
            "test": {f"TST-OSB-{number:03d}" for number in range(1, 11)},
        }
        expected_boundary_total = {"train": 25, "validation": 6, "test": 10}
        boundary_family_splits: dict[str, str] = {}
        for split in ("train", "validation", "test"):
            selected = [row for row in self.records[split] if row.get("example_id") in boundary_ids[split]]
            if len(selected) != expected_boundary_total[split]:
                self.error(f"{split} banking-boundary set has {len(selected)} records.")
            for row in selected:
                match = re.match(r"^family=([a-z0-9_]+);", row.get("annotation_note", ""))
                if match:
                    family = match.group(1)
                    if family.startswith("banking_boundary_"):
                        previous = boundary_family_splits.setdefault(family, split)
                        if previous != split:
                            self.error(f"Banking-boundary family {family} crosses splits {previous}/{split}.")
        expected_boundary_families = {
            "banking_boundary_balance", "banking_boundary_transfer_execution",
            "banking_boundary_own_bank_fees", "banking_boundary_personal_budget",
            "banking_boundary_transaction_history", "banking_boundary_branch_hours",
            "banking_boundary_loan_decision", "banking_boundary_named_bank_account_opening",
            "banking_boundary_personal_product_recommendation",
        }
        if set(boundary_family_splits) != expected_boundary_families:
            self.error(f"Banking-boundary topic families differ from required coverage: {sorted(boundary_family_splits)}.")

        for family, splits in self.families.items():
            if len(splits) > 1:
                self.error(f"Question family {family} leaks across classifier splits: {sorted(splits)}.")

    @staticmethod
    def normalize(question: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", question.casefold()))

    def check_duplicates(self) -> None:
        rows = [
            row
            for collection in ("train", "validation", "test", "answerable_validation", "answerable_test")
            for row in self.records[collection]
        ]
        first_for_normalized: dict[str, str] = {}
        token_rows: list[tuple[str, list[str]]] = []
        for row in rows:
            example_id = row["example_id"]
            normalized = self.normalize(row["question"])
            if normalized in first_for_normalized:
                self.error(f"Exact duplicate question: {first_for_normalized[normalized]} and {example_id}.")
            else:
                first_for_normalized[normalized] = example_id
            token_rows.append((example_id, normalized.split()))
        for index, (left_id, left_tokens) in enumerate(token_rows):
            if len(left_tokens) < 6:
                continue
            for right_id, right_tokens in token_rows[index + 1 :]:
                if len(right_tokens) < 6:
                    continue
                similarity = SequenceMatcher(None, left_tokens, right_tokens, autojunk=False).ratio()
                if similarity >= NEAR_DUPLICATE_THRESHOLD:
                    self.near_pairs.append((left_id, right_id, similarity))
                    self.error(f"Near-duplicate questions ({similarity:.3f}): {left_id} / {right_id}.")

        # Rewritten v1.0 texts also remain in rewritten_from. Compare each
        # answerable query against every original parent question explicitly.
        parent_rows = [
            row
            for filename in ("training_examples.json", "validation_examples.json", "test_examples.json")
            for row in self.read_json(DATA / filename)
        ]
        for collection in ("answerable_validation", "answerable_test"):
            for answerable in self.records[collection]:
                answer_tokens = self.normalize(answerable["question"]).split()
                for parent in parent_rows:
                    parent_tokens = self.normalize(parent["question"]).split()
                    if len(answer_tokens) < 6 or len(parent_tokens) < 6:
                        continue
                    similarity = SequenceMatcher(
                        None, answer_tokens, parent_tokens, autojunk=False
                    ).ratio()
                    if similarity >= NEAR_DUPLICATE_THRESHOLD:
                        self.error(
                            "Answerable query is too similar to a parent v1.0 question "
                            f"({similarity:.3f}): {answerable['example_id']} / {parent['example_id']}."
                        )

    def validate_metadata(self) -> None:
        metadata_file = VERSION_DIR / "dataset_metadata.json"
        metadata = self.read_json(metadata_file)
        if metadata.get("dataset_version") != VERSION or metadata.get("parent_dataset_version") != "day3-v1.0.0":
            self.error("Dataset version metadata is inconsistent.")
        if metadata.get("project_name") != "Customer Support AI" or metadata.get("assistant_name") != "Averse":
            self.error("Formal project or assistant name changed.")
        if set(metadata.get("fixed_intents", [])) != INTENTS or len(metadata.get("fixed_intents", [])) != 10:
            self.error("Metadata does not preserve exactly the ten fixed intents.")
        if metadata.get("counts_by_split_and_intent") != self.counts:
            self.error("Metadata count table differs from the generated core datasets.")
        for filename in ("training_examples.json", "validation_examples.json", "test_examples.json"):
            path = VERSION_DIR / filename
            if metadata.get("file_sha256", {}).get(filename) != self.sha256(path):
                self.error(f"Metadata hash for {filename} is stale or incorrect.")
        for filename in ("answerable_validation.json", "answerable_test.json"):
            path = DATA / filename
            if metadata.get("answerable_file_sha256", {}).get(filename) != self.sha256(path):
                self.error(f"Metadata hash for {filename} is stale or incorrect.")

        frozen_files = {
            "training_examples.json": DATA / "training_examples.json",
            "validation_examples.json": DATA / "validation_examples.json",
            "test_examples.json": DATA / "test_examples.json",
            "dataset_metadata.json": DATA / "dataset_metadata.json",
        }
        for filename, path in frozen_files.items():
            expected_hash = metadata.get("frozen_v1_0_sha256", {}).get(filename)
            actual_hash = self.sha256(path)
            if actual_hash != expected_hash:
                self.error(f"Frozen v1.0.0 file {filename} changed or metadata hash is wrong.")
            backup = DATA / "backups" / "day3-v1.0.0-pre-v1.1.0" / filename
            if not backup.is_file() or self.sha256(backup) != actual_hash:
                self.error(f"Frozen v1.0.0 backup does not match {filename}.")

        if metadata.get("active_retrieval_dataset_sha256") != self.sha256(DATA / "retrieval_passages.json"):
            self.error("Active retrieval dataset hash is stale.")
        if metadata.get("source_register_sha256") != self.sha256(DATA / "sources_register_final.csv"):
            self.error("Source register hash is stale.")
        collections = metadata.get("test_collections", {})
        if collections.get("baseline_classification") != 80 or collections.get("original_additional_out_of_scope") != 20 or collections.get("banking_boundary_out_of_scope") != 10 or collections.get("additional_out_of_scope_total") != 30 or collections.get("prompt_injection_adversarial_safety") != 10 or collections.get("test_total") != 120:
            self.error("Metadata test-collection counts are incorrect.")
        training = metadata.get("classifier_training", {})
        if training.get("target") != "intent" or training.get("expected_action_used_as_target") is not False or training.get("trained") is not True or training.get("evaluated") is not False:
            self.error("Classifier metadata must record intent-only training and no evaluation.")
        model_path = VERSION_DIR / "intent_models.json"
        model = self.read_json(model_path)
        if model.get("target") != "intent" or model.get("expected_action_used") is not False:
            self.error("Model artifact indicates an invalid training target.")
        if model.get("training_record_count") != 275 or model.get("training_file_sha256") != self.sha256(VERSION_DIR / "training_examples.json"):
            self.error("Model artifact was not fitted from the current training split.")
        if metadata.get("file_sha256", {}).get("intent_models.json") != self.sha256(model_path) or training.get("model_file_sha256") != self.sha256(model_path):
            self.error("Classifier model hash is missing or stale.")
        fit_data = model.get("fit_data", "").lower()
        if "training questions and intent labels only" not in fit_data or "no validation, test or retrieval-only data" not in fit_data:
            self.error("Classifier fit data description must state train-only questions/intent and exclude held-out data.")
        if training.get("validation_test_or_answerable_data_used_for_fitting") is not False:
            self.error("Metadata must state validation, test and answerable collections were excluded from fitting.")

    def validate_rewrite_answerability_inventory(self) -> int:
        rewritten = [
            row
            for split in ("train", "validation", "test")
            for row in self.records[split]
            if "rewritten_from" in row and row.get("expected_action") == "ABSTAIN_NOT_IN_SOURCES"
        ]
        if len(rewritten) != 47:
            self.error(f"Expected 47 rewritten abstentions for passage review; found {len(rewritten)}.")
        for row in rewritten:
            if row.get("supporting_passage_ids") or row.get("source_ids"):
                self.error(f"Rewritten abstention {row['example_id']} carries answer evidence.")
        return len(rewritten)

    def run(self) -> int:
        self.load_references()
        self.load_records()
        for collection, records in self.records.items():
            if not isinstance(records, list):
                self.error(f"Collection {collection} is not a JSON array.")
                continue
            for index, row in enumerate(records):
                if not isinstance(row, dict):
                    self.error(f"{collection}[{index}] is not an object.")
                    continue
                self.validate_record(row, collection, index)
        self.compare_with_v1_0()
        self.validate_counts()
        self.check_duplicates()
        self.validate_metadata()
        abstentions = self.validate_rewrite_answerability_inventory()

        print("Day 3 v1.1.0 dataset validation")
        for split in ("train", "validation", "test"):
            print(f"{split}: {len(self.records[split])} records; counts={self.counts.get(split, {})}")
        print(f"answerable_validation: {len(self.records['answerable_validation'])}")
        print(f"answerable_test: {len(self.records['answerable_test'])}")
        print(f"rewritten abstentions checked for passage eligibility: {abstentions}")
        print(f"near-duplicate pairs: {len(self.near_pairs)}")
        if self.errors:
            print(f"FAIL: {len(self.errors)} validation error(s)")
            for message in self.errors[:100]:
                print(f"- {message}")
            if len(self.errors) > 100:
                print(f"- ... {len(self.errors) - 100} more errors")
            return 1
        print("PASS: all schema, label, count, safety, evidence, split, duplicate, version and hash checks passed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(Validator().run())

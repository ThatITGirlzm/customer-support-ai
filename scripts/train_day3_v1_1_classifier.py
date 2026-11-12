"""Fit intent classifiers from v1.1.0 training questions and intent labels only."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.intent_classifier import MultinomialNaiveBayes, SoftmaxRegression, TextVectorizer


VERSION_DIR = ROOT / "data" / "day3-v1.1.0"
TRAIN_FILE = VERSION_DIR / "training_examples.json"
METADATA_FILE = VERSION_DIR / "dataset_metadata.json"
MODEL_FILE = VERSION_DIR / "intent_models.json"
CLASSES = [
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
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # Select only these two fields. expected_action is neither read as a target
    # nor used as a feature, weight, filter or training condition.
    all_records: Any = json.loads(TRAIN_FILE.read_text(encoding="utf-8"))
    questions = [row["question"] for row in all_records]
    labels = [row["intent"] for row in all_records]
    if len(questions) != len(labels) or any(not isinstance(label, str) for label in labels):
        raise SystemExit("Training examples must each have a fixed intent label.")
    if set(labels) != set(CLASSES):
        raise SystemExit("Training split must contain all ten fixed intents.")

    vectorizer = TextVectorizer().fit(questions)
    features = vectorizer.transform(questions)
    naive_bayes = MultinomialNaiveBayes(alpha=1.0).fit(features, labels, CLASSES)
    softmax = SoftmaxRegression(learning_rate=0.2, epochs=400, l2=1e-4).fit(
        features, labels, CLASSES
    )

    artifact = {
        "project_name": "Customer Support AI",
        "assistant_name": "Averse",
        "dataset_version": "day3-v1.1.0",
        "target": "intent",
        "expected_action_used": False,
        "training_file_sha256": sha256(TRAIN_FILE),
        "training_record_count": len(questions),
        "class_order": CLASSES,
        "text_processing": "ml.text_processing.preprocess_text; train-only sorted unigram vocabulary",
        "vocabulary": vectorizer.vocabulary,
        "models": {
            "naive_bayes": naive_bayes.to_dict(),
            "softmax_regression": softmax.to_dict(),
        },
        "fit_data": "Training questions and intent labels only; no validation, test or retrieval-only data.",
        "evaluation_status": "not_evaluated",
    }
    MODEL_FILE.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    metadata["classifier_training"].update(
        {
            "trained": True,
            "evaluated": False,
            "target": "intent",
            "expected_action_used_as_target": False,
            "training_record_count": len(questions),
            "training_file_sha256": sha256(TRAIN_FILE),
            "vocabulary_size": len(vectorizer.vocabulary),
            "algorithms": ["multinomial_naive_bayes", "softmax_regression_batch_gradient_descent"],
            "model_file": "data/day3-v1.1.0/intent_models.json",
            "model_file_sha256": sha256(MODEL_FILE),
            "validation_test_or_answerable_data_used_for_fitting": False,
        }
    )
    metadata["file_sha256"]["intent_models.json"] = sha256(MODEL_FILE)
    METADATA_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Trained from-scratch intent classifiers from training question/intent pairs only.")
    print(f"Training records: {len(questions)}; classes: {len(CLASSES)}; vocabulary: {len(vectorizer.vocabulary)}")
    print("Algorithms: multinomial Naive Bayes, softmax regression; evaluation: not performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

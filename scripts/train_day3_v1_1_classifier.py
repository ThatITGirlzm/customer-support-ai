"""Fit the v1.1.0 intent data with corrected preprocessing into a new Day 4 artifact.

The historical script filename is retained for command continuity. This
version never writes dataset metadata and never overwrites the Day 3 model.
Only the configured v1.1.0 training file supplies question text and intent
labels; the validation, test and answerable evaluation collections are not
opened by the trainer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.intent_classifier import MultinomialNaiveBayes, SoftmaxRegression, TextVectorizer
from ml.text_processing import TEXT_PROCESSING_VERSION


VERSION_DIR = ROOT / "data" / "day3-v1.1.0"
TRAIN_FILE = VERSION_DIR / "training_examples.json"
DEFAULT_OUTPUT_FILE = ROOT / "data" / "models" / "day4-text-processing-v2" / "intent_models.json"
FIXED_INTENTS = [
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
MODEL_VERSION = "day4-text-processing-v2"


@dataclass(frozen=True)
class TrainingConfig:
    """Fixed, reproducible settings; no validation-based tuning is performed."""

    naive_bayes_alpha: float = 1.0
    softmax_learning_rate: float = 0.2
    softmax_epochs: int = 400
    softmax_l2: float = 1e-4
    random_seed: int = 20261112


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_training_fields(training_file: Path, classes: Sequence[str]) -> tuple[list[str], list[str]]:
    """Read only question and intent from one explicitly supplied training file."""
    value: Any = json.loads(training_file.read_text(encoding="utf-8"))
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError("training file must be a JSON array of objects")

    questions: list[str] = []
    labels: list[str] = []
    valid_labels = set(classes)
    for index, row in enumerate(value):
        question = row.get("question")
        intent = row.get("intent")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"training row {index} has no non-empty question")
        if not isinstance(intent, str) or intent not in valid_labels:
            raise ValueError(f"training row {index} has an invalid intent label")
        questions.append(question)
        labels.append(intent)
    return questions, labels


def train_from_training_file(
    training_file: Path,
    output_file: Path,
    *,
    classes: Sequence[str] = FIXED_INTENTS,
    dataset_version: str = "day3-v1.1.0",
    random_seed: int = 20261112,
    config: TrainingConfig | None = None,
) -> dict[str, Any]:
    """Fit both models and save an isolated artifact without touching metadata.

    The injectable paths allow isolation tests to use temporary synthetic
    fixtures. The production entry point always supplies ``TRAIN_FILE``.
    """
    if output_file.exists():
        raise FileExistsError(f"Refusing to overwrite an existing model artifact: {output_file}")
    selected_classes = list(classes)
    settings = config or TrainingConfig(random_seed=random_seed)
    questions, labels = load_training_fields(training_file, selected_classes)
    if set(labels) != set(selected_classes):
        raise ValueError("training split must contain every configured intent")

    # Vocabulary, class priors, likelihoods and weights all derive from these
    # training questions and labels only.
    vectorizer = TextVectorizer().fit(questions)
    features = vectorizer.transform(questions)
    naive_bayes = MultinomialNaiveBayes(alpha=settings.naive_bayes_alpha).fit(
        features, labels, selected_classes
    )
    softmax = SoftmaxRegression(
        learning_rate=settings.softmax_learning_rate,
        epochs=settings.softmax_epochs,
        l2=settings.softmax_l2,
        random_seed=settings.random_seed,
    ).fit(features, labels, selected_classes)

    artifact: dict[str, Any] = {
        "project_name": "Customer Support AI",
        "assistant_name": "Averse",
        "model_version": MODEL_VERSION,
        "dataset_version": dataset_version,
        "target": "intent",
        "expected_action_used": False,
        "training_file": str(training_file.relative_to(ROOT)) if training_file.is_relative_to(ROOT) else "synthetic_fixture",
        "training_file_sha256": sha256(training_file),
        "training_record_count": len(questions),
        "class_order": selected_classes,
        "preprocessing_version": TEXT_PROCESSING_VERSION,
        "text_processing": "shared ml.text_processing.preprocess_text; sorted train-only unigram vocabulary",
        "vocabulary": vectorizer.vocabulary,
        "models": {
            "naive_bayes": naive_bayes.to_dict(),
            "softmax_regression": softmax.to_dict(),
        },
        "fit_data": "training questions and intent labels only",
        "validation_file_hash": None,
        "test_file_hash": None,
        "training_configuration": {
            **asdict(settings),
            "randomness_used": True,
            "naive_bayes": {
                "algorithm": "multinomial_naive_bayes",
                "alpha": settings.naive_bayes_alpha,
            },
            "softmax": {
                "algorithm": "batch_gradient_descent_softmax_regression",
                "learning_rate": settings.softmax_learning_rate,
                "epochs": settings.softmax_epochs,
                "l2": settings.softmax_l2,
                "initialization": "seeded_normal_mean_0_sd_0.01; zero bias",
            },
        },
        "evaluation_status": "not_evaluated",
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return artifact


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="new versioned model output path; existing files are never overwritten",
    )
    args = parser.parse_args(argv)
    artifact = train_from_training_file(TRAIN_FILE, args.output)
    print(f"Model artifact: {args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output}")
    print(f"Dataset: {artifact['dataset_version']}; records: {artifact['training_record_count']}")
    print(f"Target: {artifact['target']}; vocabulary: {len(artifact['vocabulary'])} terms")
    print(f"Preprocessing: {artifact['preprocessing_version']}; evaluation: not performed")
    print("Validation, test, answerable collections and dataset metadata were not opened or modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

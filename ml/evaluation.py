"""Deterministic classification metrics and validation-only model loading."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ml.intent_classifier import MultinomialNaiveBayes, SoftmaxRegression, TextVectorizer
from ml.text_processing import TEXT_PROCESSING_VERSION


FIXED_INTENTS: tuple[str, ...] = (
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
)

BASE_VALIDATION_FIELDS = frozenset(
    {
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
)

MODEL_VERSION = "day4-text-processing-v2"
DATASET_VERSION = "day3-v1.1.0"


def sha256_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest of already-read file bytes."""
    return hashlib.sha256(value).hexdigest()


def _read_pinned_json(path: Path, expected_sha256: str | None) -> Any:
    """Read one explicitly supplied JSON file and optionally verify its digest."""
    raw = path.read_bytes()
    actual_sha256 = sha256_bytes(raw)
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {path.name}: expected {expected_sha256}, got {actual_sha256}"
        )
    try:
        return json.loads(raw.decode("utf-8")), actual_sha256
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name} is not valid UTF-8 JSON") from exc


def load_validation_records(
    path: Path,
    *,
    expected_sha256: str | None,
    expected_count: int = 56,
    classes: Sequence[str] = FIXED_INTENTS,
) -> tuple[list[dict[str, str]], str]:
    """Load only the supplied validation JSON and retain ID, question and intent.

    The function has no training or test path and does not access action,
    passage, source, or annotation fields after checking the record schema.
    """
    value, digest = _read_pinned_json(path, expected_sha256)
    if not isinstance(value, list) or len(value) != expected_count:
        raise ValueError(f"validation collection must contain exactly {expected_count} records")

    allowed_intents = set(classes)
    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"validation row {index} must be an object")
        expected_fields = BASE_VALIDATION_FIELDS | ({"rewritten_from"} if "rewritten_from" in row else set())
        if set(row) != expected_fields:
            raise ValueError(f"validation row {index} does not match the v1.1.0 schema")
        example_id = row.get("example_id")
        question = row.get("question")
        intent = row.get("intent")
        if not isinstance(example_id, str) or not example_id.strip() or example_id in seen_ids:
            raise ValueError(f"validation row {index} has a missing or duplicate example_id")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"validation row {index} has an empty question")
        if row.get("split") != "validation":
            raise ValueError(f"validation row {index} has a non-validation split")
        if not isinstance(intent, str) or intent not in allowed_intents:
            raise ValueError(f"validation row {index} has an invalid intent")
        if "rewritten_from" in row and (
            not isinstance(row["rewritten_from"], str) or not row["rewritten_from"].strip()
        ):
            raise ValueError(f"validation row {index} has an invalid rewritten_from value")
        seen_ids.add(example_id)
        records.append({"example_id": example_id, "question": question, "intent": intent})
    return records, digest


def _finite_array(value: Any, *, label: str, ndim: int) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"model {label} must be a numeric array") from exc
    if array.ndim != ndim or not np.all(np.isfinite(array)):
        raise ValueError(f"model {label} must be a finite {ndim}-D array")
    return array


def load_serialized_models(
    artifact: dict[str, Any], *, classes: Sequence[str] = FIXED_INTENTS
) -> tuple[TextVectorizer, MultinomialNaiveBayes, SoftmaxRegression]:
    """Restore fitted parameters from JSON without calling either model's fit."""
    class_order = list(classes)
    if artifact.get("model_version") != MODEL_VERSION:
        raise ValueError("model artifact version is not the Day 4 preprocessing-v2 artifact")
    if artifact.get("dataset_version") != DATASET_VERSION:
        raise ValueError("model artifact was not fitted on day3-v1.1.0")
    if artifact.get("target") != "intent" or artifact.get("expected_action_used") is not False:
        raise ValueError("model artifact target or training fields are invalid")
    if artifact.get("preprocessing_version") != TEXT_PROCESSING_VERSION:
        raise ValueError("model preprocessing version does not match the current pipeline")
    if artifact.get("evaluation_status") != "not_evaluated":
        raise ValueError("model artifact must be the unevaluated Phase 1 artifact")
    if artifact.get("class_order") != class_order:
        raise ValueError("model artifact class order does not match the fixed intent list")
    training_count = artifact.get("training_record_count")
    if not isinstance(training_count, int) or training_count <= 0:
        raise ValueError("model artifact training record count is invalid")
    training_configuration = artifact.get("training_configuration")
    if not isinstance(training_configuration, dict):
        raise ValueError("model artifact training configuration is missing")

    vocabulary = artifact.get("vocabulary")
    if (
        not isinstance(vocabulary, list)
        or any(not isinstance(term, str) or not term for term in vocabulary)
        or vocabulary != sorted(set(vocabulary))
    ):
        raise ValueError("model vocabulary must be a unique, sorted list of strings")
    feature_count = len(vocabulary)
    class_count = len(class_order)
    model_data = artifact.get("models")
    if not isinstance(model_data, dict):
        raise ValueError("model artifact has no model parameter collection")

    vectorizer = TextVectorizer()
    vectorizer.vocabulary = list(vocabulary)
    vectorizer.token_to_index = {term: index for index, term in enumerate(vocabulary)}
    vectorizer._is_fitted = True

    nb_data = model_data.get("naive_bayes")
    if not isinstance(nb_data, dict) or nb_data.get("algorithm") != "multinomial_naive_bayes":
        raise ValueError("serialized Naive Bayes parameters are missing or have the wrong algorithm")
    if nb_data.get("classes") != class_order:
        raise ValueError("Naive Bayes class order does not match the artifact")
    alpha = nb_data.get("alpha")
    if not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("Naive Bayes alpha must be finite and positive")
    class_counts = _finite_array(nb_data.get("class_counts"), label="class_counts", ndim=1)
    feature_counts = _finite_array(
        nb_data.get("feature_counts_by_class"), label="feature_counts_by_class", ndim=2
    )
    log_priors = _finite_array(nb_data.get("log_priors"), label="log_priors", ndim=1)
    log_likelihoods = _finite_array(
        nb_data.get("log_likelihoods"), label="log_likelihoods", ndim=2
    )
    if (
        class_counts.shape != (class_count,)
        or feature_counts.shape != (class_count, feature_count)
        or log_priors.shape != (class_count,)
        or log_likelihoods.shape != (class_count, feature_count)
        or np.any(class_counts <= 0)
        or np.any(feature_counts < 0)
        or not np.allclose(class_counts, np.round(class_counts), atol=0.0, rtol=0.0)
        or int(class_counts.sum()) != training_count
    ):
        raise ValueError("serialized Naive Bayes parameter dimensions or counts are invalid")
    if not np.allclose(np.exp(log_priors).sum(), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("serialized Naive Bayes priors are not normalized")
    expected_log_priors = np.log(class_counts / training_count)
    if not np.allclose(log_priors, expected_log_priors, atol=1e-12, rtol=0.0):
        raise ValueError("serialized Naive Bayes priors do not match its frozen class counts")
    if feature_count and not np.allclose(
        np.exp(log_likelihoods).sum(axis=1), 1.0, atol=1e-12, rtol=0.0
    ):
        raise ValueError("serialized Naive Bayes likelihoods are not normalized")
    if feature_count:
        expected_log_likelihoods = np.log(
            (feature_counts + float(alpha))
            / (feature_counts + float(alpha)).sum(axis=1, keepdims=True)
        )
        if not np.allclose(log_likelihoods, expected_log_likelihoods, atol=1e-12, rtol=0.0):
            raise ValueError("serialized Naive Bayes likelihoods do not match frozen counts/config")
    if training_configuration.get("naive_bayes_alpha") != float(alpha):
        raise ValueError("Naive Bayes alpha disagrees with the recorded training configuration")

    naive_bayes = MultinomialNaiveBayes(alpha=float(alpha))
    naive_bayes.classes = class_order
    naive_bayes.n_features_in_ = feature_count
    naive_bayes.class_counts_ = class_counts
    naive_bayes.feature_counts_ = feature_counts
    naive_bayes.log_priors = log_priors
    naive_bayes.log_likelihoods = log_likelihoods

    softmax_data = model_data.get("softmax_regression")
    if (
        not isinstance(softmax_data, dict)
        or softmax_data.get("algorithm") != "softmax_regression_batch_gradient_descent"
        or softmax_data.get("classes") != class_order
    ):
        raise ValueError("serialized softmax parameters are missing or have the wrong algorithm/classes")
    weights = _finite_array(
        softmax_data.get("weights_by_feature_then_class"), label="softmax weights", ndim=2
    )
    bias = _finite_array(softmax_data.get("bias"), label="softmax bias", ndim=1)
    if weights.shape != (feature_count, class_count) or bias.shape != (class_count,):
        raise ValueError("serialized softmax parameter dimensions are invalid")
    learning_rate = softmax_data.get("learning_rate")
    epochs = softmax_data.get("epochs")
    l2 = softmax_data.get("l2")
    random_seed = softmax_data.get("random_seed")
    if (
        not isinstance(learning_rate, (int, float))
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
        or not isinstance(epochs, int)
        or epochs < 1
        or not isinstance(l2, (int, float))
        or not math.isfinite(l2)
        or l2 < 0
        or not isinstance(random_seed, int)
    ):
        raise ValueError("serialized softmax configuration is invalid")
    softmax_config = training_configuration.get("softmax")
    if (
        not isinstance(softmax_config, dict)
        or softmax_config.get("learning_rate") != learning_rate
        or softmax_config.get("epochs") != epochs
        or softmax_config.get("l2") != l2
        or training_configuration.get("random_seed") != random_seed
        or training_configuration.get("softmax_learning_rate") != learning_rate
        or training_configuration.get("softmax_epochs") != epochs
        or training_configuration.get("softmax_l2") != l2
    ):
        raise ValueError("softmax parameters disagree with the recorded training configuration")
    softmax = SoftmaxRegression(
        learning_rate=float(learning_rate),
        epochs=epochs,
        l2=float(l2),
        random_seed=random_seed,
    )
    softmax.classes = class_order
    softmax.n_features_in_ = feature_count
    softmax.weights = weights
    softmax.bias = bias
    return vectorizer, naive_bayes, softmax


def validate_probabilities(
    probabilities: np.ndarray | Sequence[Sequence[float]],
    *,
    expected_rows: int,
    expected_classes: int,
    atol: float = 1e-9,
) -> dict[str, float | int | bool]:
    """Validate a probability matrix and summarize row-normalization error."""
    values = _finite_array(probabilities, label="probabilities", ndim=2)
    if expected_rows <= 0 or expected_classes <= 0:
        raise ValueError("probability expectations must be positive")
    if values.shape != (expected_rows, expected_classes):
        raise ValueError(
            f"probability shape must be {(expected_rows, expected_classes)}, got {values.shape}"
        )
    if np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("probabilities must lie in [0, 1]")
    row_sums = values.sum(axis=1)
    max_error = float(np.max(np.abs(row_sums - 1.0)))
    if not np.allclose(row_sums, 1.0, atol=atol, rtol=0.0):
        raise ValueError("each probability row must sum to 1")
    return {
        "valid": True,
        "rows": int(values.shape[0]),
        "classes": int(values.shape[1]),
        "minimum_probability": float(values.min()),
        "maximum_probability": float(values.max()),
        "maximum_absolute_row_sum_error": max_error,
    }


def classification_metrics(
    actual: Sequence[str], predicted: Sequence[str], classes: Sequence[str]
) -> dict[str, Any]:
    """Compute accuracy, fixed-label macro metrics, and a true-row confusion matrix.

    Undefined per-class metrics are represented numerically as 0.0 and marked
    with a corresponding ``*_defined=False`` flag. Macro metrics average over
    every supplied class, including unsupported or never-predicted classes.
    """
    labels = list(classes)
    actual_values = list(actual)
    predicted_values = list(predicted)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("classes must be a non-empty sequence of unique labels")
    if not actual_values or len(actual_values) != len(predicted_values):
        raise ValueError("actual and predicted must have the same non-zero length")
    label_index = {label: index for index, label in enumerate(labels)}
    if any(label not in label_index for label in actual_values + predicted_values):
        raise ValueError("actual and predicted labels must belong to classes")

    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for truth, guess in zip(actual_values, predicted_values):
        matrix[label_index[truth], label_index[guess]] += 1

    per_class: dict[str, dict[str, Any]] = {}
    precision_values: list[float] = []
    recall_values: list[float] = []
    f1_values: list[float] = []
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        support = int(matrix[index, :].sum())
        predicted_count = int(matrix[:, index].sum())
        precision_defined = predicted_count > 0
        recall_defined = support > 0
        precision = true_positive / predicted_count if precision_defined else 0.0
        recall = true_positive / support if recall_defined else 0.0
        f1_defined = precision_defined and recall_defined
        f1 = (2.0 * precision * recall / (precision + recall)) if f1_defined and (precision + recall) else 0.0
        per_class[label] = {
            "support": support,
            "predicted_count": predicted_count,
            "true_positive": true_positive,
            "precision": precision,
            "precision_defined": precision_defined,
            "recall": recall,
            "recall_defined": recall_defined,
            "f1": f1,
            "f1_defined": f1_defined,
        }
        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)

    correct = int(np.trace(matrix))
    total = len(actual_values)
    return {
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": correct / total,
        "macro_precision": float(np.mean(precision_values)),
        "macro_recall": float(np.mean(recall_values)),
        "macro_f1": float(np.mean(f1_values)),
        "classes": labels,
        "per_intent": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def confidence_distribution(probabilities: np.ndarray | Sequence[Sequence[float]]) -> dict[str, Any]:
    """Summarize max-class confidence with fixed quantiles and probability bins."""
    values = _finite_array(probabilities, label="probabilities", ndim=2)
    if values.shape[0] == 0 or values.shape[1] == 0:
        raise ValueError("confidence distribution requires non-empty probabilities")
    confidence = values.max(axis=1)
    bin_edges = np.asarray([0.0, 0.2, 0.4, 0.6, 0.8, 1.0 + np.finfo(np.float64).eps])
    counts, _ = np.histogram(confidence, bins=bin_edges)
    quantiles = np.quantile(confidence, [0.0, 0.25, 0.5, 0.75, 1.0], method="linear")
    return {
        "count": int(confidence.size),
        "minimum": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "mean": float(np.mean(confidence)),
        "q75": float(quantiles[3]),
        "maximum": float(quantiles[4]),
        "bins": {
            "[0.00, 0.20)": int(counts[0]),
            "[0.20, 0.40)": int(counts[1]),
            "[0.40, 0.60)": int(counts[2]),
            "[0.60, 0.80)": int(counts[3]),
            "[0.80, 1.00]": int(counts[4]),
        },
    }


def prediction_errors(
    records: Sequence[dict[str, str]],
    probabilities: np.ndarray,
    classes: Sequence[str] = FIXED_INTENTS,
) -> list[dict[str, Any]]:
    """Return ID, labels, confidence and top class probabilities for errors."""
    labels = list(classes)
    values = np.asarray(probabilities, dtype=np.float64)
    if values.shape != (len(records), len(labels)):
        raise ValueError("probability matrix dimensions do not match records/classes")
    predicted_indices = values.argmax(axis=1)
    results: list[dict[str, Any]] = []
    for row_index, record in enumerate(records):
        actual_label = record["intent"]
        predicted_label = labels[int(predicted_indices[row_index])]
        if predicted_label == actual_label:
            continue
        order = np.argsort(-values[row_index], kind="stable")[:3]
        results.append(
            {
                "example_id": record["example_id"],
                "actual": actual_label,
                "predicted": predicted_label,
                "confidence": float(values[row_index, predicted_indices[row_index]]),
                "actual_probability": float(values[row_index, labels.index(actual_label)]),
                "top_probabilities": [
                    {"intent": labels[int(index)], "probability": float(values[row_index, index])}
                    for index in order
                ],
            }
        )
    return results


def _equal_prior_nb_probabilities(
    features: np.ndarray, model: MultinomialNaiveBayes
) -> np.ndarray:
    """Apply equal class priors to frozen NB likelihoods without mutating them."""
    if model.log_likelihoods is None or model.log_priors is None:
        raise ValueError("Naive Bayes model is not fitted")
    class_count = len(model.classes)
    equal_log_priors = np.full(class_count, -math.log(class_count), dtype=np.float64)
    scores = features @ model.log_likelihoods.T + equal_log_priors
    shifted = scores - np.max(scores, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def evaluate_files(
    validation_path: Path,
    model_path: Path,
    *,
    expected_validation_sha256: str | None,
    expected_model_sha256: str | None,
    expected_training_sha256: str | None = None,
    expected_count: int = 56,
    classes: Sequence[str] = FIXED_INTENTS,
) -> dict[str, Any]:
    """Evaluate a frozen artifact on the specified validation file only.

    The caller supplies only one dataset path. This function has no training
    or test path, performs no fitting, and does not modify the loaded artifact.
    """
    records, validation_digest = load_validation_records(
        validation_path,
        expected_sha256=expected_validation_sha256,
        expected_count=expected_count,
        classes=classes,
    )
    artifact, model_digest = _read_pinned_json(model_path, expected_model_sha256)
    if not isinstance(artifact, dict):
        raise ValueError("model artifact must be a JSON object")
    if (
        expected_training_sha256 is not None
        and artifact.get("training_file_sha256") != expected_training_sha256
    ):
        raise ValueError("model artifact training file fingerprint does not match v1.1.0")
    vectorizer, naive_bayes, softmax = load_serialized_models(artifact, classes=classes)

    questions = [row["question"] for row in records]
    actual = [row["intent"] for row in records]
    features = vectorizer.transform(questions)
    nb_probabilities = naive_bayes.predict_proba(features)
    nb_equal_prior_probabilities = _equal_prior_nb_probabilities(features, naive_bayes)
    softmax_probabilities = softmax.predict_proba(features)

    probability_checks = {
        "naive_bayes_learned_prior": validate_probabilities(
            nb_probabilities, expected_rows=len(records), expected_classes=len(classes)
        ),
        "naive_bayes_equal_prior": validate_probabilities(
            nb_equal_prior_probabilities, expected_rows=len(records), expected_classes=len(classes)
        ),
        "softmax_regression": validate_probabilities(
            softmax_probabilities, expected_rows=len(records), expected_classes=len(classes)
        ),
    }
    models: dict[str, Any] = {}
    for name, probabilities in (
        ("naive_bayes_learned_prior", nb_probabilities),
        ("naive_bayes_equal_prior", nb_equal_prior_probabilities),
        ("softmax_regression", softmax_probabilities),
    ):
        predicted = [list(classes)[int(index)] for index in probabilities.argmax(axis=1)]
        models[name] = {
            "metrics": classification_metrics(actual, predicted, classes),
            "probability_check": probability_checks[name],
            "confidence": confidence_distribution(probabilities),
            "errors": prediction_errors(records, probabilities, classes),
            "predictions": [
                {
                    "example_id": record["example_id"],
                    "actual": record["intent"],
                    "predicted": predicted[index],
                    "confidence": float(probabilities[index].max()),
                }
                for index, record in enumerate(records)
            ],
        }

    nb_counts = naive_bayes.class_counts_.astype(int).tolist()
    return {
        "dataset_version": DATASET_VERSION,
        "validation_file": validation_path.as_posix(),
        "validation_sha256": validation_digest,
        "validation_record_count": len(records),
        "validation_intent_support": {
            label: int(sum(record["intent"] == label for record in records)) for label in classes
        },
        "model_version": artifact["model_version"],
        "model_file": model_path.as_posix(),
        "model_sha256": model_digest,
        "preprocessing_version": artifact["preprocessing_version"],
        "training_record_count": artifact["training_record_count"],
        "training_file_sha256": artifact["training_file_sha256"],
        "training_class_counts": {label: count for label, count in zip(classes, nb_counts)},
        "training_configuration": artifact["training_configuration"],
        "macro_undefined_metric_policy": "undefined per-intent metrics are set to 0.0 and included in the fixed 10-intent macro average; *_defined flags identify undefined denominators",
        "prior_comparison_note": "Equal-prior ablation is supported for Naive Bayes by replacing only the serialized learned log priors during scoring. Softmax has no separable class-prior parameter; its learned weights and bias are evaluated unchanged.",
        "models": models,
    }

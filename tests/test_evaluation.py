"""Tests for from-scratch evaluation metrics and validation-only evaluation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from ml.evaluation import (
    FIXED_INTENTS,
    classification_metrics,
    confidence_distribution,
    evaluate_files,
    validate_probabilities,
)


def test_classification_metrics_calculate_confusion_and_macro_scores() -> None:
    result = classification_metrics(
        ["a", "a", "b"], ["a", "b", "b"], ["a", "b", "c"]
    )

    assert result["confusion_matrix"] == [[1, 1, 0], [0, 1, 0], [0, 0, 0]]
    assert result["correct"] == 2
    assert result["incorrect"] == 1
    assert result["accuracy"] == pytest.approx(2 / 3)
    assert result["per_intent"]["a"]["precision"] == pytest.approx(1.0)
    assert result["per_intent"]["a"]["recall"] == pytest.approx(0.5)
    assert result["per_intent"]["a"]["f1"] == pytest.approx(2 / 3)
    assert result["macro_precision"] == pytest.approx(0.5)
    assert result["macro_recall"] == pytest.approx(0.5)
    assert result["macro_f1"] == pytest.approx(4 / 9)


def test_undefined_metrics_are_zero_flagged_and_remain_in_macro_average() -> None:
    result = classification_metrics(["a", "a"], ["a", "a"], ["a", "b"])
    missing = result["per_intent"]["b"]

    assert missing["support"] == 0
    assert missing["predicted_count"] == 0
    assert missing["precision"] == 0.0
    assert missing["precision_defined"] is False
    assert missing["recall"] == 0.0
    assert missing["recall_defined"] is False
    assert missing["f1_defined"] is False
    assert result["macro_precision"] == pytest.approx(0.5)
    assert result["macro_recall"] == pytest.approx(0.5)


@pytest.mark.parametrize(
    "actual,predicted",
    [([], []), (["a"], []), (["unknown"], ["a"]), (["a"], ["unknown"])],
)
def test_classification_metrics_reject_invalid_labels_or_lengths(
    actual: list[str], predicted: list[str]
) -> None:
    with pytest.raises(ValueError):
        classification_metrics(actual, predicted, ["a", "b"])


def test_probability_validation_checks_normalization_and_confidence_bins() -> None:
    probabilities = np.asarray([[0.2, 0.8], [0.0, 1.0], [0.55, 0.45]])
    check = validate_probabilities(probabilities, expected_rows=3, expected_classes=2)
    summary = confidence_distribution(probabilities)

    assert check["valid"] is True
    assert check["maximum_absolute_row_sum_error"] == pytest.approx(0.0)
    assert summary["count"] == 3
    assert summary["minimum"] == pytest.approx(0.55)
    assert summary["median"] == pytest.approx(0.8)
    assert summary["maximum"] == pytest.approx(1.0)
    assert sum(summary["bins"].values()) == 3


@pytest.mark.parametrize(
    "probabilities,expected_rows,expected_classes",
    [
        ([[0.4, 0.5]], 1, 2),
        ([[-0.1, 1.1]], 1, 2),
        ([[float("nan"), 0.0]], 1, 2),
        ([[0.5, 0.5]], 2, 2),
        ([[0.5, 0.5]], 1, 1),
    ],
)
def test_probability_validation_rejects_invalid_matrices(
    probabilities: list[list[float]], expected_rows: int, expected_classes: int
) -> None:
    with pytest.raises(ValueError):
        validate_probabilities(
            probabilities,
            expected_rows=expected_rows,
            expected_classes=expected_classes,
        )


def _synthetic_model() -> dict[str, Any]:
    class_count = len(FIXED_INTENTS)
    return {
        "model_version": "day4-text-processing-v2",
        "dataset_version": "day3-v1.1.0",
        "target": "intent",
        "expected_action_used": False,
        "preprocessing_version": "2.0.0",
        "evaluation_status": "not_evaluated",
        "class_order": list(FIXED_INTENTS),
        "training_record_count": class_count,
        "training_file_sha256": "synthetic-training-hash",
        "training_configuration": {
            "random_seed": 7,
            "naive_bayes_alpha": 1.0,
            "softmax_learning_rate": 0.2,
            "softmax_epochs": 1,
            "softmax_l2": 0.0,
            "softmax": {
                "learning_rate": 0.2,
                "epochs": 1,
                "l2": 0.0,
            },
        },
        "vocabulary": ["bank"],
        "models": {
            "naive_bayes": {
                "algorithm": "multinomial_naive_bayes",
                "alpha": 1.0,
                "classes": list(FIXED_INTENTS),
                "class_counts": [1.0] * class_count,
                "feature_counts_by_class": [[1.0] for _ in FIXED_INTENTS],
                "log_priors": [-math.log(class_count)] * class_count,
                "log_likelihoods": [[0.0] for _ in FIXED_INTENTS],
            },
            "softmax_regression": {
                "algorithm": "softmax_regression_batch_gradient_descent",
                "learning_rate": 0.2,
                "epochs": 1,
                "l2": 0.0,
                "random_seed": 7,
                "classes": list(FIXED_INTENTS),
                "weights_by_feature_then_class": [[0.0] * class_count],
                "bias": [0.0] * class_count,
            },
        },
    }


def _write_synthetic_inputs(directory: Path) -> tuple[Path, Path, bytes, bytes]:
    validation = directory / "validation_examples.json"
    model = directory / "model.json"
    training_decoy = directory / "training_examples.json"
    test_decoy = directory / "test_examples.json"
    validation_bytes = json.dumps(
        [
            {
                "example_id": "VAL-SYN-001",
                "question": "What bank information is available?",
                "split": "validation",
                "intent": "out_of_scope",
                "scenario_type": "ordinary",
                "expected_action": "DECLINE_OUT_OF_SCOPE",
                "supporting_passage_ids": [],
                "source_ids": [],
                "annotation_note": "Synthetic evaluator test only.",
            }
        ]
    ).encode("utf-8")
    model_bytes = json.dumps(_synthetic_model()).encode("utf-8")
    validation.write_bytes(validation_bytes)
    model.write_bytes(model_bytes)
    training_decoy.write_text("must not be accessed", encoding="utf-8")
    test_decoy.write_text("must not be accessed", encoding="utf-8")
    return validation, model, validation_bytes, model_bytes


def test_evaluator_reads_only_supplied_validation_and_model_files(
    tmp_path: Path, monkeypatch: Any
) -> None:
    validation, model, validation_bytes, model_bytes = _write_synthetic_inputs(tmp_path)
    allowed = {validation.resolve(), model.resolve()}
    accessed: list[Path] = []
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def guarded_read_bytes(path: Path) -> bytes:
        resolved = path.resolve()
        if path.name in {"training_examples.json", "test_examples.json"}:
            raise AssertionError("evaluation attempted to read a forbidden split")
        assert resolved in allowed
        accessed.append(resolved)
        return original_read_bytes(path)

    def guarded_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        raise AssertionError("evaluation should parse the explicitly supplied JSON bytes")

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    result = evaluate_files(
        validation,
        model,
        expected_validation_sha256=hashlib.sha256(validation_bytes).hexdigest(),
        expected_model_sha256=hashlib.sha256(model_bytes).hexdigest(),
        expected_count=1,
    )

    assert accessed == [validation.resolve(), model.resolve()]
    assert result["validation_record_count"] == 1
    assert set(result["models"]) == {
        "naive_bayes_learned_prior",
        "naive_bayes_equal_prior",
        "softmax_regression",
    }
    assert result["models"]["naive_bayes_learned_prior"]["metrics"]["total"] == 1


def test_evaluation_is_reproducible_and_does_not_change_model_bytes(tmp_path: Path) -> None:
    validation, model, validation_bytes, model_bytes = _write_synthetic_inputs(tmp_path)
    validation_hash = hashlib.sha256(validation_bytes).hexdigest()
    model_hash = hashlib.sha256(model_bytes).hexdigest()

    first = evaluate_files(
        validation, model, expected_validation_sha256=validation_hash,
        expected_model_sha256=model_hash, expected_count=1,
    )
    second = evaluate_files(
        validation, model, expected_validation_sha256=validation_hash,
        expected_model_sha256=model_hash, expected_count=1,
    )

    assert first == second
    assert hashlib.sha256(model.read_bytes()).hexdigest() == model_hash


def test_evaluator_rejects_changed_pinned_inputs(tmp_path: Path) -> None:
    validation, model, _, _ = _write_synthetic_inputs(tmp_path)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        evaluate_files(
            validation, model, expected_validation_sha256="0" * 64,
            expected_model_sha256=None, expected_count=1,
        )

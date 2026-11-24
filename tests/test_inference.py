from __future__ import annotations

import math

import pytest

from ml.inference import DATASET_VERSION, FIXED_INTENTS, MODEL_VERSION, NaiveBayesInference
from ml.text_processing import TEXT_PROCESSING_VERSION


def _synthetic_artifact() -> dict:
    count = len(FIXED_INTENTS)
    return {
        "model_version": MODEL_VERSION,
        "dataset_version": DATASET_VERSION,
        "target": "intent",
        "expected_action_used": False,
        "preprocessing_version": TEXT_PROCESSING_VERSION,
        "evaluation_status": "not_evaluated",
        "class_order": list(FIXED_INTENTS),
        "training_record_count": count,
        "training_configuration": {"naive_bayes_alpha": 1.0},
        "vocabulary": ["bank"],
        "models": {
            "naive_bayes": {
                "algorithm": "multinomial_naive_bayes",
                "alpha": 1.0,
                "classes": list(FIXED_INTENTS),
                "class_counts": [1.0] * count,
                "feature_counts_by_class": [[1.0] for _ in FIXED_INTENTS],
                "log_priors": [-math.log(count)] * count,
                "log_likelihoods": [[0.0] for _ in FIXED_INTENTS],
            }
        },
    }


def test_runtime_loader_restores_only_naive_bayes_without_fitting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ml.intent_classifier import MultinomialNaiveBayes

    def forbidden_fit(*args, **kwargs):
        raise AssertionError("runtime loading must not fit a model")

    monkeypatch.setattr(MultinomialNaiveBayes, "fit", forbidden_fit)
    inference = NaiveBayesInference.from_artifact(_synthetic_artifact())

    assert inference.predict_intent("bank") == FIXED_INTENTS[0]
    assert inference.predict_intent("unseen vocabulary") is None
    assert inference.predict_intent("") is None


def test_runtime_loader_rejects_invalid_metadata_and_shapes() -> None:
    artifact = _synthetic_artifact()
    artifact["evaluation_status"] = "evaluated"
    with pytest.raises(ValueError, match="metadata"):
        NaiveBayesInference.from_artifact(artifact)

    artifact = _synthetic_artifact()
    artifact["models"]["naive_bayes"]["log_priors"] = [0.0]
    with pytest.raises(ValueError, match="dimensions"):
        NaiveBayesInference.from_artifact(artifact)


def test_runtime_loader_does_not_require_or_restore_softmax() -> None:
    artifact = _synthetic_artifact()
    assert "softmax_regression" not in artifact["models"]
    inference = NaiveBayesInference.from_artifact(artifact)
    assert inference.classes == tuple(FIXED_INTENTS)

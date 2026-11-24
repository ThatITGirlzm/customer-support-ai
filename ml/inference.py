"""Runtime inference using only the frozen Day 4 Naive Bayes parameters."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ml.intent_classifier import MultinomialNaiveBayes, TextVectorizer
from ml.text_processing import TEXT_PROCESSING_VERSION


FIXED_INTENTS = (
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
MODEL_VERSION = "day4-text-processing-v2"
DATASET_VERSION = "day3-v1.1.0"


def _finite_array(value: Any, label: str, dimensions: int) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label}") from exc
    if result.ndim != dimensions or not np.all(np.isfinite(result)):
        raise ValueError(f"invalid {label}")
    return result


class NaiveBayesInference:
    """A fitted, read-only vectorizer and Naive Bayes inference adapter."""

    def __init__(self, vectorizer: TextVectorizer, model: MultinomialNaiveBayes) -> None:
        self.vectorizer = vectorizer
        self.model = model
        self.classes = tuple(model.classes)

    @classmethod
    def from_artifact(cls, artifact: Mapping[str, Any]) -> "NaiveBayesInference":
        class_order = list(FIXED_INTENTS)
        if artifact.get("model_version") != MODEL_VERSION:
            raise ValueError("model artifact version is unsupported")
        if artifact.get("dataset_version") != DATASET_VERSION:
            raise ValueError("model artifact dataset version is unsupported")
        if (
            artifact.get("target") != "intent"
            or artifact.get("expected_action_used") is not False
            or artifact.get("preprocessing_version") != TEXT_PROCESSING_VERSION
            or artifact.get("evaluation_status") != "not_evaluated"
            or artifact.get("class_order") != class_order
        ):
            raise ValueError("model artifact metadata does not match the runtime contract")

        training_count = artifact.get("training_record_count")
        if isinstance(training_count, bool) or not isinstance(training_count, int) or training_count <= 0:
            raise ValueError("model artifact training count is invalid")
        training_configuration = artifact.get("training_configuration")
        if not isinstance(training_configuration, dict):
            raise ValueError("model artifact training configuration is missing")

        vocabulary = artifact.get("vocabulary")
        if (
            not isinstance(vocabulary, list)
            or any(not isinstance(term, str) or not term for term in vocabulary)
            or vocabulary != sorted(set(vocabulary))
        ):
            raise ValueError("model vocabulary must be unique and sorted")

        models = artifact.get("models")
        nb_data = models.get("naive_bayes") if isinstance(models, dict) else None
        if (
            not isinstance(nb_data, dict)
            or nb_data.get("algorithm") != "multinomial_naive_bayes"
            or nb_data.get("classes") != class_order
        ):
            raise ValueError("Naive Bayes parameters are missing or incompatible")

        alpha = nb_data.get("alpha")
        if (
            isinstance(alpha, bool)
            or not isinstance(alpha, (int, float))
            or not math.isfinite(alpha)
            or alpha <= 0
            or training_configuration.get("naive_bayes_alpha") != float(alpha)
        ):
            raise ValueError("Naive Bayes alpha is invalid")

        class_count = len(class_order)
        feature_count = len(vocabulary)
        class_counts = _finite_array(nb_data.get("class_counts"), "class counts", 1)
        feature_counts = _finite_array(
            nb_data.get("feature_counts_by_class"), "feature counts", 2
        )
        log_priors = _finite_array(nb_data.get("log_priors"), "log priors", 1)
        log_likelihoods = _finite_array(
            nb_data.get("log_likelihoods"), "log likelihoods", 2
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
            raise ValueError("Naive Bayes parameter dimensions or counts are invalid")
        if not np.allclose(np.exp(log_priors).sum(), 1.0, atol=1e-12, rtol=0.0):
            raise ValueError("Naive Bayes priors are not normalized")
        expected_priors = np.log(class_counts / training_count)
        if not np.allclose(log_priors, expected_priors, atol=1e-12, rtol=0.0):
            raise ValueError("Naive Bayes priors do not match class counts")
        if feature_count:
            if not np.allclose(
                np.exp(log_likelihoods).sum(axis=1), 1.0, atol=1e-12, rtol=0.0
            ):
                raise ValueError("Naive Bayes likelihoods are not normalized")
            smoothed = feature_counts + float(alpha)
            expected_likelihoods = np.log(smoothed / smoothed.sum(axis=1, keepdims=True))
            if not np.allclose(
                log_likelihoods, expected_likelihoods, atol=1e-12, rtol=0.0
            ):
                raise ValueError("Naive Bayes likelihoods do not match frozen counts")

        vectorizer = TextVectorizer()
        vectorizer.vocabulary = list(vocabulary)
        vectorizer.token_to_index = {
            term: index for index, term in enumerate(vocabulary)
        }
        vectorizer._is_fitted = True

        model = MultinomialNaiveBayes(alpha=float(alpha))
        model.classes = class_order
        model.n_features_in_ = feature_count
        model.class_counts_ = class_counts
        model.feature_counts_ = feature_counts
        model.log_priors = log_priors
        model.log_likelihoods = log_likelihoods
        return cls(vectorizer, model)

    @classmethod
    def load(cls, path: str | Path) -> "NaiveBayesInference":
        try:
            with Path(path).open("r", encoding="utf-8") as source:
                artifact = json.load(source)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Naive Bayes model artifact could not be loaded") from exc
        if not isinstance(artifact, dict):
            raise ValueError("Naive Bayes model artifact must be an object")
        return cls.from_artifact(artifact)

    def predict_intent(self, question: str) -> str | None:
        if not isinstance(question, str):
            raise TypeError("question must be a string")
        features = self.vectorizer.transform([question])
        if features.shape[1] == 0 or not np.any(features):
            return None
        prediction = self.model.predict(features)
        if len(prediction) != 1 or prediction[0] not in self.classes:
            raise ValueError("Naive Bayes returned an invalid intent")
        return prediction[0]

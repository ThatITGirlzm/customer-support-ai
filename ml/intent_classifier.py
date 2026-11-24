"""From-scratch intent vectorization and classifiers implemented with NumPy."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np

from ml.text_processing import preprocess_text


def _feature_matrix(features: np.ndarray | Sequence[Sequence[float]]) -> np.ndarray:
    """Return a finite, non-negative 2-D count matrix."""
    try:
        matrix = np.asarray(features, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("features must be a numeric 2-D matrix") from exc
    if matrix.ndim != 2:
        raise ValueError("features must be a 2-D matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("features must contain only finite values")
    if np.any(matrix < 0.0):
        raise ValueError("features must be non-negative counts")
    return matrix


def _class_list(classes: Sequence[str]) -> list[str]:
    result = list(classes)
    if not result or any(not isinstance(value, str) or not value for value in result):
        raise ValueError("classes must contain non-empty string labels")
    if len(set(result)) != len(result):
        raise ValueError("classes must be unique")
    return result


def _training_label_indices(
    labels: Sequence[str], classes: Sequence[str], row_count: int
) -> np.ndarray:
    if len(labels) != row_count:
        raise ValueError("features and labels must have the same length")
    if row_count == 0:
        raise ValueError("at least one training example is required")
    class_to_index = {label: index for index, label in enumerate(classes)}
    if any(not isinstance(label, str) or label not in class_to_index for label in labels):
        raise ValueError("every training label must be included in classes")
    observed = set(labels)
    missing = set(classes) - observed
    if missing:
        raise ValueError(f"every class needs training examples; missing={sorted(missing)}")
    return np.asarray([class_to_index[label] for label in labels], dtype=np.int64)


def _normalized_rows(features: np.ndarray) -> np.ndarray:
    """Normalize count vectors; zero rows remain zero vectors."""
    totals = features.sum(axis=1, keepdims=True)
    return features / np.maximum(totals, 1.0)


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Compute row-wise probabilities with max-subtraction for stability."""
    if logits.ndim != 2:
        raise ValueError("logits must be a 2-D matrix")
    if logits.shape[0] == 0:
        return np.zeros_like(logits, dtype=np.float64)
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def _softmax_loss_and_gradients(
    normalized_features: np.ndarray,
    label_indices: np.ndarray,
    weights: np.ndarray,
    bias: np.ndarray,
    l2: float,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Cross-entropy objective and analytical gradients for softmax regression."""
    if normalized_features.shape[0] == 0:
        raise ValueError("at least one example is required to calculate loss")
    class_count = weights.shape[1]
    targets = np.zeros((len(label_indices), class_count), dtype=np.float64)
    targets[np.arange(len(label_indices)), label_indices] = 1.0

    logits = normalized_features @ weights + bias
    probabilities = _softmax(logits)
    selected = probabilities[np.arange(len(label_indices)), label_indices]
    cross_entropy = -np.log(np.maximum(selected, np.finfo(np.float64).tiny)).mean()
    regularization = 0.5 * l2 * float(np.sum(weights * weights))
    loss = cross_entropy + regularization

    error = (probabilities - targets) / len(label_indices)
    gradient_weights = normalized_features.T @ error + l2 * weights
    gradient_bias = error.sum(axis=0)
    return loss, gradient_weights, gradient_bias


class TextVectorizer:
    """Build and apply a deterministic sorted unigram count vocabulary."""

    def __init__(self) -> None:
        self.vocabulary: list[str] = []
        self.token_to_index: dict[str, int] = {}
        self._is_fitted = False

    @staticmethod
    def _validated_questions(questions: Sequence[str]) -> list[str]:
        values = list(questions)
        if any(not isinstance(question, str) for question in values):
            raise TypeError("questions must contain only strings")
        return values

    def fit(self, questions: Sequence[str]) -> "TextVectorizer":
        values = self._validated_questions(questions)
        tokens = {token for question in values for token in preprocess_text(question)}
        self.vocabulary = sorted(tokens)
        self.token_to_index = {token: index for index, token in enumerate(self.vocabulary)}
        self._is_fitted = True
        return self

    def transform(self, questions: Sequence[str]) -> np.ndarray:
        if not self._is_fitted:
            raise ValueError("The vectorizer must be fitted before transform().")
        values = self._validated_questions(questions)
        matrix = np.zeros((len(values), len(self.vocabulary)), dtype=np.float64)
        for row_index, question in enumerate(values):
            for token, count in Counter(preprocess_text(question)).items():
                column = self.token_to_index.get(token)
                if column is not None:
                    matrix[row_index, column] = float(count)
        return matrix

    def fit_transform(self, questions: Sequence[str]) -> np.ndarray:
        values = self._validated_questions(questions)
        self.fit(values)
        return self.transform(values)


class MultinomialNaiveBayes:
    """Multinomial Naive Bayes with additive Laplace smoothing."""

    def __init__(self, alpha: float = 1.0) -> None:
        if not np.isfinite(alpha) or alpha <= 0.0:
            raise ValueError("alpha must be finite and positive")
        self.alpha = float(alpha)
        self.classes: list[str] = []
        self.n_features_in_: int | None = None
        self.class_counts_: np.ndarray | None = None
        self.feature_counts_: np.ndarray | None = None
        self.log_priors: np.ndarray | None = None
        self.log_likelihoods: np.ndarray | None = None

    def fit(
        self,
        features: np.ndarray | Sequence[Sequence[float]],
        labels: Sequence[str],
        classes: Sequence[str],
    ) -> "MultinomialNaiveBayes":
        matrix = _feature_matrix(features)
        self.classes = _class_list(classes)
        label_indices = _training_label_indices(labels, self.classes, matrix.shape[0])
        self.n_features_in_ = matrix.shape[1]

        self.class_counts_ = np.bincount(
            label_indices, minlength=len(self.classes)
        ).astype(np.float64)
        self.feature_counts_ = np.zeros(
            (len(self.classes), matrix.shape[1]), dtype=np.float64
        )
        for row_index, class_index in enumerate(label_indices):
            self.feature_counts_[class_index] += matrix[row_index]

        self.log_priors = np.log(self.class_counts_ / self.class_counts_.sum())
        if matrix.shape[1] == 0:
            # With no observed terms, all document evidence is the class prior.
            self.log_likelihoods = np.zeros((len(self.classes), 0), dtype=np.float64)
        else:
            smoothed_counts = self.feature_counts_ + self.alpha
            denominators = smoothed_counts.sum(axis=1, keepdims=True)
            self.log_likelihoods = np.log(smoothed_counts / denominators)
        return self

    def _check_fitted(self) -> None:
        if self.log_priors is None or self.log_likelihoods is None or self.n_features_in_ is None:
            raise ValueError("The model must be fitted before prediction.")

    def _prediction_features(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        self._check_fitted()
        matrix = _feature_matrix(features)
        if matrix.shape[1] != self.n_features_in_:
            raise ValueError(
                f"feature count mismatch: expected {self.n_features_in_}, got {matrix.shape[1]}"
            )
        return matrix

    def predict_log_proba(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        matrix = self._prediction_features(features)
        scores = matrix @ self.log_likelihoods.T + self.log_priors
        if scores.shape[0] == 0:
            return scores
        row_maxima = scores.max(axis=1, keepdims=True)
        shifted = scores - row_maxima
        log_normalizers = row_maxima + np.log(np.exp(shifted).sum(axis=1, keepdims=True))
        return scores - log_normalizers

    def predict_proba(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        return np.exp(self.predict_log_proba(features))

    def predict(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> list[str]:
        probabilities = self.predict_proba(features)
        return [self.classes[index] for index in probabilities.argmax(axis=1)]

    def to_dict(self) -> dict[str, object]:
        self._check_fitted()
        return {
            "algorithm": "multinomial_naive_bayes",
            "alpha": self.alpha,
            "classes": self.classes,
            "class_counts": self.class_counts_.tolist(),
            "feature_counts_by_class": self.feature_counts_.tolist(),
            "log_priors": self.log_priors.tolist(),
            "log_likelihoods": self.log_likelihoods.tolist(),
        }


class SoftmaxRegression:
    """Multiclass softmax regression with deterministic seeded initialization."""

    def __init__(
        self,
        learning_rate: float = 0.2,
        epochs: int = 400,
        l2: float = 1e-4,
        random_seed: int = 20261112,
    ) -> None:
        if not np.isfinite(learning_rate) or learning_rate <= 0.0:
            raise ValueError("learning_rate must be finite and positive")
        if not isinstance(epochs, int) or epochs < 1:
            raise ValueError("epochs must be a positive integer")
        if not np.isfinite(l2) or l2 < 0.0:
            raise ValueError("l2 must be finite and non-negative")
        if not isinstance(random_seed, int):
            raise ValueError("random_seed must be an integer")
        self.learning_rate = float(learning_rate)
        self.epochs = epochs
        self.l2 = float(l2)
        self.random_seed = random_seed
        self.classes: list[str] = []
        self.n_features_in_: int | None = None
        self.weights: np.ndarray | None = None
        self.bias: np.ndarray | None = None

    def fit(
        self,
        features: np.ndarray | Sequence[Sequence[float]],
        labels: Sequence[str],
        classes: Sequence[str],
    ) -> "SoftmaxRegression":
        matrix = _feature_matrix(features)
        self.classes = _class_list(classes)
        label_indices = _training_label_indices(labels, self.classes, matrix.shape[0])
        self.n_features_in_ = matrix.shape[1]
        normalized = _normalized_rows(matrix)

        rng = np.random.default_rng(self.random_seed)
        self.weights = rng.normal(
            loc=0.0,
            scale=0.01,
            size=(matrix.shape[1], len(self.classes)),
        )
        self.bias = np.zeros(len(self.classes), dtype=np.float64)
        for _ in range(self.epochs):
            _, gradient_weights, gradient_bias = _softmax_loss_and_gradients(
                normalized, label_indices, self.weights, self.bias, self.l2
            )
            self.weights -= self.learning_rate * gradient_weights
            self.bias -= self.learning_rate * gradient_bias
        return self

    def _check_fitted(self) -> None:
        if self.weights is None or self.bias is None or self.n_features_in_ is None:
            raise ValueError("The model must be fitted before prediction.")

    def _prediction_features(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        self._check_fitted()
        matrix = _feature_matrix(features)
        if matrix.shape[1] != self.n_features_in_:
            raise ValueError(
                f"feature count mismatch: expected {self.n_features_in_}, got {matrix.shape[1]}"
            )
        return _normalized_rows(matrix)

    def decision_function(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        normalized = self._prediction_features(features)
        return normalized @ self.weights + self.bias

    def predict_proba(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> np.ndarray:
        return _softmax(self.decision_function(features))

    def predict(
        self, features: np.ndarray | Sequence[Sequence[float]]
    ) -> list[str]:
        probabilities = self.predict_proba(features)
        return [self.classes[index] for index in probabilities.argmax(axis=1)]

    def loss_and_gradients(
        self,
        features: np.ndarray | Sequence[Sequence[float]],
        labels: Sequence[str],
    ) -> tuple[float, np.ndarray, np.ndarray]:
        self._check_fitted()
        matrix = _feature_matrix(features)
        if matrix.shape[1] != self.n_features_in_:
            raise ValueError(
                f"feature count mismatch: expected {self.n_features_in_}, got {matrix.shape[1]}"
            )
        class_to_index = {label: index for index, label in enumerate(self.classes)}
        if len(labels) != matrix.shape[0] or matrix.shape[0] == 0:
            raise ValueError("features and labels must have the same non-zero length")
        if any(not isinstance(label, str) or label not in class_to_index for label in labels):
            raise ValueError("every label must be included in the fitted classes")
        label_indices = np.asarray([class_to_index[label] for label in labels], dtype=np.int64)
        return _softmax_loss_and_gradients(
            _normalized_rows(matrix), label_indices, self.weights, self.bias, self.l2
        )

    def loss(
        self,
        features: np.ndarray | Sequence[Sequence[float]],
        labels: Sequence[str],
    ) -> float:
        return self.loss_and_gradients(features, labels)[0]

    def to_dict(self) -> dict[str, object]:
        self._check_fitted()
        return {
            "algorithm": "softmax_regression_batch_gradient_descent",
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "l2": self.l2,
            "random_seed": self.random_seed,
            "classes": self.classes,
            "weights_by_feature_then_class": self.weights.tolist(),
            "bias": self.bias.tolist(),
        }

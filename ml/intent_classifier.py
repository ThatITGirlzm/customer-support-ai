"""Small from-scratch intent models using NumPy and the shared tokenizer."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np

from ml.text_processing import preprocess_text


class TextVectorizer:
    """Build a deterministic count vocabulary from the supplied training text."""

    def __init__(self) -> None:
        self.vocabulary: list[str] = []
        self.token_to_index: dict[str, int] = {}

    def fit(self, questions: Sequence[str]) -> "TextVectorizer":
        tokens = {token for question in questions for token in preprocess_text(question)}
        self.vocabulary = sorted(tokens)
        self.token_to_index = {token: index for index, token in enumerate(self.vocabulary)}
        return self

    def transform(self, questions: Sequence[str]) -> np.ndarray:
        if not self.vocabulary:
            raise ValueError("The vectorizer must be fitted before transform().")
        matrix = np.zeros((len(questions), len(self.vocabulary)), dtype=np.float64)
        for row_index, question in enumerate(questions):
            for token, count in Counter(preprocess_text(question)).items():
                column = self.token_to_index.get(token)
                if column is not None:
                    matrix[row_index, column] = float(count)
        return matrix


class MultinomialNaiveBayes:
    """Multinomial Naive Bayes with Laplace smoothing, implemented in NumPy."""

    def __init__(self, alpha: float = 1.0) -> None:
        if alpha <= 0:
            raise ValueError("alpha must be positive.")
        self.alpha = alpha
        self.classes: list[str] = []
        self.log_priors: np.ndarray | None = None
        self.log_likelihoods: np.ndarray | None = None

    def fit(self, features: np.ndarray, labels: Sequence[str], classes: Sequence[str]) -> "MultinomialNaiveBayes":
        self.classes = list(classes)
        class_to_index = {label: index for index, label in enumerate(self.classes)}
        if any(label not in class_to_index for label in labels):
            raise ValueError("Every training label must be in the fixed intent list.")

        label_indices = np.asarray([class_to_index[label] for label in labels], dtype=np.int64)
        class_counts = np.bincount(label_indices, minlength=len(self.classes)).astype(np.float64)
        token_counts = np.zeros((len(self.classes), features.shape[1]), dtype=np.float64)
        for row_index, class_index in enumerate(label_indices):
            token_counts[class_index] += features[row_index]

        self.log_priors = np.log(class_counts / class_counts.sum())
        smoothed = token_counts + self.alpha
        denominators = smoothed.sum(axis=1, keepdims=True)
        self.log_likelihoods = np.log(smoothed / denominators)
        return self

    def to_dict(self) -> dict[str, object]:
        if self.log_priors is None or self.log_likelihoods is None:
            raise ValueError("The model must be fitted before serialization.")
        return {
            "algorithm": "multinomial_naive_bayes",
            "alpha": self.alpha,
            "classes": self.classes,
            "log_priors": self.log_priors.tolist(),
            "log_likelihoods": self.log_likelihoods.tolist(),
        }


class SoftmaxRegression:
    """Multiclass softmax regression trained by deterministic batch gradient descent."""

    def __init__(self, learning_rate: float = 0.2, epochs: int = 400, l2: float = 1e-4) -> None:
        if learning_rate <= 0 or epochs < 1 or l2 < 0:
            raise ValueError("Invalid softmax hyperparameters.")
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2
        self.classes: list[str] = []
        self.weights: np.ndarray | None = None
        self.bias: np.ndarray | None = None

    def fit(self, features: np.ndarray, labels: Sequence[str], classes: Sequence[str]) -> "SoftmaxRegression":
        self.classes = list(classes)
        class_to_index = {label: index for index, label in enumerate(self.classes)}
        if any(label not in class_to_index for label in labels):
            raise ValueError("Every training label must be in the fixed intent list.")
        if features.shape[0] != len(labels):
            raise ValueError("Feature rows and training labels must have equal length.")

        # Per-question count normalization keeps longer requests from dominating.
        row_totals = np.maximum(features.sum(axis=1, keepdims=True), 1.0)
        x = features / row_totals
        label_indices = np.asarray([class_to_index[label] for label in labels], dtype=np.int64)
        targets = np.zeros((len(labels), len(self.classes)), dtype=np.float64)
        targets[np.arange(len(labels)), label_indices] = 1.0

        self.weights = np.zeros((x.shape[1], len(self.classes)), dtype=np.float64)
        self.bias = np.zeros(len(self.classes), dtype=np.float64)
        for _ in range(self.epochs):
            logits = x @ self.weights + self.bias
            logits -= logits.max(axis=1, keepdims=True)
            probabilities = np.exp(logits)
            probabilities /= probabilities.sum(axis=1, keepdims=True)
            error = (probabilities - targets) / len(labels)
            gradient_weights = x.T @ error + self.l2 * self.weights
            gradient_bias = error.sum(axis=0)
            self.weights -= self.learning_rate * gradient_weights
            self.bias -= self.learning_rate * gradient_bias
        return self

    def to_dict(self) -> dict[str, object]:
        if self.weights is None or self.bias is None:
            raise ValueError("The model must be fitted before serialization.")
        return {
            "algorithm": "softmax_regression_batch_gradient_descent",
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "l2": self.l2,
            "classes": self.classes,
            "weights_by_feature_then_class": self.weights.tolist(),
            "bias": self.bias.tolist(),
        }

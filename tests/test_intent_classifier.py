"""Numerical and API tests for the from-scratch intent classifiers."""

from __future__ import annotations

import numpy as np
import pytest

from ml.intent_classifier import MultinomialNaiveBayes, SoftmaxRegression, TextVectorizer


def test_vectorizer_builds_sorted_vocabulary_and_count_features() -> None:
    vectorizer = TextVectorizer().fit(["Banks fees fees", "bank fee"])

    assert vectorizer.vocabulary == ["bank", "fee"]
    np.testing.assert_array_equal(
        vectorizer.transform(["Banks fees fees", "bank fee"]),
        np.asarray([[1.0, 2.0], [1.0, 1.0]]),
    )


def test_vectorizer_ignores_unknown_terms_and_accepts_empty_text() -> None:
    vectorizer = TextVectorizer().fit(["bank account"])
    features = vectorizer.transform(["unseen token", "", "??? 42"])

    assert features.shape == (3, len(vectorizer.vocabulary))
    np.testing.assert_array_equal(features[0], np.zeros(len(vectorizer.vocabulary)))
    np.testing.assert_array_equal(features[1], np.zeros(len(vectorizer.vocabulary)))
    np.testing.assert_array_equal(features[2], np.zeros(len(vectorizer.vocabulary)))


def test_vectorizer_supports_fitted_empty_vocabulary() -> None:
    vectorizer = TextVectorizer().fit(["?!", "—"])
    assert vectorizer.vocabulary == []
    assert vectorizer.transform(["", "numbers 7.5"]).shape == (2, 0)
    assert vectorizer.transform([]).shape == (0, 0)


def test_vectorizer_requires_fit_and_string_inputs() -> None:
    with pytest.raises(ValueError, match="fitted"):
        TextVectorizer().transform(["bank"])
    with pytest.raises(TypeError, match="string"):
        TextVectorizer().fit(["bank", None])  # type: ignore[list-item]


def test_naive_bayes_calculates_priors_and_laplace_likelihoods() -> None:
    features = np.asarray([[2.0, 0.0], [0.0, 0.0], [0.0, 4.0]])
    labels = ["complaints_process", "complaints_process", "out_of_scope"]
    model = MultinomialNaiveBayes(alpha=1.0).fit(
        features, labels, ["complaints_process", "out_of_scope"]
    )

    np.testing.assert_allclose(model.log_priors, np.log([2.0 / 3.0, 1.0 / 3.0]))
    np.testing.assert_allclose(
        np.exp(model.log_likelihoods),
        np.asarray([[3.0 / 4.0, 1.0 / 4.0], [1.0 / 6.0, 5.0 / 6.0]]),
    )
    np.testing.assert_allclose(np.exp(model.log_likelihoods).sum(axis=1), [1.0, 1.0])


def test_naive_bayes_probabilities_normalize_and_predictions_use_class_labels() -> None:
    features = np.asarray([[2.0, 0.0], [0.0, 2.0]])
    labels = ["complaints_process", "out_of_scope"]
    classes = ["complaints_process", "out_of_scope"]
    model = MultinomialNaiveBayes().fit(features, labels, classes)

    probabilities = model.predict_proba(np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]))
    assert probabilities.shape == (3, 2)
    assert np.all(np.isfinite(probabilities))
    assert np.all(probabilities >= 0.0)
    np.testing.assert_allclose(probabilities.sum(axis=1), np.ones(3))
    assert model.predict(np.asarray([[1.0, 0.0], [0.0, 1.0]])) == [
        "complaints_process",
        "out_of_scope",
    ]
    assert set(model.predict(np.asarray([[0.0, 0.0]]))).issubset(set(classes))


def test_naive_bayes_empty_vocabulary_uses_class_priors() -> None:
    features = np.zeros((3, 0), dtype=np.float64)
    model = MultinomialNaiveBayes().fit(
        features, ["complaints_process", "complaints_process", "out_of_scope"],
        ["complaints_process", "out_of_scope"],
    )
    np.testing.assert_allclose(
        model.predict_proba(np.zeros((1, 0))),
        np.asarray([[2.0 / 3.0, 1.0 / 3.0]]),
    )


def test_naive_bayes_fit_is_deterministic() -> None:
    features = np.asarray([[1.0, 0.0], [0.0, 2.0], [1.0, 1.0]])
    labels = ["a", "b", "a"]
    first = MultinomialNaiveBayes(alpha=0.5).fit(features, labels, ["a", "b"])
    second = MultinomialNaiveBayes(alpha=0.5).fit(features, labels, ["a", "b"])

    np.testing.assert_array_equal(first.log_priors, second.log_priors)
    np.testing.assert_array_equal(first.log_likelihoods, second.log_likelihoods)
    np.testing.assert_array_equal(first.predict_proba(features), second.predict_proba(features))


def test_naive_bayes_rejects_invalid_training_inputs() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        MultinomialNaiveBayes().fit(np.asarray([[1.0, -1.0]]), ["a"], ["a"])
    with pytest.raises(ValueError, match="label"):
        MultinomialNaiveBayes().fit(np.asarray([[1.0]]), ["b"], ["a"])
    with pytest.raises(ValueError, match="length"):
        MultinomialNaiveBayes().fit(np.asarray([[1.0]]), [], ["a"])


def test_softmax_forward_pass_matches_hand_calculated_logits() -> None:
    model = SoftmaxRegression(epochs=1, random_seed=13).fit(
        np.asarray([[1.0, 0.0], [0.0, 1.0]]),
        ["complaints_process", "out_of_scope"],
        ["complaints_process", "out_of_scope"],
    )
    model.weights = np.asarray([[0.5, -0.5], [-0.25, 0.25]])
    model.bias = np.asarray([0.1, -0.1])
    features = np.asarray([[2.0, 0.0], [0.0, 4.0]])

    np.testing.assert_allclose(
        model.decision_function(features),
        np.asarray([[0.6, -0.6], [-0.15, 0.15]]),
    )
    expected = np.exp([[0.6, -0.6], [-0.15, 0.15]])
    expected /= expected.sum(axis=1, keepdims=True)
    np.testing.assert_allclose(model.predict_proba(features), expected)


def test_softmax_gradient_matches_finite_differences() -> None:
    features = np.asarray([[2.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    labels = ["a", "b", "c"]
    model = SoftmaxRegression(epochs=1, l2=0.07, random_seed=5).fit(
        features, labels, ["a", "b", "c"]
    )
    model.weights = np.asarray([[0.13, -0.08, 0.04], [-0.11, 0.09, 0.02]])
    model.bias = np.asarray([0.03, -0.02, 0.01])
    loss, gradient_weights, gradient_bias = model.loss_and_gradients(features, labels)
    assert np.isfinite(loss)

    epsilon = 1e-6
    numeric_weights = np.zeros_like(model.weights)
    for index in np.ndindex(model.weights.shape):
        original = model.weights[index]
        model.weights[index] = original + epsilon
        plus = model.loss(features, labels)
        model.weights[index] = original - epsilon
        minus = model.loss(features, labels)
        model.weights[index] = original
        numeric_weights[index] = (plus - minus) / (2.0 * epsilon)

    numeric_bias = np.zeros_like(model.bias)
    for index in range(len(model.bias)):
        original = model.bias[index]
        model.bias[index] = original + epsilon
        plus = model.loss(features, labels)
        model.bias[index] = original - epsilon
        minus = model.loss(features, labels)
        model.bias[index] = original
        numeric_bias[index] = (plus - minus) / (2.0 * epsilon)

    np.testing.assert_allclose(gradient_weights, numeric_weights, rtol=1e-5, atol=1e-7)
    np.testing.assert_allclose(gradient_bias, numeric_bias, rtol=1e-5, atol=1e-7)


def test_softmax_probabilities_and_predictions_are_valid() -> None:
    features = np.asarray([[2.0, 0.0], [0.0, 2.0], [1.0, 1.0]])
    labels = ["complaints_process", "out_of_scope", "complaints_process"]
    classes = ["complaints_process", "out_of_scope"]
    model = SoftmaxRegression(epochs=20, random_seed=21).fit(features, labels, classes)
    probabilities = model.predict_proba(np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]))

    assert probabilities.shape == (3, 2)
    assert np.all(np.isfinite(probabilities))
    assert np.all(probabilities >= 0.0)
    assert np.all(probabilities <= 1.0)
    np.testing.assert_allclose(probabilities.sum(axis=1), np.ones(3))
    assert set(model.predict(features)).issubset(set(classes))


def test_softmax_unknown_terms_and_empty_vocabulary_are_supported() -> None:
    vectorizer = TextVectorizer().fit(["bank fee", "wallet payment"])
    training = vectorizer.transform(["bank fee", "wallet payment"])
    model = SoftmaxRegression(epochs=3, random_seed=3).fit(
        training, ["complaints_process", "payments_mobile_money"],
        ["complaints_process", "payments_mobile_money"],
    )
    unknown = vectorizer.transform(["unseen phrase", ""])
    assert np.all(unknown == 0.0)
    assert model.predict_proba(unknown).shape == (2, 2)

    empty = np.zeros((2, 0), dtype=np.float64)
    empty_model = SoftmaxRegression(epochs=2, random_seed=3).fit(
        empty, ["a", "b"], ["a", "b"]
    )
    assert empty_model.predict_proba(np.zeros((1, 0))).shape == (1, 2)


def test_softmax_training_is_deterministic_for_a_fixed_seed() -> None:
    features = np.asarray([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    labels = ["a", "b", "a"]
    first = SoftmaxRegression(epochs=12, random_seed=20261112).fit(features, labels, ["a", "b"])
    second = SoftmaxRegression(epochs=12, random_seed=20261112).fit(features, labels, ["a", "b"])

    np.testing.assert_array_equal(first.weights, second.weights)
    np.testing.assert_array_equal(first.bias, second.bias)
    np.testing.assert_array_equal(first.predict_proba(features), second.predict_proba(features))


def test_models_validate_probability_inputs_and_unfitted_state() -> None:
    with pytest.raises(ValueError, match="fitted"):
        MultinomialNaiveBayes().predict(np.zeros((1, 1)))
    with pytest.raises(ValueError, match="fitted"):
        SoftmaxRegression().predict_proba(np.zeros((1, 1)))

    model = SoftmaxRegression(epochs=1).fit(
        np.asarray([[1.0], [2.0]]), ["a", "b"], ["a", "b"]
    )
    with pytest.raises(ValueError, match="feature"):
        model.predict_proba(np.zeros((1, 2)))
    with pytest.raises(ValueError, match="finite"):
        model.predict_proba(np.asarray([[np.nan]]))


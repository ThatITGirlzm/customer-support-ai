"""Tests that classifier fitting reads training inputs only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from scripts.train_day3_v1_1_classifier import train_from_training_file


TWO_CLASSES = ["complaints_process", "out_of_scope"]


def write_training_fixture(path: Path, actions: list[str] | None = None) -> None:
    actions = actions or ["unused-one", "unused-two", "unused-three", "unused-four"]
    rows = [
        {"example_id": "A", "question": "complaint about a provider", "intent": "complaints_process", "expected_action": actions[0]},
        {"example_id": "B", "question": "raise a provider complaint", "intent": "complaints_process", "expected_action": actions[1]},
        {"example_id": "C", "question": "please access my own account", "intent": "out_of_scope", "expected_action": actions[2]},
        {"example_id": "D", "question": "look up my personal balance", "intent": "out_of_scope", "expected_action": actions[3]},
    ]
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_training_reads_only_the_training_fixture(tmp_path: Path, monkeypatch: Any) -> None:
    training = tmp_path / "training_examples.json"
    validation = tmp_path / "validation_examples.json"
    test = tmp_path / "test_examples.json"
    output = tmp_path / "models" / "model.json"
    metadata = tmp_path / "dataset_metadata.json"
    write_training_fixture(training)
    validation.write_text("DO NOT READ VALIDATION", encoding="utf-8")
    test.write_text("DO NOT READ TEST", encoding="utf-8")
    metadata.write_text('{"sentinel":"unchanged"}', encoding="utf-8")
    original_metadata = metadata.read_bytes()

    read_text = Path.read_text
    read_bytes = Path.read_bytes
    accessed: list[Path] = []

    def guarded_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        accessed.append(path.resolve())
        assert path.resolve() not in {validation.resolve(), test.resolve()}
        assert path.resolve() != metadata.resolve()
        return read_text(path, *args, **kwargs)

    def guarded_read_bytes(path: Path, *args: Any, **kwargs: Any) -> bytes:
        accessed.append(path.resolve())
        assert path.resolve() not in {validation.resolve(), test.resolve()}
        assert path.resolve() != metadata.resolve()
        return read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    artifact = train_from_training_file(
        training, output, classes=TWO_CLASSES, dataset_version="synthetic-test-fixture"
    )

    assert set(accessed) == {training.resolve()}
    assert output.is_file()
    assert read_bytes(metadata) == original_metadata
    assert artifact["target"] == "intent"
    assert artifact["expected_action_used"] is False
    assert artifact["training_record_count"] == 4
    assert artifact["dataset_version"] == "synthetic-test-fixture"
    assert artifact["validation_file_hash"] is None
    assert artifact["test_file_hash"] is None


def test_expected_action_values_do_not_change_fitted_parameters(tmp_path: Path) -> None:
    first_file = tmp_path / "first_training.json"
    second_file = tmp_path / "second_training.json"
    write_training_fixture(first_file, ["one", "one", "one", "one"])
    write_training_fixture(second_file, ["different", "values", "ignored", "actions"])

    first = train_from_training_file(
        first_file, tmp_path / "first.json", classes=TWO_CLASSES,
        dataset_version="synthetic-test-fixture", random_seed=17,
    )
    second = train_from_training_file(
        second_file, tmp_path / "second.json", classes=TWO_CLASSES,
        dataset_version="synthetic-test-fixture", random_seed=17,
    )

    assert first["vocabulary"] == second["vocabulary"]
    assert first["models"] == second["models"]
    assert first["target"] == "intent"
    assert first["expected_action_used"] is False


def test_training_configuration_and_preprocessing_version_are_recorded(tmp_path: Path) -> None:
    training = tmp_path / "training_examples.json"
    write_training_fixture(training)
    artifact = train_from_training_file(
        training, tmp_path / "model.json", classes=TWO_CLASSES,
        dataset_version="day3-v1.1.0", random_seed=20261112,
    )

    assert artifact["preprocessing_version"] == "2.0.0"
    assert artifact["training_configuration"]["random_seed"] == 20261112
    assert artifact["training_configuration"]["randomness_used"] is True
    assert artifact["training_configuration"]["naive_bayes_alpha"] == 1.0
    assert artifact["training_configuration"]["softmax_epochs"] == 400
    assert artifact["fit_data"] == "training questions and intent labels only"
    assert "expected_action" not in artifact["training_configuration"]


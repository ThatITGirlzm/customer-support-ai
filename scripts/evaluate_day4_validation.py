"""Evaluate the pinned Day 4 models on the frozen v1.1.0 validation set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.evaluation import evaluate_files


VALIDATION_FILE = ROOT / "data" / "day3-v1.1.0" / "validation_examples.json"
MODEL_FILE = ROOT / "data" / "models" / "day4-text-processing-v2" / "intent_models.json"
VALIDATION_SHA256 = "75afa098c7ee5d2fc87d3898c58bbab404522dbf7f1f3ffb0e261efdeff99c89"
MODEL_SHA256 = "728b0b9437c135254f504de199b57417027e739725651421e30b87f405fc5f12"
TRAINING_SHA256 = "1681ab46cde745fd2fb3863f165e752d7d4cdca52b3a264be79a10362c25610a"


def main() -> int:
    """Run a read-only evaluation with pinned input paths and fingerprints."""
    results = evaluate_files(
        VALIDATION_FILE,
        MODEL_FILE,
        expected_validation_sha256=VALIDATION_SHA256,
        expected_model_sha256=MODEL_SHA256,
        expected_training_sha256=TRAINING_SHA256,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

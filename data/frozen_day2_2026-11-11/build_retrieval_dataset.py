"""Build the approved, retrieval-enabled passage dataset from its source file.

Run with ``python build_retrieval_dataset.py --write`` to materialize the
retrieval input, or ``--check`` to confirm the checked-in dataset is current.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APPROVED_FILE = ROOT / "data" / "approved_passages.json"
RETRIEVAL_FILE = ROOT / "data" / "retrieval_passages.json"


def expected_records() -> list[dict[str, object]]:
    """Return only approved records explicitly enabled for retrieval."""
    records = json.loads(APPROVED_FILE.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("approved_passages.json must contain a JSON array")
    return [
        row
        for row in records
        if isinstance(row, dict)
        and row.get("status") == "APPROVED"
        and row.get("retrieval_enabled") is True
    ]


def serialized(records: list[dict[str, object]]) -> str:
    """Serialize deterministically for readable diffs and reproducible checks."""
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="write the derived dataset")
    action.add_argument("--check", action="store_true", help="check it matches the source dataset")
    args = parser.parse_args()
    expected = serialized(expected_records())

    if args.write:
        RETRIEVAL_FILE.write_text(expected, encoding="utf-8", newline="\n")
        print(f"Wrote {len(json.loads(expected))} retrieval-enabled approved passages to {RETRIEVAL_FILE.relative_to(ROOT)}.")
        return 0

    if not RETRIEVAL_FILE.is_file():
        print(f"FAIL: missing {RETRIEVAL_FILE.relative_to(ROOT)}; run with --write.")
        return 1
    actual = RETRIEVAL_FILE.read_text(encoding="utf-8")
    if actual != expected:
        print("FAIL: retrieval_passages.json is stale; regenerate it with --write.")
        return 1
    print(f"PASS: retrieval_passages.json exactly matches {len(json.loads(expected))} approved, retrieval-enabled passages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

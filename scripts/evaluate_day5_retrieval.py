"""Run the frozen Day 5 retrieval evaluation on validation data only.

This script intentionally has no command-line dataset selector and contains
no test-set path. It verifies the pinned validation and retrieval-corpus
hashes before parsing either file.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.retrieval import load_corpus
from ml.retrieval_evaluation import evaluate_records


CORPUS_FILE = ROOT / "data" / "retrieval_passages.json"
VALIDATION_FILE = ROOT / "data" / "answerable_validation.json"
CORPUS_SHA256 = "be6e2104182827fb5065dadab82295007886695964a920183a895db467c7a193"
VALIDATION_SHA256 = "2d61fb74f51372a4323b6c21182914cdc778369d0cc9d210a8bbf6c78e89adcd"
EXPECTED_VALIDATION_COUNT = 15


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    """Verify pinned inputs and report validation-only ranking metrics."""
    actual_corpus_hash = _sha256(CORPUS_FILE)
    actual_validation_hash = _sha256(VALIDATION_FILE)
    if actual_corpus_hash != CORPUS_SHA256:
        raise SystemExit("retrieval corpus hash changed; evaluation stopped")
    if actual_validation_hash != VALIDATION_SHA256:
        raise SystemExit("retrieval validation hash changed; evaluation stopped")

    passages = load_corpus(CORPUS_FILE)
    rows = _load_json(VALIDATION_FILE)
    if not isinstance(rows, list) or len(rows) != EXPECTED_VALIDATION_COUNT:
        raise SystemExit(f"expected exactly {EXPECTED_VALIDATION_COUNT} validation rows")

    passages_by_id = {passage.passage_id: passage for passage in passages}
    for row in rows:
        if not isinstance(row, dict):
            raise SystemExit("validation records must be JSON objects")
        if row.get("split") != "validation":
            raise SystemExit(f"record {row.get('example_id')!r} is not in validation split")
        if row.get("expected_action") != "ANSWER_FROM_SOURCE":
            raise SystemExit(f"record {row.get('example_id')!r} is not answerable")
        support_ids = row.get("supporting_passage_ids")
        if not isinstance(support_ids, list) or len(support_ids) != 1:
            raise SystemExit(f"record {row.get('example_id')!r} must have one supporting passage")
        if support_ids[0] not in passages_by_id:
            raise SystemExit(f"record {row.get('example_id')!r} references an inactive passage")
        expected_sources = {passages_by_id[passage_id].source_id for passage_id in support_ids}
        if set(row.get("source_ids", [])) != expected_sources:
            raise SystemExit(f"record {row.get('example_id')!r} source references do not match")

    results = evaluate_records(passages, rows, ks=(1, 3))
    per_query_summary = {
        method: [
            {
                "example_id": row["example_id"],
                "relevant_passage_ids": row["relevant_passage_ids"],
                "top_ranked_passage_id": row["ranked"][0]["passage_id"] if row["ranked"] else None,
                "first_relevant_rank": row["first_relevant_rank"],
                "hit": row["hit"],
                "query_corpus_token_overlap": row["query_corpus_token_overlap"],
            }
            for row in method_rows
        ]
        for method, method_rows in results["per_method"].items()
    }
    output = {
        "evaluation": "validation_only_retrieval",
        "dataset_version": "day3-v1.1.0 retrieval validation",
        "validation_count": len(rows),
        "corpus_count": len(passages),
        "corpus_sha256": actual_corpus_hash,
        "validation_sha256": actual_validation_hash,
        "relevance_interpretation": "binary; supporting_passage_ids are relevant",
        "ndcg": "not calculated; no graded relevance labels are present",
        "k_values": [1, 3],
        "summaries": results["summaries"],
        "per_query_summary": per_query_summary,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

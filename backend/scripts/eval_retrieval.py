"""Measure retrieval quality on a labeled query set.

Usage (from the backend directory):

    python scripts/eval_retrieval.py \
        --collection my_collection \
        --queries scripts/eval_queries.example.jsonl \
        --n-results 10

Each JSONL line must look like:

    {"query": "who is the captain?", "expected_ids": ["book.pdf_123_4"]}
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.internal.retrieval import retrieve  # noqa: E402


def load_queries(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def recall_at_k(retrieved: List[str], expected: List[str], k: int) -> float:
    if not expected:
        return 0.0
    hits = len(set(retrieved[:k]) & set(expected))
    return hits / len(expected)


def reciprocal_rank(retrieved: List[str], expected: List[str]) -> float:
    expected_set = set(expected)
    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in expected_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: List[str], expected: List[str], k: int) -> float:
    if not expected:
        return 0.0
    expected_set = set(expected)
    dcg = 0.0
    for index, chunk_id in enumerate(retrieved[:k], start=1):
        if chunk_id in expected_set:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(expected), k)
    idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval precision")
    parser.add_argument("--collection", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--n-results", type=int, default=10)
    parser.add_argument("--fetch-k", type=int, default=None)
    parser.add_argument("--no-rerank", action="store_true")
    args = parser.parse_args()

    rows = load_queries(args.queries)
    totals = {"recall": 0.0, "mrr": 0.0, "ndcg": 0.0}

    for row in rows:
        result = retrieve(
            args.collection,
            row["query"],
            n_results=args.n_results,
            fetch_k=args.fetch_k,
            rerank=not args.no_rerank,
        )
        retrieved = result["results"]["ids"][0]
        expected = row.get("expected_ids", [])

        recall = recall_at_k(retrieved, expected, args.n_results)
        mrr = reciprocal_rank(retrieved, expected)
        ndcg = ndcg_at_k(retrieved, expected, args.n_results)
        totals["recall"] += recall
        totals["mrr"] += mrr
        totals["ndcg"] += ndcg
        print(
            f"recall@{args.n_results}={recall:.3f} "
            f"mrr={mrr:.3f} ndcg@{args.n_results}={ndcg:.3f}  {row['query']}"
        )

    count = len(rows) or 1
    print("\nAverages over", len(rows), "queries")
    print(f"  recall@{args.n_results}: {totals['recall'] / count:.3f}")
    print(f"  mrr:            {totals['mrr'] / count:.3f}")
    print(f"  ndcg@{args.n_results}:     {totals['ndcg'] / count:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

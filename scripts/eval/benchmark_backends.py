"""
Lightweight backend benchmarking harness.

Measures best-effort latency for insert/query across configured backends.
Backends with missing dependencies or config are skipped safely.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List


def try_import(name: str):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def bench_faiss(n: int, dim: int) -> Dict[str, Any]:
    if not try_import("faiss"):  # pragma: no cover - optional dep
        return {"backend": "faiss", "status": "skipped", "reason": "faiss missing"}
    import faiss  # type: ignore
    import numpy as np

    xb = np.random.random((n, dim)).astype("float32")
    xq = np.random.random((10, dim)).astype("float32")

    t0 = time.perf_counter()
    index = faiss.IndexFlatL2(dim)
    index.add(xb)
    build_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    index.search(xq, 5)
    query_s = time.perf_counter() - t1

    return {
        "backend": "faiss",
        "status": "ok",
        "build_seconds": round(build_s, 4),
        "query_seconds": round(query_s, 4),
        "n": n,
        "dim": dim,
    }


def bench_stub(name: str) -> Dict[str, Any]:
    # Placeholder for pinecone/weaviate; skipped unless deps are present.
    if not try_import(name):  # pragma: no cover - optional dep
        return {"backend": name, "status": "skipped", "reason": f"{name} missing"}
    # If deps exist, we still avoid real network calls; just report available.
    return {"backend": name, "status": "available", "note": "no live benchmark run"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backend benchmark harness (best-effort)")
    p.add_argument(
        "--backends",
        nargs="+",
        default=["faiss", "pinecone", "weaviate"],
        help="Backends to check",
    )
    p.add_argument("--n", type=int, default=2000, help="Vectors to index (faiss)")
    p.add_argument("--dim", type=int, default=384, help="Vector dimension (faiss)")
    p.add_argument("--out", help="Optional path to write JSON report")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    results: List[Dict[str, Any]] = []

    for backend in args.backends:
        if backend.lower() == "faiss":
            results.append(bench_faiss(args.n, args.dim))
        elif backend.lower() == "pinecone":
            results.append(bench_stub("pinecone"))
        elif backend.lower() == "weaviate":
            results.append(bench_stub("weaviate"))
        else:
            results.append({"backend": backend, "status": "skipped", "reason": "unknown"})

    summary = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "available": sum(1 for r in results if r["status"] == "available"),
    }

    report = {"summary": summary, "results": results}
    print(json.dumps(report, indent=2))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


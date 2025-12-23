"""
Offline evaluation harness.

Reads a JSONL dataset of prompts and expected keywords, calls the API, and
computes simple heuristic scores (keyword hits, PHI leakage checks). Designed
to fail gracefully if the API is unavailable or dependencies are missing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_requests():
    try:
        import requests  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency missing
        print(
            "The 'requests' package is required. Install with: pip install requests",
            file=sys.stderr,
        )
        raise exc
    return requests


PHI_REGEXES = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-like
    re.compile(r"\b\d{10}\b"),  # simple phone-like
    re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),  # phone with separators
]


def detect_phi(text: str) -> bool:
    return any(rx.search(text) for rx in PHI_REGEXES)


def score_keywords(text: str, keywords: List[str]) -> float:
    if not keywords:
        return 1.0
    hits = sum(1 for kw in keywords if kw.lower() in text.lower())
    return hits / len(keywords)


def eval_case(
    session,
    base_url: str,
    item: Dict[str, Any],
    timeout: float,
) -> Dict[str, Any]:
    payload = {"query": item["query"], "user_id": "offline-eval"}
    try:
        resp = session.post(f"{base_url}/agent/run", json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        text = json.dumps(data)
    except Exception as exc:  # pragma: no cover - network dependent
        return {
            "id": item.get("id"),
            "status": "error",
            "error": str(exc),
        }

    keyword_score = score_keywords(text, item.get("expected_keywords", []))
    phi_found = detect_phi(text) and not item.get("allow_phi", False)

    return {
        "id": item.get("id"),
        "status": "ok",
        "keyword_score": keyword_score,
        "phi_found": phi_found,
    }


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    errors = [r for r in results if r["status"] != "ok"]
    oks = [r for r in results if r["status"] == "ok"]
    avg_keyword = (
        sum(r.get("keyword_score", 0) for r in oks) / len(oks) if oks else 0.0
    )
    phi_violations = sum(1 for r in oks if r.get("phi_found"))
    return {
        "total": total,
        "ok": len(oks),
        "errors": len(errors),
        "avg_keyword_score": round(avg_keyword, 3),
        "phi_violations": phi_violations,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Offline eval runner")
    p.add_argument("--dataset", required=True, help="Path to JSONL dataset")
    p.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    p.add_argument("--out", help="Optional path to write JSON report")
    p.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    requests = load_requests()
    session = requests.Session()

    items = load_dataset(dataset_path)
    results: List[Dict[str, Any]] = []
    for item in items:
        results.append(eval_case(session, args.base_url, item, args.timeout))

    report = {
        "summary": summarize(results),
        "results": results,
    }

    print(json.dumps(report["summary"], indent=2))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report to {out_path}")

    # Exit non-zero if any phi violation or errors
    if report["summary"]["phi_violations"] > 0 or report["summary"]["errors"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())


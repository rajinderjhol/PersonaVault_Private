"""Replay a capture through merge variants and score them.

Offline and repeatable: the same `buckets.json` always produces the same
numbers, so a difference between two runs is a difference between two
algorithms and nothing else.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from search_mcp.aggregator import (  # noqa: E402
    _NATIVE_CATEGORY_WEIGHT,
    _RRF_K,
    _dedup_by_title,
    _native_engines,
    _normalize_url,
)

DATA_PATH = pathlib.Path(__file__).parent / "buckets.json"


def load():
    if not DATA_PATH.exists():
        raise SystemExit(
            f"{DATA_PATH} not found — run `python evals/ranking/capture.py` first."
        )
    return json.loads(DATA_PATH.read_text())


def merge(case, *, k=_RRF_K, native_weight=_NATIVE_CATEGORY_WEIGHT, cap=50):
    """A standalone copy of `_merge`'s scoring, parameterised.

    Deliberately not a call into `_merge`: the point is to compare the shipped
    configuration against alternatives it does not support.
    """
    native = _native_engines(case["category"])
    scores: dict[str, float] = {}
    rep: dict[str, dict] = {}
    engines_for: dict[str, list[str]] = {}
    for name, rows in case["buckets"].items():
        weight = native_weight if name in native else 1.0
        for r in rows:
            url = _normalize_url(r["url"])
            if not url:
                continue
            scores[url] = scores.get(url, 0.0) + weight / (k + r["rank"])
            engines_for.setdefault(url, []).append(name)
            if url not in rep:
                rep[url] = dict(r) | {"url": url}
    out = []
    for url, score in sorted(scores.items(), key=lambda kv: -kv[1]):
        rec = rep[url]
        rec["engines"] = sorted(set(engines_for[url]))
        rec["score"] = score
        rec.pop("rank", None)
        rec.pop("engine", None)
        out.append(rec)
    return _dedup_by_title(out)[:cap]


def rank_of(results, expect):
    for i, r in enumerate(results, 1):
        if expect.lower() in r["url"].lower():
            return i
    return None


def evaluate(data, **kw):
    hit1 = hit3 = 0
    mrr = 0.0
    detail = []
    for case in data:
        pos = rank_of(merge(case, **kw), case["expect"])
        hit1 += pos == 1
        hit3 += bool(pos and pos <= 3)
        mrr += (1.0 / pos) if pos else 0.0
        detail.append((case["query"], case["category"], pos))
    n = len(data) or 1
    return {"hit@1": hit1, "hit@3": hit3, "mrr": round(mrr / n, 4), "n": len(data)}, detail


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--detail", action="store_true",
                    help="per-query before/after table")
    ap.add_argument("--sweep", action="store_true",
                    help="grid over k and the native weight")
    args = ap.parse_args()
    data = load()

    shipped, shipped_detail = evaluate(data)
    print(f"shipped (k={_RRF_K}, native_weight={_NATIVE_CATEGORY_WEIGHT}): {shipped}")

    if args.sweep:
        print(f"\n{'k':>6} {'weight':>7} | {'hit@1':>5} {'hit@3':>5} {'MRR':>8}")
        print("-" * 40)
        for k in (60.0, 30.0, 10.0, 5.0):
            for w in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
                m, _ = evaluate(data, k=k, native_weight=w)
                print(f"{k:>6} {w:>7} | {m['hit@1']:>5} {m['hit@3']:>5} {m['mrr']:>8.4f}")

    if args.detail:
        # The comparison that gates a change: an aggregate win is not enough,
        # nothing individual may get worse.
        _, before = evaluate(data, native_weight=1.0)
        print(f"\n{'plain':>7}{'shipped':>8}   category            query")
        improved = regressed = 0
        for (q, c, a), (_, _, b) in zip(before, shipped_detail, strict=True):
            av, bv = (a or 999), (b or 999)
            tag = ""
            if bv < av:
                tag, improved = "  improved", improved + 1
            elif bv > av:
                tag, regressed = "  REGRESSED", regressed + 1
            print(f"{str(a):>7}{str(b):>8}   {str(c):18}  {q[:36]}{tag}")
        print(f"\nimproved={improved}  regressed={regressed}")


if __name__ == "__main__":
    main()

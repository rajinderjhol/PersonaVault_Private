"""Capture the raw per-engine results for the eval queries, once.

Replaying a saved capture is what isolates the MERGE from network variance.
Hits the network; run it directly, not under pytest.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from search_mcp.aggregator import _is_exclusive, engines_for_category  # noqa: E402
from search_mcp.config import settings  # noqa: E402
from search_mcp.engines import SearchFilters, category_group, get_engine  # noqa: E402

OUT = pathlib.Path(__file__).parent / "buckets.json"

# (query, category, substring identifying the one correct result)
CASES = [
    ("reciprocal rank fusion", "paper", "10.1145/1571941.1572114"),
    ("attention is all you need", "paper", "1706.03762"),
    ("deep residual learning for image recognition", "paper", "10.1109/cvpr.2016.90"),
    # PubMed and Europe PMC are equally right here; demanding one of them
    # measured an engine outage rather than the ranking.
    ("crispr base editing", "paper.biomed", "ncbi.nlm.nih.gov"),
    ("reciprocal rank fusion", "paper.cs", "10.1145/1571941.1572114"),
    ("NVDA risk factors", "finance.filings", "sec.gov/Archives"),
    ("NVIDIA 10-K risk factors", "finance.filings", "sec.gov/Archives"),
    ("人工智能", "finance.filings", "static.cninfo.com.cn"),
    ("vietnam gdp growth", "finance.macro", "imf.org/external/datamapper"),
    ("semaglutide obesity", "paper.trial", "clinicaltrials.gov/study"),
    ("python asyncio", None, "docs.python.org"),
    ("rust ownership borrowing", None, "doc.rust-lang.org"),
    ("postgres explain analyze", None, "postgresql.org/docs"),
    ("kubernetes operator pattern", None, "kubernetes.io/docs"),
]

N = 10


def _engine_names(category: str | None) -> list[str]:
    """Mirror `aggregate_search`'s routing so the capture matches a real run."""
    if category and _is_exclusive(category):
        return engines_for_category(category) or list(settings.default_engines)
    names = list(settings.default_engines)
    if category:
        names += engines_for_category(category, exclude=names)
    return names


async def main() -> None:
    out = []
    for query, category, expect in CASES:
        names = _engine_names(category)
        filters = SearchFilters(
            category=category_group(category), category_token=category
        )

        # Bind the loop variables explicitly: a closure over them would have
        # every engine search for whatever query the loop had reached by the
        # time it ran.
        async def run(name: str, query=query, filters=filters):
            try:
                return name, await get_engine(name).search(query, N, filters)
            except Exception as exc:  # a dead engine is data, not a crash
                print(f"    {name}: {type(exc).__name__}", file=sys.stderr)
                return name, []

        got = await asyncio.gather(*(run(n) for n in names))
        buckets = {
            name: [r.to_dict() | {"rank": r.rank, "engine": r.engine} for r in rows]
            for name, rows in got
        }
        total = sum(len(v) for v in buckets.values())
        print(f"{query!r:46} cat={str(category):18} engines={len(names)} raw={total}")
        out.append(
            {
                "query": query,
                "category": category,
                "expect": expect,
                "engines": names,
                "buckets": buckets,
            }
        )
    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print(f"\nwrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    asyncio.run(main())

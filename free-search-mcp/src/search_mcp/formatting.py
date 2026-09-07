"""LLM-friendly output formatters.

Three concerns:
1. Token estimation — char heuristic (4ch/token Latin, 2ch/token CJK), good
   enough for budgeting without paying for the tiktoken dependency.
2. Smart truncation — break at paragraph > newline > sentence, never mid-word.
3. Markdown views of every tool result so the LLM gets readable text rather
   than a JSON blob it has to parse before reading.
"""
from __future__ import annotations

from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough token count without a tokenizer.

    Latin scripts ≈ 4 chars/token, CJK ≈ 1 char/token. Off by 10–20% on weird
    inputs but plenty good for a 'is this going to blow my context window?'
    decision.
    """
    if not text:
        return 0
    cjk = 0
    for c in text:
        o = ord(c)
        if (
            0x3000 <= o <= 0x303F      # CJK symbols & punctuation （。！？…）
            or 0x3040 <= o <= 0x30FF   # Japanese hiragana/katakana
            or 0x3400 <= o <= 0x4DBF   # CJK Extension-A
            or 0x4E00 <= o <= 0x9FFF   # CJK unified ideographs
            or 0xAC00 <= o <= 0xD7A3   # Korean hangul syllables
            or 0xF900 <= o <= 0xFAFF   # CJK compatibility ideographs
            or 0xFF00 <= o <= 0xFFEF   # fullwidth forms / halfwidth kana
        ):
            cjk += 1
    latin = len(text) - cjk
    return cjk + max(1, latin // 4)


_BOUNDARIES = ("\n\n", "\n", "。", ". ", "！", "! ", "？", "? ")


def smart_truncate(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate at the latest natural boundary within the budget.

    Refuses to cut more than 30% past the boundary — falls back to a hard cut
    if the only boundary is way too early.
    """
    if len(text) <= max_chars:
        return text, False
    head = text[:max_chars]
    floor = int(max_chars * 0.7)
    best = -1
    for sep in _BOUNDARIES:
        idx = head.rfind(sep)
        if idx >= floor and idx + len(sep) > best:
            best = idx + len(sep)
    if best <= 0:
        return head.rstrip() + " …", True
    return head[:best].rstrip() + "\n\n[…truncated]", True


def render_search(payload: dict[str, Any]) -> str:
    """Render aggregator output as a numbered Markdown list with provenance."""
    query = payload.get("query", "")
    requested = payload.get("engines") or []
    results = payload.get("results") or []
    errors = payload.get("errors") or {}
    cached = payload.get("cached")

    # The header names the engines that actually PRODUCED these results, not
    # the ones that were asked to. `payload["engines"]` is the request — the
    # list the cache key is built from — and when a requested engine fails the
    # rescue pass substitutes another. Printing the request made the header
    # claim `engines: nope_not_an_engine` above ten results that every
    # per-result byline correctly attributed to `bing`.
    contributed = list(
        dict.fromkeys(e for r in results for e in (r.get("engines") or []))
    )
    engines = ", ".join(contributed or requested)

    lines = [f"# Search: {query}", "", f"_engines: {engines}_  _results: {len(results)}_"]
    missing = [e for e in requested if e not in contributed]
    if contributed and missing:
        lines.append(f"_(requested but contributed nothing: {', '.join(missing)})_")
    if cached:
        lines.append("_(from cache)_")
    lines.append("")

    # Extractive lead from the top result that mentions the query terms — sits
    # above the result list so the model sees an answer-shaped fragment first.
    lead = payload.get("lead_snippet")
    if lead:
        lines.append(f"> **Lead:** {lead}")
        lines.append("")

    if not results:
        lines.append("**No results.** Try a broader query, different engines, "
                     "or check `errors` if any engine failed.")
        if errors:
            lines.append("")
            for name, err in errors.items():
                lines.append(f"- {name}: {err}")
        lines.extend(_render_search_hints(payload))
        # Filter diagnostics matter MOST at zero results — that is exactly when
        # "your filters dropped all 17 hits" is the answer and the silent-engine
        # note above is a red herring. This branch used to return before the
        # block below ever ran, so the one case the diagnostics were written for
        # was the one case that never showed them.
        diag = payload.get("filter_diagnostics")
        if diag:
            lines.extend(_render_filter_diagnostics(diag))
        return "\n".join(lines).rstrip() + "\n"

    for i, r in enumerate(results, 1):
        title = (r.get("title") or "(untitled)").strip()
        url = r.get("url") or ""
        snippet = (r.get("snippet") or "").strip()
        engines_for = ", ".join(r.get("engines") or [])
        score = r.get("score")
        meta = f"_{engines_for}_" + (f" · score {score}" if score is not None else "")
        if r.get("published_age"):
            meta += f" · {r['published_age']}"
        lines.append(f"## {i}. {title}")
        lines.append(f"<{url}>")
        if snippet:
            lines.append("")
            lines.append(f"> {snippet}")
        lines.append("")
        lines.append(meta)
        lines.append("")

    if errors:
        lines.append("---")
        lines.append("**Engine errors (non-fatal):**")
        for name, err in errors.items():
            lines.append(f"- {name}: {err}")

    lines.extend(_render_search_hints(payload))

    diag = payload.get("filter_diagnostics")
    if diag:
        lines.extend(_render_filter_diagnostics(diag))

    return "\n".join(lines).rstrip() + "\n"


def _render_search_hints(payload: dict[str, Any]) -> list[str]:
    """Gate / silent-empty / rescue notes the aggregator attached to the payload.

    Rendered in BOTH the results and no-results branches — a gated or silently
    blocked engine matters most exactly when the list came back empty.
    """
    lines: list[str] = []
    gated_hint = payload.get("gated_hint")
    if gated_hint:
        lines.append("")
        lines.append(f"⚠️ **Gated engines:** {gated_hint}")
    empty_hint = payload.get("empty_hint")
    if empty_hint:
        lines.append("")
        lines.append(f"⚠️ **Silent engines:** {empty_hint}")
    rate_limited_hint = payload.get("rate_limited_hint")
    if rate_limited_hint:
        lines.append("")
        lines.append(f"⚠️ **Rate-limited engines:** {rate_limited_hint}")
    rescued = payload.get("rescued_via")
    if rescued:
        lines.append("")
        lines.append(
            f"ℹ️ **Rescued:** the requested engines came up short; "
            f"results above include a rescue pass via {rescued}."
        )
    return lines


def _render_filter_diagnostics(diag: dict[str, Any]) -> list[str]:
    """Format the filter_diagnostics block as Markdown lines.

    Sits AFTER the result list (and after any engine-error block) because
    it's a meta-explanation, not a result. Marked clearly so the LLM can
    spot it and decide whether to retry with looser filters.
    """
    raw_per_engine = diag.get("raw_per_engine") or {}
    after_per_engine = diag.get("after_filter_per_engine") or {}
    drops = diag.get("drops_by_reason") or {}
    hint = diag.get("hint") or ""

    raw_total = sum(raw_per_engine.values())
    after_total = sum(after_per_engine.values())
    n_engines = len(raw_per_engine) or len(after_per_engine)

    lines: list[str] = []
    lines.append("")
    lines.append("---")
    lines.append("⚠️ **Filter diagnostics** (results were sparse)")
    lines.append("")
    lines.append(
        f"Raw results: {raw_total} across {n_engines} engine"
        f"{'s' if n_engines != 1 else ''} → {after_total} after filters."
    )
    if drops:
        # Sort by drop count desc so the worst offender leads.
        ordered = sorted(drops.items(), key=lambda kv: kv[1], reverse=True)
        top = ", ".join(f"{name} ({n})" for name, n in ordered)
        lines.append(f"Top drops: {top}.")
    if hint:
        lines.append("")
        lines.append(f"Hint: {hint}")
    return lines


def render_fetch(result: dict[str, Any]) -> str:
    """Render a fetched page as a Markdown document with metadata header."""
    url = result.get("url", "")
    title = result.get("title") or "(untitled)"
    method = result.get("method", "")
    truncated = result.get("truncated", False)
    tokens = result.get("tokens_estimated")
    author = result.get("author") or ""
    published_date = result.get("published_date") or ""
    sitename = result.get("sitename") or ""
    content = result.get("content") or ""

    byline_parts: list[str] = []
    if sitename:
        byline_parts.append(sitename)
    if author:
        byline_parts.append(f"by {author}")
    if published_date:
        byline_parts.append(published_date)
    byline = " · ".join(byline_parts)

    meta_line = (
        f"_fetched via {method}_"
        + (f" · ~{tokens} tokens" if tokens else "")
        + (" · truncated" if truncated else "")
    )

    header = [f"# {title}", f"<{url}>"]
    if byline:
        header.append(f"_{byline}_")
    header.append(meta_line)
    # Blank line between the metadata block and the body — "\n".join already
    # ends the header with a single newline, so appending the content directly
    # glued the page's first paragraph onto the italic meta line. render_doc
    # gets this right; render_fetch did not, on every fetch/fetch_batch call.
    return "\n".join(header) + "\n\n" + content.rstrip() + "\n"


def render_doc(result: dict[str, Any]) -> str:
    source = result.get("source", "")
    fmt = result.get("format", "")
    title = result.get("title") or ""
    pages = result.get("pages")
    truncated = result.get("truncated", False)
    tokens = result.get("tokens_estimated")
    start = result.get("start", 0)
    length = result.get("returned_chars")
    total_chars = result.get("total_chars")
    content = result.get("content") or ""

    parts = [f"_{fmt}: {source}_"]
    if pages:
        parts.append(f"{pages} pages")
    if tokens:
        parts.append(f"~{tokens} tokens")
    # Only show the slice crumb for a genuine sub-range. A full read (start==0
    # AND the whole document was returned) prints no crumb, since the crumb
    # implies pagination that isn't happening (A7).
    full_read = start == 0 and length is not None and length == total_chars
    if (start or length) and not full_read:
        parts.append(f"slice [{start}:{(start + length) if length else ''}]")
    if truncated:
        parts.append("truncated")
    head = " · ".join(parts)

    title_line = f"# {title}\n\n" if title else ""
    return f"{title_line}{head}\n\n{content.rstrip()}\n"


def render_research(payload: dict[str, Any]) -> str:
    question = payload.get("question", "")
    sources = payload.get("sources") or []
    docs = payload.get("documents") or []
    tokens = payload.get("tokens_estimated")
    engines = ", ".join(payload.get("engines") or [])

    lines = [f"# Research brief: {question}", ""]
    meta = [f"engines: {engines}", f"sources: {len(sources)}"]
    if tokens:
        meta.append(f"~{tokens} tokens")
    lines.append("_" + " · ".join(meta) + "_")
    lines.append("")

    lines.append("## Sources")
    if not sources:
        lines.append("_(none — the search returned nothing to read)_")
    for s in sources:
        lines.append(f"- [{s.get('rank')}] **{s.get('title')}** — <{s.get('url')}>")
        sn = (s.get("snippet") or "").strip()
        if sn:
            lines.append(f"    > {sn}")
    lines.append("")

    # Same reporting contract as render_search: engine errors and the
    # gate/silent/filter notes explain an empty or thin brief, and were
    # previously computed and then dropped on the floor here.
    errors = payload.get("errors") or {}
    if errors:
        lines.append("**Engine errors (non-fatal):**")
        for name, err in errors.items():
            lines.append(f"- {name}: {err}")
        lines.append("")
    lines.extend(_render_search_hints(payload))
    diag = payload.get("filter_diagnostics")
    if diag:
        lines.extend(_render_filter_diagnostics(diag))
    if errors or payload.get("empty_hint") or payload.get("gated_hint") or diag:
        lines.append("")

    if docs:
        lines.append("## Documents")
        lines.append("")
        for d in docs:
            if "error" in d:
                lines.append(f"### ⚠ {d.get('url')}")
                lines.append(f"_failed: {d.get('error')}_")
                lines.append("")
                continue
            title = d.get("title") or "(untitled)"
            url = d.get("url", "")
            tok = d.get("tokens_estimated")
            tcrumb = f" · ~{tok} tokens" if tok else ""
            lines.append(f"### {title}")
            lines.append(f"<{url}>{tcrumb}")
            lines.append("")
            lines.append((d.get("content") or "").rstrip())
            lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_compare(payload: dict[str, Any]) -> str:
    """Render a `compare_urls` payload as a Markdown brief, one section per URL."""
    question = payload.get("question", "")
    excerpts = payload.get("excerpts") or []
    tokens = payload.get("tokens_estimated")
    lines = [f"# Compare: {question}", ""]
    if tokens:
        lines.append(f"_~{tokens} tokens across {len(excerpts)} URLs_")
        lines.append("")
    for i, e in enumerate(excerpts, 1):
        if "error" in e:
            lines.append(f"## {i}. ⚠ {e['url']}")
            lines.append(f"_failed: {e['error']}_")
            lines.append("")
            continue
        lines.append(f"## {i}. {e.get('title') or '(untitled)'}")
        lines.append(f"<{e['url']}>")
        meta_bits: list[str] = []
        if e.get("sitename"):
            meta_bits.append(e["sitename"])
        if e.get("published_date"):
            meta_bits.append(e["published_date"])
        if e.get("truncated"):
            meta_bits.append("truncated")
        if meta_bits:
            lines.append(f"_{' · '.join(meta_bits)}_")
        lines.append("")
        lines.append((e.get("excerpt") or "").rstrip())
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


_STRUCTURED_KEYS = ("json_ld", "microdata", "opengraph", "rdfa", "microformat")


def render_structured(payload: dict[str, Any]) -> str:
    """Render an `extract_structured` payload as Markdown with JSON code blocks.

    Surfaces a top-of-page hint (when ``hint`` is set) and a Meta-tags table
    (when ``meta_fallback`` is set) so callers can tell apart "no data" from
    "blocked by bot shield".
    """
    import json

    url = payload.get("url", "")
    lines = [f"# Structured data: {url}", ""]

    hint = payload.get("hint")
    if hint:
        lines.append("> **No structured data found.**")
        lines.append(">")
        lines.append(f"> {hint}")
        lines.append("")

    any_section = False
    for key in _STRUCTURED_KEYS:
        items = payload.get(key) or []
        if not items:
            continue
        any_section = True
        lines.append(f"## {key}")
        for it in items:
            lines.append("```json")
            lines.append(json.dumps(it, ensure_ascii=False, indent=2)[:2000])
            lines.append("```")
        lines.append("")

    meta_fallback = payload.get("meta_fallback") or {}
    if meta_fallback:
        lines.append("## Meta tags")
        lines.append("")
        lines.append("| key | value |")
        lines.append("| --- | --- |")
        for k, v in meta_fallback.items():
            # Escape pipes in values so the Markdown table doesn't break.
            safe_v = str(v).replace("|", "\\|").replace("\n", " ").strip()
            if len(safe_v) > 200:
                safe_v = safe_v[:200] + " …"
            lines.append(f"| `{k}` | {safe_v} |")
        lines.append("")
        any_section = True

    if not any_section and not hint:
        # Defensive: payload had no syntaxes and no hint (shouldn't happen
        # with the new extractor, but keeps render side-effect free).
        lines.append("_No structured data found on this page._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def errors_to_hint(errors: dict[str, str] | None) -> str | None:
    """Translate engine errors into an actionable hint for the LLM."""
    if not errors:
        return None
    failed = list(errors.keys())
    return (
        f"Engines that failed: {', '.join(failed)}. "
        "If results are thin, retry the call with `engines=` set to the working ones, "
        "or rephrase the query."
    )


def render_engines(
    taxonomy: dict[str, dict[str, list[str]]],
    descriptions: dict[str, str],
    needs_key: set[str] | None = None,
) -> str:
    """Render the source taxonomy as a `group -> sub-group -> engine` tree.

    Built entirely from what the registry reports, so it cannot drift the way
    the hand-maintained buckets it replaces did — those advertised `pubmed` for
    `category="paper"` while the engine limit kept it from ever running, and
    never mentioned `openverse` or `zenodo`.
    """
    if not taxonomy:
        return "No engines matched that group.\n"

    keyed = needs_key or set()

    def _bullets(names: list[str]) -> list[str]:
        out = []
        for n in names:
            line = f"- `{n}` — {descriptions.get(n, '')}".rstrip(" —")
            # Derived from the keystore's provider registry, not a second
            # hand-kept list, so it can never disagree with what the admin UI
            # asks the operator to configure.
            if n in keyed:
                line += " **(API key required)**"
            out.append(line)
        return out

    lines: list[str] = []
    for group, subs in taxonomy.items():
        lines.append(f"## {group}")
        # The "" bucket holds engines that declare the group and nothing
        # narrower; it is empty whenever every engine in the group has a
        # sub-group, so it must not leave a stray blank section behind.
        ungrouped = subs.get("") or []
        if ungrouped:
            lines.append("")
            lines.extend(_bullets(ungrouped))
        for sub, names in subs.items():
            if not sub:
                continue
            lines.append("")
            lines.append(f"### {group}.{sub}")
            lines.append("")
            lines.extend(_bullets(names))
        lines.append("")
    lines.append(
        "Pass a group or sub-group as `category=` to route automatically; pass a "
        "name as `engines=[...]` to force one source."
    )
    return "\n".join(lines) + "\n"


def _paper_graph_node(node: dict[str, Any], index: int) -> list[str]:
    bits: list[str] = []
    year = node.get("year")
    if year:
        bits.append(str(year))
    cited = node.get("cited_by_count") or 0
    if cited:
        bits.append(f"cited by {cited}")
    doi = node.get("doi")
    if doi:
        bits.append(f"doi:{doi}")
    flag = " ⚠️ **RETRACTED**" if node.get("retracted") else ""
    line = f"{index}. **{node.get('title') or '(untitled)'}**{flag}"
    out = [line]
    url = node.get("url")
    if url:
        out.append(f"   <{url}>")
    if bits:
        out.append(f"   _{' · '.join(bits)}_")
    return out


def render_paper_graph(payload: dict[str, Any]) -> str:
    """Render a paper's citation neighbourhood.

    References and citations get their own sections because they answer
    different questions — what this stood on, and what stood on it — and the
    retraction banner goes first, before anything a reader might quote.
    """
    paper = payload.get("paper")
    notes = payload.get("notes") or []
    if not paper:
        head = f"# No paper matched `{payload.get('query', '')}`"
        return "\n".join([head, ""] + [f"_{n}_" for n in notes]) + "\n"

    lines: list[str] = []
    if paper.get("retracted"):
        lines.append("> ⚠️ **RETRACTED PAPER** — do not cite this as a standing result.")
        lines.append("")

    lines.append(f"# {paper.get('title') or '(untitled)'}")
    lines.append("")
    if paper.get("url"):
        lines.append(f"<{paper['url']}>")
    meta: list[str] = []
    if paper.get("year"):
        meta.append(str(paper["year"]))
    meta.append(f"cited by {paper.get('cited_by_count', 0)}")
    if paper.get("doi"):
        meta.append(f"doi:{paper['doi']}")
    if paper.get("openalex_id"):
        meta.append(paper["openalex_id"])
    lines.append(f"_{' · '.join(meta)}_")

    crossref = paper.get("crossref") or {}
    if crossref.get("registered") is False:
        lines.append("")
        lines.append(
            "**Not in Crossref** — likely a DataCite DOI, so retraction notices "
            "could not be checked."
        )
    for notice in crossref.get("notices") or []:
        kind = str(notice.get("type", "")).replace("_", " ")
        date = notice.get("date")
        lines.append("")
        lines.append(
            f"**{kind.title()}** ({date or 'undated'}) — <https://doi.org/{notice.get('doi')}>"
        )

    for key, heading in (
        ("references", "References (what it builds on)"),
        ("citations", "Cited by (what built on it)"),
    ):
        nodes = payload.get(key) or []
        if not nodes:
            continue
        lines.append("")
        lines.append(f"## {heading}")
        lines.append("")
        for i, node in enumerate(nodes, 1):
            lines.extend(_paper_graph_node(node, i))
            lines.append("")
        lines.pop()

    if notes:
        lines.append("")
        for note in notes:
            lines.append(f"_{note}_")
    return "\n".join(lines) + "\n"

"""MCP server entry point. Tool docstrings are written for an LLM to read:
each tool says when to use it, when NOT to use it, what it returns, and the
mistakes models commonly make when calling it."""
from __future__ import annotations

import logging
from typing import Any, Literal

from mcp.server.caching import CacheHint
from mcp.server.mcpserver import Context, Image, MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from . import __version__, downloads
from .aggregator import aggregate_search, list_engines
from .browser import pool
from .cache import cache
from .compare import compare_urls
from .config import settings
from .documents import read_document
from .engines import ENGINES, Category, source_taxonomy
from .fetcher import decode_cached_title, fetch_bytes, fetch_many, fetch_page
from .formatting import (
    errors_to_hint,
    render_compare,
    render_doc,
    render_engines,
    render_fetch,
    render_paper_graph,
    render_research,
    render_search,
    render_structured,
)
from .keystore import PROVIDERS
from .paper_graph import paper_graph as run_paper_graph
from .research import research as run_research
from .structured import extract_structured as _extract_structured

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Protocol-level logging (`notifications/message`) is deprecated as of the
# 2026-07-28 revision; stderr via the stdlib is the recommended replacement,
# which is what basicConfig above already gives us on stdio.
log = logging.getLogger(__name__)

# Every list here is fixed for the life of the process — tools, prompts and
# resource templates are all declared at import time and nothing mutates them.
# Saying so lets clients cache and stop re-listing. `resources/read` is the
# exception: it serves this machine's page cache, so it is per-user and short.
_STATIC_LIST = CacheHint(ttl_ms=3_600_000, scope="public")
_CACHE_HINTS = {
    "tools/list": _STATIC_LIST,
    "prompts/list": _STATIC_LIST,
    "resources/list": _STATIC_LIST,
    "resources/templates/list": _STATIC_LIST,
    "resources/read": CacheHint(ttl_ms=60_000, scope="private"),
}

# Keyword args throughout: MCPServer's positional order is
# (name, title, description, instructions, ...), so a positional `instructions`
# would silently land in the `title` slot.
mcp = MCPServer(
    "search-mcp",
    title="Free Search",
    instructions=(
        "Multi-engine web search, fetching, and document reading with no API "
        "key required. Use `search` for queries, `fetch`/`fetch_batch` to read "
        "specific URLs, `research` when you want search and reading in one "
        "round trip, and `engines` to discover which backends are available. "
        "Every tool takes format='markdown' (default, compact) or "
        "format='json' (structured)."
    ),
    website_url="https://github.com/sweetcornna/free-search-mcp",
    version=__version__,
    cache_hints=_CACHE_HINTS,
)

Format = Literal["markdown", "json"]

# ToolAnnotations meaning recap (for the maintainers, not for the LLM):
#   read_only_hint   - the call does not change server state visible to others
#   idempotent_hint  - same args yield the same result
#   open_world_hint  - the tool reaches outside the server (network, real world)


def _maybe_render(payload: dict[str, Any], fmt: Format, renderer) -> str | dict[str, Any]:
    if fmt == "json":
        return payload
    return renderer(payload)


def _max_age_to_seconds(max_age_hours: float | None) -> int | None:
    if max_age_hours is None:
        return None
    return int(max_age_hours * 3600)


# FTS5 boolean keywords are only valid as INFIX operators between two terms.
_FTS_OPERATORS = {"AND", "OR", "NOT", "NEAR"}


def _invalid_fts_hint(query: str) -> str | None:
    """Return a sanitized hint if `query` is malformed FTS5 syntax, else None.

    The cache layer already swallows the SQLite OperationalError and returns []
    (so we never leak raw SQL), but an empty result then looks identical to a
    legitimate "no pages matched". This heuristic detects the common syntax
    mistakes an LLM makes so the tool can explain *why* it got nothing, without
    re-running SQL or echoing SQLite's error text.
    """
    q = query.strip()
    if not q:
        return None  # empty query is "no input", not "bad syntax"
    # Unbalanced double quotes -> unterminated phrase.
    if q.count('"') % 2 == 1:
        return (
            "Your query has an unterminated quote. FTS5 phrases need matching "
            'double quotes, e.g. `"exact phrase"`.'
        )
    # Unbalanced parentheses.
    if q.count("(") != q.count(")"):
        return (
            "Your query has unbalanced parentheses. Group sub-expressions like "
            "`(a OR b) c`."
        )
    tokens = q.split()
    upper = [t.upper() for t in tokens]
    # A boolean operator may not lead or trail the expression.
    if upper[0] in _FTS_OPERATORS or upper[-1] in _FTS_OPERATORS:
        return (
            "Your query starts or ends with a boolean operator (AND/OR/NOT/NEAR). "
            "These join two terms, e.g. `cats AND dogs`, not `cats AND`."
        )
    # Two boolean operators in a row (e.g. `a AND OR b`).
    for prev, cur in zip(upper, upper[1:], strict=False):
        if prev in _FTS_OPERATORS and cur in _FTS_OPERATORS:
            return (
                "Your query has two boolean operators in a row. Put a term "
                "between them, e.g. `a AND b OR c`."
            )
    return None


async def _safe_progress(
    ctx: Context | None, current: float, total: float, message: str,
) -> None:
    """report_progress() raises when called from non-MCP contexts (unit tests,
    ad-hoc scripts, or clients that didn't pass a progressToken). Swallow that
    so progress is a nice-to-have, not a crash trigger.

    The catch is deliberately broad: the exception type is SDK plumbing that
    has already changed once across protocol revisions, and no failure to emit
    a progress ping is worth losing an otherwise-complete search result over.
    """
    if ctx is None:
        return
    try:
        await ctx.report_progress(current, total, message)
    except Exception:
        log.debug("progress notification dropped", exc_info=True)


@mcp.tool(
    title="Web search (multi-engine, no API key)",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def search(
    query: str,
    engines: list[str] | None = None,
    max_results: int = 10,
    use_cache: bool = True,
    max_age_hours: float | None = None,
    freshness: Literal["day", "week", "month", "year"] | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    category: Category | None = None,
    include_text: str | None = None,
    exclude_text: str | None = None,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Run a multi-engine web search and return a ranked, deduplicated link list.

    Best for:
    - Discovery queries ("what is X", "find me X", "who is X").
    - Getting a list of URLs you can hand to `fetch` / `fetch_batch` next.
    - Topics likely to be after your knowledge cutoff (use `freshness="week"`).
    - Filtering to specific domains (`include_domains=["python.org"]`) or
      a kind of source (`category="paper"` / `"finance"`, or a sub-group like
      `category="paper.biomed"` / `"finance.filings"` — see `engines()` for the
      full tree).

    Not recommended for:
    - You already know the URL -> use `fetch` instead.
    - You want both links AND their full text in one call -> use `research`.
    - You want to query pages already in the local cache -> use `cache_search`.
    - Reading PDFs/DOCX from a known URL -> use `read_doc`.
    - Following one paper's references or citations -> use `paper_graph`.

    Returns:
    - markdown (default): numbered list of `n. title`, `<url>`, snippet — ~40%
      fewer tokens than json.
    - json: dict with `results` (list of {title,url,snippet,engines,score}),
      `engines`, `cached`, optional `errors` map, optional `hint` string.
      `engines` is what was REQUESTED; each result's own `engines` is what
      actually found it, and those differ whenever the rescue pass substitutes
      a source (see `rescued_via`).

    Common mistakes:
    - Passing a URL as `query` — that's `fetch`'s job.
    - Cranking `max_results` up hoping for better recall; engines cap around
      10-20 each, anything beyond is duplicate noise (and 50 is the ceiling).
    - Adding `engines=["startpage","brave","bing","baidu"]` by default — those
      need browser rendering or captcha-friendly conditions; stick with the
      defaults unless they returned 0. If the defaults DO return 0, the keyless
      HTTP extras `engines=["google"]` or `engines=["anysearch"]` (no key, no
      browser) are the best recovery before reaching for the browser-gated ones.
    - Using `category="news"` for breaking news without also setting
      `freshness="day"` — the index lag is days, not minutes.

    Args:
        query: Natural-language query (the same string a human would type).
        engines: Subset of `engines()`. None = duckduckgo+mojeek+googlenews+bing.
            (startpage is opt-in and browser-rendered.)
        max_results: Merged result count after dedup, clamped to 1-50. It is
            also the PER-ENGINE budget, so it multiplies across the fan-out;
            5-20 is the useful range and anything past that is duplicate noise
            bought with real latency. Omit it for the configured default.
        use_cache: Reuse the last result for this exact (query, engines,
            max_results, AND all active filters — freshness, include/exclude
            domains, category, include/exclude text) within the cache TTL.
            Changing any filter is a different cache entry. False forces a
            re-fetch.
        max_age_hours: Treat cached results older than this as a read miss; a
            fresh result is ALWAYS written back to the cache regardless of this
            value, so caching is never disabled. Use 0 to force-refresh while
            keeping cache writes; None = use server default TTL (7 days).
        freshness: "day"|"week"|"month"|"year" — restrict to recent results.
            Best-effort: applied as an engine time-window param AND a client-side
            date check, but most HTML-engine results carry no parseable date, so
            undated results are kept rather than dropped (unknown != old). Treat
            it as a strong hint, not a hard filter; googlenews dates are exact.
        include_domains: List of domains to restrict to (e.g. ["python.org"]).
        exclude_domains: List of domains to exclude.
        category: Which KIND of source to search — the enum lists every value.
            A bare group widens: "paper" adds one specialist per sub-group to the
            default web pool. A dotted sub-group narrows to just the sources that
            index it ("paper.biomed" => the biomedical indexes only). It also
            RERANKS: engines that natively index the category count double in
            the fusion, so the filing outranks the commentary about it. Call
            `engines()` for the group -> sub-group -> engine tree with a line on
            each source. Two behaviours worth knowing: "image"/"dataset" REPLACE
            the web pool rather than augment it (a web engine cannot return an
            image file), and "news"/"paper"/"forum"/"github"/"blog" also filter
            general-web hits by hostname, so a strict category can thin those
            engines out — the specialists it routes to are exempt.
        include_text: Substring required in title or snippet (case-insensitive).
        exclude_text: Substring forbidden in title or snippet.
        format: "markdown" (default) or "json".
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    # aggregate_search owns the single cache key/read/write path. We just hand it
    # the tighter read TTL (max_age_seconds); it tightens the cache READ but
    # ALWAYS writes a fresh non-empty result, so caching is never disabled by a
    # freshness request. This also keeps news-category engine routing inside the
    # one place that computes the key, so the read key can't drift from the
    # write key.
    payload = await aggregate_search(
        query,
        engines=engines,
        max_results=max_results,
        use_cache=use_cache,
        max_age_seconds=_max_age_to_seconds(max_age_hours),
        freshness=freshness,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        category=category,
        include_text=include_text,
        exclude_text=exclude_text,
    )
    hint = errors_to_hint(payload.get("errors"))
    if hint:
        payload["hint"] = hint
    return _maybe_render(payload, format, render_search)


@mcp.tool(
    title="Fetch a URL: page text, document, or resource",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    ),
    # This tool can return page text, a JSON payload, or an actual image.
    # There is no single JSON Schema that covers an ImageContent block, and
    # from 2026-07-28 the SDK VALIDATES returns against the derived schema —
    # so deriving one here would reject every inline image at call time.
    structured_output=False,
)
async def fetch(
    url: str,
    render: Literal["auto", "http", "browser"] = "auto",
    force_refresh: bool = False,
    max_age_hours: float | None = None,
    inline: bool = False,
    format: Format = "markdown",
) -> str | dict[str, Any] | Image:
    """Fetch one URL: page text, or a description of a non-text resource.

    Handles any http(s) resource, not just HTML:
    - HTML pages -> reader-mode Markdown (nav/footer/scripts stripped).
    - PDF/DOCX/XLSX/PPTX/EPUB/CSV/code/archives -> parsed text (same engine as
      `read_doc`, which you should prefer when you need pagination).
    - Images, video, audio, fonts, opaque binaries -> a description
      (media type, byte size, dimensions, sha256), NOT the bytes.

    Best for:
    - You already have a URL (from `search`, the user, or your own knowledge)
      and need the actual page text.
    - Verifying a single claim by reading the source.
    - Checking what a resource IS before deciding to spend tokens on it.

    Not recommended for:
    - Multiple URLs at once -> use `fetch_batch` (concurrent, one round-trip).
    - "Search then read top N" -> use `research` (one call, not two).
    - Long documents you need to page through -> use `read_doc` (start/length).
    - You don't have a URL yet -> use `search` first.

    Returns:
    - markdown (default): a small header (URL, render method, token count)
      plus the cleaned page body.
    - json: {url, title, content, method, truncated, tokens_estimated,
      author, published_date, sitename}, plus {media_type, bytes_size, sha256,
      width, height} for non-text resources.
    - With `inline=True` on an image: the image itself, viewable by a
      vision-capable model.

    Common mistakes:
    - Passing a search query instead of a URL.
    - Using `render="http"` on a JS-only SPA — it returns near-empty content;
      use "auto" (default) or "browser".
    - Setting `inline=True` on a large image out of habit. A 1MB image costs
      well over a thousand tokens; fetch it plainly first and inline only if
      the description says it's worth looking at.
    - Forgetting that results are cached 7 days — use `force_refresh=True`
      or `max_age_hours=0` for a fresh pull.

    Args:
        url: Absolute http(s) URL.
        render: "auto" (try HTTP, fall back to stealth Chromium), "http"
            (fast, fails on JS), "browser" (slow, robust).
        force_refresh: Bypass the page cache entirely.
        max_age_hours: Treat cached pages older than this as a miss. 0 = same
            as force_refresh. None = server default TTL (7 days).
        inline: For images only — return the image itself instead of a
            description, so a vision-capable model can see it. Ignored for
            text resources.
        format: "markdown" or "json".
    """
    # max_age_hours=0 means "force refresh"; anything else just tightens the
    # cache-read TTL, which fetch_page applies against the RESOLVED url.
    effective_force = force_refresh or max_age_hours == 0
    max_age_seconds = (
        _max_age_to_seconds(max_age_hours)
        if max_age_hours is not None and max_age_hours > 0
        else None
    )
    result = await fetch_page(
        url,
        render=render,
        force_refresh=effective_force,
        inline=inline,
        max_age_seconds=max_age_seconds,
    )
    if result.data is not None and result.media_type.startswith("image/"):
        # Hand back real MCP image content rather than base64 in a string —
        # the client decides how to show it, and non-vision clients can skip it.
        return Image(data=result.data, format=result.media_type.split("/", 1)[-1])
    payload = result.to_dict()
    return _maybe_render(payload, format, render_fetch)


@mcp.tool(
    title="Fetch many URLs concurrently",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def fetch_batch(
    urls: list[str],
    render: Literal["auto", "http", "browser"] = "auto",
    format: Format = "markdown",
    ctx: Context | None = None,
) -> str | list[dict[str, Any]]:
    """Fetch a list of URLs in parallel. Per-URL failures do not raise.

    Best for:
    - 2+ URLs you want to read in one round-trip.
    - Reading the top N results of a previous `search` call.

    Not recommended for:
    - A single URL -> `fetch` (no list-wrapping overhead).
    - "Search and then read" -> `research` collapses both into one tool call.
    - PDFs/DOCX -> `read_doc` per file.

    Returns:
    - markdown (default): each page rendered as a Markdown section, separated
      by horizontal rules; failed URLs become inline error notes.
    - json: list[dict], one entry per URL, with `error` set on failures.

    Common mistakes:
    - Passing a single URL inside a 1-element list — use `fetch` directly.
    - Assuming an exception means the whole batch failed; check each item's
      `error` field instead.

    Args:
        urls: List of absolute http(s) URLs (max 20 per call).
        render: Same as `fetch`.
        format: "markdown" or "json".
    """
    if not urls:
        # An empty string reads as "all of them failed silently". Say which of
        # the two it is, in the same voice as the >20 branch below.
        return (
            "_No URLs given. Pass 1-20 absolute http(s) URLs._\n"
            if format == "markdown"
            else []
        )
    if len(urls) > 20:
        raise ValueError(
            f"fetch_batch accepts at most 20 URLs per call (got {len(urls)}); "
            "split the list across calls"
        )
    await _safe_progress(ctx, 0.0, float(len(urls)), "starting batch fetch")
    raw = await fetch_many(urls, render=render)
    items: list[dict[str, Any]] = []
    for idx, r in enumerate(raw, 1):
        items.append(r.to_dict() if hasattr(r, "to_dict") else r)
        await _safe_progress(ctx, float(idx), float(len(urls)), f"fetched {idx}/{len(urls)}")
    if format == "json":
        return items
    sections = []
    for it in items:
        if "error" in it:
            sections.append(f"### ⚠ {it.get('url', '')}\n_failed: {it['error']}_\n")
        else:
            sections.append(render_fetch(it))
    return "\n---\n\n".join(sections)


@mcp.tool(
    title="Read a remote (or sandboxed local) document",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        # Reads http(s) URLs over the network, so this is an open-world tool.
        open_world_hint=True,
    ),
)
async def read_doc(
    source: str,
    start: int = 0,
    length: int | None = None,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Read an http(s) document (or a sandboxed local file) into Markdown.

    Best for:
    - Remote PDFs and DOCX from an http(s) URL (parsed locally, no remote API).
    - Local PDF/DOCX/text/Markdown files — ONLY when local reads are enabled
      (see Security below).
    - Paginating through a long document via `start` / `length`.

    Not recommended for:
    - Arbitrary HTML web pages -> `fetch` does reader-mode cleanup that this
      tool does not.
    - Pages discovered through search -> `fetch` or `research`.

    Security (local files are sandboxed and OFF by default):
    - Local-file reads are DISABLED unless the server operator sets the
      SEARCH_MCP_DOCUMENT_ROOT env var to a directory. With it unset, a local
      path raises a "local file reads are disabled" error — pass an http(s)
      URL instead, or ask the operator to enable the sandbox.
    - When enabled, `source` must resolve INSIDE that root; relative paths
      resolve against the root (not the process CWD) and any `..` traversal
      that escapes the root is rejected. `file://` URLs are always rejected.
    - Remote http(s) sources are unaffected by this setting.

    Returns:
    - markdown (default): rendered document text with a small header.
    - json: {content, title, format, total_chars, start, returned_chars,
      truncated}. Use `total_chars` and `returned_chars` to drive pagination.

    Common mistakes:
    - Calling this on a normal article URL — you'll get raw HTML noise; use
      `fetch` instead.
    - Forgetting to advance `start` when paginating: next call should pass
      `start = previous_start + returned_chars`.
    - Passing a negative `length` (raises an error) or a `start` past the end
      (clamped to EOF: you'll get `returned_chars == 0`, `start == total_chars`,
      and `truncated == False` — that's the signal you've paged off the end).

    Args:
        source: http(s) URL, or a local path UNDER SEARCH_MCP_DOCUMENT_ROOT when
            local reads are enabled (disabled by default — see Security).
        start: Character offset to begin reading from. Default 0. Clamped into
            [0, total_chars]; a negative value is treated as 0.
        length: Max characters to return; None = read to end (still capped by
            the per-call max content size). Must be >= 0 — a negative length
            is rejected with a ValueError.
        format: "markdown" or "json".
    """
    # Reject a negative `start` at the boundary with a clear, LLM-readable
    # message. documents.py would silently clamp it to 0; surfacing the mistake
    # is more helpful to a calling model than swallowing it. Negative `length`
    # and out-of-range `start` are validated/clamped inside read_document — we
    # do NOT duplicate that logic here (it would risk diverging behavior).
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    # A blank source is a caller mistake. Passed through, it fell to the
    # local-file branch and came back as "Local file reads are disabled; set
    # SEARCH_MCP_DOCUMENT_ROOT" — an answer to a question nobody asked, and one
    # that sends the caller to configure a sandbox they do not need.
    if not source.strip():
        raise ValueError("source must not be empty: pass an http(s) URL or a file path")
    result = await read_document(source, start=start, length=length)
    payload = result.to_dict()
    return _maybe_render(payload, format, render_doc)


@mcp.tool(
    title="Search and read in one call",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def research(
    question: str,
    depth: int = 3,
    engines: list[str] | None = None,
    fetch: bool = True,
    use_cache: bool = True,
    max_age_hours: float | None = None,
    freshness: Literal["day", "week", "month", "year"] | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    category: Category | None = None,
    include_text: str | None = None,
    exclude_text: str | None = None,
    format: Format = "markdown",
    ctx: Context | None = None,
) -> str | dict[str, Any]:
    """One-shot research: search the web, fetch the top results, return both.

    Best for:
    - Open-ended questions that need finding sources AND reading them
      ("what's new with X", "summarize the controversy around Y").
    - Replacing a `search` + N x `fetch` chain with one call.
    - Producing a citable brief with [n]-style source references.

    Not recommended for:
    - You only need links -> `search` (cheaper, no fetching).
    - You only need to read one URL you already have -> `fetch`.
    - You want to query previously-fetched cached pages -> `cache_search`.
    - Checking or expanding one paper's citations -> `paper_graph`.

    Returns:
    - markdown (default): a "Research brief" with a Sources index then the
      full Markdown body of each fetched document, separated by horizontal
      rules; includes a token estimate.
    - json: {question, engines, sources:[{rank,title,url,snippet,...}],
      documents:[...], tokens_estimated, errors}.

    Common mistakes:
    - Using `depth=8` for a quick lookup — that's 8 page fetches; 2-3 is
      almost always enough.
    - Calling `research` for a known URL — that's `fetch` territory.
    - Forgetting that `fetch=False` returns sources only (much cheaper if
      the LLM only needs to pick which one to read).

    Args:
        question: What you want to know, in natural language.
        depth: How many top results to fetch (1-8). 3 is a good default.
        engines: Override the engine set (see `engines()` for names). Prefer
            `category=` — naming engines turns category routing off.
        fetch: If False, return source list without reading them.
        freshness: "day"|"week"|"month"|"year" — restrict to recent results.
            Best-effort; undated results are kept rather than dropped.
        include_domains: Restrict to these domains (e.g. ["python.org"]).
        exclude_domains: Drop results from these domains.
        category: Which KIND of source to search; a bare group widens, a dotted
            sub-group narrows. Same values as `search` — see `engines()`.
        include_text: Substring required in title or snippet (case-insensitive).
        exclude_text: Substring forbidden in title or snippet.
        use_cache: Reuse cached search/page data within TTL.
        max_age_hours: Treat cached search results AND cached page bodies older
            than this as a read miss; fresh data is always written back. 0 =
            force-refresh both the engine search and every fetched page body;
            None = server default TTL (7 days). A non-zero value is honored for
            both halves (it used to be ignored for anything but 0).
        format: "markdown" or "json".
    """
    await _safe_progress(ctx, 0.05, 1.0, "starting research")

    # max_age_hours tightens the READ TTL for BOTH the search-cache and the
    # page-cache; aggregate_search/_fetch_with_freshness still write fresh data
    # back, so caching is never disabled. max_age_hours=0 force-refreshes both
    # the engine search and every fetched page body.
    max_age_seconds = _max_age_to_seconds(max_age_hours)

    await _safe_progress(ctx, 0.15, 1.0, "searching engines")

    payload = await run_research(
        question,
        depth=depth,
        engines=engines,
        fetch=fetch,
        use_cache=use_cache,
        max_age_seconds=max_age_seconds,
        page_max_age_seconds=max_age_seconds,
        freshness=freshness,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        category=category,
        include_text=include_text,
        exclude_text=exclude_text,
    )

    # Coarse end-of-fetch milestones — research.py runs fetch_many internally
    # so we can't checkpoint per-URL without rewriting it.
    n_docs = max(1, len(payload.get("documents") or [1]))
    await _safe_progress(ctx, 0.95, 1.0, f"fetched {n_docs} sources")
    await _safe_progress(ctx, 1.0, 1.0, "done")

    return _maybe_render(payload, format, render_research)


@mcp.tool(
    title="Walk a paper's citation graph",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def paper_graph(
    paper: str,
    direction: Literal["both", "references", "citations"] = "both",
    limit: int = 10,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Follow the citations of ONE paper, and check whether it still stands.

    `search` finds papers that MENTION your words. This follows the edges
    instead: what a specific paper built on, and what has built on it since.

    Best for:
    - Checking a citation before repeating it: is the DOI real, and has the
      paper been retracted or corrected?
    - "What happened after this result" — citing works come back ordered by how
      much the field cited them, so a 2019 paper leads to the current state of
      the art rather than to the most recent preprint about it.
    - Building a reading list backwards from one good paper.

    Not recommended for:
    - Finding papers by topic -> `search(category="paper")`, or a sub-group
      like `"paper.biomed"` / `"paper.cs"` / `"paper.preprint"`.
    - Reading the paper itself -> `read_doc` on the returned URL.

    Returns:
    - markdown (default): the paper with its retraction/correction notices,
      then "References" and "Cited by" sections.
    - json: {paper, references, citations, notes}, where `paper.crossref`
      carries `registered` and every post-publication `notices` entry.

    Common mistakes:
    - Passing a topic instead of a paper. A title resolves to its single best
      match; a phrase that names no specific paper resolves to the wrong one.
    - Reading an empty `citations` list as "uncited" when `notes` says the
      lookup was truncated.

    Args:
        paper: DOI (`10.1145/1571941.1572114`, or a doi.org URL), an OpenAlex
            ID (`W2148972377`), or the paper's exact title.
        direction: "both", "references" (what it cites) or "citations" (what
            cites it).
        limit: Max neighbours per direction, 1-50.
        format: "markdown" or "json".
    """
    if not paper.strip():
        raise ValueError(
            "paper must not be empty: pass a DOI, an OpenAlex ID, or the exact title"
        )
    payload = await run_paper_graph(paper, direction=direction, limit=limit)
    return _maybe_render(payload, format, render_paper_graph)


@mcp.tool(
    title="Search local cache (FTS5)",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def cache_search(
    query: str,
    limit: int = 10,
    format: Format = "markdown",
) -> str | list[dict[str, Any]]:
    """Full-text search over pages already fetched into the local SQLite FTS5 index.

    Best for:
    - Recalling something the user/agent fetched earlier in the conversation
      ("what did that Wikipedia page say about X").
    - Avoiding re-fetching content already in the local cache.
    - Quick keyword grep across the corpus you've built up.

    Not recommended for:
    - Discovering new pages on the open web -> use `search` or `research`.
    - When the cache is empty (fresh install) -> `search`/`research` first to
      populate it.

    Returns:
    - markdown (default): a per-hit list of title, URL, and a `[bracket]`-
      highlighted snippet around the matched terms.
    - json: list of {url, title, snippet, author, date, sitename}. The last
      three are "" when the cached row predates metadata capture.

    Common mistakes:
    - Treating this like web search — it ONLY hits pages already in the local
      cache. If the user hasn't fetched anything, you'll get zero hits.
    - Using natural-language phrases without quoting them; FTS5 splits on
      whitespace as AND. For an exact phrase use `"like this"`.

    Args:
        query: FTS5 query. Bare terms = AND. Supports OR / NOT, prefix
            (`term*`), and phrase (`"exact phrase"`).
        limit: Max hits to return.
        format: "markdown" or "json".
    """
    # The cache stores metadata packed behind a sentinel in the title column,
    # so raw rows would hand the caller "\x01META\x01{...}" as a page title.
    if not query.strip():
        # Distinct from "the cache has nothing": telling a caller to populate a
        # cache that may already be full sends them to fix the wrong thing.
        if format == "json":
            return []
        return "_Empty query. Pass FTS5 terms, e.g. `asyncio` or `\"exact phrase\"`._\n"
    rows = [decode_cached_title(r) for r in await cache.search_pages(query, limit=limit)]
    if format == "json":
        return rows
    if not rows:
        bad = _invalid_fts_hint(query)
        if bad:
            return (
                f"_No results — your search syntax looks invalid. {bad}_\n"
            )
        return (
            f"_No cached pages match `{query}`. "
            "Use `fetch` or `research` to populate the cache._\n"
        )
    lines = [f"# Cache hits for `{query}`", ""]
    for r in rows:
        lines.append(f"## {r.get('title') or '(untitled)'}")
        lines.append(f"<{r.get('url')}>")
        sn = r.get("snippet")
        if sn:
            lines.append("")
            lines.append(f"> {sn}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool(
    title="List available search engines",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def engines(
    group: str | None = None,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """List the available sources, grouped by what they index.

    Best for:
    - Choosing a source deliberately: which one indexes filings, or preprints,
      or Chinese-language pages.
    - Checking a name before passing it to `engines=` on `search` / `research`.

    Not recommended for:
    - Calling on every search — the list is static; read it once.

    Returns (markdown): a `group -> sub-group -> engine` tree, one line of
    description per engine. `group="paper"` restricts it to that group.
    Returns (json): `{"engines": [...names...], "taxonomy": {...},
    "descriptions": {...}}`.

    Prefer `category=` over `engines=`. `category="paper"` WIDENS — it routes to
    one specialist per sub-group. A dotted sub-group NARROWS: `"paper.biomed"`
    queries only the biomedical indexes. Naming engines explicitly turns that
    routing off entirely, so reach for it only to force a specific source.

    Common mistakes:
    - Passing one of these names as `query` — they belong in `engines=`.
    - Passing a key-only engine with no key configured; it returns an
      actionable error, not results.
    """
    taxonomy = source_taxonomy()
    if group:
        key = group.split(".", 1)[0].strip().lower()
        taxonomy = {key: taxonomy[key]} if key in taxonomy else {}
    names = [n for subs in taxonomy.values() for names_ in subs.values() for n in names_]
    descriptions = {n: ENGINES[n].description for n in dict.fromkeys(names)}
    # A provider marked `optional` works keyless (anysearch, github); the rest
    # cannot run at all without a key. Derived from the keystore registry the
    # admin UI already drives, so the two can never disagree.
    needs_key = {p.engine for p in PROVIDERS if not p.optional}
    if format == "json":
        return {
            "engines": list_engines() if not group else list(descriptions),
            "taxonomy": taxonomy,
            "descriptions": descriptions,
            "needs_api_key": sorted(needs_key & set(descriptions)),
        }
    return render_engines(taxonomy, descriptions, needs_key)


@mcp.tool(
    title="Compare URLs side-by-side",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def compare(
    question: str,
    urls: list[str],
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Fetch 2-5 URLs concurrently and return per-URL excerpts so the LLM can
    compare them against a single question in one round trip.

    Best for:
    - Side-by-side product/feature/article comparisons.
    - "Compare X to Y" or "How does A differ from B" queries.
    - Triangulating a fact across multiple sources.

    Not recommended for:
    - >5 URLs -> use `fetch_batch`.
    - 1 URL -> use `fetch`.
    - Don't have URLs yet -> use `search` or `research` first.

    Returns:
    - markdown (default): a comparison brief with per-URL sections, each
      containing title, sitename, published date, and a smart-truncated excerpt.
    - json: {question, urls, excerpts:[{url, title, excerpt, ...}],
      tokens_estimated}.

    Common mistakes:
    - Asking `compare` to actually answer the question — it returns material,
      the LLM does the comparison.
    - Passing >5 URLs and expecting them all to fit in context — use
      `fetch_batch` for bulk reads.

    Args:
        question: The comparison question the LLM will answer using the
            returned excerpts.
        urls: 2-5 absolute http(s) URLs.
        format: "markdown" (default) or "json".
    """
    payload = await compare_urls(question, urls)
    return _maybe_render(payload, format, render_compare)


@mcp.tool(
    title="Extract structured data from a URL",
    annotations=ToolAnnotations(
        read_only_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def extract_structured(
    url: str,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Pull JSON-LD, OpenGraph, Twitter cards, and microdata from a web page.

    Best for:
    - Product pages (price, currency, availability, brand, rating).
    - Article pages (author, publish date, image, headline).
    - Recipe / event / video pages where rich metadata IS the answer.
    - Cases where `fetch` returns prose but you need fields.

    Not recommended for:
    - Just reading a page -> use `fetch`.
    - PDFs / DOCX -> use `read_doc`.
    - Pages that don't publish schema.org metadata (most blogs) — you'll get
      empty lists; fall back to `fetch`.

    Returns:
    - json: {url, json_ld:[], microdata:[], opengraph:[], rdfa:[]}. Twitter
      card meta tags are surfaced inside the `opengraph` list.
    - markdown (default): a flattened key/value view with each block printed
      as a JSON code block under its syntax heading.

    Common mistakes:
    - Calling on every URL "just in case" — most sites have no structured
      data, and `fetch` is what you actually want.

    Args:
        url: Absolute http(s) URL.
        format: "markdown" (default) or "json".
    """
    payload = await _extract_structured(url)
    return _maybe_render(payload, format, render_structured)


@mcp.tool(
    title="Download a file to disk",
    annotations=ToolAnnotations(
        # The one tool here that creates a caller-visible local file.
        read_only_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
)
async def download(
    url: str,
    format: Format = "markdown",
) -> str | dict[str, Any]:
    """Save a file from a URL to a local, auto-expiring download directory.

    Downloads are enabled by default and saved under
    `SEARCH_MCP_CACHE_DIR/downloads`. Set `SEARCH_MCP_DOWNLOAD_ENABLED=false`
    to disable them or `SEARCH_MCP_DOWNLOAD_DIR` to override the destination.

    Best for:
    - Keeping an actual file (installer, dataset, archive, image) rather than
      its text.
    - Handing a path to another tool that needs a real file on disk.

    Not recommended for:
    - Reading a document's contents -> use `read_doc`, which parses it without
      touching the filesystem.
    - Looking at a web page -> use `fetch`.
    - Viewing an image -> use `fetch(inline=True)`.

    Returns:
    - markdown (default): where the file was saved, its size and type.
    - json: {url, saved_path, media_type, bytes_size, sha256, expires_in_hours}.
      An expires_in_hours value of 0 means TTL cleanup is disabled.

    Retention: files older than SEARCH_MCP_DOWNLOAD_TTL_HOURS (default 24) are
    deleted before the next download and at startup. A value of 0 disables TTL
    cleanup. Otherwise, treat the path as short-lived and copy it elsewhere if
    you need to keep it.

    Args:
        url: Absolute http(s) URL of the file to save.
        format: "markdown" or "json".
    """
    downloads.require_download_dir()

    import anyio

    # Directory scans and writes are blocking syscalls; keep them off the event
    # loop so a large download directory or save cannot stall other requests.
    await anyio.to_thread.run_sync(downloads.purge_expired)
    result = await fetch_bytes(url)
    path = await anyio.to_thread.run_sync(
        downloads.save, url, result.data or b"", result.media_type
    )

    payload = {
        "url": url,
        "saved_path": str(path),
        "media_type": result.media_type,
        "bytes_size": result.bytes_size,
        "sha256": result.sha256,
        "expires_in_hours": settings.download_ttl_hours,
    }
    if result.width is not None:
        payload["width"] = result.width
        payload["height"] = result.height
    if format == "json":
        return payload
    lines = [
        f"# Downloaded `{path.name}`",
        "",
        f"- **Saved to:** `{path}`",
        f"- **Type:** {result.media_type or 'unknown'}",
        f"- **Size:** {result.bytes_size:,} bytes",
    ]
    if result.width is not None:
        lines.append(f"- **Dimensions:** {result.width}×{result.height}px")
    lines.append(f"- **SHA-256:** `{result.sha256}`")
    lines.append("")
    if settings.download_ttl_hours == 0:
        lines.append("> TTL cleanup is disabled; this file will not expire automatically.")
    else:
        lines.append(
            f"> Deleted automatically after {settings.download_ttl_hours}h. "
            "Copy it elsewhere to keep it."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompts (slash-commands in MCP clients)
# ---------------------------------------------------------------------------


@mcp.prompt(title="Research thoroughly")
def research_prompt(question: str, depth: int = 3) -> str:
    """Instruct the model to do a thorough, cited research pass on a question."""
    return (
        f"You have access to the search-mcp tools. Research the following "
        f"question thoroughly and produce a well-cited answer.\n\n"
        f"QUESTION: {question}\n\n"
        f"PROCEDURE:\n"
        f"1. Call the `research` tool with question={question!r} and depth={depth}.\n"
        f"2. Read each fetched source. If a source seems unreliable, call "
        f"`search` for a corroborating source.\n"
        f"3. If any document was truncated, call `fetch` again with that URL "
        f"or use `read_doc` for paginating PDFs.\n"
        f"4. Write a synthesis (3-8 paragraphs) that:\n"
        f"   - Answers the question directly in the first sentence.\n"
        f"   - Cites sources inline using [1], [2], ... markers that match the\n"
        f"     order returned by `research`.\n"
        f"   - Notes any disagreement between sources.\n"
        f"   - Lists the full source URLs at the end under a 'Sources' header.\n"
        f"5. If you could not find a confident answer, say so explicitly and\n"
        f"   show what was checked."
    )


@mcp.prompt(title="Fact-check claim")
def factcheck_prompt(claim: str) -> str:
    """Instruct the model to fact-check a specific claim with citations."""
    return (
        f"Fact-check the following claim using the search-mcp tools.\n\n"
        f"CLAIM: {claim}\n\n"
        f"PROCEDURE:\n"
        f"1. Call `search` with a focused query (key entities + date if any).\n"
        f"2. Call `fetch_batch` on the 3-5 most authoritative-looking URLs\n"
        f"   (prefer primary sources, official sites, established outlets).\n"
        f"3. For each source, quote the supporting or contradicting passage.\n"
        f"4. Output a verdict on a 5-point scale: TRUE / MOSTLY TRUE / MIXED /\n"
        f"   MOSTLY FALSE / FALSE, followed by a one-paragraph justification\n"
        f"   with [n]-style citations matching the source order.\n"
        f"5. End with a 'Sources' list of URLs.\n"
        f"6. If sources disagree, surface that explicitly rather than picking\n"
        f"   one side silently."
    )


@mcp.prompt(title="Compare sources")
def compare_sources(question: str, urls: str) -> str:
    """Instruct the model to use `compare` against several URLs and answer
    the question with per-URL citations."""
    return (
        f"Use the `compare` tool with question={question!r} and "
        f"urls={urls!r} (comma-separated). For each excerpt returned, "
        "answer the question with [n] citations to the URL it came from. "
        "If the excerpts disagree, surface that explicitly rather than "
        "picking one side silently."
    )


@mcp.prompt(title="News brief")
def news_brief(topic: str, since: str = "day") -> str:
    """Instruct the model to produce a fresh news brief using `search` +
    `fetch_batch`, with citations."""
    return (
        f"Use the `search` tool with query={topic!r}, category='news', "
        f"freshness={since!r}. Then fetch the top 3 results in parallel "
        "via `fetch_batch`. Produce a 5-bullet brief, with [n] citations "
        "matching the order returned by `search`. End with a 'Sources' "
        "list of URLs."
    )


# ---------------------------------------------------------------------------
# Resource templates — expose cached data as readable resources
# ---------------------------------------------------------------------------


@mcp.resource("cache://page/{url}", title="Cached page")
async def cached_page(url: str) -> str:
    """Return the cached Markdown body for a previously-fetched URL.

    The URL must be percent-encoded when embedded in the resource URI
    (RFC 6570 templates do not allow `:` or `/` inside variable expansions).
    """
    from urllib.parse import unquote
    decoded = unquote(url)
    page = await cache.get_page(decoded)
    if not page:
        raise ResourceNotFoundError(f"Not in cache: {decoded}")
    return page.get("content") or ""


@mcp.resource("cache://search/{query_hash}", title="Cached search result")
async def cached_search(query_hash: str) -> str:
    """Return the cached merged result list for a search query hash.

    The hash is the same one the aggregator uses internally to key the
    `search_cache` table. Useful for exposing prior `search` invocations
    as MCP resources without re-running them.
    """
    hit = await cache.get_search(query_hash)
    if hit is None:
        raise ResourceNotFoundError(f"No cached search for hash: {query_hash}")
    # get_search also returns the provenance recorded with the row; this
    # resource is defined as the merged RESULT LIST, so only that half is
    # serialised. Changing the shape here would break every existing reader.
    rows, _meta = hit
    import json
    return json.dumps(rows, ensure_ascii=False, indent=2)


_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "[::1]")


def _http_security(host: str, port: int) -> TransportSecuritySettings:
    """Build the DNS-rebinding guard for the HTTP transport.

    Passing no settings at all leaves the guard OFF (the SDK defaults that way
    for backwards compatibility), which would let any web page a user visits
    drive this server through their browser. So it is always constructed —
    every host/origin that can legitimately reach the bind address is
    enumerated instead.
    """
    hosts = [f"{h}:{port}" for h in _LOOPBACK_HOSTS]
    origins = [f"http://{h}:{port}" for h in _LOOPBACK_HOSTS]
    if host not in (*_LOOPBACK_HOSTS, "0.0.0.0", "::"):  # noqa: S104 - comparison, not a bind
        hosts.append(f"{host}:{port}")
        origins.append(f"http://{host}:{port}")
    extra = [o for o in settings.http_allowed_origins.replace(",", " ").split() if o]
    origins.extend(extra)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def run(
    transport: str | None = None,
    host: str | None = None,
    port: int | None = None,
    path: str | None = None,
) -> None:
    """Start the MCP server. Arguments override the SEARCH_MCP_* settings."""
    transport = transport or settings.transport
    # Ephemeral downloads are swept here as well as before each download:
    # this process is often short-lived, so a background timer would
    # frequently never fire.
    downloads.purge_expired()
    try:
        if transport == "streamable-http":
            host = host or settings.http_host
            port = port if port is not None else settings.http_port
            path = path or settings.http_path
            log.info("search-mcp listening on http://%s:%s%s", host, port, path)
            mcp.run(
                transport="streamable-http",
                host=host,
                port=port,
                streamable_http_path=path,
                transport_security=_http_security(host, port),
            )
        else:
            mcp.run()
    finally:
        try:
            import anyio
            anyio.run(pool.shutdown)
        except Exception:
            pass
        try:
            import anyio
            # A clean close checkpoints the WAL; without it the daemon-thread
            # workaround in cache.py is the only thing standing between us and
            # a hung exit.
            anyio.run(cache.close)
        except Exception:
            pass


__all__ = ["mcp", "run"]

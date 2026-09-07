"""Finance sources: SEC EDGAR, Yahoo Finance, cninfo, World Bank, IMF (offline).

The fixtures below are trimmed copies of real responses. Tests call the pure
mappers and `build_url` directly, so nothing here touches the network; a small
live suite at the end is gated on SEARCH_MCP_TEST_NETWORK=1.
"""

from __future__ import annotations

import os

import pytest

from search_mcp.engines import ENGINES, SearchFilters, get_engine
from search_mcp.engines.cninfo import CninfoEngine
from search_mcp.engines.imf import ImfEngine
from search_mcp.engines.sec_edgar import (
    SecEdgarEngine,
    _split_forms,
    _split_ticker,
    _user_agent,
)
from search_mcp.engines.worldbank import WorldBankEngine
from search_mcp.engines.yahoofinance import YahooFinanceEngine, _entity_query

# pytest.ini sets `asyncio_mode = auto` so async tests are auto-marked.

NETWORK = os.environ.get("SEARCH_MCP_TEST_NETWORK") == "1"
skip_offline = pytest.mark.skipif(
    not NETWORK, reason="set SEARCH_MCP_TEST_NETWORK=1 to run"
)

FINANCE = ["sec_edgar", "yahoofinance", "worldbank", "cninfo", "imf"]


# ---------------------------------------------------------------------------
# Registry contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", FINANCE)
def test_registered_and_declares_finance_category(name):
    assert name in ENGINES
    engine = get_engine(name)
    assert engine.name == name
    assert "finance" in engine.categories


@pytest.mark.parametrize("name", FINANCE)
def test_not_in_the_default_pool(name):
    """Finance sources are routed by `category=`, never paid for on every
    ordinary web search."""
    from search_mcp.config import Settings

    assert name not in Settings().default_engines


# ---------------------------------------------------------------------------
# SEC EDGAR
# ---------------------------------------------------------------------------

_EDGAR = {
    "hits": {
        "total": {"value": 105},
        "hits": [
            {
                "_id": "0001654954-26-001943:inuvo_10k.htm",
                "_source": {
                    "ciks": ["0000829323"],
                    "display_names": ["Inuvo, Inc.  (INUV)  (CIK 0000829323)"],
                    "form": "10-K",
                    "file_date": "2026-03-05",
                    "period_ending": "2025-12-31",
                    "file_description": "FORM 10-K",
                    "biz_locations": ["Little Rock, AR"],
                },
            },
            {
                "_id": "0001213900-24-030023:ea172503_424b2.htm",
                "_source": {
                    "ciks": ["0000019617"],
                    "display_names": [
                        "JPMORGAN CHASE & CO (JPM, AMJB, JPM-PC, JPM-PD)  (CIK 0000019617)"
                    ],
                    "form": "424B2",
                    "file_date": "2024-04-04",
                },
            },
            # No `ciks`: the archive path cannot be built, so it must be dropped
            # rather than emitted as a broken URL.
            {"_id": "0000000000-00-000000:x.htm", "_source": {"form": "8-K"}},
        ],
    }
}


def test_sec_user_agent_carries_no_url():
    """SEC answers 403 to a User-Agent containing a URL — the package's usual
    `free-search-mcp/1.0 (+https://github.com/...)` string is rejected outright
    while a plain name-and-contact form gets a 200. This is the single reason
    the engine overrides `api_headers`, so it is worth a regression test."""
    ua = _user_agent()
    assert "http" not in ua.lower()
    assert ua.startswith("free-search-mcp")


def test_sec_user_agent_includes_the_configured_contact(monkeypatch):
    from search_mcp.engines import sec_edgar

    monkeypatch.setattr(sec_edgar.settings, "contact_email", "ops@example.com")
    assert _user_agent() == "free-search-mcp ops@example.com"


def test_sec_headers_are_used_instead_of_a_browser_fingerprint():
    engine = SecEdgarEngine()
    assert engine.impersonate is None
    assert "http" not in engine.api_headers["User-Agent"].lower()


@pytest.mark.parametrize(
    ("query", "text", "forms"),
    [
        ("NVDA 10-K risk factors", "NVDA risk factors", ["10-K"]),
        ("tesla 8-K 10-Q", "tesla", ["8-K", "10-Q"]),
        ("artificial intelligence", "artificial intelligence", []),
        ("SC 13D activist stake", "activist stake", ["SC 13D"]),
        # A query that is nothing BUT a form name keeps its text: `forms=` with
        # an empty `q` is not a search.
        ("10-K", "10-K", ["10-K"]),
    ],
)
def test_sec_splits_form_names_out_of_the_query(query, text, forms):
    """EDGAR's relevance ranking alone is dominated by structured-product
    pricing supplements; routing a named form to `forms=` (which filters)
    instead of leaving it in `q` (which merely matches documents MENTIONING it)
    took "artificial intelligence risk" from 276 mixed hits to 20 annual
    reports."""
    assert _split_forms(query) == (text, forms)


@pytest.mark.parametrize(
    ("query", "entity"),
    [
        ("NVDA risk factors", "NVDA"),
        ("NVDA", "NVDA"),
        ("BRK.B annual report", "BRK.B"),
        # Case is load-bearing: lower-cased, the ticker space is a minefield of
        # ordinary words (`IT`, `ALL`, `ON`, `SO`, `NOW`, `GO`, `CAR` are all
        # real tickers).
        ("all filings on risk", ""),
        ("nvda risk factors", ""),
        # Upper-cased abbreviations a person did not mean as an issuer.
        ("US GDP outlook", ""),
        ("AI chips", ""),
        ("artificial intelligence", ""),
    ],
)
def test_sec_recognises_a_ticker_only_when_written_as_one(query, entity):
    assert _split_ticker(query)[1] == entity


def test_sec_leaves_the_ticker_in_the_query_text():
    """`entityName` narrows to the issuer, but `q` still has to match something
    — and for a bare "NVDA" the ticker is the only term there is."""
    assert _split_ticker("NVDA")[0] == "NVDA"


def test_sec_scopes_a_ticker_query_to_the_issuer():
    """Unscoped, "NVDA risk factors" led with four ProShares and Investment
    Managers 497Ks that merely MENTION the ticker; `entityName=NVDA` returns
    NVIDIA's own 10-K and 10-Qs."""
    url = SecEdgarEngine().build_url("NVDA risk factors", 10)
    assert "entityName=NVDA" in url


def test_sec_scoping_can_be_turned_off_for_the_retry():
    """A ticker guess that matches no issuer would turn a query that had
    answers into one that has none, so an empty scoped search is re-run
    unscoped."""
    url = SecEdgarEngine().build_url("NVDA risk factors", 10, scoped=False)
    assert "entityName" not in url
    assert "q=NVDA+risk+factors" in url


async def test_sec_retries_unscoped_when_the_ticker_guess_finds_nothing(
    monkeypatch,
):
    engine = SecEdgarEngine()
    urls: list[str] = []

    async def fake(url, **kw):
        urls.append(url)
        return _EDGAR if "entityName" not in url else {"hits": {"hits": []}}

    monkeypatch.setattr(engine, "_get_json", fake)
    out = await engine.fetch_results("NVDA risk factors", 10, None)
    assert len(urls) == 2
    assert "entityName=NVDA" in urls[0] and "entityName" not in urls[1]
    assert out


async def test_sec_does_not_retry_when_there_was_no_guess_to_undo(monkeypatch):
    """A query with no ticker has nothing to widen, so a second identical
    request would only cost a round trip."""
    engine = SecEdgarEngine()
    urls: list[str] = []

    async def fake(url, **kw):
        urls.append(url)
        return {"hits": {"hits": []}}

    monkeypatch.setattr(engine, "_get_json", fake)
    assert await engine.fetch_results("artificial intelligence", 10, None) == []
    assert len(urls) == 1


def test_sec_build_url_sends_forms_and_a_custom_date_range():
    url = SecEdgarEngine().build_url(
        "NVDA 10-K risk", 10, SearchFilters(freshness="month")
    )
    assert "q=NVDA+risk" in url
    assert "forms=10-K" in url
    # startdt/enddt are IGNORED unless dateRange=custom rides along.
    assert "dateRange=custom" in url
    assert "startdt=" in url and "enddt=" in url


def test_sec_maps_hits_to_archive_document_urls():
    out = SecEdgarEngine().map_results(_EDGAR)
    assert [r.url for r in out] == [
        "https://www.sec.gov/Archives/edgar/data/829323/000165495426001943/inuvo_10k.htm",
        "https://www.sec.gov/Archives/edgar/data/19617/000121390024030023/ea172503_424b2.htm",
    ]
    assert out[0].title == "10-K — Inuvo, Inc. (INUV)"
    assert out[0].published_age == "2026-03-05"
    assert out[0].published_age_confident is True


def test_sec_title_keeps_only_the_first_ticker():
    """Multi-listed issuers carry every ticker and warrant class in the display
    name; one identifies the company and the rest is noise."""
    out = SecEdgarEngine().map_results(_EDGAR)
    assert out[1].title == "424B2 — JPMORGAN CHASE & CO (JPM)"


def test_sec_drops_a_hit_it_cannot_build_a_url_for():
    out = SecEdgarEngine().map_results(_EDGAR)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# Yahoo Finance
# ---------------------------------------------------------------------------

_YAHOO = {
    "quotes": [
        {
            "symbol": "NVDA",
            "shortname": "NVIDIA Corporation",
            "longname": "NVIDIA Corporation",
            "typeDisp": "Equity",
            "exchDisp": "NASDAQ",
            "sectorDisp": "Technology",
            "industryDisp": "Semiconductors",
        },
        {
            "symbol": "NVHE-U.TO",
            "longname": "Harvest NVIDIA Enhanced High Income Shares ETF",
            "typeDisp": "ETF",
        },
    ],
    "news": [
        {
            "title": "Wall Street is turning Nvidia's AI chips into a futures market",
            "link": "https://finance.yahoo.com/markets/article/nvidia-futures.html",
            "publisher": "Yahoo Finance",
            "providerPublishTime": 1788005497,
        },
        {
            "title": "Down 35% From Its High, Is Sandisk Stock a Bargain?",
            "link": "https://finance.yahoo.com/m/sandisk.html",
            "publisher": "Motley Fool",
            "providerPublishTime": 1788005497,
        },
    ],
}


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("nvidia earnings", "nvidia"),
        ("tesla stock price forecast", "tesla"),
        ("AAPL", "AAPL"),
        # Pure filler has no entity to find, so the original survives.
        ("stock price", "stock price"),
    ],
)
def test_yahoo_strips_filler_before_resolving(query, expected):
    """A multi-word query stops resolving: `q=nvidia` returns NVDA and friends,
    `q=nvidia earnings` returns an empty `quotes[]`."""
    assert _entity_query(query) == expected


def test_yahoo_emits_quotes_with_symbol_and_sector():
    out = YahooFinanceEngine()._quotes(_YAHOO["quotes"])
    assert out[0].title == "NVDA — NVIDIA Corporation"
    assert out[0].url == "https://finance.yahoo.com/quote/NVDA"
    assert "NASDAQ" in out[0].snippet and "Semiconductors" in out[0].snippet


def test_yahoo_keeps_only_news_that_names_the_resolved_company():
    """`news[]` is NOT scoped to the query — it is a generic markets feed. Only
    headlines that actually mention the query or the resolved instrument are
    results; the rest would be confidently-presented noise."""
    engine = YahooFinanceEngine()
    quotes = engine._quotes(_YAHOO["quotes"])
    news = engine._news(_YAHOO["news"], "nvidia", quotes)
    assert [r.title for r in news] == [
        "Wall Street is turning Nvidia's AI chips into a futures market"
    ]


def test_yahoo_company_terms_come_from_the_top_match_only():
    """Harvesting words from the ETF rows admitted headlines on the strength of
    "high": "Down 35% From Its High, Is Sandisk Stock a Bargain" scored as an
    Nvidia story."""
    engine = YahooFinanceEngine()
    terms = engine._relevance_terms("nvidia", engine._quotes(_YAHOO["quotes"]))
    assert "high" not in terms
    assert "nvidia" in terms and "nvda" in terms


def test_yahoo_drops_all_news_when_nothing_resolved():
    engine = YahooFinanceEngine()
    assert engine._news(_YAHOO["news"], "zzzz", []) == []


def test_yahoo_news_carries_a_confident_publish_date():
    engine = YahooFinanceEngine()
    quotes = engine._quotes(_YAHOO["quotes"])
    news = engine._news(_YAHOO["news"], "nvidia", quotes)
    assert news[0].published_age == "2026-08-29"
    assert news[0].published_age_confident is True


# ---------------------------------------------------------------------------
# cninfo
# ---------------------------------------------------------------------------

_CNINFO = {
    "totalAnnouncement": 238,
    "announcements": [
        {
            "secCode": "688525",
            "secName": "佰维存储",
            "announcementTitle": "关于参加科创板<em>人工智能</em>行业集体业绩说明会的公告",
            "announcementTime": 1787932800000,
            "adjunctUrl": "finalpage/2026-08-29/1225533987.PDF",
            "adjunctSize": 113,
            "adjunctType": "PDF",
            "pageColumn": "SHKCB",
        },
        # No adjunctUrl: nothing to link to.
        {"secCode": "000001", "secName": "X", "announcementTitle": "公告"},
    ],
}


def test_cninfo_strips_highlight_markup_and_prefixes_the_issuer():
    """Titles arrive with `<em>` highlight markup around the matched terms, and
    a bare "关于…的公告" is unattributable without the issuer."""
    out = CninfoEngine().map_results(_CNINFO)
    assert len(out) == 1
    assert out[0].title == (
        "佰维存储 (688525) 关于参加科创板人工智能行业集体业绩说明会的公告"
    )
    assert "<em>" not in out[0].title


def test_cninfo_builds_an_https_static_url_and_a_confident_date():
    out = CninfoEngine().map_results(_CNINFO)
    assert out[0].url == (
        "https://static.cninfo.com.cn/finalpage/2026-08-29/1225533987.PDF"
    )
    assert out[0].published_age == "2026-08-29"
    assert out[0].published_age_confident is True


def test_cninfo_posts_a_form_with_a_date_window():
    form = CninfoEngine()._form("人工智能", 5, SearchFilters(freshness="month"))
    assert form["searchkey"] == "人工智能"
    assert form["pageSize"] == 5
    assert "~" in form["seDate"]


def test_cninfo_omits_the_date_window_without_a_freshness_filter():
    assert "seDate" not in CninfoEngine()._form("x", 5, None)


# ---------------------------------------------------------------------------
# World Bank
# ---------------------------------------------------------------------------

_WORLDBANK = {
    "total": 499,
    "documents": {
        "D32417241": {
            "id": "32417241",
            "count": "Viet Nam",
            "docty": "Brief",
            "docdt": "2020-09-01T04:00:00Z",
            "display_title": "Vietnam Macro Monitoring",
            "url": "http://documents.worldbank.org/curated/en/213631600443823992",
            "pdfurl": "http://documents.worldbank.org/curated/en/213631600443823992/pdf/x.pdf",
            "abstracts": {"cdata!": "This brief focuses on economic developments."},
        },
        # The hit map carries non-document siblings that must not be mapped.
        "facets": {},
    },
}


def test_worldbank_skips_the_facets_sibling_in_the_hit_map():
    out = WorldBankEngine().map_results(_WORLDBANK)
    assert len(out) == 1
    assert out[0].title == "Vietnam Macro Monitoring"


def test_worldbank_prefers_the_landing_page_and_upgrades_it_to_https():
    """The landing page links the PDF, the text and the metadata, and is far
    cheaper for `fetch` than a multi-megabyte download. The catalogue still
    emits http:// links; the same host serves https."""
    out = WorldBankEngine().map_results(_WORLDBANK)
    assert out[0].url == "https://documents.worldbank.org/curated/en/213631600443823992"


def test_worldbank_snippet_leads_with_type_and_country():
    out = WorldBankEngine().map_results(_WORLDBANK)
    assert out[0].snippet.startswith("Brief · Viet Nam —")
    assert out[0].published_age == "2020-09-01"
    assert out[0].published_age_confident is True


def test_worldbank_asks_for_only_the_fields_it_renders():
    url = WorldBankEngine().build_url("inflation", 5)
    assert "fl=" in url and "rows=5" in url


# ---------------------------------------------------------------------------
# IMF
# ---------------------------------------------------------------------------

_IMF_INDICATORS = {
    "NGDP_RPCH": {
        "label": "Real GDP growth",
        "description": "Gross domestic product at constant prices.",
        "unit": "Annual percent change",
        "dataset": "WEO",
        "source": "World Economic Outlook (April 2026)",
    },
    "PCPIPCH": {
        "label": "Inflation rate, average consumer prices",
        "description": "Consumer price inflation.",
        "unit": "Annual percent change",
        "dataset": "WEO",
        "source": "World Economic Outlook (April 2026)",
    },
    "NGDPRPC_PCH": {
        "label": "Real Per Capita GDP Growth",
        "description": "Real per capita GDP growth.",
        "unit": "Annual percent change",
        "dataset": "WEO",
        "source": "World Economic Outlook (April 2026)",
    },
    "GDP": {
        "label": "Nominal GDP",
        "description": "Gross domestic product at current prices.",
        "unit": "Millions of US Dollars",
        "dataset": "CF",
        "source": "Capital Flows",
    },
}

_IMF_COUNTRIES = {
    "VNM": "Vietnam",
    "CHN": "China, People's Republic of",
    "USA": "United States",
    "TCD": "Chad",
}


def test_imf_matches_a_country_by_its_short_name():
    """The catalogue's official form is unusable as-is: a query says "china",
    the catalogue says "China, People's Republic of"."""
    assert ImfEngine()._match_countries("china inflation", _IMF_COUNTRIES) == ["CHN"]


def test_imf_matches_a_country_by_iso3_code():
    assert ImfEngine()._match_countries("VNM gdp", _IMF_COUNTRIES) == ["VNM"]


def test_imf_country_matching_respects_word_boundaries():
    """"chad" must not be found inside "chadwick"."""
    assert ImfEngine()._match_countries("chadwick holdings", _IMF_COUNTRIES) == []


def test_imf_strips_the_country_before_scoring_indicators():
    """Leaving the country in costs real accuracy: "vietnam real gdp growth"
    scored 57.9 against "Real GDP growth" — the extra token counts against the
    ratio — and lost to an unrelated capital-flows series."""
    engine = ImfEngine()
    codes = engine._match_countries("vietnam real gdp growth", _IMF_COUNTRIES)
    metric = engine._strip_countries(
        "vietnam real gdp growth", codes, _IMF_COUNTRIES
    )
    assert metric == "real gdp growth"
    assert engine._match_indicators(metric, _IMF_INDICATORS)[0] == "NGDP_RPCH"


def test_imf_code_shortcut_needs_the_code_typed_as_a_code():
    """Three of the 132 IMF codes are ordinary words — `GDP` is Capital Flows'
    NOMINAL GDP, `LP` is Population, `LUR` is Unemployment rate. A case-folded
    shortcut fired on every query containing "gdp" and pinned nominal GDP at
    100, beating the indicator literally called "Real GDP growth"."""
    engine = ImfEngine()
    assert engine._match_indicators("real gdp growth", _IMF_INDICATORS)[0] == (
        "NGDP_RPCH"
    )
    # Typed as a code, it IS the code.
    assert engine._match_indicators("GDP", _IMF_INDICATORS)[0] == "GDP"
    assert engine._match_indicators("NGDP_RPCH", _IMF_INDICATORS) == ["NGDP_RPCH"]


def test_imf_scoring_ignores_capitalization():
    """rapidfuzz normalizes nothing by default, so a lowercase query scored 73
    against its own indicator's label purely on case — uncomfortably close to
    the 60 cutoff."""
    assert ImfEngine()._ratio("real gdp growth", "Real GDP growth") == 100.0


def test_imf_exact_label_outranks_a_label_that_merely_contains_the_query():
    """`token_set_ratio` scores the INTERSECTION, so every superset label ties
    at 100: "real gdp growth" matched "Real Per Capita GDP Growth" as perfectly
    as "Real GDP growth", and alphabetical order then picked the wrong one."""
    assert ImfEngine()._match_indicators("real gdp growth", _IMF_INDICATORS) == [
        "NGDP_RPCH",
        "NGDPRPC_PCH",
    ]


def test_imf_returns_nothing_rather_than_an_unrelated_series():
    """A number always looks authoritative, so a weak match is worse than no
    match at all."""
    assert ImfEngine()._match_indicators("zzzzqqq", _IMF_INDICATORS) == []


def test_imf_recent_keeps_the_last_observations_including_forecasts():
    values = {str(y): float(y) for y in range(1990, 2032)}
    recent = ImfEngine()._recent(values)
    assert [y for y, _v in recent][-1] == "2031"
    assert len(recent) == 8


# ---------------------------------------------------------------------------
# Live network — opt-in
# ---------------------------------------------------------------------------


@skip_offline
@pytest.mark.parametrize(
    ("name", "query"),
    [
        ("sec_edgar", "NVIDIA 10-K risk factors"),
        ("yahoofinance", "nvidia"),
        ("worldbank", "vietnam inflation"),
        ("cninfo", "人工智能"),
        ("imf", "vietnam real gdp growth"),
    ],
)
async def test_live_finance_engine_returns_results(name, query):
    out = await get_engine(name).search(query, 3)
    if not out:
        pytest.skip(f"{name} returned nothing for {query!r}")
    assert all(r.url.startswith("http") for r in out)
    assert all(r.title for r in out)

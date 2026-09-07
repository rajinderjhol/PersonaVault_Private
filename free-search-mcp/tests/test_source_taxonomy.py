"""Drift guards for the two-level source taxonomy (group -> sub-group -> engine).

Every fact the `engines` tool renders and every routing decision
`engines_for_category` makes is DERIVED from `Engine.categories` and
`Engine.description`. That is the point — the hand-maintained buckets these
replaced had drifted badly, advertising `pubmed` for `category="paper"` long
after `category_engine_limit` stopped it from ever running, and never
mentioning `openverse` or `zenodo` at all.

Derived output only stays honest if the declarations underneath it do, so these
tests pin the declaration rules rather than any particular rendering.

All offline and pure — no network, no event loop.
"""

from __future__ import annotations

import typing

import pytest

from search_mcp.aggregator import _is_exclusive, engines_for_category
from search_mcp.engines import ENGINES, Category, CategoryGroup, source_taxonomy
from search_mcp.engines.base import category_group

_CATEGORY_TOKENS = set(typing.get_args(Category))
_GROUPS = set(typing.get_args(CategoryGroup))


# ---------------------------------------------------------------------------
# Declaration rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_every_engine_has_a_one_line_description(name):
    """This string IS the description an LLM reads when choosing a source, so a
    missing one is a source the model cannot evaluate."""
    description = ENGINES[name].description
    assert description, f"{name} has no description"
    assert "\n" not in description, f"{name}'s description spans lines"
    assert len(description) <= 100, f"{name}'s description is {len(description)} chars"


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_declaring_a_sub_group_implies_declaring_its_group(name):
    """`frozenset({"paper.biomed"})` without `"paper"` breaks TWO things: the
    engine drops out of `category="paper"` routing, and — worse — it loses the
    `native` bypass in `finalize_results`, so its own doi.org/europepmc.org
    URLs get discarded by the hostname allowlist that exists purely to
    approximate the category for general web engines."""
    categories = ENGINES[name].categories
    for token in categories:
        if "." in token:
            assert category_group(token) in categories, (
                f"{name} declares {token!r} without its group"
            )


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_every_declared_category_is_in_the_agent_facing_enum(name):
    """A token no `Category` member matches is unreachable: the model can never
    select it, because the enum in the tool schema is the whole menu."""
    for token in ENGINES[name].categories:
        assert token in _CATEGORY_TOKENS, f"{name} declares unroutable {token!r}"


def test_every_group_token_is_a_category_group():
    for token in _CATEGORY_TOKENS:
        if "." not in token:
            assert token in _GROUPS, f"{token!r} is in Category but not CategoryGroup"


# `pdf` and `blog` are pure POST-FILTER categories: no source indexes "a PDF"
# or "a blog" as such, so they narrow the general web pool by URL/hostname
# instead of routing anywhere. Every other group must have a specialist.
_FILTER_ONLY_GROUPS = {"pdf", "blog"}


def test_every_sub_group_token_has_at_least_one_engine():
    """An enum value that routes nowhere is a dead end the model will still
    try."""
    for token in _CATEGORY_TOKENS:
        if "." in token:
            assert engines_for_category(token), f"{token!r} routes to no engine"
    for group in _GROUPS - _FILTER_ONLY_GROUPS:
        assert engines_for_category(group), f"{group!r} routes to no engine"


def test_exclusive_categories_name_real_groups_or_tokens():
    from search_mcp.aggregator import _EXCLUSIVE_CATEGORIES

    for token in _EXCLUSIVE_CATEGORIES:
        assert token in _CATEGORY_TOKENS, f"{token!r} is not a Category value"


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def test_exclusivity_survives_a_dotted_token():
    """`category in _EXCLUSIVE_CATEGORIES` was a bare-string test, so any dotted
    image/dataset token fell through to the augmenting branch and re-admitted
    the four web engines exclusivity exists to keep out."""
    assert _is_exclusive("image") is True
    assert _is_exclusive("image.anything") is True
    assert _is_exclusive("paper") is False
    assert _is_exclusive("paper.biomed") is False
    assert _is_exclusive(None) is False


def test_bare_group_spreads_across_sub_groups_before_repeating_one():
    """Registry order alone spent the whole `category_engine_limit` budget on
    whichever sub-group sorted first: `category="paper"` picked
    `arxiv, openalex, crossref` — two of them overlapping DOI indexes — and
    dropped `pubmed` entirely, in a category four separate docs advertised it
    for."""
    picks = engines_for_category("paper")
    subs = []
    for name in picks:
        sub = sorted(
            t for t in ENGINES[name].categories if t.startswith("paper.")
        )
        subs.append(sub[0] if sub else "")
    assert len(set(subs)) == len(subs), f"a sub-group repeated before others ran: {picks}"


def test_paper_routing_reaches_the_biomedical_index():
    """`category="paper"` used to return arxiv + two overlapping DOI indexes and
    nothing biomedical — the whole reason for the round-robin."""
    biomed = set(engines_for_category("paper.biomed"))
    assert biomed & set(engines_for_category("paper")), biomed


def test_sub_group_narrows_to_its_own_engines():
    for token in ("paper.preprint", "paper.index", "paper.biomed", "news.world"):
        group = category_group(token)
        for name in engines_for_category(token):
            assert token in ENGINES[name].categories
            assert group in ENGINES[name].categories


def test_taxonomy_lists_every_engine_once_per_sub_group():
    """An engine may legitimately appear under several sub-groups — Europe PMC
    serves biomed, preprint AND openaccess, and the tree should say so in all
    three. What must never happen is the same name twice in ONE bucket, or an
    engine listed both under a group and under that group's sub-groups."""
    taxonomy = source_taxonomy()
    for group, subs in taxonomy.items():
        for sub, names in subs.items():
            assert len(names) == len(set(names)), f"{group}.{sub} lists a name twice"
        ungrouped = set(subs.get("") or [])
        nested = {n for sub, names in subs.items() if sub for n in names}
        assert not (ungrouped & nested), f"{group} lists an engine at both levels"


def test_taxonomy_covers_every_registered_engine():
    taxonomy = source_taxonomy()
    listed = {n for subs in taxonomy.values() for names in subs.values() for n in names}
    assert listed == set(ENGINES)


def test_finance_group_reaches_filings_market_and_macro():
    """The three finance sub-groups answer different questions and none
    substitutes for another, so a bare `category="finance"` must touch all
    three rather than spending its budget inside one."""
    picks = set(engines_for_category("finance"))
    for sub in ("finance.filings", "finance.market", "finance.macro"):
        assert picks & set(engines_for_category(sub)), sub

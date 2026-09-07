"""Cache internals: single long-lived connection, WAL + busy_timeout,
race-free initialization, and FTS5 MATCH hardening.

All tests use an isolated tmp sqlite file (never the user's real cache) by
constructing a fresh Cache() and pointing its _path at tmp_path.
"""
from __future__ import annotations

import asyncio

import aiosqlite
import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fresh_cache(tmp_path, monkeypatch):
    """A brand-new Cache pointed at an isolated tmp sqlite file.

    Also redirect settings.cache_dir so settings.cache_path() (used by the
    Cache constructor) never touches the user's real ~/.cache dir.
    """
    from search_mcp import cache as cache_mod
    from search_mcp.config import settings

    monkeypatch.setattr(settings, "cache_dir", tmp_path)
    c = cache_mod.Cache()
    c._path = str(tmp_path / "test_cache.sqlite")
    return c


# --- #15: single long-lived connection, WAL, busy_timeout, race-free init ---


async def test_conn_is_reused_single_connection(fresh_cache):
    """_conn() must hand back the *same* connection object every time."""
    a = await fresh_cache._conn()
    b = await fresh_cache._conn()
    assert a is b
    assert fresh_cache._conn_obj is a
    await fresh_cache.close()


async def test_journal_mode_is_wal(fresh_cache):
    conn = await fresh_cache._conn()
    cur = await conn.execute("PRAGMA journal_mode")
    row = await cur.fetchone()
    assert row is not None
    assert str(row[0]).lower() == "wal"
    await fresh_cache.close()


async def test_busy_timeout_is_set(fresh_cache):
    conn = await fresh_cache._conn()
    cur = await conn.execute("PRAGMA busy_timeout")
    row = await cur.fetchone()
    assert row is not None
    assert int(row[0]) == 5000
    await fresh_cache.close()


async def test_concurrent_first_access_initializes_once(fresh_cache):
    """Many coroutines hitting _conn() for the first time concurrently must
    all share ONE connection and the schema must be initialized exactly once
    (no race between the read and the write of the init flag)."""
    conns = await asyncio.gather(*[fresh_cache._conn() for _ in range(20)])
    first = conns[0]
    assert all(c is first for c in conns)

    # Schema present exactly once and queryable on the shared connection.
    cur = await first.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pages'",
    )
    assert await cur.fetchone() is not None
    await fresh_cache.close()


async def test_concurrent_put_page_all_succeed(fresh_cache):
    """Concurrent writes through the single connection must all land."""
    urls = [f"https://example.com/{i}" for i in range(25)]
    await asyncio.gather(
        *[fresh_cache.put_page(u, f"t{i}", f"body {i}") for i, u in enumerate(urls)]
    )
    for i, u in enumerate(urls):
        page = await fresh_cache.get_page(u)
        assert page is not None
        assert page["content"] == f"body {i}"
    await fresh_cache.close()


async def test_external_writer_visible_through_wal(fresh_cache):
    """A second connection (mirroring what test_resources.py does to rewind
    timestamps) must be able to write and have it seen by the long-lived
    connection — i.e. WAL doesn't strand the long-lived reader."""
    url = "https://example.com/wal"
    await fresh_cache.put_page(url, "t", "original")

    conn = await aiosqlite.connect(fresh_cache._path)
    try:
        await conn.execute("PRAGMA busy_timeout=5000")
        await conn.execute(
            "UPDATE pages SET content=? WHERE url=?", ("rewritten", url)
        )
        await conn.commit()
    finally:
        await conn.close()

    page = await fresh_cache.get_page(url)
    assert page is not None
    assert page["content"] == "rewritten"
    await fresh_cache.close()


async def test_close_is_idempotent(fresh_cache):
    await fresh_cache._conn()
    await fresh_cache.close()
    assert fresh_cache._conn_obj is None
    # second close must not raise
    await fresh_cache.close()
    # and the cache must still be usable afterwards (re-opens lazily)
    await fresh_cache.put_page("https://x", "t", "b")
    assert (await fresh_cache.get_page("https://x"))["content"] == "b"
    await fresh_cache.close()


# --- #13: FTS5 MATCH hardening — malformed input returns [], never raises ---


@pytest.mark.parametrize(
    "bad_query",
    [
        "a AND",          # trailing operator
        '"',              # unbalanced quote
        "title:val",      # column filter on a column that isn't queryable
        "AND OR NOT",     # bare operators
        "foo(",           # unbalanced paren
        "NEAR(",          # malformed NEAR
        "*",              # bare prefix token
    ],
)
async def test_search_pages_malformed_query_returns_empty(fresh_cache, bad_query):
    # Seed a row so the FTS index is non-empty (proves we don't just get []
    # because the table is empty).
    await fresh_cache.put_page("https://example.com/a", "Hello", "the quick brown fox")
    result = await fresh_cache.search_pages(bad_query)
    assert result == []
    await fresh_cache.close()


async def test_search_pages_valid_query_still_works(fresh_cache):
    """The try/except must not swallow legitimate matches."""
    await fresh_cache.put_page("https://example.com/a", "Hello", "the quick brown fox")
    await fresh_cache.put_page("https://example.com/b", "Other", "lazy dog sleeps")
    hits = await fresh_cache.search_pages("quick")
    assert len(hits) == 1
    assert hits[0]["url"] == "https://example.com/a"
    await fresh_cache.close()


# --- opportunistic maintenance: TTL purge + size cap -------------------------


async def test_maintain_purges_expired_rows(fresh_cache, monkeypatch):
    from search_mcp.config import settings

    conn = await fresh_cache._conn()
    now = int(__import__("time").time())
    stale = now - 10_000
    await conn.execute(
        "INSERT INTO search_cache (cache_key, query, engines, results, created) "
        "VALUES ('old', 'q', 'e', '[]', ?)",
        (stale,),
    )
    await conn.execute(
        "INSERT INTO pages (url, title, content, fetched) "
        "VALUES ('https://old.example/', 't', 'old body text', ?)",
        (stale,),
    )
    await conn.commit()
    await fresh_cache.put_page("https://new.example/", "t", "fresh body text")

    monkeypatch.setattr(settings, "cache_ttl_seconds", 3600)
    await fresh_cache._maintain(conn)

    cur = await conn.execute("SELECT cache_key FROM search_cache")
    assert await cur.fetchall() == []
    cur = await conn.execute("SELECT url FROM pages")
    assert [r[0] for r in await cur.fetchall()] == ["https://new.example/"]
    # FTS stays consistent: the purged page is gone from full-text search too.
    assert await fresh_cache.search_pages("old") == []
    assert len(await fresh_cache.search_pages("fresh")) == 1
    await fresh_cache.close()


async def test_maintain_enforces_size_cap_dropping_oldest(fresh_cache, monkeypatch):
    from search_mcp.config import settings

    monkeypatch.setattr(settings, "cache_ttl_seconds", 10**9)  # nothing expires
    conn = await fresh_cache._conn()
    # ~40 pages x ~50KB => ~2MB file; cap at 1MB.
    body = "x" * 50_000
    now = int(__import__("time").time())
    for i in range(40):
        await conn.execute(
            "INSERT INTO pages (url, title, content, fetched) VALUES (?, ?, ?, ?)",
            (f"https://example.com/{i}", f"t{i}", body, now - (40 - i)),
        )
    await conn.commit()
    assert fresh_cache._db_size() > 1024 * 1024

    monkeypatch.setattr(settings, "cache_max_mb", 1)
    await fresh_cache._maintain(conn)

    assert fresh_cache._db_size() <= 1024 * 1024
    cur = await conn.execute("SELECT COUNT(*), MAX(fetched), MIN(fetched) FROM pages")
    count, newest, oldest = await cur.fetchone()
    # Some rows survived, and the survivors are the NEWEST ones.
    assert 0 < count < 40
    assert newest == now - 1
    assert oldest > now - 40
    await fresh_cache.close()


async def test_maintain_disabled_when_cap_is_zero(fresh_cache, monkeypatch):
    from search_mcp.config import settings

    monkeypatch.setattr(settings, "cache_ttl_seconds", 10**9)
    monkeypatch.setattr(settings, "cache_max_mb", 0)
    conn = await fresh_cache._conn()
    body = "y" * 50_000
    for i in range(30):
        await fresh_cache.put_page(f"https://example.com/z{i}", "t", body)
    before = fresh_cache._db_size()
    await fresh_cache._maintain(conn)
    cur = await conn.execute("SELECT COUNT(*) FROM pages")
    assert (await cur.fetchone())[0] == 30
    assert before > 0
    await fresh_cache.close()


async def test_writes_trigger_maintenance_on_cadence(fresh_cache, monkeypatch):
    calls = []

    async def _fake_maintain(conn):
        calls.append(1)

    # _conn() runs one maintenance at init; silence it via the fake AFTER init.
    await fresh_cache._conn()
    monkeypatch.setattr(fresh_cache, "_maintain", _fake_maintain)
    monkeypatch.setattr(type(fresh_cache), "_MAINTAIN_EVERY", 5, raising=True)

    for i in range(12):
        await fresh_cache.put_page(f"https://example.com/c{i}", "t", "body")
    # Maintenance is now fire-and-forget; let the scheduled tasks run.
    await asyncio.sleep(0)
    assert len(calls) == 2  # at write #5 and #10
    await fresh_cache.close()


# --- FTS index stays in sync with the content table ------------------------


async def test_refetching_a_url_keeps_it_findable(fresh_cache):
    """The regression that made `cache_search` useless.

    `INSERT OR REPLACE` resolved the url conflict by DELETING the old row and
    inserting a new one with a NEW rowid — and SQLite fires DELETE triggers on
    that path only when `recursive_triggers` is on, which it is not by default.
    So every re-fetch orphaned the old rowid's postings. External-content FTS5
    reads column values back from `pages` by rowid, so the first orphan made
    EVERY query raise `fts5: missing row N`, which the malformed-query handler
    swallowed into "no cached pages match".
    """
    for i in range(4):
        await fresh_cache.put_page(
            "https://example.com/a", f"Title {i}", f"body revision {i} zebrafish"
        )
    hits = await fresh_cache.search_pages("zebrafish")
    assert [h["url"] for h in hits] == ["https://example.com/a"]
    await fresh_cache.close()


async def test_refetching_replaces_the_old_text_in_the_index(fresh_cache):
    """Stale content must not stay searchable — the update trigger has to
    delete the old FTS row, not just add a second one."""
    await fresh_cache.put_page("https://example.com/a", "T", "aardvark original")
    await fresh_cache.put_page("https://example.com/a", "T", "buffalo replacement")
    assert await fresh_cache.search_pages("aardvark") == []
    assert len(await fresh_cache.search_pages("buffalo")) == 1
    await fresh_cache.close()


async def test_refetching_keeps_the_rowid(fresh_cache):
    """Rowid stability is the whole mechanism: it is the key the FTS index and
    the content table agree on."""
    await fresh_cache.put_page("https://example.com/a", "T", "one")
    conn = await fresh_cache._conn()
    cur = await conn.execute("SELECT rowid FROM pages WHERE url = 'https://example.com/a'")
    before = (await cur.fetchone())[0]
    await fresh_cache.put_page("https://example.com/a", "T", "two")
    cur = await conn.execute("SELECT rowid FROM pages WHERE url = 'https://example.com/a'")
    assert (await cur.fetchone())[0] == before
    await fresh_cache.close()


async def test_fts_integrity_survives_many_rewrites(fresh_cache):
    """FTS5's own checker is the authority on whether the index is sane."""
    for i in range(6):
        await fresh_cache.put_page("https://example.com/a", "T", f"content {i}")
        await fresh_cache.put_page("https://example.com/b", "T", f"other {i}")
    conn = await fresh_cache._conn()
    await conn.execute("INSERT INTO pages_fts(pages_fts) VALUES('integrity-check')")
    await fresh_cache.close()


async def test_a_desynced_index_is_rebuilt_instead_of_reported_as_empty(fresh_cache):
    """Caches written by earlier versions are already poisoned, so the read
    path has to repair rather than silently return nothing."""
    await fresh_cache.put_page("https://example.com/a", "T", "narwhal")
    conn = await fresh_cache._conn()
    # Forge exactly the corruption REPLACE used to leave behind: a posting for
    # a rowid the content table does not have.
    await conn.execute(
        "INSERT INTO pages_fts(rowid, url, title, content) "
        "VALUES (9999, 'https://example.com/ghost', 'ghost', 'narwhal')"
    )
    await conn.commit()
    with pytest.raises(Exception):
        cur = await conn.execute("SELECT url FROM pages_fts WHERE pages_fts MATCH 'narwhal'")
        await cur.fetchall()

    hits = await fresh_cache.search_pages("narwhal")
    assert [h["url"] for h in hits] == ["https://example.com/a"]
    await fresh_cache.close()


async def test_a_desync_is_classified_the_same_under_either_sqlite_wording():
    """SQLite 3.42+ names the condition; older builds only say the file is
    malformed. The repair must trigger on both, so the classifier keys on the
    one case that must NOT repair rather than on corruption wording."""
    import sqlite3

    from search_mcp.cache import _is_bad_match_query

    for text in (
        "fts5: missing row 9999 from content table 'main'.'pages'",
        "database disk image is malformed",
        "database or disk is full",
    ):
        assert not _is_bad_match_query(sqlite3.OperationalError(text)), text


async def test_a_bad_match_query_is_never_treated_as_corruption():
    """Rebuilding on the caller's typo would turn a one-character mistake into
    an O(corpus) reindex on every such query."""
    import sqlite3

    from search_mcp.cache import _is_bad_match_query

    for text in (
        'fts5: syntax error near ""',
        "no such column: nosuchcol",
        "unknown special query: foo",
        "unterminated string",
    ):
        assert _is_bad_match_query(sqlite3.OperationalError(text)), text


async def test_a_malformed_query_is_still_just_no_matches(fresh_cache):
    """The rebuild path must not swallow the syntax-error path it sits next
    to — a bad query is a user error, not a corrupt index."""
    await fresh_cache.put_page("https://example.com/a", "T", "narwhal")
    assert await fresh_cache.search_pages('"unclosed') == []
    assert await fresh_cache.search_pages("nosuchcol:x") == []
    await fresh_cache.close()


async def test_existing_caches_are_rebuilt_once_on_open(tmp_path, monkeypatch):
    """A file written before the fix carries orphaned postings, and only a
    rebuild clears them. `user_version` gates it to once per file — the
    rebuild is O(corpus) and must not run on every start.
    """
    import sqlite3

    from search_mcp import cache as cache_mod
    from search_mcp.config import settings

    monkeypatch.setattr(settings, "cache_dir", tmp_path)
    path = tmp_path / "legacy.sqlite"

    first = cache_mod.Cache()
    first._path = str(path)
    await first.put_page("https://example.com/a", "T", "pangolin")
    conn = await first._conn()
    # Undo the version stamp and forge the legacy damage.
    await conn.execute("PRAGMA user_version=0")
    await conn.execute(
        "INSERT INTO pages_fts(rowid, url, title, content) "
        "VALUES (4242, 'https://example.com/ghost', 'g', 'pangolin')"
    )
    await conn.commit()
    await first.close()

    reopened = cache_mod.Cache()
    reopened._path = str(path)
    hits = await reopened.search_pages("pangolin")
    assert [h["url"] for h in hits] == ["https://example.com/a"]
    await reopened.close()

    stamped = sqlite3.connect(str(path))
    assert stamped.execute("PRAGMA user_version").fetchone()[0] == cache_mod._USER_VERSION
    stamped.close()

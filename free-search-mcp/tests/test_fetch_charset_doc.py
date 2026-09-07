"""Offline tests for the fetcher charset decode + binary-document routing.

The helpers under test are pure/sync (no event loop, no network): charset
detection from header/meta, and the URL/content-type document classifiers
that route PDFs/DOCX to the document parser instead of decoding bytes as text.
"""
from __future__ import annotations

from search_mcp.fetcher import (
    _ctype_is_markup,
    _decode_body,
    _is_document_ctype,
    _is_document_url,
)

# --- charset decode --------------------------------------------------------


def test_decode_honors_header_charset_gbk():
    # GBK-encoded Chinese must not be decoded as UTF-8 (would be mojibake).
    text = "中文内容"
    body = text.encode("gbk")
    out = _decode_body(body, "text/html; charset=gbk")
    assert out == text


def test_decode_sniffs_meta_charset_when_header_lacks_one():
    text = "日本語のテスト"
    body = (
        b"<html><head><meta charset='shift_jis'></head><body>"
        + text.encode("shift_jis")
        + b"</body></html>"
    )
    out = _decode_body(body, "text/html")  # header has no charset
    assert text in out


def test_decode_defaults_to_utf8_and_never_raises_on_bad_codec():
    text = "ünïcode ✓ 中文"
    body = text.encode("utf-8")
    # No charset anywhere -> UTF-8.
    assert _decode_body(body, "text/html") == text
    # Bogus codec label -> falls back to UTF-8 instead of raising LookupError.
    assert _decode_body(body, "text/html; charset=not-a-real-codec") == text


# --- document routing classifiers -----------------------------------------


def test_is_document_url_matches_pdf_and_docx_suffixes():
    assert _is_document_url("https://arxiv.org/pdf/1706.03762.pdf")
    assert _is_document_url("https://example.com/report.docx")
    assert _is_document_url(["https://example.com/paper.PDF", "download=1"][0])
    assert not _is_document_url("https://example.com/article.html")
    assert not _is_document_url("https://example.com/")


def test_is_document_ctype_matches_binary_doc_types():
    assert _is_document_ctype("application/pdf")
    assert _is_document_ctype(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert not _is_document_ctype("text/html; charset=utf-8")
    assert not _is_document_ctype("application/json")


def test_ctype_is_markup_treats_empty_as_recoverable():
    assert _ctype_is_markup("")  # http fetch failed -> allow browser fallback
    assert _ctype_is_markup("text/html")
    assert _ctype_is_markup("application/xml")
    assert not _ctype_is_markup("application/json")
    assert not _ctype_is_markup("text/plain")


# --- read_doc honours the same charset the fetcher does --------------------
#
# `read_doc` used to hardcode `blob.decode("utf-8", errors="replace")` in every
# text parser while `_read_remote` already had the Content-Type in hand and fed
# it only to the format detector. So `fetch` rendered a GBK page correctly and
# `read_doc` returned a screen of U+FFFD for the same URL — exactly the CJK
# case `_decode_body`'s own comment says it exists for.


def test_read_doc_html_parser_honours_header_charset():
    from search_mcp.documents import _parse_html

    body = "<html><body><p>中文正文</p></body></html>".encode("gbk")
    assert "中文正文" in _parse_html(body, "text/html; charset=gbk")


def test_read_doc_text_parser_honours_header_charset():
    from search_mcp.documents import _parse_text

    assert _parse_text("中文标题".encode("gbk"), "text/plain; charset=GBK") == "中文标题"


def test_read_doc_csv_parser_honours_header_charset():
    from search_mcp.documents import _parse_csv

    table, _ = _parse_csv("列一,列二\n中文,值".encode("gbk"), "text/csv; charset=gbk")
    assert "列一" in table and "中文" in table


def test_read_doc_code_parser_honours_header_charset():
    from search_mcp.documents import _parse_code

    out = _parse_code("# 中文注释".encode("gbk"), "a.py", "text/plain; charset=gbk")
    assert "中文注释" in out


def test_read_doc_html_parser_sniffs_meta_charset_without_a_header():
    """A local file has no Content-Type at all, so the in-document declaration
    is the only signal there is."""
    from search_mcp.documents import _parse_html

    body = "<html><head><meta charset='gbk'></head><body><p>中文</p></body></html>".encode(
        "gbk"
    )
    assert "中文" in _parse_html(body, "")

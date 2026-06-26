"""Hidden Unicode control character tests."""

from tools.static_policy_audit import scan_hidden_unicode


def test_rejects_bidi_override() -> None:
    assert scan_hidden_unicode("a\u202eb")


def test_rejects_zero_width_space() -> None:
    assert scan_hidden_unicode("a\u200bc")


def test_rejects_bom() -> None:
    assert scan_hidden_unicode("\ufeffhello")


def test_allows_plain_ascii() -> None:
    assert scan_hidden_unicode("hello\nworld\t!") == []


def test_allows_newlines_tabs() -> None:
    assert scan_hidden_unicode("line1\nline2\r\nline3\ttab") == []

"""Tests for output parsers."""

from __future__ import annotations

from panelize_code.config import PanelConfig
from panelize_code.parsers import parse


def _panel(**kw) -> PanelConfig:  # type: ignore[no-untyped-def]
    base = {"id": "x", "title": "x", "command": "x"}
    base.update(kw)
    return PanelConfig(**base)


def test_parse_raw() -> None:
    rows = parse("hello world\n", _panel(parser="raw"))
    assert rows == [["hello world"]]


def test_parse_raw_empty() -> None:
    assert parse("", _panel(parser="raw")) == []
    assert parse("\n", _panel(parser="raw")) == []


def test_parse_lines() -> None:
    rows = parse("a\nb\n\nc\n", _panel(parser="lines"))
    assert rows == [["a"], ["b"], ["c"]]


def test_parse_tsv() -> None:
    rows = parse("a\tb\tc\nd\te\tf\n", _panel(parser="tsv"))
    assert rows == [["a", "b", "c"], ["d", "e", "f"]]


def test_parse_csv() -> None:
    rows = parse('a,b,"c with comma"\n1,2,3\n', _panel(parser="csv"))
    assert rows == [["a", "b", "c with comma"], ["1", "2", "3"]]


def test_parse_json_list_of_dicts_columns() -> None:
    out = '[{"name":"a","val":1},{"name":"b","val":2}]'
    rows = parse(out, _panel(parser="json", columns=["name", "val"]))
    assert rows == [["a", "1"], ["b", "2"]]


def test_parse_json_dict_wrapped() -> None:
    out = '{"name":"a","val":1}'
    rows = parse(out, _panel(parser="json", columns=["name", "val"]))
    assert rows == [["a", "1"]]


def test_parse_json_template() -> None:
    out = '[{"name":"a","val":1}]'
    rows = parse(out, _panel(parser="json", template="{name}={val}"))
    assert rows == [["a=1"]]


def test_parse_json_deep_get() -> None:
    out = '[{"meta":{"name":"a"},"status":{"phase":"Running"}}]'
    rows = parse(
        out,
        _panel(parser="json", template="{meta.name}\t{status.phase}", columns=["X", "Y"]),
    )
    assert rows == [["a\tRunning"]]


def test_parse_json_invalid() -> None:
    rows = parse("not json", _panel(parser="json"))
    assert rows and "json error" in rows[0][0]


def test_parse_regex_named_groups() -> None:
    out = "pid=42 name=foo\npid=43 name=bar\n"
    rows = parse(
        out,
        _panel(
            parser="regex",
            pattern=r"pid=(?P<pid>\d+) name=(?P<name>\w+)",
            columns=["pid", "name"],
        ),
    )
    assert rows == [["42", "foo"], ["43", "bar"]]


def test_parse_regex_positional_groups() -> None:
    rows = parse("a:1\nb:2\n", _panel(parser="regex", pattern=r"(\w+):(\d+)"))
    assert rows == [["a", "1"], ["b", "2"]]


def test_parse_regex_skips_nonmatch() -> None:
    rows = parse("ok 1\nbad\nok 2\n", _panel(parser="regex", pattern=r"^ok (\d+)$"))
    assert rows == [["1"], ["2"]]


def test_parse_regex_invalid_pattern_returns_error() -> None:
    # Bypass pydantic validator by manually constructing
    panel = PanelConfig(id="x", title="x", command="x", parser="lines")
    panel.parser = "regex"  # type: ignore[assignment]
    panel.pattern = "[invalid"
    rows = parse("x", panel)
    assert rows and "regex error" in rows[0][0]


def test_unknown_parser() -> None:
    panel = PanelConfig(id="x", title="x", command="x")
    panel.parser = "bogus"  # type: ignore[assignment]
    rows = parse("x", panel)
    assert "unknown parser" in rows[0][0]

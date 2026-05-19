"""Output parsers: raw / lines / tsv / csv / json / regex.

Each parser takes raw stdout (str) + the PanelConfig and returns a list of rows,
where each row is a list of strings (1 column = 1 cell).
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import PanelConfig


Row = list[str]


def parse_raw(stdout: str, panel: PanelConfig) -> list[Row]:
    """Single cell containing the full output."""
    text = stdout.rstrip("\n")
    return [[text]] if text else []


def parse_lines(stdout: str, panel: PanelConfig) -> list[Row]:
    """1 non-empty line = 1 row, single column."""
    return [[line] for line in stdout.splitlines() if line.strip()]


def parse_tsv(stdout: str, panel: PanelConfig) -> list[Row]:
    """Tab-separated values. Each line split on tabs."""
    rows: list[Row] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        rows.append(line.split("\t"))
    return rows


def parse_csv(stdout: str, panel: PanelConfig) -> list[Row]:
    """Comma-separated values."""
    reader = csv.reader(io.StringIO(stdout))
    return [list(row) for row in reader if row]


def parse_json(stdout: str, panel: PanelConfig) -> list[Row]:
    """JSON output. Accepts list[dict], list[list], dict, or list[primitive].

    If `columns` is set, extract those keys from each dict.
    If `template` is set ("{name}\\t{status}"), render each item.
    Otherwise dump compact JSON repr per item.
    """
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [[f"[json error] {exc.msg}"]]

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return [[str(data)]]

    rows: list[Row] = []
    for item in data:
        if isinstance(item, dict):
            if panel.template:
                rows.append([_render_template(panel.template, item)])
            elif panel.columns:
                rows.append([_deep_get(item, col) for col in panel.columns])
            else:
                rows.append([json.dumps(item, separators=(",", ":"))])
        elif isinstance(item, list):
            rows.append([str(x) for x in item])
        else:
            rows.append([str(item)])
    return rows


def parse_regex(stdout: str, panel: PanelConfig) -> list[Row]:
    """Apply regex to each line. Capture groups become columns.

    Lines that don't match are skipped.
    Named groups override positional groups for column order if `columns` is set.
    """
    try:
        pattern = re.compile(panel.pattern)
    except re.error as exc:
        return [[f"[regex error] {exc}"]]

    rows: list[Row] = []
    for line in stdout.splitlines():
        m = pattern.search(line)
        if not m:
            continue
        if panel.columns:
            named = m.groupdict()
            rows.append([str(named.get(c, "")) for c in panel.columns])
        else:
            groups = m.groups()
            rows.append(list(groups) if groups else [m.group(0)])
    return rows


def _deep_get(obj: dict, dotted_key: str) -> str:
    """Resolve 'a.b.c' nested dict access. Returns '' if missing."""
    cur: object = obj
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return ""
    return str(cur)


def _render_template(template: str, item: dict) -> str:
    """Render '{key}' placeholders. Supports dotted keys via _deep_get."""
    out = template
    for match in re.finditer(r"\{([^}]+)\}", template):
        key = match.group(1)
        value = _deep_get(item, key) if "." in key else str(item.get(key, ""))
        out = out.replace(match.group(0), value)
    return out


PARSERS = {
    "raw": parse_raw,
    "lines": parse_lines,
    "tsv": parse_tsv,
    "csv": parse_csv,
    "json": parse_json,
    "regex": parse_regex,
}


def parse(stdout: str, panel: PanelConfig) -> list[Row]:
    """Dispatch to the right parser based on panel.parser."""
    fn = PARSERS.get(panel.parser)
    if fn is None:
        return [[f"[unknown parser: {panel.parser}]"]]
    return fn(stdout, panel)

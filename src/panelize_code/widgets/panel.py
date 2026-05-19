"""Generic panel widget. Renders rows from a PanelSnapshot in a DataTable."""

from __future__ import annotations

import contextlib
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from ..config import PanelConfig
from ..provider import PanelSnapshot
from ..theme import COLORS


class PanelWidget(Vertical):
    """One TUI panel = title bar + DataTable + status footer.

    Stateless w.r.t. data: parent App calls update_snapshot() with fresh data.
    """

    DEFAULT_CSS = """
    PanelWidget {
        border: round $primary;
        padding: 0 1;
    }
    PanelWidget > .panel-title {
        height: 1;
        color: $accent;
        text-style: bold;
    }
    PanelWidget > .panel-status {
        height: 1;
        color: $primary-muted;
        dock: bottom;
    }
    PanelWidget > DataTable {
        height: 1fr;
    }
    """

    def __init__(self, panel_config: PanelConfig, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.panel_config = panel_config
        self.border_title = f"{panel_config.icon} {panel_config.title}".strip()
        self._last_snapshot: PanelSnapshot | None = None

    def compose(self) -> ComposeResult:
        yield Static("", classes="panel-title", id=f"title-{self.panel_config.id}")
        table: DataTable[str] = DataTable(id=f"table-{self.panel_config.id}")
        table.cursor_type = "row"
        table.zebra_stripes = True
        yield table
        yield Static("loading...", classes="panel-status", id=f"status-{self.panel_config.id}")

    def update_snapshot(self, snapshot: PanelSnapshot) -> None:
        """Refresh the table with new rows. Idempotent."""
        self._last_snapshot = snapshot
        table = self.query_one(f"#table-{self.panel_config.id}", DataTable)
        table.clear(columns=True)

        if not snapshot.ok:
            error_color = COLORS["error"]
            table.add_column("status")
            table.add_row(f"[{error_color}]✗ {snapshot.error}[/]")
            self._set_status(f"error · {snapshot.duration_ms}ms")
            return

        if not snapshot.rows:
            muted = COLORS["muted"]
            table.add_column("status")
            table.add_row(f"[{muted}]no output[/]")
            self._set_status(f"empty · {snapshot.duration_ms}ms")
            return

        # Build columns: explicit columns config wins, else use first row length.
        columns = self.panel_config.columns
        if not columns:
            n_cols = max(len(r) for r in snapshot.rows)
            columns = [f"col{i + 1}" for i in range(n_cols)] if n_cols > 1 else [""]

        for col in columns:
            table.add_column(col or " ")
        for row in snapshot.rows:
            padded = row + [""] * (len(columns) - len(row))
            table.add_row(*padded[: len(columns)])

        now = datetime.now().strftime("%H:%M:%S")
        self._set_status(f"{len(snapshot.rows)} row(s) · {snapshot.duration_ms}ms · {now}")

    def _set_status(self, text: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one(f"#status-{self.panel_config.id}", Static).update(text)

"""Generic Textual app. Iterates over the panels declared in the config."""

from __future__ import annotations

from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.widgets import Footer, Header

from .config import DashboardConfig
from .layout import grid_dimensions
from .provider import run_action, run_panel
from .theme import BUILTIN_THEMES, DEFAULT_THEME
from .widgets import PanelWidget


class PanelizeApp(App[int]):
    """Generic config-driven Textual dashboard."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("a", "show_actions", "Actions", show=True),
        Binding("t", "next_theme", "Theme", show=True),
        Binding("p", "toggle_pause", "Pause", show=True),
        Binding("q,ctrl+c", "quit_app", "Quit", show=True),
        Binding("question_mark,f1", "help", "Help", show=True, key_display="?"),
    ]

    def __init__(self, config: DashboardConfig) -> None:
        super().__init__()
        self.config = config
        self.paused = False
        self._theme_index = 0
        self._panel_widgets: dict[str, PanelWidget] = {}
        self.last_update: datetime | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        cols, _ = grid_dimensions(len(self.config.panels))
        grid = Grid(id="panel-grid")
        grid.styles.grid_size_columns = cols
        with grid:
            for panel_cfg in self.config.panels:
                widget = PanelWidget(panel_cfg, id=f"panel-{panel_cfg.id}")
                self._panel_widgets[panel_cfg.id] = widget
                yield widget
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.register_theme(DEFAULT_THEME)
            self.theme = self.config.app.theme or "panelize"
        except Exception:
            pass

        self.title = self.config.app.title
        self.sub_title = f"refresh {self.config.app.refresh}s"

        self.refresh_all()
        if self.config.app.refresh > 0:
            self.set_interval(self.config.app.refresh, self._on_refresh_tick)

        # Per-panel custom refresh intervals
        for panel in self.config.panels:
            if panel.refresh and panel.refresh != self.config.app.refresh:
                self.set_interval(
                    panel.refresh, lambda p=panel: self.refresh_panel(p.id)
                )

    # --- Refresh ---

    def _on_refresh_tick(self) -> None:
        if not self.paused:
            self.refresh_all()

    def refresh_all(self) -> None:
        """Spawn a worker per panel (parallel)."""
        for panel in self.config.panels:
            self.refresh_panel(panel.id)
        self.last_update = datetime.now()
        self.sub_title = (
            f"refresh {self.config.app.refresh}s | "
            f"{self.last_update:%H:%M:%S}{' [PAUSED]' if self.paused else ''}"
        )

    def refresh_panel(self, panel_id: str) -> None:
        panel = next((p for p in self.config.panels if p.id == panel_id), None)
        if panel is None:
            return

        def task() -> None:
            snap = run_panel(panel)
            self.call_from_thread(self._apply_snapshot, panel_id, snap)

        self.run_worker(task, thread=True, exclusive=False)

    def _apply_snapshot(self, panel_id: str, snapshot) -> None:  # type: ignore[no-untyped-def]
        widget = self._panel_widgets.get(panel_id)
        if widget is not None:
            widget.update_snapshot(snapshot)

    # --- Actions ---

    def action_refresh(self) -> None:
        self.refresh_all()
        self.notify("Refresh triggered.", timeout=1)

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        msg = "Paused (auto-refresh off)" if self.paused else "Resumed"
        self.notify(msg, timeout=2)

    def action_next_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(BUILTIN_THEMES)
        try:
            self.theme = BUILTIN_THEMES[self._theme_index]
            self.notify(f"Theme: {self.theme}", timeout=1)
        except Exception as exc:
            self.notify(f"Theme failed: {exc}", severity="warning")

    def action_quit_app(self) -> None:
        self.exit(0)

    def action_help(self) -> None:
        lines = [
            f"[bold]{self.config.app.title}[/bold]",
            "",
            "Keys:",
            "  r       Refresh all panels",
            "  a       Show actions menu",
            "  t       Cycle theme",
            "  p       Pause/resume auto-refresh",
            "  q       Quit",
            "  ?       This help",
            "",
            f"Panels: {len(self.config.panels)} · Actions: {len(self.config.actions)}",
        ]
        self.notify("\n".join(lines), timeout=10)

    def action_show_actions(self) -> None:
        if not self.config.actions:
            self.notify("No actions defined in config.", timeout=2)
            return
        # Simple text listing; for richer UI a modal would be added in a later version.
        names = [f"  [{a.shortcut or '-'}] {a.name}" for a in self.config.actions]
        self.notify(
            "Actions:\n" + "\n".join(names) + "\n(press shortcut key)", timeout=5
        )

    def on_key(self, event) -> None:  # type: ignore[no-untyped-def]
        # Action shortcuts (single-key, lowercase)
        if not self.config.actions:
            return
        key = event.key
        for action in self.config.actions:
            if action.shortcut and action.shortcut == key:
                self._run_action(action)
                event.stop()
                return

    def _run_action(self, action) -> None:  # type: ignore[no-untyped-def]
        self.notify(f"Running: {action.name}...", timeout=1)

        def task() -> None:
            result = run_action(action)
            self.call_from_thread(self._action_done, result)

        self.run_worker(task, thread=True)

    def _action_done(self, result) -> None:  # type: ignore[no-untyped-def]
        if result.ok:
            self.notify(f"{result.name}: OK", timeout=3)
            self.refresh_all()
        else:
            err = result.stderr[:120] if result.stderr else f"exit {result.exit_code}"
            self.notify(f"{result.name}: FAIL — {err}", severity="error", timeout=5)

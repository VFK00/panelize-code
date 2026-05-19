"""Built-in Textual theme + color palette."""

from __future__ import annotations

from textual.theme import Theme

DEFAULT_THEME = Theme(
    name="panelize",
    primary="#7AA2F7",
    secondary="#BB9AF7",
    accent="#F7768E",
    foreground="#C0CAF5",
    background="#1A1B26",
    success="#9ECE6A",
    warning="#E0AF68",
    error="#F7768E",
    surface="#24283B",
    panel="#1F2335",
    dark=True,
)

BUILTIN_THEMES = [
    "panelize",
    "tokyo-night",
    "monokai",
    "gruvbox",
    "nord",
    "flexoki",
]

COLORS = {
    "ok": "#9ECE6A",
    "warn": "#E0AF68",
    "error": "#F7768E",
    "info": "#7AA2F7",
    "muted": "#565F89",
}

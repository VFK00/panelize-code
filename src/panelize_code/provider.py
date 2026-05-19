"""Subprocess provider: run a panel's command, capture stdout, parse it."""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass, field

from .config import ActionConfig, PanelConfig
from .parsers import Row, parse


@dataclass
class PanelSnapshot:
    """Result of running a panel's command."""

    panel_id: str
    rows: list[Row] = field(default_factory=list)
    ok: bool = True
    error: str = ""
    duration_ms: int = 0
    exit_code: int = 0


@dataclass
class ActionResult:
    """Result of running an action."""

    name: str
    ok: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


def _to_args(command: str | list[str], shell: bool) -> tuple[list[str] | str, bool]:
    """Return (args, shell_flag) tuple for subprocess.run."""
    if isinstance(command, list):
        return command, False
    if shell:
        return command, True
    return shlex.split(command), False


def run_panel(panel: PanelConfig) -> PanelSnapshot:
    """Execute panel.command, capture stdout, parse, return snapshot."""
    snap = PanelSnapshot(panel_id=panel.id)
    args, use_shell = _to_args(panel.command, panel.shell)

    started = time.monotonic()
    try:
        result = subprocess.run(
            args,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=panel.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        snap.ok = False
        snap.error = f"timeout after {panel.timeout}s"
        snap.duration_ms = int((time.monotonic() - started) * 1000)
        return snap
    except FileNotFoundError as exc:
        snap.ok = False
        snap.error = f"command not found: {exc.filename or 'unknown'}"
        snap.duration_ms = int((time.monotonic() - started) * 1000)
        return snap
    except Exception as exc:  # noqa: BLE001
        snap.ok = False
        snap.error = f"exec failed: {exc}"
        snap.duration_ms = int((time.monotonic() - started) * 1000)
        return snap

    snap.duration_ms = int((time.monotonic() - started) * 1000)
    snap.exit_code = result.returncode

    if result.returncode != 0:
        snap.ok = False
        snap.error = (result.stderr or result.stdout or "exit != 0").strip().splitlines()[0][:200]
        return snap

    snap.rows = parse(result.stdout, panel)
    return snap


def run_action(action: ActionConfig) -> ActionResult:
    """Execute action.command, return stdout/stderr/exit."""
    args, use_shell = _to_args(action.command, action.shell)
    try:
        result = subprocess.run(
            args,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=action.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ActionResult(name=action.name, ok=False, stderr=f"timeout after {action.timeout}s")
    except FileNotFoundError as exc:
        return ActionResult(
            name=action.name, ok=False, stderr=f"command not found: {exc.filename or 'unknown'}"
        )
    except Exception as exc:  # noqa: BLE001
        return ActionResult(name=action.name, ok=False, stderr=f"exec failed: {exc}")

    return ActionResult(
        name=action.name,
        ok=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )

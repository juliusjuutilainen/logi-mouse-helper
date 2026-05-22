from __future__ import annotations

import json
import shutil
import subprocess
import sys
from html import escape
from pathlib import Path


def _command(name: str) -> str:
    local = Path.home() / ".local" / "bin" / name
    if local.exists():
        return str(local)
    return shutil.which(name) or name


def _emit_tag(name: str, value: object) -> None:
    print(f"<{name}>{escape(str(value), quote=False)}</{name}>")


def run_helperctl(args: list[str]) -> dict:
    helperctl = _command("mouse-helperctl")
    # Try with daemon first
    cmd = [helperctl, "--daemon", "--json"] + args
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        # Fall back to direct mode
        cmd = [helperctl, "--json"] + args
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

    if completed.returncode != 0:
        return {
            "online": False,
            "errors": [
                completed.stderr.strip() or completed.stdout.strip()
            ],
        }

    try:
        return json.loads(completed.stdout)
    except Exception as e:
        return {
            "online": False,
            "errors": [f"JSON parse error: {e}", completed.stdout],
        }


def main() -> int:
    state = run_helperctl(["status"])

    if not state.get("online"):
        # Offline state
        icon = "input-mouse-symbolic"
        txt = "Mouse"
        errors = state.get("errors") or []
        err_msg = f"\nError: {errors[0]}" if errors else ""
        tool = f"No Superlight detected.{err_msg}"
        click = _command("mouse-helper-menu")

        _emit_tag("icon", icon)
        _emit_tag("txt", txt)
        _emit_tag("tool", tool)
        _emit_tag("click", click)
        _emit_tag("iconclick", click)
        return 0

    # Online state
    name = state.get("name", "Logitech Superlight")
    dpi = state.get("dpi") or "?"
    battery_percent = state.get("battery_percent")
    battery_status = state.get("battery_status") or ""
    report_rate = state.get("report_rate") or "?"

    battery = f"{battery_percent}%" if battery_percent is not None else "?"
    if battery_status:
        battery += f" ({battery_status})"

    tool = f"{name}\nBattery: {battery}\nDPI: {dpi}\nRate: {report_rate}"
    click = _command("mouse-helper-menu")
    icon = "input-mouse-symbolic"

    # Show warning if battery is low (<= 20%) and not charging
    is_charging = "charging" in battery_status.lower() or "charging" in (
        state.get("battery_status") or ""
    ).lower()
    if (
        battery_percent is not None
        and battery_percent <= 20
        and not is_charging
    ):
        txt = f"⚠️ {dpi}"
    else:
        txt = f"{dpi}"

    _emit_tag("icon", icon)
    _emit_tag("txt", txt)
    _emit_tag("tool", tool)
    _emit_tag("click", click)
    _emit_tag("iconclick", click)
    return 0


if __name__ == "__main__":
    sys.exit(main())

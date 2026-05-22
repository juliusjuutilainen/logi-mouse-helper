from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


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


def trigger_genmon_refresh():
    try:
        panel = shutil.which("xfce4-panel") or "xfce4-panel"
        res = subprocess.run(
            ["xfconf-query", "-c", "xfce4-panel", "-p", "/plugins", "-lv"],
            capture_output=True,
            text=True,
            check=True,
        )
        pattern = r"/plugins/plugin-(\d+)/command\s+(.*mouse-helper-genmon.*)"
        for line in res.stdout.splitlines():
            match = re.search(pattern, line)
            if match:
                plugin_id = match.group(1)
                subprocess.run(
                    [
                        panel,
                        f"--plugin-event=genmon-{plugin_id}:refresh:bool:true",
                    ],
                    check=False,
                )
    except Exception:
        pass


def _command(name: str) -> str:
    local = Path.home() / ".local" / "bin" / name
    if local.exists():
        return str(local)
    return shutil.which(name) or name


def main() -> int:
    try:
        import gi

        gi.require_version("Gdk", "3.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, Gtk
    except Exception as exc:
        print(f"mouse-helper-menu: GTK unavailable: {exc}", file=sys.stderr)
        return 1

    # Fetch status
    state = run_helperctl(["status"])
    online = state.get("online", False)

    # Initialize GTK
    Gtk.init(None)

    menu = Gtk.Menu()

    def on_dpi_selected(_item, dpi: int):
        run_helperctl(["set", "dpi", str(dpi)])
        trigger_genmon_refresh()
        Gtk.main_quit()

    def on_doctor_clicked(_item):
        result = subprocess.run(
            [_command("mouse-helperctl"), "--json", "doctor"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Copy to clipboard
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(result.stdout.strip(), -1)
            clipboard.store()
        Gtk.main_quit()

    if not online:
        header_item = Gtk.MenuItem(label="No Superlight detected")
        header_item.set_sensitive(False)
        menu.append(header_item)

        errors = state.get("errors") or []
        if errors:
            err_item = Gtk.MenuItem(label=f"Error: {errors[0]}")
            err_item.set_sensitive(False)
            menu.append(err_item)
    else:
        name = state.get("name", "Logitech Superlight")
        battery_percent = state.get("battery_percent")
        battery_status = state.get("battery_status") or ""
        current_dpi = state.get("dpi")
        report_rate = state.get("report_rate") or "?"

        battery = f"{battery_percent}%" if battery_percent is not None else "?"
        if battery_status:
            battery += f" ({battery_status})"

        # Header with status info
        status_label = f"{name} | {battery} | {report_rate}"
        header_item = Gtk.MenuItem(label=status_label)
        header_item.set_sensitive(False)
        menu.append(header_item)

        menu.append(Gtk.SeparatorMenuItem())

        # DPI Choices
        dpi_presets = [600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400]
        dpi_choices = state.get("dpi_choices") or dpi_presets

        for dpi in dpi_choices:
            if dpi == current_dpi:
                label = f"● {dpi} DPI"
            else:
                label = f"  {dpi} DPI"
            item = Gtk.MenuItem(label=label)
            item.connect("activate", on_dpi_selected, dpi)
            menu.append(item)

    menu.append(Gtk.SeparatorMenuItem())

    doctor_item = Gtk.MenuItem(label="Copy Doctor JSON")
    doctor_item.connect("activate", on_doctor_clicked)
    menu.append(doctor_item)

    # Quit / Close menu item
    quit_item = Gtk.MenuItem(label="Cancel")
    quit_item.connect("activate", lambda _item: Gtk.main_quit())
    menu.append(quit_item)

    menu.show_all()

    # Quit main loop on menu deactivate
    menu.connect("deactivate", lambda _m: Gtk.main_quit())

    try:
        display = Gdk.Display.get_default()
        seat = display.get_default_seat() if display is not None else None
        pointer = seat.get_pointer() if seat is not None else None
        if pointer is None:
            raise RuntimeError("no pointer device")
        screen, x, y = pointer.get_position()
        rect = Gdk.Rectangle()
        rect.x = x
        rect.y = y
        rect.width = 1
        rect.height = 1
        menu.popup_at_rect(
            screen.get_root_window(),
            rect,
            Gdk.Gravity.NORTH_WEST,
            Gdk.Gravity.NORTH_WEST,
            None,
        )
    except Exception:
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import subprocess


def _run(*args: str) -> str:
    completed = subprocess.run(
        ["mouse-helperctl", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout.strip()


def main() -> int:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("XApp", "1.0")
        from gi.repository import Gtk, XApp
    except Exception as exc:
        print(f"mouse-helper-tray: GTK/XApp unavailable: {exc}")
        return 1

    icon = XApp.StatusIcon.new_with_name("mouse-helper")
    icon.set_icon_name("input-mouse")
    icon.set_tooltip_text("Mouse Helper")

    menu = Gtk.Menu()
    status_item = Gtk.MenuItem(label="Status")
    status_item.set_sensitive(False)
    menu.append(status_item)

    def refresh(_item=None):
        status_item.set_label(_run("status") or "No status")

    refresh_item = Gtk.MenuItem(label="Refresh")
    refresh_item.connect("activate", refresh)
    menu.append(refresh_item)

    for dpi in (400, 800, 1600, 3200):
        item = Gtk.MenuItem(label=f"{dpi} DPI")
        item.connect("activate", lambda _item, value=dpi: _run("set", "dpi", str(value)))
        menu.append(item)

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda _item: Gtk.main_quit())
    menu.append(quit_item)
    menu.show_all()
    icon.set_primary_menu(menu)

    refresh()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

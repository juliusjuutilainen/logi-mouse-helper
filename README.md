# mouse-helper

`mouse-helper` is my personal Linux mouse control tool.

The goal is a small, dependable, universal Linux helper for the Logitech gaming
mice I actually use, with simple desktop integration instead of a large device
manager. It currently focuses on the Logitech PRO X Superlight family, but the
shape of the project is intentionally generic: CLI first, daemon second, desktop
widgets on top.

Anyone can use it, fork it, break it, adapt it, or turn it into something else
under the project license. The defaults and priorities are tuned for my own
Linux desktop, but the code is not meant to be locked to one distribution.

For setup instructions, start with [docs/install.md](docs/install.md).

## Vision

- A universal Linux mouse helper for personal daily use.
- Small enough to understand and repair quickly.
- Works without heavyweight desktop dependencies for core control.
- Desktop widgets are optional convenience layers over the CLI.
- Prefer direct, inspectable HID++ behavior over broad device abstraction.
- Support the hardware I own first, then make extension straightforward.

This is not trying to replace Solaar, Piper, or libratbag. Those projects solve
the broad hardware-manager problem. `mouse-helper` solves my narrower problem:
make my mouse status and controls available everywhere I log in.

## Current State

Working now:

- Detect supported Logitech hidraw nodes from `/sys/class/hidraw`.
- Probe HID++ feature support with a focused HID++ 2.0/4.x transport.
- Read best-effort battery, DPI, report rate, and onboard profile state.
- Set DPI where the device accepts the HID++ command.
- Store desired defaults in `~/.config/mouse-helper/config.json`.
- Run a user daemon over a local Unix socket.
- Provide a CLI through `mouse-helperctl`.
- Provide an XFCE panel widget through `xfce4-genmon-plugin`.
- Provide a GTK popup menu for XFCE DPI control and diagnostics.
- Provide a Cinnamon panel applet.
- Ship local install assets for wrappers, udev, systemd user service, desktop
  launcher, Cinnamon applet, and XFCE GenMon configuration.

Still deliberately conservative:

- Button remapping and flash profile editing are not enabled yet.
- On the original PRO X Superlight, report rate is profile-bound. The app reads
  it, but does not write flash profile sectors yet.
- Firmware updates are out of scope.
- Extended DPI / 8 kHz controls are reported, but writes are guarded because
  newer firmware is picky about payload details.

## Supported Devices

Initial supported targets:

- Logitech PRO X Superlight / PRO X Wireless, WPID `4093`
- Logitech PRO X Superlight receiver, USB `046d:c547`
- Logitech PRO X Superlight wired transport, USB `046d:c094`
- Logitech PRO X 2 / Superlight 2, WPID `40a9`
- Logitech PRO X 2 receiver, USB `046d:c54d`
- Logitech PRO X 2 wired transport, USB `046d:c09b`

Other Logitech HID++ devices may be detectable, but they are not a support
promise yet.

## Desktop And Distro Matrix

The core CLI/daemon should work on any modern Linux system with `hidraw`,
`udev`, Python 3, and access to the target device. Desktop integration depends
on the panel environment.

### Desktop Environments

| Desktop environment | Status | Integration | Notes |
| --- | --- | --- | --- |
| XFCE | Daily driver | `xfce4-genmon-plugin` + GTK menu | Current primary widget. Shows DPI/status and opens controls from the panel icon. |
| Cinnamon | Supported | Native Cinnamon applet | Mint-oriented applet is included and installed locally. |
| MATE | Expected | Tray or future panel item | Core CLI should work; no dedicated MATE applet yet. |
| GNOME Shell | Expected | Tray or extension later | Core CLI should work; native Shell extension is not implemented. |
| KDE Plasma | Expected | Tray or widget later | Core CLI should work; Plasma widget is not implemented. |
| LXQt | Expected | Tray later | Core CLI should work; panel integration is not implemented. |
| Sway / wlroots | CLI only | None yet | CLI/daemon should work; no Waybar module shipped yet. |
| i3 / Openbox | CLI only | None yet | CLI/daemon should work; scriptable status output is available through `mouse-helper-genmon`. |

### Common Linux Distros

| Distro family / distro | Status | Notes |
| --- | --- | --- |
| Linux Mint XFCE | Daily driver | Current primary target environment. |
| Linux Mint Cinnamon | Supported | Cinnamon applet and Mint install docs are included. |
| Ubuntu / Xubuntu | Expected | Should work with Python 3, `python3-gi`, udev, and `xfce4-genmon-plugin` for XFCE. |
| Debian | Expected | Should work with equivalent packages and udev rules. |
| Fedora | Expected | Core should work; package names and udev flow may differ. |
| Arch / EndeavourOS | Expected | Core should work; install dependencies through pacman/AUR as needed. |
| openSUSE | Expected | Core should work; package names may differ. |
| NixOS | Manual | Core should work, but udev/systemd/user service setup should be expressed in Nix config. |
| Alpine | Unknown | Musl/minimal desktop setup is untested. |

## Quick Start

For the complete clean-machine install flow, see
[docs/install.md](docs/install.md).

From the repository root:

```bash
./scripts/install-local.sh
mouse-helperctl doctor
systemctl --user enable --now mouse-helper.service
```

If `doctor` reports permission errors on `/dev/hidraw*`, reinstall the udev
rule and unplug/replug the receiver or mouse:

```bash
sudo install -Dm644 data/udev/70-mouse-helper-logitech.rules /etc/udev/rules.d/70-mouse-helper-logitech.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## XFCE Panel Widget

The current daily-driver desktop integration is XFCE via Generic Monitor
(`xfce4-genmon-plugin`).

Install dependencies:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 xfce4-genmon-plugin
```

Then install locally:

```bash
./scripts/install-local.sh
```

Add a Generic Monitor item to the XFCE panel if one does not already exist, and
set:

- Command: `~/.local/bin/mouse-helper-genmon`
- Period: `10`
- Label: disabled

The widget displays the active DPI and exposes a tooltip with battery, DPI, and
report-rate status. Click the mouse icon part of the widget to open the GTK
control menu.

See [docs/install-xfce.md](docs/install-xfce.md) for the detailed XFCE flow.

## Cinnamon Applet

The Cinnamon applet is available at:

```text
cinnamon/mouse-helper@local
```

The local installer copies it to:

```text
~/.local/share/cinnamon/applets/mouse-helper@local
```

Then add `mouse-helper@local` from Cinnamon's Applets settings.

See [docs/install-linux-mint.md](docs/install-linux-mint.md) for the Mint /
Cinnamon install flow.

## Useful Commands

```bash
mouse-helperctl doctor
mouse-helperctl --json status
mouse-helperctl list --json
mouse-helperctl status
mouse-helperctl set dpi 800
mouse-helperctl set report-rate 1ms
mouse-helperctl set profile 1
mouse-helperd --foreground
mouse-helper-genmon
mouse-helper-menu
```

## Project Layout

- `src/mouse_helper/cli.py`: command-line interface.
- `src/mouse_helper/daemon.py`: user daemon and Unix socket server.
- `src/mouse_helper/superlight.py`: HID++ device/session logic.
- `src/mouse_helper/hidraw.py`: Linux hidraw discovery.
- `src/mouse_helper/genmon.py`: XFCE GenMon output.
- `src/mouse_helper/menu.py`: GTK popup control menu.
- `cinnamon/mouse-helper@local/`: Cinnamon applet.
- `data/udev/`: hidraw access rules.
- `data/systemd/user/`: user service.
- `scripts/install-local.sh`: local development install.

## Development

Run tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

This project is intentionally direct and practical. If it works reliably on my
Linux machines and remains easy to inspect, it is doing its job.

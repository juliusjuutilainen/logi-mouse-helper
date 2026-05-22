# Linux Mint Install

These steps are meant for Linux Mint Cinnamon 22.x and Ubuntu 24.04-based Mint
systems.

## 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-gi gir1.2-gtk-3.0 gir1.2-xapp-1.0
```

`mouse-helper` uses only the Python standard library for hidraw access. The GTK
packages are for the optional tray helper.

## 2. Install From This Workspace

```bash
cd ~/Documents/projects/mouse-helper
./scripts/install-local.sh
```

The installer copies:

- wrapper commands to `~/.local/bin/`
- `data/udev/70-mouse-helper-logitech.rules` to `/etc/udev/rules.d/`
- `data/systemd/user/mouse-helper.service` to `~/.config/systemd/user/`
- `data/applications/io.github.local.mouse-helper.desktop` to
  `~/.local/share/applications/`
- `cinnamon/mouse-helper@local` to `~/.local/share/cinnamon/applets/`

## 3. Reload Device Permissions

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Unplug and replug the Logitech receiver or mouse after this. On most Mint
systems, `TAG+="uaccess"` grants your logged-in desktop user access to the
matching `/dev/hidraw*` nodes.

## 4. Start The Daemon

```bash
systemctl --user daemon-reload
systemctl --user enable --now mouse-helper.service
```

Check it:

```bash
systemctl --user status mouse-helper.service
journalctl --user -u mouse-helper.service -f
```

## 5. Add The Cinnamon Applet

Open Cinnamon Applets settings and add `mouse-helper@local` to the panel. If it
does not appear, restart Cinnamon with `Alt+F2`, type `r`, and press Enter.

## 6. Verify

```bash
mouse-helperctl doctor
mouse-helperctl status
mouse-helperctl set dpi 800
mouse-helperctl set report-rate 1ms
```

If writes fail, run:

```bash
mouse-helperctl doctor --json
```

The JSON output includes the hidraw node, USB IDs, permission status, and the
HID++ probe error for each candidate.

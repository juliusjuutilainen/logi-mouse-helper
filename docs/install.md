# Install mouse-helper

This is the practical install guide for a normal Linux desktop. It assumes a
supported Logitech PRO X Superlight-family mouse and a user account with `sudo`.

The safest current target is Linux Mint / Ubuntu / Debian with XFCE or
Cinnamon. Other distros should work for the CLI/daemon if they provide Python 3,
udev, systemd user services, and hidraw access.

## 1. Clone The Project

For friends or public sharing, HTTPS is easiest:

```bash
git clone https://github.com/juliusjuutilainen/logi-mouse-helper.git
cd logi-mouse-helper
```

If you have SSH access configured for GitHub, this also works:

```bash
git clone git@github.com:juliusjuutilainen/logi-mouse-helper.git
cd logi-mouse-helper
```

## 2. Install Dependencies

### Linux Mint / Ubuntu / Debian

Core CLI and daemon:

```bash
sudo apt update
sudo apt install git python3
```

XFCE panel widget and popup menu:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 xfce4-genmon-plugin
```

Cinnamon applet / optional tray pieces:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-xapp-1.0
```

### Other Distros

Install equivalent packages for:

- `git`
- Python 3.10 or newer
- GTK 3 Python bindings / PyGObject, if using the popup menu or tray
- `xfce4-genmon-plugin`, if using XFCE
- `systemd --user`, if using the daemon service
- udev, for hidraw permission rules

The CLI does not require GTK. Desktop integrations do.

## 3. Install Local Wrappers And Desktop Assets

Run from the repository root:

```bash
./scripts/install-local.sh
```

This installs:

- `~/.local/bin/mouse-helperctl`
- `~/.local/bin/mouse-helperd`
- `~/.local/bin/mouse-helper-genmon`
- `~/.local/bin/mouse-helper-menu`
- `~/.config/systemd/user/mouse-helper.service`
- `~/.local/share/applications/io.github.local.mouse-helper.desktop`
- Cinnamon applet files, if using Cinnamon
- XFCE GenMon config for existing GenMon panel items

Make sure `~/.local/bin` is in your `PATH`:

```bash
echo "$PATH" | tr ':' '\n' | grep -x "$HOME/.local/bin"
```

If that prints nothing, log out and back in, or add this to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 4. Install Device Permission Rules

The helper talks to the mouse through `/dev/hidraw*`. Install the udev rule:

```bash
sudo install -Dm644 data/udev/70-mouse-helper-logitech.rules /etc/udev/rules.d/70-mouse-helper-logitech.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then unplug and replug the Logitech receiver or mouse.

Verify access:

```bash
mouse-helperctl doctor
mouse-helperctl status
```

If `doctor` reports missing permission or missing `/dev/hidraw*` nodes, replug
the receiver and run:

```bash
mouse-helperctl --json doctor
```

The JSON output includes the detected USB IDs, hidraw candidates, permission
state, and probe errors.

## 5. Start The User Daemon

The daemon is optional but recommended. It gives panel widgets and CLI commands
a faster, shared status/control path.

```bash
systemctl --user daemon-reload
systemctl --user enable --now mouse-helper.service
systemctl --user status mouse-helper.service
```

View logs:

```bash
journalctl --user -u mouse-helper.service -f
```

## 6. Add Desktop Integration

### XFCE

Install `xfce4-genmon-plugin` first, then add a Generic Monitor item to the
panel:

1. Right-click the XFCE panel.
2. Open **Panel** -> **Add New Items...**.
3. Add **Generic Monitor**.
4. Right-click the new item and open **Properties**.
5. Set **Command** to:

```text
~/.local/bin/mouse-helper-genmon
```

6. Set period to `10`.
7. Disable the label.

The widget shows the active DPI. Hover for battery/status. Click the mouse icon
part of the widget to open the control menu.

If the panel shows `(genmon)XXX`, the command failed to spawn. Check:

```bash
~/.local/bin/mouse-helper-genmon
cat ~/.config/xfce4/panel/genmon-*.rc
```

### Cinnamon

The installer copies the applet to:

```text
~/.local/share/cinnamon/applets/mouse-helper@local
```

Open Cinnamon Applets settings and add `mouse-helper@local` to the panel. If it
does not appear, restart Cinnamon with `Alt+F2`, type `r`, and press Enter.

## 7. Basic Usage

```bash
mouse-helperctl status
mouse-helperctl set dpi 800
mouse-helperctl set dpi 1200
mouse-helperctl set profile 1
mouse-helperctl doctor
```

The currently supported DPI presets in the desktop menu are conservative by
design. The CLI can set any value accepted by the device in the supported range.

## Uninstall

From the repository root:

```bash
./scripts/uninstall-local.sh
```

Remove the udev rule manually if you no longer want it:

```bash
sudo rm -f /etc/udev/rules.d/70-mouse-helper-logitech.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

# mouse-helper

`mouse-helper` is a small Linux Mint/Cinnamon-focused Logitech G Pro Superlight
control app. It is intentionally narrower than Solaar or Piper: one tiny daemon,
one CLI, and one Cinnamon applet for the panel.

The first target devices are:

- Logitech PRO X Superlight / PRO X Wireless, WPID `4093`
- Logitech PRO X Superlight receiver, USB `046d:c547`
- Logitech PRO X Superlight wired transport, USB `046d:c094`
- Logitech PRO X 2 / Superlight 2, WPID `40a9`
- Logitech PRO X 2 receiver, USB `046d:c54d`
- Logitech PRO X 2 wired transport, USB `046d:c09b`

## Current Scope

Working now:

- Detect matching Logitech hidraw nodes from `/sys/class/hidraw`
- Probe HID++ feature support with a focused HID++ 2.0/4.x transport
- Read best-effort battery, DPI, report rate, and onboard profile state
- Set standard DPI where the device accepts the HID++ command
- Store desired defaults in `~/.config/mouse-helper/config.json`
- Run a small user daemon over a local Unix socket
- Provide a Cinnamon panel applet that calls `mouse-helperctl`
- Ship Linux Mint install assets for udev, systemd user, desktop, and applet

Still deliberately conservative:

- Button remapping and flash profile editing are not enabled yet.
- On the original PRO X Superlight, report rate is profile-bound. The app reads
  it, but does not write flash profile sectors yet.
- Firmware updates are out of scope.
- Extended DPI / 8 kHz controls are reported, but writes are guarded because
  newer firmware is picky about lift-off-distance payloads.

## Quick Start

```bash
./scripts/install-local.sh
mouse-helperctl doctor
systemctl --user enable --now mouse-helper.service
```

Then add the Cinnamon applet from Cinnamon's Applets settings:
`mouse-helper@local`.

See [docs/install-linux-mint.md](docs/install-linux-mint.md) for the full Mint
install flow.

## Useful Commands

```bash
mouse-helperctl doctor
mouse-helperctl list --json
mouse-helperctl status
mouse-helperctl set dpi 800
mouse-helperctl set report-rate 1ms
mouse-helperctl set profile 1
mouse-helperd --foreground
```

If `doctor` reports permission errors on `/dev/hidraw*`, reinstall the udev rule
and unplug/replug the receiver or mouse.

# Architecture

`mouse-helper` is split into three small pieces.

## Daemon

`mouse-helperd` runs as a systemd user service and owns the hardware polling
loop. It exposes a newline-delimited JSON protocol over:

```text
$XDG_RUNTIME_DIR/mouse-helper.sock
```

The socket is intentionally simpler than D-Bus for the first version. A D-Bus
adapter can sit in front of the same `SuperlightManager` later without changing
the hardware layer.

## CLI

`mouse-helperctl` talks directly to the manager by default and can also talk to
the daemon socket. Direct mode is useful before the daemon is installed.

## Cinnamon Applet

`cinnamon/mouse-helper@local` is a native Cinnamon applet. It keeps no hardware
state itself. It periodically runs `mouse-helperctl --json status` and uses
`mouse-helperctl set ...` for user actions.

This keeps USB/HID parsing out of Cinnamon's process. If the hardware layer has
a bug, the panel should stay alive.

## HID++ Scope

The HID++ implementation is deliberately focused on the G Pro Superlight family:

- feature discovery through ROOT `0x0000`
- battery through UNIFIED_BATTERY `0x1004`
- DPI through ADJUSTABLE_DPI `0x2201`
- report rate through REPORT_RATE `0x8060`
- extended report-rate discovery through `0x8061`
- onboard profile state through ONBOARD_PROFILES `0x8100`

Button remapping and profile flash writes come after we can dump and restore
profiles safely.

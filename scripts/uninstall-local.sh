#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now mouse-helper.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/mouse-helper.service"
rm -f "$HOME/.local/share/applications/io.github.local.mouse-helper.desktop"
rm -f "$HOME/.local/bin/mouse-helperctl" "$HOME/.local/bin/mouse-helperd" "$HOME/.local/bin/mouse-helper-tray" "$HOME/.local/bin/mouse-helper-genmon" "$HOME/.local/bin/mouse-helper-menu"
rm -rf "$HOME/.local/share/cinnamon/applets/mouse-helper@local"

if [ -t 0 ]; then
  echo "Removing udev rule requires sudo."
  sudo rm -f /etc/udev/rules.d/70-mouse-helper-logitech.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
else
  cat <<'MSG'
Skipping udev rule removal because sudo cannot prompt in this shell.
Run this in a terminal:
  sudo rm -f /etc/udev/rules.d/70-mouse-helper-logitech.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
MSG
fi
systemctl --user daemon-reload || true

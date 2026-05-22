#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install -d "$HOME/.local/bin"
cat > "$HOME/.local/bin/mouse-helperctl" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m mouse_helper.cli "\$@"
EOF
cat > "$HOME/.local/bin/mouse-helperd" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m mouse_helper.daemon "\$@"
EOF
cat > "$HOME/.local/bin/mouse-helper-tray" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m mouse_helper.tray "\$@"
EOF
cat > "$HOME/.local/bin/mouse-helper-genmon" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m mouse_helper.genmon "\$@"
EOF
cat > "$HOME/.local/bin/mouse-helper-menu" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$ROOT/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec /usr/bin/python3 -m mouse_helper.menu "\$@"
EOF
chmod +x "$HOME/.local/bin/mouse-helperctl" "$HOME/.local/bin/mouse-helperd" "$HOME/.local/bin/mouse-helper-tray" "$HOME/.local/bin/mouse-helper-genmon" "$HOME/.local/bin/mouse-helper-menu"

if command -v xfconf-query >/dev/null 2>&1; then
  GENMON="$HOME/.local/bin/mouse-helper-genmon"
  while IFS= read -r plugin_id; do
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/command" -s "$GENMON" || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/period" -s 10 || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/show-label" -s false || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/Command" -n -t string -s "$GENMON" || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/Text" -n -t string -s "Mouse" || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/UseLabel" -n -t bool -s false || true
    xfconf-query -c xfce4-panel -p "/plugins/plugin-${plugin_id}/UpdatePeriod" -n -t int -s 10 || true
    install -d "$HOME/.config/xfce4/panel"
    cat > "$HOME/.config/xfce4/panel/genmon-${plugin_id}.rc" <<RC
Command=$GENMON
UseLabel=0
Text=Mouse
UpdatePeriod=10000
Font=Ubuntu 10
RC
  done < <(
    xfconf-query -c xfce4-panel -p /plugins -lv 2>/dev/null \
      | awk '$2 == "genmon" { sub(".*/plugin-", "", $1); print $1 }'
  )
fi

install -Dm644 "$ROOT/data/systemd/user/mouse-helper.service" \
  "$HOME/.config/systemd/user/mouse-helper.service"
install -Dm644 "$ROOT/data/applications/io.github.local.mouse-helper.desktop" \
  "$HOME/.local/share/applications/io.github.local.mouse-helper.desktop"
install -d "$HOME/.local/share/cinnamon/applets"
rm -rf "$HOME/.local/share/cinnamon/applets/mouse-helper@local"
cp -a "$ROOT/cinnamon/mouse-helper@local" "$HOME/.local/share/cinnamon/applets/"

if [ -t 0 ]; then
  echo "Installing udev rule requires sudo."
  sudo install -Dm644 "$ROOT/data/udev/70-mouse-helper-logitech.rules" \
    /etc/udev/rules.d/70-mouse-helper-logitech.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
else
  cat <<MSG
Skipping udev rule installation because sudo cannot prompt in this shell.
Run this in a terminal:
  sudo install -Dm644 "$ROOT/data/udev/70-mouse-helper-logitech.rules" /etc/udev/rules.d/70-mouse-helper-logitech.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
MSG
fi

systemctl --user daemon-reload || true

cat <<'MSG'
Installed mouse-helper assets.

Next:
  1. Unplug/replug the Logitech receiver or mouse.
  2. Run: mouse-helperctl doctor
  3. Run: systemctl --user enable --now mouse-helper.service
  4. Add the mouse-helper@local applet from Cinnamon Applets settings.
     On XFCE, add a Generic Monitor panel item with command:
       ~/.local/bin/mouse-helper-genmon
MSG

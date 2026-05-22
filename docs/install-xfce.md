# XFCE Panel Widget Install

These steps describe how to set up the premium `mouse-helper` panel widget on XFCE using the Generic Monitor plugin.

---

## 1. Install Dependencies

In addition to core dependencies, the XFCE panel widget uses `PyGObject` (GTK 3) for the interactive popup menu, and requires the **xfce4-genmon-plugin**:

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 xfce4-genmon-plugin
```

---

## 2. Install mouse-helper

Run the local installer from the repository root:

```bash
cd ~/Documents/projects/mouse-helper
./scripts/install-local.sh
```

This will generate and install the wrappers to your local bin directory:
- `~/.local/bin/mouse-helper-genmon` (periodic status monitor)
- `~/.local/bin/mouse-helper-menu` (interactive GTK dropdown menu)

Ensure `~/.local/bin` is in your environment `$PATH` (standard on modern distributions).

---

## 3. Add the Widget to Your XFCE Panel

1. **Add Generic Monitor**:
   - Right-click anywhere on an empty spot of your XFCE panel.
   - Select **Panel** -> **Add New Items...**
   - Search for **Generic Monitor** (labeled as `xfce4-genmon-plugin`).
   - Click **Add**, then close the dialog.
   - Right-click the newly added monitor and click **Move** to position it wherever you like.

2. **Configure the Monitor Properties**:
   - Right-click the Generic Monitor widget and click **Properties**.
   - Set the configuration as follows:
     - **Command**: `mouse-helper-genmon`
     - **Label**: (Uncheck **Show label** so only the clean mouse icon and DPI text are shown)
     - **Period (s)**: `10` (or `5` for faster updates)
   - Click **Save** / **Close**.

---

## 4. Features & Usage

- **Panel Status**: Displays a sleek symbolic mouse icon followed by the active DPI (e.g. `800`).
- **Low Battery Indicator**: If the battery drops to **20% or lower** (and is not currently charging), a warning emoji `⚠️` is prepended to the DPI label to alert you.
- **Detailed Tooltip**: Hovering over the widget reveals a detailed tooltip showing the mouse model name, precise battery percentage and charging state, active DPI, and current report rate.
- **Interactive Menu**: Left-clicking the widget immediately opens a premium GTK dropdown selection menu at your mouse pointer. You can see the full device status, click any DPI preset to instantly change it, copy diagnostic Doctor JSON directly to your clipboard, or cancel.

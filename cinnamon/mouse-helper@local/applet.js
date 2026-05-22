const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Mainloop = imports.mainloop;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const ByteArray = imports.byteArray;

const DPI_PRESETS = [
    600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400
];

function runCommand(args) {
    let argv = ["/usr/bin/env", "mouse-helperctl", "--daemon"].concat(args);
    try {
        let [ok, stdout, stderr, status] = GLib.spawn_sync(
            null,
            argv,
            null,
            GLib.SpawnFlags.SEARCH_PATH,
            null
        );
        if (!ok || status !== 0) {
            argv = ["/usr/bin/env", "mouse-helperctl"].concat(args);
            [ok, stdout, stderr, status] = GLib.spawn_sync(
                null,
                argv,
                null,
                GLib.SpawnFlags.SEARCH_PATH,
                null
            );
            if (!ok || status !== 0) {
                return { ok: false, error: ByteArray.toString(stderr).trim() };
            }
        }
        return { ok: true, stdout: ByteArray.toString(stdout).trim() };
    } catch (e) {
        return { ok: false, error: e.message };
    }
}

function runJson(args) {
    let result = runCommand(["--json"].concat(args));
    if (!result.ok) {
        return { online: false, errors: [result.error] };
    }
    try {
        return JSON.parse(result.stdout);
    } catch (e) {
        return { online: false, errors: [e.message] };
    }
}

class MouseHelperApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.set_applet_icon_symbolic_name("input-mouse-symbolic");
        this.set_applet_label("Mouse");
        this.set_applet_tooltip("Mouse Helper");

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);

        this._dpiChoicesKey = "";
        this._buildMenu(DPI_PRESETS);
        this._timer = null;
        this.refresh();
        this._schedule();
    }

    _buildMenu(dpiChoices) {
        this.menu.removeAll();
        this._dpiChoicesKey = dpiChoices.join(",");

        this.statusItem = new PopupMenu.PopupMenuItem("Loading...", { reactive: false });
        this.menu.addMenuItem(this.statusItem);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        dpiChoices.forEach((dpi) => {
            let item = new PopupMenu.PopupMenuItem(`${dpi} DPI`);
            item.connect("activate", () => {
                runCommand(["set", "dpi", String(dpi)]);
                this.refresh();
            });
            this.menu.addMenuItem(item);
        });

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        let doctor = new PopupMenu.PopupMenuItem("Copy Doctor JSON");
        doctor.connect("activate", () => {
            let result = runCommand(["--json", "doctor"]);
            if (result.ok) {
                St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, result.stdout);
            }
        });
        this.menu.addMenuItem(doctor);
    }

    _schedule() {
        if (this._timer !== null) {
            Mainloop.source_remove(this._timer);
        }
        this._timer = Mainloop.timeout_add_seconds(10, () => {
            this.refresh();
            return true;
        });
    }

    refresh() {
        let state = runJson(["status"]);
        if (!state.online) {
            this.set_applet_label("Mouse");
            this.set_applet_tooltip("No Superlight detected");
            let errors = state.errors && state.errors.length ? "\n" + state.errors[0] : "";
            this.statusItem.label.set_text("No Superlight detected" + errors);
            return;
        }
        let dpiChoices = state.dpi_choices && state.dpi_choices.length ? state.dpi_choices : DPI_PRESETS;
        let dpiChoicesKey = dpiChoices.join(",");
        if (dpiChoicesKey !== this._dpiChoicesKey) {
            this._buildMenu(dpiChoices);
        }
        let battery = state.battery_percent === null ? "?" : `${state.battery_percent}%`;
        let dpi = state.dpi || "?";
        let rate = state.report_rate || "?";
        this.set_applet_label(`${dpi}`);
        this.set_applet_tooltip(`${state.name}\nBattery ${battery}\nDPI ${dpi}\nRate ${rate}`);
        this.statusItem.label.set_text(`${state.name}\nBattery ${battery}\nDPI ${dpi}\nRate ${rate}`);
    }

    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        if (this._timer !== null) {
            Mainloop.source_remove(this._timer);
            this._timer = null;
        }
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new MouseHelperApplet(metadata, orientation, panelHeight, instanceId);
}

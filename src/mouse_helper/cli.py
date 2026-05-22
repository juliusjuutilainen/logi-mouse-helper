from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .ipc import request_daemon
from .superlight import SuperlightManager


def _emit(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    elif isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2, sort_keys=True))


def _format_state(state: dict[str, Any]) -> str:
    if not state.get("online"):
        errors = state.get("errors") or []
        extra = f"\nErrors:\n  " + "\n  ".join(errors) if errors else ""
        return f"No Superlight detected.{extra}"
    bits = [
        f"{state.get('name')} on {state.get('hidraw')} index {state.get('device_index')}",
        f"Battery: {state.get('battery_percent', '?')}% {state.get('battery_status') or ''}".strip(),
        f"DPI: {state.get('dpi') or '?'}",
        f"Report rate: {state.get('report_rate') or '?'}",
        f"Onboard profile: {state.get('onboard_profile')}",
    ]
    return "\n".join(bits)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mouse-helperctl")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--daemon", action="store_true", help="talk to the running daemon")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="print diagnostics")
    sub.add_parser("list", help="list candidate hidraw nodes")
    sub.add_parser("status", help="show current mouse state")
    sub.add_parser("probe-dpi", help=argparse.SUPPRESS)
    sub.add_parser("probe-battery", help=argparse.SUPPRESS)
    sub.add_parser("probe-report-rate", help=argparse.SUPPRESS)
    sub.add_parser("probe-report-rate-setters", help=argparse.SUPPRESS)

    set_parser = sub.add_parser("set", help="change a setting")
    set_sub = set_parser.add_subparsers(dest="setting", required=True)
    dpi = set_sub.add_parser("dpi")
    dpi.add_argument("value", type=int)
    rate = set_sub.add_parser("report-rate")
    rate.add_argument("value")
    profile = set_sub.add_parser("profile")
    profile.add_argument("value", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manager = SuperlightManager()

    try:
        command = args.command or "status"
        if args.daemon:
            if command == "status":
                data = request_daemon("status")["state"]
            elif command == "doctor":
                data = request_daemon("doctor")["doctor"]
            elif command == "list":
                data = request_daemon("list")["hidraw"]
            elif command == "probe-dpi":
                data = request_daemon("probe_dpi")["probe"]
            elif command == "probe-battery":
                data = request_daemon("probe_battery")["probe"]
            elif command == "probe-report-rate":
                data = request_daemon("probe_report_rate")["probe"]
            elif command == "probe-report-rate-setters":
                data = request_daemon("probe_report_rate_setters")["probe"]
            elif command == "set":
                data = request_daemon(
                    "set",
                    key=args.setting.replace("-", "_"),
                    value=args.value,
                )["state"]
            else:
                parser.error(f"unknown command {command}")
        else:
            if command == "status":
                data = manager.status().to_dict()
            elif command == "doctor":
                data = manager.doctor()
            elif command == "list":
                data = [device.to_dict() for device in manager.list_hidraw()]
            elif command == "probe-dpi":
                data = manager.probe_dpi()
            elif command == "probe-battery":
                data = manager.probe_battery()
            elif command == "probe-report-rate":
                data = manager.probe_report_rate()
            elif command == "probe-report-rate-setters":
                data = manager.probe_report_rate_setters()
            elif command == "set":
                if args.setting == "dpi":
                    data = manager.set_dpi(args.value).to_dict()
                elif args.setting == "report-rate":
                    data = manager.set_report_rate(args.value).to_dict()
                elif args.setting == "profile":
                    data = manager.set_profile(args.value).to_dict()
                else:
                    parser.error(f"unknown setting {args.setting}")
            else:
                parser.error(f"unknown command {command}")

        if command == "status" and not args.json:
            _emit(_format_state(data), False)
        else:
            _emit(data, args.json)
        return 0
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        else:
            print(f"mouse-helperctl: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

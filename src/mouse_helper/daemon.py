from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import threading
import time
from typing import Any

from .config import socket_path
from .superlight import SuperlightManager


class MouseHelperDaemon:
    def __init__(self, interval: float = 60.0):
        self.interval = interval
        self.manager = SuperlightManager()
        self.hardware_lock = threading.Lock()
        self.stop_event = threading.Event()

    def _handle(self, request: dict[str, Any]) -> dict[str, Any]:
        command = request.get("command")
        if command == "status":
            return {"ok": True, "state": self.manager.status().to_dict()}
        if command == "doctor":
            return {"ok": True, "doctor": self.manager.doctor()}
        if command == "list":
            devices = [device.to_dict() for device in self.manager.list_hidraw()]
            return {"ok": True, "hidraw": devices}
        if command == "probe_dpi":
            return {"ok": True, "probe": self.manager.probe_dpi()}
        if command == "probe_battery":
            return {"ok": True, "probe": self.manager.probe_battery()}
        if command == "probe_report_rate":
            return {"ok": True, "probe": self.manager.probe_report_rate()}
        if command == "probe_report_rate_setters":
            return {"ok": True, "probe": self.manager.probe_report_rate_setters()}
        if command == "set":
            key = request.get("key")
            value = request.get("value")
            if key == "dpi":
                state = self.manager.set_dpi(int(value))
            elif key == "report_rate":
                state = self.manager.set_report_rate(str(value))
            elif key == "profile":
                state = self.manager.set_profile(int(value))
            else:
                raise ValueError(f"unknown setting {key!r}")
            return {"ok": True, "state": state.to_dict()}
        raise ValueError(f"unknown command {command!r}")

    def _serve_client(self, conn: socket.socket) -> None:
        with conn:
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            try:
                request = json.loads(data.decode("utf-8"))
                response = self._handle(request)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            conn.sendall(json.dumps(response, sort_keys=True).encode("utf-8") + b"\n")

    def _apply_loop(self) -> None:
        while not self.stop_event.wait(self.interval):
            with self.hardware_lock:
                self.manager.apply_desired()

    def run(self) -> None:
        path = socket_path()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.exists():
            path.unlink()

        signal.signal(signal.SIGTERM, lambda *_: self.stop_event.set())
        signal.signal(signal.SIGINT, lambda *_: self.stop_event.set())

        worker = threading.Thread(target=self._apply_loop, daemon=True)
        worker.start()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(path))
            os.chmod(path, 0o600)
            server.listen(8)
            server.settimeout(0.5)
            while not self.stop_event.is_set():
                try:
                    conn, _ = server.accept()
                except TimeoutError:
                    continue
                threading.Thread(target=self._serve_client_locked, args=(conn,), daemon=True).start()

        with contextlib_suppress(FileNotFoundError):
            path.unlink()

    def _serve_client_locked(self, conn: socket.socket) -> None:
        with self.hardware_lock:
            self._serve_client(conn)


class contextlib_suppress:
    def __init__(self, *exceptions: type[BaseException]):
        self.exceptions = exceptions

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type: type[BaseException] | None, *_exc: object) -> bool:
        return exc_type is not None and issubclass(exc_type, self.exceptions)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the mouse-helper daemon")
    parser.add_argument("--foreground", action="store_true", help="stay in the foreground")
    parser.add_argument("--interval", type=float, default=60.0, help="desired-state apply interval")
    args = parser.parse_args(argv)

    daemon = MouseHelperDaemon(interval=args.interval)
    try:
        daemon.run()
    except Exception as exc:
        print(f"mouse-helperd: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

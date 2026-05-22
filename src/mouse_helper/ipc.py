from __future__ import annotations

import json
import socket
from typing import Any

from .config import socket_path


def request_daemon(command: str, **payload: Any) -> dict[str, Any]:
    path = socket_path()
    request = {"command": command, **payload}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(str(path))
        sock.sendall(json.dumps(request).encode("utf-8") + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    response = json.loads(data.decode("utf-8"))
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "daemon request failed"))
    return response

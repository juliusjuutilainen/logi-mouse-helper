from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .constants import APP_NAME, SOCKET_NAME


def config_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def runtime_dir() -> Path:
    base = os.environ.get("XDG_RUNTIME_DIR")
    if base:
        return Path(base)
    fallback = Path("/tmp") / f"{APP_NAME}-{os.getuid()}"
    fallback.mkdir(mode=0o700, exist_ok=True)
    return fallback


def socket_path() -> Path:
    return runtime_dir() / SOCKET_NAME


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {"desired": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"desired": {}}
    if not isinstance(data, dict):
        return {"desired": {}}
    data.setdefault("desired", {})
    if not isinstance(data["desired"], dict):
        data["desired"] = {}
    return data


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def set_desired(key: str, value: Any) -> dict[str, Any]:
    data = load_config()
    desired = data.setdefault("desired", {})
    desired[key] = value
    save_config(data)
    return data

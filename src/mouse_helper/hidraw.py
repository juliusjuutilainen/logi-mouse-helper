from __future__ import annotations

import os
from pathlib import Path

from .constants import (
    DIRECT_PRODUCT_IDS,
    LOGITECH_VENDOR_ID,
    RECEIVER_PRODUCT_IDS,
    SUPERLIGHT_USB_IDS,
)
from .models import HidrawDeviceInfo


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _parse_hex(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value.strip(), 16)
    except ValueError:
        return None


def _parse_uevent(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    text = _read_text(path)
    if not text:
        return data
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def _walk_attr(start: Path, attr: str) -> str | None:
    current = start
    while True:
        value = _read_text(current / attr)
        if value:
            return value
        if current.parent == current:
            return None
        current = current.parent


def _ids_from_hid_id(hid_id: str | None) -> tuple[int | None, int | None]:
    if not hid_id:
        return None, None
    parts = hid_id.split(":")
    if len(parts) != 3:
        return None, None
    return _parse_hex(parts[1]), _parse_hex(parts[2])


def _role(product_id: int | None) -> str:
    if product_id in RECEIVER_PRODUCT_IDS:
        return "lightspeed-receiver"
    if product_id in DIRECT_PRODUCT_IDS:
        return "wired-device"
    return "logitech-hidraw"


def scan_hidraw(include_all_logitech: bool = False) -> list[HidrawDeviceInfo]:
    devices: list[HidrawDeviceInfo] = []
    root = Path("/sys/class/hidraw")
    if not root.exists():
        return devices

    for entry in sorted(root.glob("hidraw*")):
        device_dir = (entry / "device").resolve()
        uevent = _parse_uevent(device_dir / "uevent")
        vendor_id, product_id = _ids_from_hid_id(uevent.get("HID_ID"))
        vendor_id = vendor_id or _parse_hex(_walk_attr(device_dir, "idVendor"))
        product_id = product_id or _parse_hex(_walk_attr(device_dir, "idProduct"))

        hid_name = uevent.get("HID_NAME") or _walk_attr(device_dir, "name")
        manufacturer = _walk_attr(device_dir, "manufacturer")
        product = _walk_attr(device_dir, "product")
        serial = _walk_attr(device_dir, "serial")

        is_logitech = vendor_id == LOGITECH_VENDOR_ID or "logitech" in (
            hid_name or product or manufacturer or ""
        ).lower()
        is_target = vendor_id == LOGITECH_VENDOR_ID and product_id in SUPERLIGHT_USB_IDS
        if not (is_target or (include_all_logitech and is_logitech)):
            continue

        dev_node = f"/dev/{entry.name}"
        dev_path = Path(dev_node)
        info = HidrawDeviceInfo(
            name=entry.name,
            dev_node=dev_node,
            sys_path=str(device_dir),
            vendor_id=vendor_id,
            product_id=product_id,
            hid_name=hid_name,
            manufacturer=manufacturer,
            product=product,
            serial=serial,
            readable=os.access(dev_node, os.R_OK),
            writable=os.access(dev_node, os.W_OK),
            role=_role(product_id),
        )
        if not dev_path.exists():
            info.errors.append("device node missing; reload udev rules and replug")
        elif not info.readable or not info.writable:
            info.errors.append("missing read/write permission; check udev rule and replug")
        devices.append(info)

    return devices

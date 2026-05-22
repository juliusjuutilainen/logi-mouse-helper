from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class HidrawDeviceInfo:
    name: str
    dev_node: str
    sys_path: str
    vendor_id: int | None = None
    product_id: int | None = None
    hid_name: str | None = None
    manufacturer: str | None = None
    product: str | None = None
    serial: str | None = None
    readable: bool = False
    writable: bool = False
    role: str = "unknown"
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["vendor_hex"] = f"{self.vendor_id:04x}" if self.vendor_id is not None else None
        data["product_hex"] = f"{self.product_id:04x}" if self.product_id is not None else None
        return data


@dataclass(slots=True)
class MouseState:
    online: bool
    name: str = "No Superlight detected"
    hidraw: str | None = None
    device_index: int | None = None
    vendor_id: int | None = None
    product_id: int | None = None
    battery_percent: int | None = None
    battery_status: str | None = None
    dpi: int | None = None
    dpi_choices: list[int] = field(default_factory=list)
    report_rate: str | None = None
    report_rate_choices: list[str] = field(default_factory=list)
    onboard_profile: int | None = None
    features: dict[str, bool] = field(default_factory=dict)
    desired: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["vendor_hex"] = f"{self.vendor_id:04x}" if self.vendor_id is not None else None
        data["product_hex"] = f"{self.product_id:04x}" if self.product_id is not None else None
        return data

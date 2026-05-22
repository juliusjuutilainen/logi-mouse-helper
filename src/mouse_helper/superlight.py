from __future__ import annotations

import time
from contextlib import suppress
from typing import Any

from .config import load_config, set_desired
from .constants import (
    BATTERY_LEVEL,
    BATTERY_STATUS,
    DPI_PRESETS,
    EXTENDED_REPORT_RATE_LABELS,
    EXTENDED_REPORT_RATE_VALUES,
    Feature,
    RECEIVER_PRODUCT_IDS,
    REPORT_RATE_LABELS,
    REPORT_RATE_VALUES,
    SUPERLIGHT2_PRODUCT_IDS,
    SUPERLIGHT_USB_IDS,
)
from .hidpp import HidppClient, HidppException, HidrawTransport
from .hidraw import scan_hidraw
from .models import HidrawDeviceInfo, MouseState


def _int_from_bytes(data: bytes) -> int | None:
    if not data:
        return None
    return int.from_bytes(data, "big")


def _parse_dpi(data: bytes) -> int | None:
    if len(data) >= 5:
        current = int.from_bytes(data[1:3], "big")
        if 50 <= current <= 64000:
            return current
    candidates = []
    if len(data) >= 2:
        candidates.append(int.from_bytes(data[:2], "big"))
    if len(data) >= 4:
        candidates.append(int.from_bytes(data[2:4], "big"))
    for value in candidates:
        if 50 <= value <= 64000:
            return value
    return None


def _parse_battery(data: bytes) -> tuple[int | None, str | None]:
    if not data:
        return None, None
    percent = data[0] if data[0] <= 100 else None
    level_bits = data[1] if len(data) > 1 else 0
    charge_status = data[2] if len(data) > 2 else None

    status = BATTERY_STATUS.get(charge_status)
    if charge_status == 0 and level_bits:
        for bit in (0x08, 0x04, 0x02, 0x01):
            if level_bits & bit:
                level = BATTERY_LEVEL[bit]
                status = level if level in ("critical", "low") else "discharging"
                break
    return percent, status


class SuperlightSession:
    def __init__(self, info: HidrawDeviceInfo, device_index: int):
        self.info = info
        self.device_index = device_index
        self.transport = HidrawTransport(info.dev_node)
        self.client: HidppClient | None = None

    def __enter__(self) -> "SuperlightSession":
        self.transport.__enter__()
        self.client = HidppClient(self.transport, self.device_index)
        return self

    def __exit__(self, *exc: object) -> None:
        self.transport.__exit__(*exc)

    def feature_available(self, feature: int, attempts: int = 3) -> bool:
        assert self.client is not None
        for attempt in range(attempts):
            with suppress(HidppException, OSError, IndexError):
                self.client.get_feature(feature)
                return True
            if attempt + 1 < attempts:
                time.sleep(0.05)
        return False

    def feature_request(self, feature: int, fnid: int, params: bytes = b"", attempts: int = 3) -> bytes:
        assert self.client is not None
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self.client.feature_request(feature, fnid, params)
            except (HidppException, OSError, IndexError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(0.05)
        if last_error is not None:
            raise last_error
        raise HidppException("feature request failed")

    def read_state(self) -> MouseState:
        assert self.client is not None
        state = MouseState(
            online=True,
            name=SUPERLIGHT_USB_IDS.get(self.info.product_id or 0, self.info.hid_name or "Logitech mouse"),
            hidraw=self.info.dev_node,
            device_index=self.device_index,
            vendor_id=self.info.vendor_id,
            product_id=self.info.product_id,
            desired=load_config().get("desired", {}),
        )

        has_extended_features = self.info.product_id in SUPERLIGHT2_PRODUCT_IDS
        features = {
            "battery": self.feature_available(Feature.UNIFIED_BATTERY),
            "dpi": self.feature_available(Feature.ADJUSTABLE_DPI),
            "dpi_extended": has_extended_features
            and self.feature_available(Feature.EXTENDED_ADJUSTABLE_DPI, attempts=1),
            "report_rate": self.feature_available(Feature.REPORT_RATE),
            "report_rate_extended": has_extended_features
            and self.feature_available(Feature.EXTENDED_REPORT_RATE, attempts=1),
            "onboard_profiles": self.feature_available(Feature.ONBOARD_PROFILES),
        }
        state.features = features

        if features["battery"]:
            with suppress(HidppException, OSError, IndexError):
                reply = self.feature_request(Feature.UNIFIED_BATTERY, 0x10)
                state.battery_percent, state.battery_status = _parse_battery(reply)

        if features["dpi"]:
            with suppress(HidppException, OSError, IndexError):
                reply = self.feature_request(Feature.ADJUSTABLE_DPI, 0x20)
                state.dpi = _parse_dpi(reply)
                state.dpi_choices = DPI_PRESETS

        if features["report_rate"]:
            with suppress(HidppException, OSError, IndexError):
                choices_reply = self.feature_request(Feature.REPORT_RATE, 0x00)
                flags = choices_reply[0] if choices_reply else 0
                state.report_rate_choices = [
                    REPORT_RATE_LABELS[i + 1] for i in range(8) if flags & (1 << i)
                ]
                current = self.feature_request(Feature.REPORT_RATE, 0x10)
                if current:
                    state.report_rate = REPORT_RATE_LABELS.get(current[0])

        if not state.report_rate and features["report_rate_extended"]:
            with suppress(HidppException, OSError, IndexError):
                choices_reply = self.feature_request(Feature.EXTENDED_REPORT_RATE, 0x10)
                flags = int.from_bytes(choices_reply[:2], "big") if choices_reply else 0
                state.report_rate_choices = [
                    EXTENDED_REPORT_RATE_LABELS[i] for i in range(7) if flags & (1 << i)
                ]
                current = self.feature_request(Feature.EXTENDED_REPORT_RATE, 0x20)
                if current:
                    state.report_rate = EXTENDED_REPORT_RATE_LABELS.get(current[0])

        if features["onboard_profiles"]:
            with suppress(HidppException, OSError, IndexError):
                enabled = self.feature_request(Feature.ONBOARD_PROFILES, 0x20)
                if enabled and enabled[0] == 0x01:
                    active = self.feature_request(Feature.ONBOARD_PROFILES, 0x40)
                    if len(active) >= 2:
                        state.onboard_profile = int.from_bytes(active[:2], "big")
                else:
                    state.onboard_profile = 0

        return state

    def set_dpi(self, dpi: int) -> None:
        assert self.client is not None
        if dpi < 50 or dpi > 64000:
            raise ValueError("DPI must be between 50 and 64000")
        payload = b"\x00" + dpi.to_bytes(2, "big")
        self.feature_request(Feature.ADJUSTABLE_DPI, 0x30, payload)
        reply = self.feature_request(Feature.ADJUSTABLE_DPI, 0x20)
        applied = _parse_dpi(reply)
        if applied != dpi:
            raise RuntimeError(f"mouse reported DPI {applied} after setting {dpi}")

    def set_report_rate(self, label: str) -> str:
        assert self.client is not None
        normalized = label.lower()
        if self.feature_available(Feature.EXTENDED_REPORT_RATE) and normalized in EXTENDED_REPORT_RATE_VALUES:
            value = EXTENDED_REPORT_RATE_VALUES[normalized]
            self.feature_request(Feature.EXTENDED_REPORT_RATE, 0x30, bytes([value]))
            return EXTENDED_REPORT_RATE_LABELS[value]
        if self.feature_available(Feature.REPORT_RATE) and normalized in REPORT_RATE_VALUES:
            raise NotImplementedError(
                "standard report rate is stored in onboard profile memory on this device"
            )
        raise ValueError(f"unsupported report rate: {label}")

    def set_profile(self, profile: int) -> None:
        assert self.client is not None
        if profile == 0:
            self.feature_request(Feature.ONBOARD_PROFILES, 0x10, b"\x02")
            return
        if profile < 1 or profile > 15:
            raise ValueError("profile must be 0 or 1..15")
        self.feature_request(Feature.ONBOARD_PROFILES, 0x10, b"\x01")
        self.feature_request(Feature.ONBOARD_PROFILES, 0x30, profile.to_bytes(2, "big"))

    def probe_dpi(self) -> dict[str, str]:
        assert self.client is not None
        result: dict[str, str] = {}
        for fnid in (0x00, 0x10, 0x20, 0x30):
            try:
                reply = self.client.feature_request(Feature.ADJUSTABLE_DPI, fnid)
                result[f"fnid_0x{fnid:02x}"] = reply[:16].hex(" ")
            except Exception as exc:
                result[f"fnid_0x{fnid:02x}"] = f"error: {exc}"
        return result

    def probe_battery(self) -> dict[str, str]:
        assert self.client is not None
        result: dict[str, str] = {}
        for fnid in (0x00, 0x10, 0x20, 0x30):
            try:
                reply = self.client.feature_request(Feature.UNIFIED_BATTERY, fnid)
                result[f"fnid_0x{fnid:02x}"] = reply[:16].hex(" ")
            except Exception as exc:
                result[f"fnid_0x{fnid:02x}"] = f"error: {exc}"
        return result

    def probe_report_rate(self) -> dict[str, str]:
        assert self.client is not None
        result: dict[str, str] = {}
        for fnid in (0x00, 0x10, 0x20, 0x30, 0x40, 0x50):
            try:
                reply = self.client.feature_request(Feature.REPORT_RATE, fnid)
                result[f"fnid_0x{fnid:02x}"] = reply[:16].hex(" ")
            except Exception as exc:
                result[f"fnid_0x{fnid:02x}"] = f"error: {exc}"
        return result

    def probe_report_rate_setters(self) -> list[dict[str, str]]:
        assert self.client is not None
        attempts: list[tuple[int, bytes]] = [
            (0x10, b"\x08"),
            (0x20, b"\x08"),
            (0x20, b"\x00\x08"),
            (0x20, b"\x08\x00"),
            (0x30, b"\x08"),
            (0x30, b"\x00\x08"),
            (0x30, b"\x08\x00"),
        ]
        results: list[dict[str, str]] = []
        for fnid, payload in attempts:
            item = {"fnid": f"0x{fnid:02x}", "payload": payload.hex(" ")}
            try:
                reply = self.feature_request(Feature.REPORT_RATE, fnid, payload, attempts=1)
                item["reply"] = reply[:16].hex(" ")
            except Exception as exc:
                item["reply"] = f"error: {exc}"
            try:
                current = self.feature_request(Feature.REPORT_RATE, 0x10)
                item["current"] = current[:16].hex(" ")
            except Exception as exc:
                item["current"] = f"error: {exc}"
            results.append(item)
        return results


class SuperlightManager:
    def list_hidraw(self, include_all_logitech: bool = False) -> list[HidrawDeviceInfo]:
        return scan_hidraw(include_all_logitech=include_all_logitech)

    def _device_priority(self, info: HidrawDeviceInfo) -> int:
        if info.product_id in RECEIVER_PRODUCT_IDS:
            if ":1.2/" in info.sys_path:
                return 0
            if ":1.1/" in info.sys_path:
                return 1
            if ":1.0/" in info.sys_path:
                return 2
        return 0

    def _candidate_indexes(self, info: HidrawDeviceInfo) -> list[int]:
        if info.product_id in RECEIVER_PRODUCT_IDS:
            return [1, 2, 3, 4, 5, 6, 0xFF]
        return [0xFF, 1]

    def _probe_session(self) -> tuple[SuperlightSession, MouseState] | tuple[None, MouseState]:
        errors: list[str] = []
        for info in sorted(self.list_hidraw(), key=self._device_priority):
            if not info.readable or not info.writable:
                errors.extend([f"{info.dev_node}: {err}" for err in info.errors])
                continue
            for index in self._candidate_indexes(info):
                try:
                    session = SuperlightSession(info, index)
                    session.__enter__()
                    try:
                        state = session.read_state()
                        if any(state.features.values()):
                            return session, state
                        session.__exit__(None, None, None)
                    except Exception:
                        session.__exit__(None, None, None)
                        raise
                except (OSError, HidppException, IndexError, ValueError) as exc:
                    errors.append(f"{info.dev_node} index {index}: {exc}")
        return None, MouseState(online=False, errors=errors, desired=load_config().get("desired", {}))

    def _state_needs_retry(self, state: MouseState) -> bool:
        if not state.online:
            return False
        return (
            (state.features.get("battery") and state.battery_percent is None)
            or (state.features.get("dpi") and state.dpi is None)
            or (state.features.get("report_rate") and state.report_rate is None)
        )

    def status(self) -> MouseState:
        last_state: MouseState | None = None
        for attempt in range(2):
            session, state = self._probe_session()
            if session is not None:
                session.__exit__(None, None, None)
            last_state = state
            if not self._state_needs_retry(state):
                return state
            if attempt == 0:
                time.sleep(0.1)
        assert last_state is not None
        return last_state

    def _raw_status(self) -> MouseState:
        session, state = self._probe_session()
        if session is not None:
            session.__exit__(None, None, None)
        return state

    def doctor(self, include_all_logitech: bool = True) -> dict[str, Any]:
        devices = self.list_hidraw(include_all_logitech=include_all_logitech)
        state = self.status()
        return {
            "config": load_config(),
            "state": state.to_dict(),
            "hidraw": [device.to_dict() for device in devices],
        }

    def probe_dpi(self) -> dict[str, Any]:
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            return {
                "state": state.to_dict(),
                "dpi_probe": session.probe_dpi(),
            }
        finally:
            session.__exit__(None, None, None)

    def probe_battery(self) -> dict[str, Any]:
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            return {
                "state": state.to_dict(),
                "battery_probe": session.probe_battery(),
            }
        finally:
            session.__exit__(None, None, None)

    def probe_report_rate(self) -> dict[str, Any]:
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            return {
                "state": state.to_dict(),
                "report_rate_probe": session.probe_report_rate(),
            }
        finally:
            session.__exit__(None, None, None)

    def probe_report_rate_setters(self) -> dict[str, Any]:
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            return {
                "state": state.to_dict(),
                "report_rate_setter_probe": session.probe_report_rate_setters(),
            }
        finally:
            session.__exit__(None, None, None)

    def set_dpi(self, dpi: int) -> MouseState:
        set_desired("dpi", dpi)
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            session.set_dpi(dpi)
            return session.read_state()
        finally:
            session.__exit__(None, None, None)

    def set_report_rate(self, label: str) -> MouseState:
        applied = label.lower()
        session, state = self._probe_session()
        if session is None:
            set_desired("report_rate", applied)
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            applied = session.set_report_rate(label)
            set_desired("report_rate", applied)
            return session.read_state()
        finally:
            session.__exit__(None, None, None)

    def set_profile(self, profile: int) -> MouseState:
        set_desired("profile", profile)
        session, state = self._probe_session()
        if session is None:
            raise RuntimeError("; ".join(state.errors) or "no Superlight detected")
        try:
            session.set_profile(profile)
            return session.read_state()
        finally:
            session.__exit__(None, None, None)

    def apply_desired(self) -> MouseState:
        desired = load_config().get("desired", {})
        state = self.status()
        if not state.online:
            return state
        if (
            isinstance(desired.get("dpi"), int)
            and state.dpi is not None
            and state.dpi != desired["dpi"]
        ):
            with suppress(Exception):
                state = self.set_dpi(desired["dpi"])
        if (
            isinstance(desired.get("report_rate"), str)
            and state.report_rate is not None
            and state.report_rate != desired["report_rate"]
        ):
            with suppress(Exception):
                state = self.set_report_rate(desired["report_rate"])
        if (
            isinstance(desired.get("profile"), int)
            and state.onboard_profile is not None
            and state.onboard_profile != desired["profile"]
        ):
            with suppress(Exception):
                state = self.set_profile(desired["profile"])
        return state

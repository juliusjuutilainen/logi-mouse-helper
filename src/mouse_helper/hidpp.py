from __future__ import annotations

import errno
import os
import select
import time
from dataclasses import dataclass


HIDPP_SHORT = 0x10
HIDPP_LONG = 0x11
HIDPP_ERROR = 0x8F


class HidppException(Exception):
    """Base HID++ error."""


class HidppTimeout(HidppException):
    """Timed out waiting for a matching HID++ response."""


class HidppProtocolError(HidppException):
    """Device returned a HID++ protocol error."""

    def __init__(self, code: int, message: bytes):
        super().__init__(f"HID++ error 0x{code:02x}: {message.hex(' ')}")
        self.code = code
        self.message = message


@dataclass(slots=True)
class FeatureInfo:
    index: int
    feature: int
    kind: int | None = None
    version: int | None = None


class HidrawTransport:
    def __init__(self, path: str, timeout: float = 0.75):
        self.path = path
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self) -> "HidrawTransport":
        self.fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK)
        self.flush()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def flush(self) -> None:
        if self.fd is None:
            return
        while True:
            try:
                os.read(self.fd, 64)
            except BlockingIOError:
                return
            except OSError as exc:
                if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    return
                raise

    def write(self, report: bytes) -> None:
        if self.fd is None:
            raise HidppException("transport is not open")
        os.write(self.fd, report)

    def read(self, timeout: float | None = None) -> bytes:
        if self.fd is None:
            raise HidppException("transport is not open")
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HidppTimeout(f"timeout reading {self.path}")
            ready, _, _ = select.select([self.fd], [], [], remaining)
            if not ready:
                raise HidppTimeout(f"timeout reading {self.path}")
            try:
                return os.read(self.fd, 64)
            except BlockingIOError:
                continue


class HidppClient:
    def __init__(self, transport: HidrawTransport, device_index: int):
        self.transport = transport
        self.device_index = device_index
        self._feature_cache: dict[int, FeatureInfo] = {}
        self._software_id = 0

    def request(self, feature_index: int, fnid: int, params: bytes = b"") -> bytes:
        self._software_id = (self._software_id % 0x0F) + 1
        fnid_with_sw = (fnid & 0xF0) | self._software_id
        report_id = HIDPP_SHORT if len(params) <= 3 else HIDPP_LONG
        size = 7 if report_id == HIDPP_SHORT else 20
        payload = bytes([report_id, self.device_index, feature_index, fnid_with_sw]) + params
        report = payload.ljust(size, b"\x00")
        self.transport.flush()
        self.transport.write(report)

        deadline = time.monotonic() + self.transport.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HidppTimeout(
                    f"no response for feature index 0x{feature_index:02x} fnid 0x{fnid:02x}"
                )
            response = self.transport.read(remaining)
            if len(response) < 4 or response[0] not in (HIDPP_SHORT, HIDPP_LONG):
                continue
            if response[1] != self.device_index:
                continue
            if response[2] == HIDPP_ERROR:
                code = response[5] if len(response) > 5 else 0
                raise HidppProtocolError(code, response)
            if response[2] != feature_index:
                continue
            if response[3] != fnid_with_sw:
                continue
            return response[4:]

    def get_feature(self, feature: int) -> FeatureInfo:
        cached = self._feature_cache.get(feature)
        if cached:
            return cached
        response = self.request(0x00, 0x00, feature.to_bytes(2, "big"))
        if not response or response[0] == 0:
            raise HidppException(f"feature 0x{feature:04x} is not available")
        info = FeatureInfo(
            index=response[0],
            feature=feature,
            kind=response[1] if len(response) > 1 else None,
            version=response[2] if len(response) > 2 else None,
        )
        self._feature_cache[feature] = info
        return info

    def feature_request(self, feature: int, fnid: int, params: bytes = b"") -> bytes:
        info = self.get_feature(feature)
        return self.request(info.index, fnid, params)

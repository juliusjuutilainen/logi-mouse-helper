from __future__ import annotations

APP_ID = "io.github.local.mouse-helper"
APP_NAME = "mouse-helper"
SOCKET_NAME = "mouse-helper.sock"

LOGITECH_VENDOR_ID = 0x046D

SUPERLIGHT_USB_IDS = {
    0xC547: "PRO X Superlight LIGHTSPEED receiver",
    0xC094: "PRO X Superlight wired",
    0xC54D: "PRO X 2 LIGHTSPEED receiver",
    0xC09B: "PRO X 2 wired",
}

RECEIVER_PRODUCT_IDS = {0xC547, 0xC54D}
DIRECT_PRODUCT_IDS = {0xC094, 0xC09B}
SUPERLIGHT2_PRODUCT_IDS = {0xC54D, 0xC09B}

WPID_NAMES = {
    "4093": "PRO X Wireless",
    "40A9": "PRO X 2",
}

DPI_PRESETS = [
    600,
    700,
    800,
    900,
    1000,
    1100,
    1200,
    1300,
    1400,
]


class Feature:
    ROOT = 0x0000
    FEATURE_SET = 0x0001
    DEVICE_FW_VERSION = 0x0003
    DEVICE_NAME = 0x0005
    WIRELESS_DEVICE_STATUS = 0x1D4B
    UNIFIED_BATTERY = 0x1004
    ADJUSTABLE_DPI = 0x2201
    EXTENDED_ADJUSTABLE_DPI = 0x2202
    REPORT_RATE = 0x8060
    EXTENDED_REPORT_RATE = 0x8061
    ONBOARD_PROFILES = 0x8100


REPORT_RATE_LABELS = {
    1: "1ms",
    2: "2ms",
    3: "3ms",
    4: "4ms",
    5: "5ms",
    6: "6ms",
    7: "7ms",
    8: "8ms",
}

REPORT_RATE_VALUES = {label: value for value, label in REPORT_RATE_LABELS.items()}
REPORT_RATE_VALUES.update(
    {
        "1000hz": 1,
        "500hz": 2,
        "250hz": 4,
        "125hz": 8,
        "1000": 1,
        "500": 2,
        "250": 4,
        "125": 8,
    }
)

EXTENDED_REPORT_RATE_LABELS = {
    0: "8ms",
    1: "4ms",
    2: "2ms",
    3: "1ms",
    4: "500us",
    5: "250us",
    6: "125us",
}

EXTENDED_REPORT_RATE_VALUES = {
    label: value for value, label in EXTENDED_REPORT_RATE_LABELS.items()
}
EXTENDED_REPORT_RATE_VALUES.update(
    {
        "125hz": 0,
        "250hz": 1,
        "500hz": 2,
        "1000hz": 3,
        "2000hz": 4,
        "4000hz": 5,
        "8000hz": 6,
    }
)

BATTERY_STATUS = {
    0: "discharging",
    1: "charging",
    2: "charging slowly",
    3: "full",
    4: "charging error",
}

BATTERY_LEVEL = {
    0x01: "critical",
    0x02: "low",
    0x04: "good",
    0x08: "full",
}

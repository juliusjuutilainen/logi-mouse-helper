import unittest
from pathlib import Path
from unittest import mock

from mouse_helper.hidraw import _ids_from_hid_id, scan_hidraw


class HidrawTests(unittest.TestCase):
    def test_ids_from_hid_id(self) -> None:
        self.assertEqual(_ids_from_hid_id("0003:0000046D:0000C547"), (0x046D, 0xC547))

    def test_ids_from_bad_hid_id(self) -> None:
        self.assertEqual(_ids_from_hid_id("not-a-hid-id"), (None, None))

    def test_scan_reports_missing_dev_node(self) -> None:
        def fake_read_text(path: Path) -> str | None:
            if path.name == "uevent":
                return "\n".join(
                    [
                        "HID_ID=0003:0000046D:0000C547",
                        "HID_NAME=Logitech USB Receiver",
                    ]
                )
            return None

        entries = [Path("/sys/class/hidraw/hidraw7")]
        def fake_exists(path: Path) -> bool:
            return str(path) != "/dev/hidraw7"

        with (
            mock.patch("mouse_helper.hidraw.Path.exists", fake_exists),
            mock.patch("mouse_helper.hidraw.Path.glob", return_value=entries),
            mock.patch("mouse_helper.hidraw.Path.resolve", return_value=Path("/sys/devices/fake")),
            mock.patch("mouse_helper.hidraw._read_text", side_effect=fake_read_text),
            mock.patch("mouse_helper.hidraw.os.access", return_value=False),
        ):
            devices = scan_hidraw()

        self.assertEqual(devices[0].errors, ["device node missing; reload udev rules and replug"])

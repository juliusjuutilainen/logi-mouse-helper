import unittest

from mouse_helper.superlight import _parse_battery, _parse_dpi


class SuperlightTests(unittest.TestCase):
    def test_parse_dpi_first_word(self) -> None:
        self.assertEqual(_parse_dpi(bytes.fromhex("03 20 00 00")), 800)

    def test_parse_dpi_second_word(self) -> None:
        self.assertEqual(_parse_dpi(bytes.fromhex("00 00 06 40")), 1600)

    def test_parse_dpi_current_default_reply(self) -> None:
        self.assertEqual(_parse_dpi(bytes.fromhex("00 03 20 03 20")), 800)

    def test_parse_dpi_current_default_6400_reply(self) -> None:
        self.assertEqual(_parse_dpi(bytes.fromhex("00 19 00 03 20")), 6400)

    def test_parse_dpi_rejects_empty(self) -> None:
        self.assertIsNone(_parse_dpi(b""))

    def test_parse_unified_battery_status(self) -> None:
        self.assertEqual(_parse_battery(bytes.fromhex("3e 08 00 00")), (62, "discharging"))

    def test_parse_unified_battery_charging(self) -> None:
        self.assertEqual(_parse_battery(bytes.fromhex("40 04 01 01")), (64, "charging"))

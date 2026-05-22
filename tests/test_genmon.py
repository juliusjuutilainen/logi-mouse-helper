import unittest
from pathlib import Path
from unittest import mock

from mouse_helper import genmon


class GenmonTests(unittest.TestCase):
    def test_emit_tag_escapes_xml_content(self) -> None:
        with mock.patch("builtins.print") as print_mock:
            genmon._emit_tag("tool", "A&B < C")

        print_mock.assert_called_once_with("<tool>A&amp;B &lt; C</tool>")

    def test_command_prefers_path_lookup(self) -> None:
        with (
            mock.patch("pathlib.Path.home", return_value=Path("/home/user")),
            mock.patch("pathlib.Path.exists", return_value=False),
            mock.patch("shutil.which", return_value="/usr/bin/mouse-helper-menu"),
        ):
            self.assertEqual(
                genmon._command("mouse-helper-menu"),
                "/usr/bin/mouse-helper-menu",
            )

    def test_command_falls_back_to_name(self) -> None:
        with (
            mock.patch("pathlib.Path.exists", return_value=False),
            mock.patch("shutil.which", return_value=None),
        ):
            self.assertEqual(genmon._command("mouse-helper-menu"), "mouse-helper-menu")

    def test_command_prefers_local_bin(self) -> None:
        with (
            mock.patch("pathlib.Path.home", return_value=Path("/home/user")),
            mock.patch("pathlib.Path.exists", return_value=True),
        ):
            self.assertEqual(
                genmon._command("mouse-helper-menu"),
                "/home/user/.local/bin/mouse-helper-menu",
            )

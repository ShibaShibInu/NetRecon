"""test_display_options.py - tests for show_ipv4, show_ipv6 and show_meta in display.py (QA: Justin).

No internet is used. The printed output is captured in memory.
"""

import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import display as display_module  # noqa: E402

NA = "Not available"
V4 = "203.0.113.10"
V6 = "2001:db8::1"
GOOD_META = {"city": "Quezon City", "region": "Metro Manila",
             "country": "Philippines", "country_code": "PH",
             "org": "Example ISP", "asn": "AS64500"}
STATUS = "IPv4 and IPv6 detected"
ADDRESS_LABELS = ("Public IPv4", "Public IPv6")
META_LABELS = ("Network / Org", "ASN", "City", "Region", "Country", "Country Code")


def capture(**options):
    """Call display() with the given show options and return (result, printed text)."""
    buf = io.StringIO()
    with patch.dict(os.environ, {"COLUMNS": "120"}), contextlib.redirect_stdout(buf):
        result = display_module.display(V4, V6, GOOD_META, STATUS, **options)
    return result, buf.getvalue()


def content_rows(text):
    """Return the text of each line inside the panel, without the box lines."""
    rows = []
    for line in text.splitlines():
        if line.startswith("│"):
            rows.append(line.strip("│ ").strip())
    return rows


class TestDefaults(unittest.TestCase):

    def test_everything_is_shown_by_default(self):
        _, text = capture()
        for label in ADDRESS_LABELS + META_LABELS + ("Status",):
            self.assertIn(label, text)

    def test_options_set_to_true_give_the_same_output(self):
        _, default = capture()
        _, explicit = capture(show_ipv4=True, show_ipv6=True, show_meta=True)
        self.assertEqual(default, explicit)

    def test_still_returns_nothing(self):
        result, _ = capture(show_ipv6=False, show_meta=False)
        self.assertIsNone(result)


class TestHideAddresses(unittest.TestCase):

    def test_hide_ipv6_only(self):
        _, text = capture(show_ipv6=False)
        self.assertIn("Public IPv4", text)
        self.assertIn(V4, text)
        self.assertNotIn("Public IPv6", text)
        self.assertNotIn(V6, text)

    def test_hide_ipv4_only(self):
        _, text = capture(show_ipv4=False)
        self.assertIn("Public IPv6", text)
        self.assertIn(V6, text)
        self.assertNotIn("Public IPv4", text)
        self.assertNotIn(V4, text)

    def test_hide_both_addresses_keeps_the_details(self):
        _, text = capture(show_ipv4=False, show_ipv6=False)
        for label in ADDRESS_LABELS:
            self.assertNotIn(label, text)
        for label in META_LABELS:
            self.assertIn(label, text)


class TestHideMeta(unittest.TestCase):

    def test_hide_details_keeps_the_addresses(self):
        _, text = capture(show_meta=False)
        self.assertIn(V4, text)
        self.assertIn(V6, text)
        for label in META_LABELS:
            self.assertNotIn(label, text)
        self.assertNotIn("Quezon City", text)
        self.assertNotIn("AS64500", text)

    def test_ipv4_without_details(self):
        _, text = capture(show_ipv6=False, show_meta=False)
        self.assertIn(V4, text)
        self.assertNotIn("Public IPv6", text)
        self.assertNotIn("Example ISP", text)


class TestStatusAlwaysShown(unittest.TestCase):

    def test_status_is_shown_for_every_combination(self):
        for v4 in (True, False):
            for v6 in (True, False):
                for meta in (True, False):
                    with self.subTest(v4=v4, v6=v6, meta=meta):
                        _, text = capture(show_ipv4=v4, show_ipv6=v6, show_meta=meta)
                        self.assertIn("Status", text)
                        self.assertIn(STATUS, text)

    def test_title_and_subtitle_are_still_there_when_everything_is_hidden(self):
        _, text = capture(show_ipv4=False, show_ipv6=False, show_meta=False)
        self.assertIn("NetRecon - Public IP Information", text)
        self.assertIn("Location is approximate", text)


class TestSpacing(unittest.TestCase):

    def test_no_double_blank_lines_for_any_combination(self):
        for v4 in (True, False):
            for v6 in (True, False):
                for meta in (True, False):
                    with self.subTest(v4=v4, v6=v6, meta=meta):
                        _, text = capture(show_ipv4=v4, show_ipv6=v6, show_meta=meta)
                        rows = content_rows(text)
                        # one blank line at the top and bottom is the panel padding
                        self.assertEqual(rows[0], "")
                        self.assertNotEqual(rows[1], "")
                        self.assertEqual(rows[-1], "")
                        self.assertNotEqual(rows[-2], "")
                        for before, after in zip(rows, rows[1:]):
                            self.assertFalse(before == "" and after == "",
                                             "two blank lines in a row")

    def test_status_follows_the_last_group_after_one_blank_line(self):
        _, text = capture(show_ipv4=False, show_ipv6=False)
        rows = [row for row in content_rows(text)]
        status_at = next(i for i, row in enumerate(rows) if row.startswith("Status"))
        self.assertEqual(rows[status_at - 1], "")
        self.assertTrue(rows[status_at - 2].startswith("Country Code"))


class TestStillSafeWithOptions(unittest.TestCase):

    def test_square_brackets_in_text_are_still_escaped(self):
        buf = io.StringIO()
        meta = dict(GOOD_META, city="[Beta]")
        with patch.dict(os.environ, {"COLUMNS": "120"}), contextlib.redirect_stdout(buf):
            display_module.display(V4, V6, meta, "[red]x[/red]", show_ipv4=False)
        self.assertIn("[Beta]", buf.getvalue())
        self.assertIn("[red]x[/red]", buf.getvalue())

    def test_missing_values_still_show_not_available(self):
        buf = io.StringIO()
        with patch.dict(os.environ, {"COLUMNS": "120"}), contextlib.redirect_stdout(buf):
            display_module.display(None, None, None, STATUS, show_meta=False)
        self.assertEqual(buf.getvalue().count(NA), 2)   # IPv4 and IPv6 rows only

    def test_old_four_argument_call_still_works(self):
        buf = io.StringIO()
        with patch.dict(os.environ, {"COLUMNS": "120"}), contextlib.redirect_stdout(buf):
            display_module.display(V4, V6, GOOD_META, STATUS)
        self.assertIn(V4, buf.getvalue())


if __name__ == "__main__":
    unittest.main()

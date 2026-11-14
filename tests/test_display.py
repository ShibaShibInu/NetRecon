"""test_display.py - unit tests for display.py (QA: Justin).

No internet is used. The printed output is captured in memory.
"""

import contextlib
import io
import os
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import display as display_module  # noqa: E402

NA = "Not available"
V4 = "203.0.113.10"
V6 = "2001:db8::1"
KEYS = ("city", "region", "country", "country_code", "org", "asn")
GOOD_META = {"city": "Quezon City", "region": "Metro Manila",
             "country": "Philippines", "country_code": "PH",
             "org": "Example ISP", "asn": "AS64500"}
ALL_NA = {key: NA for key in KEYS}


def capture(ipv4, ipv6, meta, status):
    """Call display() and return (its return value, the text it printed).

    COLUMNS=120 stops long lines from wrapping, so the checks are reliable.
    """
    buf = io.StringIO()
    with patch.dict(os.environ, {"COLUMNS": "120"}), contextlib.redirect_stdout(buf):
        result = display_module.display(ipv4, ipv6, meta, status)
    return result, buf.getvalue()


class TestFmt(unittest.TestCase):

    def test_none(self):
        self.assertEqual(display_module._fmt(None), "[dim]Not available[/dim]")

    def test_empty_string(self):
        self.assertEqual(display_module._fmt(""), "[dim]Not available[/dim]")

    def test_whitespace(self):
        self.assertEqual(display_module._fmt("   "), "[dim]Not available[/dim]")

    def test_not_available_text(self):
        self.assertEqual(display_module._fmt(NA), "[dim]Not available[/dim]")

    def test_normal_text(self):
        self.assertEqual(display_module._fmt(" Quezon City "), "Quezon City")

    def test_zero_is_a_real_value(self):
        self.assertEqual(display_module._fmt(0), "0")


class TestStatusStyle(unittest.TestCase):

    def test_both_found_is_green(self):
        self.assertEqual(display_module._status_style("IPv4 and IPv6 detected"), "green")

    def test_both_found_but_no_details_is_yellow(self):
        self.assertEqual(display_module._status_style(
            "IPv4 and IPv6 detected; network details not available"), "yellow")

    def test_no_ipv6_is_yellow_not_red(self):
        self.assertEqual(display_module._status_style(
            "IPv4 detected; IPv6 not available"), "yellow")

    def test_no_ipv4_is_yellow(self):
        self.assertEqual(display_module._status_style(
            "IPv6 detected; IPv4 not available"), "yellow")

    def test_odd_input_never_red(self):
        for odd in (None, "", 123, "[red]"):
            self.assertNotEqual(display_module._status_style(odd), "red")


class TestDisplay(unittest.TestCase):

    def test_returns_none(self):
        result, _ = capture(V4, V6, GOOD_META, "IPv4 and IPv6 detected")
        self.assertIsNone(result)

    def test_title_and_all_labels_present(self):
        _, out = capture(V4, V6, GOOD_META, "IPv4 and IPv6 detected")
        self.assertIn("NetRecon - Public IP Information", out)
        for label in ("Public IPv4", "Public IPv6", "Network / Org", "ASN",
                      "City", "Region", "Country", "Country Code", "Status"):
            self.assertIn(label, out)

    def test_all_values_present(self):
        _, out = capture(V4, V6, GOOD_META, "IPv4 and IPv6 detected")
        for value in (V4, V6, "Example ISP", "AS64500", "Quezon City",
                      "Metro Manila", "Philippines", "PH", "IPv4 and IPv6 detected"):
            self.assertIn(value, out)

    def test_missing_ipv6_shows_not_available_on_the_ipv6_row(self):
        _, out = capture(V4, None, GOOD_META, "IPv4 detected; IPv6 not available")
        line = next(l for l in out.splitlines() if "Public IPv6" in l)
        self.assertIn(NA, line)
        self.assertNotIn(V4, line)   # an IPv4 must never appear as IPv6

    def test_missing_ipv4_shows_not_available_on_the_ipv4_row(self):
        _, out = capture(None, V6, ALL_NA, "IPv6 detected; IPv4 not available")
        line = next(l for l in out.splitlines() if "Public IPv4" in l)
        self.assertIn(NA, line)
        self.assertNotIn(V6, line)

    def test_every_missing_value_shows_not_available(self):
        _, out = capture(V4, None, ALL_NA,
                         "IPv4 detected; IPv6 not available; network details not available")
        # IPv6 row + the six metadata rows = 7
        self.assertEqual(out.count(NA), 7)

    def test_meta_none_does_not_crash(self):
        _, out = capture(V4, None, None, "IPv4 detected; IPv6 not available")
        self.assertIn(NA, out)

    def test_meta_empty_dict_does_not_crash(self):
        _, out = capture(V4, V6, {}, "IPv4 and IPv6 detected")
        self.assertIn(NA, out)

    def test_square_brackets_cannot_break_output(self):
        meta = dict(GOOD_META, city="[bold]Evil[/bold]", org="[/bold]")
        _, out = capture(V4, V6, meta, "[red]oops[/red]")
        self.assertIn("[bold]Evil[/bold]", out)
        self.assertIn("[/bold]", out)
        self.assertIn("[red]oops[/red]", out)

    def test_plain_output_has_no_colour_codes(self):
        # Not a terminal here, so rich should switch colour off.
        # (If FORCE_COLOR is set on your PC, this one can fail for that reason.)
        _, out = capture(V4, V6, GOOD_META, "IPv4 and IPv6 detected")
        self.assertNotIn("\x1b", out)

    def test_unicode_text(self):
        meta = dict(GOOD_META, city="São Paulo", region="東京")
        _, out = capture(V4, V6, meta, "IPv4 and IPv6 detected")
        self.assertIn("São Paulo", out)
        self.assertIn("東京", out)

    def test_very_long_value(self):
        meta = dict(GOOD_META, org="A" * 60)
        _, out = capture(V4, V6, meta, "IPv4 and IPv6 detected")
        self.assertIn("A" * 60, out)


class TestStress(unittest.TestCase):
    """Throw 500 random garbage inputs at display(). It must never crash."""

    def test_fuzz_never_crashes(self):
        rnd = random.Random(42)  # fixed seed = repeatable
        junk = [None, "", " ", "x", 0, 1, 3.14, True, [], {}, [1], {"a": 1},
                "😀", "[bold]", "[/bold]", "[/]", "[", "]", "\\", "[red]x",
                V4, V6, NA]
        for _ in range(500):
            meta = rnd.choice([None, {}, {key: rnd.choice(junk) for key in KEYS}])
            result, out = capture(rnd.choice(junk), rnd.choice(junk),
                                  meta, rnd.choice(junk))
            self.assertIsNone(result)
            self.assertIn("NetRecon - Public IP Information", out)


if __name__ == "__main__":
    unittest.main()
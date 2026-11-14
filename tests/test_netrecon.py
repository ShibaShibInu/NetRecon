"""test_netrecon.py - unit tests for netrecon.py (QA: Justin).

All tests use MOCKED (fake) detection, metadata and display functions.
No internet is used.
"""

import contextlib
import io
import os
import random
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import netrecon  # noqa: E402

NA = "Not available"
V4 = "203.0.113.10"
V6 = "2001:db8::1"
KEYS = ("city", "region", "country", "country_code", "org", "asn")
ALL_NA = {key: NA for key in KEYS}
GOOD_META = {"city": "Quezon City", "region": "Metro Manila",
             "country": "Philippines", "country_code": "PH",
             "org": "Example ISP", "asn": "AS64500"}
NO_ADDRESS_MSG = "No public IP address detected. Check your internet connection."


def run_main(ipv4=V4, ipv6=V6, meta=GOOD_META, argv=None):
    """Run netrecon.main() with everything mocked.

    Returns an object with: code (exit code), out (printed text), and the
    mocks v4, v6, meta, display so tests can check how they were called.
    """
    buf = io.StringIO()
    with patch.object(sys, "argv", argv or ["netrecon"]), \
            patch("netrecon.get_public_ipv4", return_value=ipv4) as p4, \
            patch("netrecon.get_public_ipv6", return_value=ipv6) as p6, \
            patch("netrecon.get_metadata", return_value=meta) as pm, \
            patch("netrecon.display") as pd, \
            contextlib.redirect_stdout(buf):
        code = netrecon.main()
    return SimpleNamespace(code=code, out=buf.getvalue(),
                           v4=p4, v6=p6, meta=pm, display=pd)


class TestPickStatus(unittest.TestCase):

    def test_both_found(self):
        self.assertEqual(netrecon.pick_status(V4, V6, GOOD_META),
                         "IPv4 and IPv6 detected")

    def test_ipv4_only(self):
        self.assertEqual(netrecon.pick_status(V4, None, GOOD_META),
                         "IPv4 detected; IPv6 not available")

    def test_ipv6_only(self):
        self.assertEqual(netrecon.pick_status(None, V6, ALL_NA),
                         "IPv6 detected; IPv4 not available")

    def test_ipv4_only_and_no_details(self):
        self.assertEqual(netrecon.pick_status(V4, None, ALL_NA),
                         "IPv4 detected; IPv6 not available; network details not available")

    def test_both_found_and_no_details(self):
        self.assertEqual(netrecon.pick_status(V4, V6, ALL_NA),
                         "IPv4 and IPv6 detected; network details not available")

    def test_ipv6_only_never_adds_details_note(self):
        # The note is only for when an IPv4 was found (contract, section 6).
        self.assertNotIn("network details", netrecon.pick_status(None, V6, ALL_NA))

    def test_partial_metadata_is_not_flagged(self):
        meta = dict(ALL_NA, city="Quezon City")
        self.assertEqual(netrecon.pick_status(V4, None, meta),
                         "IPv4 detected; IPv6 not available")


class TestMain(unittest.TestCase):

    def test_both_found(self):
        r = run_main()
        self.assertEqual(r.code, 0)
        r.display.assert_called_once_with(V4, V6, GOOD_META, "IPv4 and IPv6 detected")

    def test_ipv6_missing_is_still_success(self):
        r = run_main(ipv6=None)
        self.assertEqual(r.code, 0)
        r.display.assert_called_once_with(V4, None, GOOD_META,
                                          "IPv4 detected; IPv6 not available")

    def test_ipv4_missing_is_still_success(self):
        r = run_main(ipv4=None, meta=ALL_NA)
        self.assertEqual(r.code, 0)
        r.meta.assert_called_once_with(None)
        r.display.assert_called_once_with(None, V6, ALL_NA,
                                          "IPv6 detected; IPv4 not available")

    def test_neither_found_exits_1(self):
        r = run_main(ipv4=None, ipv6=None, meta=ALL_NA)
        self.assertEqual(r.code, 1)
        self.assertIn(NO_ADDRESS_MSG, r.out)
        r.display.assert_not_called()

    def test_metadata_failed_adds_note(self):
        r = run_main(meta=ALL_NA)
        self.assertEqual(r.code, 0)
        r.display.assert_called_once_with(
            V4, V6, ALL_NA, "IPv4 and IPv6 detected; network details not available")

    def test_call_order(self):
        order = []

        def f4():
            order.append("ipv4")
            return V4

        def f6():
            order.append("ipv6")
            return V6

        def fm(ip):
            order.append("meta")
            return GOOD_META

        def fd(*args):
            order.append("display")

        with patch.object(sys, "argv", ["netrecon"]), \
                patch("netrecon.get_public_ipv4", side_effect=f4), \
                patch("netrecon.get_public_ipv6", side_effect=f6), \
                patch("netrecon.get_metadata", side_effect=fm), \
                patch("netrecon.display", side_effect=fd):
            netrecon.main()
        self.assertEqual(order, ["ipv4", "ipv6", "meta", "display"])

    def test_help_prints_usage_and_exits_0(self):
        buf = io.StringIO()
        with patch.object(sys, "argv", ["netrecon", "--help"]), \
                patch("netrecon.get_public_ipv4") as p4, \
                patch("netrecon.get_public_ipv6") as p6, \
                contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                netrecon.main()
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("usage: netrecon", buf.getvalue())
        p4.assert_not_called()   # --help must not touch the network
        p6.assert_not_called()

    def test_unknown_flag_exits_2_calmly(self):
        err = io.StringIO()
        with patch.object(sys, "argv", ["netrecon", "--bogus"]), \
                patch("netrecon.get_public_ipv4") as p4, \
                contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                netrecon.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("usage", err.getvalue().lower())
        p4.assert_not_called()

    def test_help_from_the_real_command_line(self):
        """Runs `python netrecon.py --help` as a real process (no internet needed)."""
        result = subprocess.run([sys.executable, os.path.join(ROOT, "netrecon.py"), "--help"],
                                capture_output=True, text=True, timeout=30, cwd=ROOT)
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage", result.stdout.lower())


class TestStress(unittest.TestCase):
    """Run main() 500 times with random found/missing combinations."""

    def test_random_combinations(self):
        rnd = random.Random(42)  # fixed seed = repeatable
        allowed = {
            "IPv4 and IPv6 detected",
            "IPv4 and IPv6 detected; network details not available",
            "IPv4 detected; IPv6 not available",
            "IPv4 detected; IPv6 not available; network details not available",
            "IPv6 detected; IPv4 not available",
        }
        for _ in range(500):
            ipv4 = rnd.choice([None, V4])
            ipv6 = rnd.choice([None, V6])
            meta = rnd.choice([ALL_NA, GOOD_META])
            r = run_main(ipv4=ipv4, ipv6=ipv6, meta=meta)
            if ipv4 is None and ipv6 is None:
                self.assertEqual(r.code, 1)
                r.display.assert_not_called()
            else:
                self.assertEqual(r.code, 0)
                shown_ipv4, shown_ipv6, _, status = r.display.call_args[0]
                self.assertEqual((shown_ipv4, shown_ipv6), (ipv4, ipv6))
                self.assertIn(status, allowed)


if __name__ == "__main__":
    unittest.main()
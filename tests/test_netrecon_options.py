"""test_netrecon_options.py - tests for the new options in netrecon.py (QA: Justin).

Covers --ipv4, --ipv6, --no-metadata, --json, --lookup and -o.
All tests use MOCKED (fake) detection and metadata functions. No internet is used.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
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
JSON_KEYS = ["ipv4", "ipv6", "city", "region", "country", "country_code",
             "org", "asn", "status"]
NO_ADDRESS_MSG = "No public IP address detected. Check your internet connection."


def run_main(argv, ipv4=V4, ipv6=V6, meta=GOOD_META, mock_display=True):
    """Run netrecon.main() with the given command line and fake lookups.

    Returns an object with: code, out (printed text), err (error text) and the
    mocks v4, v6, meta, display so tests can check how they were called.
    """
    out, err = io.StringIO(), io.StringIO()
    with patch.dict(os.environ, {"COLUMNS": "120"}), \
            patch.object(sys, "argv", ["netrecon"] + argv), \
            patch("netrecon.get_public_ipv4", return_value=ipv4) as p4, \
            patch("netrecon.get_public_ipv6", return_value=ipv6) as p6, \
            patch("netrecon.get_metadata", return_value=meta) as pm, \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        if mock_display:
            with patch("netrecon.display") as pd:
                code = netrecon.main()
        else:
            pd = None
            code = netrecon.main()
    return SimpleNamespace(code=code, out=out.getvalue(), err=err.getvalue(),
                           v4=p4, v6=p6, meta=pm, display=pd)


def exit_code_of(argv):
    """Run main() with options that argparse refuses and return the exit code."""
    with patch.object(sys, "argv", ["netrecon"] + argv), \
            patch("netrecon.get_public_ipv4") as p4, \
            patch("netrecon.get_public_ipv6") as p6, \
            contextlib.redirect_stderr(io.StringIO()):
        with unittest.TestCase().assertRaises(SystemExit) as cm:
            netrecon.main()
    assert not p4.called and not p6.called  # nothing was looked up
    return cm.exception.code


class TestPickStatusNoMetadata(unittest.TestCase):

    def test_no_note_when_details_were_not_wanted(self):
        self.assertEqual(netrecon.pick_status(V4, V6, ALL_NA, no_metadata=True),
                         "IPv4 and IPv6 detected")

    def test_note_still_added_by_default(self):
        self.assertEqual(netrecon.pick_status(V4, V6, ALL_NA),
                         "IPv4 and IPv6 detected; network details not available")


class TestIpv4Option(unittest.TestCase):

    def test_only_asks_for_ipv4(self):
        r = run_main(["--ipv4"])
        self.assertEqual(r.code, 0)
        r.v4.assert_called_once()
        r.v6.assert_not_called()
        r.meta.assert_called_once_with(V4)

    def test_hides_the_ipv6_row(self):
        r = run_main(["--ipv4"])
        r.display.assert_called_once_with(V4, None, GOOD_META, "IPv4 detected",
                                          show_ipv6=False)

    def test_no_ipv4_found_exits_1(self):
        r = run_main(["--ipv4"], ipv4=None, meta=ALL_NA)
        self.assertEqual(r.code, 1)
        self.assertIn(NO_ADDRESS_MSG, r.out)
        r.display.assert_not_called()

    def test_failed_details_add_a_note(self):
        r = run_main(["--ipv4"], meta=ALL_NA)
        r.display.assert_called_once_with(
            V4, None, ALL_NA, "IPv4 detected; network details not available",
            show_ipv6=False)


class TestIpv6Option(unittest.TestCase):

    def test_only_asks_for_ipv6(self):
        r = run_main(["--ipv6"])
        self.assertEqual(r.code, 0)
        r.v6.assert_called_once()
        r.v4.assert_not_called()
        r.meta.assert_called_once_with(V6)

    def test_hides_the_ipv4_row(self):
        r = run_main(["--ipv6"])
        r.display.assert_called_once_with(None, V6, GOOD_META, "IPv6 detected",
                                          show_ipv4=False)

    def test_no_ipv6_found_exits_1(self):
        # A network without IPv6 is normal, but with --ipv6 there is nothing to show.
        r = run_main(["--ipv6"], ipv6=None, meta=ALL_NA)
        self.assertEqual(r.code, 1)
        self.assertIn(NO_ADDRESS_MSG, r.out)
        r.display.assert_not_called()


class TestNoMetadataOption(unittest.TestCase):

    def test_makes_no_details_request(self):
        r = run_main(["--no-metadata"], meta=ALL_NA)
        self.assertEqual(r.code, 0)
        r.meta.assert_called_once_with(None)   # None means no request is made

    def test_hides_the_details_and_skips_the_note(self):
        r = run_main(["--no-metadata"], meta=ALL_NA)
        r.display.assert_called_once_with(V4, V6, ALL_NA, "IPv4 and IPv6 detected",
                                          show_meta=False)

    def test_works_together_with_ipv4(self):
        r = run_main(["--ipv4", "--no-metadata"], meta=ALL_NA)
        r.v6.assert_not_called()
        r.display.assert_called_once_with(V4, None, ALL_NA, "IPv4 detected",
                                          show_ipv6=False, show_meta=False)


class TestJsonOption(unittest.TestCase):

    def test_prints_valid_json_with_the_nine_keys(self):
        r = run_main(["--json"])
        self.assertEqual(r.code, 0)
        data = json.loads(r.out)
        self.assertEqual(list(data), JSON_KEYS)
        self.assertEqual(data["ipv4"], V4)
        self.assertEqual(data["ipv6"], V6)
        self.assertEqual(data["city"], "Quezon City")
        self.assertEqual(data["status"], "IPv4 and IPv6 detected")

    def test_does_not_use_the_formatted_report(self):
        r = run_main(["--json"])
        r.display.assert_not_called()

    def test_with_ipv4_the_ipv6_is_not_available(self):
        data = json.loads(run_main(["--json", "--ipv4"]).out)
        self.assertEqual(data["ipv4"], V4)
        self.assertEqual(data["ipv6"], NA)
        self.assertEqual(data["status"], "IPv4 detected")

    def test_with_no_metadata_the_details_are_not_available(self):
        data = json.loads(run_main(["--json", "--no-metadata"], meta=ALL_NA).out)
        for key in KEYS:
            self.assertEqual(data[key], NA)

    def test_nothing_found_prints_no_json(self):
        r = run_main(["--json"], ipv4=None, ipv6=None, meta=ALL_NA)
        self.assertEqual(r.code, 1)
        self.assertIn(NO_ADDRESS_MSG, r.out)


class TestBadCombinations(unittest.TestCase):

    def test_ipv4_and_ipv6_together_exit_2(self):
        self.assertEqual(exit_code_of(["--ipv4", "--ipv6"]), 2)

    def test_lookup_and_ipv4_together_exit_2(self):
        self.assertEqual(exit_code_of(["--lookup", "8.8.8.8", "--ipv4"]), 2)

    def test_lookup_and_ipv6_together_exit_2(self):
        self.assertEqual(exit_code_of(["--lookup", "8.8.8.8", "--ipv6"]), 2)

    def test_lookup_without_an_address_exit_2(self):
        self.assertEqual(exit_code_of(["--lookup"]), 2)


class TestLookupOption(unittest.TestCase):

    def test_public_ipv4(self):
        r = run_main(["--lookup", "8.8.8.8"])
        self.assertEqual(r.code, 0)
        r.meta.assert_called_once_with("8.8.8.8")
        r.display.assert_called_once_with("8.8.8.8", None, GOOD_META,
                                          "Lookup for 8.8.8.8")

    def test_public_ipv6(self):
        r = run_main(["--lookup", "2001:4860:4860::8888"])
        r.meta.assert_called_once_with("2001:4860:4860::8888")
        r.display.assert_called_once_with(None, "2001:4860:4860::8888", GOOD_META,
                                          "Lookup for 2001:4860:4860::8888")

    def test_never_detects_our_own_address(self):
        r = run_main(["--lookup", "8.8.8.8"])
        r.v4.assert_not_called()
        r.v6.assert_not_called()

    def test_private_address_makes_no_request(self):
        for address in ("192.168.1.5", "10.0.0.1", "127.0.0.1", "169.254.1.1", "::1"):
            with self.subTest(address=address):
                r = run_main(["--lookup", address], meta=ALL_NA)
                self.assertEqual(r.code, 0)
                r.meta.assert_called_once_with(None)
                status = r.display.call_args.args[3]
                self.assertIn("private or reserved address", status)

    def test_spaces_and_upper_case_are_cleaned(self):
        r = run_main(["--lookup", "  2001:DB8::1  "], meta=ALL_NA)
        self.assertEqual(r.display.call_args.args[1], "2001:db8::1")

    def test_invalid_address_exits_2_with_a_message(self):
        for bad in ("nope", "999.1.1.1", "8.8.8.8:80", "1.2.3", "example.com"):
            with self.subTest(bad=bad):
                r = run_main(["--lookup", bad])
                self.assertEqual(r.code, 2)
                self.assertIn("is not a valid IP address", r.err)
                r.meta.assert_not_called()
                r.display.assert_not_called()

    def test_failed_details_add_a_note(self):
        r = run_main(["--lookup", "8.8.8.8"], meta=ALL_NA)
        self.assertEqual(r.display.call_args.args[3],
                         "Lookup for 8.8.8.8; network details not available")

    def test_with_no_metadata_makes_no_request(self):
        r = run_main(["--lookup", "8.8.8.8", "--no-metadata"], meta=ALL_NA)
        r.meta.assert_called_once_with(None)
        r.display.assert_called_once_with("8.8.8.8", None, ALL_NA,
                                          "Lookup for 8.8.8.8", show_meta=False)

    def test_with_json(self):
        data = json.loads(run_main(["--lookup", "8.8.8.8", "--json"]).out)
        self.assertEqual(data["ipv4"], "8.8.8.8")
        self.assertEqual(data["ipv6"], NA)
        self.assertEqual(data["status"], "Lookup for 8.8.8.8")


class TestOutputOption(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "report.txt")

    def read(self, path=None):
        with open(path or self.path, encoding="utf-8") as file:
            return file.read()

    def test_saves_the_report_instead_of_printing_it(self):
        r = run_main(["-o", self.path], mock_display=False)
        self.assertEqual(r.code, 0)
        self.assertEqual(r.out.strip(), f"Saved to {self.path}")
        text = self.read()
        self.assertIn("Public IPv4", text)
        self.assertIn(V4, text)
        self.assertIn("Quezon City", text)

    def test_long_option_name_works_too(self):
        r = run_main(["--output", self.path], mock_display=False)
        self.assertEqual(r.code, 0)
        self.assertTrue(os.path.exists(self.path))

    def test_saves_json_when_asked(self):
        r = run_main(["--json", "-o", self.path])
        self.assertEqual(r.code, 0)
        self.assertEqual(json.loads(self.read())["ipv4"], V4)

    def test_saved_report_follows_the_other_options(self):
        run_main(["--ipv4", "--no-metadata", "-o", self.path], mock_display=False)
        text = self.read()
        self.assertIn(V4, text)
        self.assertNotIn("Public IPv6", text)
        self.assertNotIn("Quezon City", text)

    def test_works_with_lookup(self):
        r = run_main(["--lookup", "8.8.8.8", "-o", self.path], mock_display=False)
        self.assertEqual(r.code, 0)
        self.assertIn("8.8.8.8", self.read())

    def test_file_has_no_colour_codes(self):
        run_main(["-o", self.path], mock_display=False)
        self.assertNotIn("\x1b", self.read())

    def test_overwrites_an_old_file(self):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("old text")
        run_main(["-o", self.path], mock_display=False)
        self.assertNotIn("old text", self.read())

    def test_bad_path_exits_2_with_a_message(self):
        bad = os.path.join(self.folder.name, "no_such_folder", "report.txt")
        r = run_main(["-o", bad], mock_display=False)
        self.assertEqual(r.code, 2)
        self.assertIn("Could not save to", r.err)
        self.assertNotIn("Saved to", r.out)

    def test_nothing_found_creates_no_file(self):
        r = run_main(["-o", self.path], ipv4=None, ipv6=None, meta=ALL_NA)
        self.assertEqual(r.code, 1)
        self.assertFalse(os.path.exists(self.path))

    def test_without_o_nothing_is_saved(self):
        before = os.listdir(self.folder.name)
        run_main([], mock_display=False)
        self.assertEqual(os.listdir(self.folder.name), before)


if __name__ == "__main__":
    unittest.main()

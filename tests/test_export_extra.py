"""test_export_extra.py - extra tests for export.py build_json (QA: Justin).

Fake data only. No internet is used.
"""

import contextlib
import copy
import io
import json
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from export import build_json  # noqa: E402

NA = "Not available"
V4 = "203.0.113.10"
V6 = "2001:db8::1"
META_KEYS = ["city", "region", "country", "country_code", "org", "asn"]
EXPECTED_KEYS = ["ipv4", "ipv6"] + META_KEYS + ["status"]
GOOD_META = {"city": "Quezon City", "region": "Metro Manila",
             "country": "Philippines", "country_code": "PH",
             "org": "Example ISP", "asn": "AS64500"}
STATUS = "IPv4 and IPv6 detected"


class TestBuildJsonExtra(unittest.TestCase):

    def test_keys_are_in_the_agreed_order(self):
        data = json.loads(build_json(V4, V6, GOOD_META, STATUS))
        self.assertEqual(list(data), EXPECTED_KEYS)

    def test_one_address_missing_keeps_the_other(self):
        only_v4 = json.loads(build_json(V4, None, GOOD_META, "x"))
        only_v6 = json.loads(build_json(None, V6, GOOD_META, "x"))
        self.assertEqual((only_v4["ipv4"], only_v4["ipv6"]), (V4, NA))
        self.assertEqual((only_v6["ipv4"], only_v6["ipv6"]), (NA, V6))

    def test_extra_meta_keys_are_ignored(self):
        meta = dict(GOOD_META, secret="x", latitude=1.5)
        data = json.loads(build_json(V4, V6, meta, STATUS))
        self.assertEqual(list(data), EXPECTED_KEYS)

    def test_square_brackets_are_kept(self):
        meta = dict(GOOD_META, city="[bold]Evil[/bold]")
        data = json.loads(build_json(V4, V6, meta, "[red]x[/red]"))
        self.assertEqual(data["city"], "[bold]Evil[/bold]")
        self.assertEqual(data["status"], "[red]x[/red]")

    def test_does_not_change_the_meta_it_was_given(self):
        meta = dict(GOOD_META)
        before = copy.deepcopy(meta)
        build_json(V4, V6, meta, STATUS)
        self.assertEqual(meta, before)

    def test_prints_nothing(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            build_json(V4, V6, GOOD_META, STATUS)
        self.assertEqual(buf.getvalue(), "")

    def test_non_ascii_is_readable_in_the_raw_text(self):
        # Aaron's test reads the JSON back, so it cannot tell if the text was
        # turned into \u00e3 escapes. This checks the raw string a user sees.
        meta = dict(GOOD_META, city="São Paulo", region="東京")
        text = build_json(V4, V6, meta, STATUS)
        self.assertIn("São Paulo", text)
        self.assertIn("東京", text)

    def test_missing_status_becomes_not_available(self):
        for missing in (None, ""):
            data = json.loads(build_json(V4, V6, GOOD_META, missing))
            self.assertEqual(data["status"], NA)

    def test_meta_given_as_a_list_does_not_crash(self):
        data = json.loads(build_json(V4, V6, [("city", "x")], STATUS))
        self.assertEqual(data["city"], NA)


class TestStress(unittest.TestCase):
    """Throw 2000 random inputs at build_json. It must never crash."""

    def test_fuzz_never_crashes_and_keeps_the_keys(self):
        rnd = random.Random(42)  # fixed seed = repeatable
        junk = [None, "", " ", "x", 0, 1, -5, 3.14, True, False, [], {}, [1],
                {"a": 1}, "😀", "[bold]", "\\", '"', V4, V6, NA]
        for _ in range(2000):
            meta = rnd.choice([None, {}, junk[3], [1],
                               {key: rnd.choice(junk) for key in META_KEYS}])
            text = build_json(rnd.choice(junk), rnd.choice(junk), meta, rnd.choice(junk))
            data = json.loads(text)
            self.assertEqual(list(data), EXPECTED_KEYS)


if __name__ == "__main__":
    unittest.main()
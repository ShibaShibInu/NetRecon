# Owner: Aaron Yumul (tests for build_json). No internet needed.
import json
import unittest

from export import build_json

META = {
    "city": "Mountain View",
    "region": "California",
    "country": "United States",
    "country_code": "US",
    "org": "Google LLC",
    "asn": "AS15169",
}
EXPECTED_KEYS = ["ipv4", "ipv6", "city", "region", "country",
                 "country_code", "org", "asn", "status"]


class TestBuildJson(unittest.TestCase):
    def test_returns_a_string_that_parses(self):
        out = build_json("8.8.8.8", "2001:db8::1", META, "OK")
        self.assertIsInstance(out, str)
        self.assertIsInstance(json.loads(out), dict)

    def test_has_exactly_the_expected_keys(self):
        data = json.loads(build_json("8.8.8.8", None, META, "OK"))
        self.assertEqual(sorted(data), sorted(EXPECTED_KEYS))

    def test_values_are_copied(self):
        data = json.loads(build_json("8.8.8.8", "2001:db8::1", META, "OK"))
        self.assertEqual(data["ipv4"], "8.8.8.8")
        self.assertEqual(data["ipv6"], "2001:db8::1")
        self.assertEqual(data["asn"], "AS15169")
        self.assertEqual(data["status"], "OK")

    def test_none_ips_become_not_available(self):
        data = json.loads(build_json(None, None, META, "OK"))
        self.assertEqual(data["ipv4"], "Not available")
        self.assertEqual(data["ipv6"], "Not available")

    def test_missing_meta_keys(self):
        data = json.loads(build_json("8.8.8.8", None, {"city": "Paris"}, "OK"))
        self.assertEqual(data["city"], "Paris")
        self.assertEqual(data["org"], "Not available")

    def test_meta_none_or_wrong_type(self):
        for bad in (None, "text", 5):
            data = json.loads(build_json("8.8.8.8", None, bad, "OK"))
            self.assertEqual(data["country"], "Not available")

    def test_empty_values_become_not_available(self):
        meta = dict(META, city="", org=None)
        data = json.loads(build_json("8.8.8.8", None, meta, "OK"))
        self.assertEqual(data["city"], "Not available")
        self.assertEqual(data["org"], "Not available")

    def test_non_ascii_city_is_kept(self):
        data = json.loads(build_json("8.8.8.8", None, dict(META, city="São Paulo"), "OK"))
        self.assertEqual(data["city"], "São Paulo")


if __name__ == "__main__":
    unittest.main()

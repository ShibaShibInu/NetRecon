"""test_metadata.py - unit tests for metadata.py (QA: Justin).

All tests use MOCKED (fake) API replies. No internet is used.
"""

import os
import random
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import metadata  

NA = "Not available"
KEYS = {"city", "region", "country", "country_code", "org", "asn"}

GOOD = {
    "success": True,
    "city": "Quezon City",
    "region": "Metro Manila",
    "country": "Philippines",
    "country_code": "PH",
    "connection": {"asn": 64500, "org": "Example Org", "isp": "Example ISP"},
}


def fake_response(json_data=None, http_error=None, json_error=None):
    """Build a fake requests response."""
    resp = MagicMock()
    if http_error:
        resp.raise_for_status.side_effect = http_error
    if json_error:
        resp.json.side_effect = json_error
    else:
        resp.json.return_value = json_data
    return resp


@patch("metadata.requests.get")
class TestGetMetadata(unittest.TestCase):

    def test_full_success(self, mock_get):
        mock_get.return_value = fake_response(GOOD)
        meta = metadata.get_metadata("203.0.113.10")
        self.assertEqual(meta, {
            "city": "Quezon City", "region": "Metro Manila",
            "country": "Philippines", "country_code": "PH",
            "org": "Example Org", "asn": "AS64500"})

    def test_exactly_six_keys(self, mock_get):
        mock_get.return_value = fake_response(GOOD)
        self.assertEqual(set(metadata.get_metadata("1.2.3.4")), KEYS)

    def test_uses_5_second_timeout_and_right_url(self, mock_get):
        mock_get.return_value = fake_response(GOOD)
        metadata.get_metadata("203.0.113.10")
        mock_get.assert_called_once_with("https://ipwho.is/203.0.113.10", timeout=5)

    def test_none_input_makes_no_request(self, mock_get):
        meta = metadata.get_metadata(None)
        self.assertEqual(set(meta.values()), {NA})
        mock_get.assert_not_called()

    def test_empty_string_input(self, mock_get):
        self.assertEqual(set(metadata.get_metadata("").values()), {NA})
        mock_get.assert_not_called()

    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_http_429_rate_limit(self, mock_get):
        mock_get.return_value = fake_response(http_error=requests.HTTPError("429"))
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_http_500(self, mock_get):
        mock_get.return_value = fake_response(http_error=requests.HTTPError("500"))
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_bad_json(self, mock_get):
        mock_get.return_value = fake_response(json_error=ValueError("bad json"))
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_success_false(self, mock_get):
        mock_get.return_value = fake_response({"success": False, "message": "Invalid IP"})
        self.assertEqual(set(metadata.get_metadata("192.168.1.5").values()), {NA})

    def test_success_missing(self, mock_get):
        data = dict(GOOD); del data["success"]
        mock_get.return_value = fake_response(data)
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_success_is_string_true_rejected(self, mock_get):
        data = dict(GOOD); data["success"] = "true"
        mock_get.return_value = fake_response(data)
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_json_is_a_list_not_dict(self, mock_get):
        mock_get.return_value = fake_response([1, 2, 3])
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_json_is_null(self, mock_get):
        mock_get.return_value = fake_response(None)
        self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})

    def test_missing_city_only(self, mock_get):
        data = dict(GOOD); del data["city"]
        mock_get.return_value = fake_response(data)
        meta = metadata.get_metadata("1.2.3.4")
        self.assertEqual(meta["city"], NA)
        self.assertEqual(meta["country"], "Philippines")

    def test_blank_and_whitespace_values(self, mock_get):
        data = dict(GOOD); data["city"] = ""; data["region"] = "   "; data["country"] = None
        mock_get.return_value = fake_response(data)
        meta = metadata.get_metadata("1.2.3.4")
        self.assertEqual((meta["city"], meta["region"], meta["country"]), (NA, NA, NA))

    def test_no_connection_object(self, mock_get):
        data = dict(GOOD); del data["connection"]
        mock_get.return_value = fake_response(data)
        meta = metadata.get_metadata("1.2.3.4")
        self.assertEqual((meta["org"], meta["asn"]), (NA, NA))
        self.assertEqual(meta["city"], "Quezon City")

    def test_connection_not_a_dict(self, mock_get):
        data = dict(GOOD); data["connection"] = "oops"
        mock_get.return_value = fake_response(data)
        meta = metadata.get_metadata("1.2.3.4")
        self.assertEqual((meta["org"], meta["asn"]), (NA, NA))

    def test_org_falls_back_to_isp(self, mock_get):
        data = dict(GOOD); data["connection"] = {"asn": 15169, "org": "", "isp": "Backup ISP"}
        mock_get.return_value = fake_response(data)
        self.assertEqual(metadata.get_metadata("1.2.3.4")["org"], "Backup ISP")

    def test_org_and_isp_both_missing(self, mock_get):
        data = dict(GOOD); data["connection"] = {"asn": 15169}
        mock_get.return_value = fake_response(data)
        self.assertEqual(metadata.get_metadata("1.2.3.4")["org"], NA)

    def test_asn_missing(self, mock_get):
        data = dict(GOOD); data["connection"] = {"org": "X"}
        mock_get.return_value = fake_response(data)
        self.assertEqual(metadata.get_metadata("1.2.3.4")["asn"], NA)

    def test_asn_formats(self, mock_get):
        for raw, expected in [(15169, "AS15169"), ("15169", "AS15169"), (0, "AS0"), ("", NA), (None, NA)]:
            data = dict(GOOD); data["connection"] = {"asn": raw, "org": "X"}
            mock_get.return_value = fake_response(data)
            self.assertEqual(metadata.get_metadata("1.2.3.4")["asn"], expected, raw)

    def test_square_brackets_pass_through_unchanged(self, mock_get):

        data = dict(GOOD); data["city"] = "[bold]Evil[/bold]"
        mock_get.return_value = fake_response(data)
        self.assertEqual(metadata.get_metadata("1.2.3.4")["city"], "[bold]Evil[/bold]")


@patch("metadata.requests.get")
class TestStress(unittest.TestCase):
    """Throw 2000 random garbage replies at get_metadata. It must never crash."""

    def test_fuzz_never_crashes_and_keeps_contract(self, mock_get):
        rnd = random.Random(42) 
        junk = [None, "", "x", 0, 1, -5, 3.14, True, False, [], {}, [1], {"a": 1}, "  ", "😀"]

        def junky_dict():
            return {
                "success": rnd.choice([True, False, None, "true", 1]),
                "city": rnd.choice(junk), "region": rnd.choice(junk),
                "country": rnd.choice(junk), "country_code": rnd.choice(junk),
                "connection": rnd.choice(junk + [{"asn": rnd.choice(junk),
                                                  "org": rnd.choice(junk),
                                                  "isp": rnd.choice(junk)}]),
            }

        for _ in range(2000):
            mock_get.return_value = fake_response(rnd.choice(junk + [junky_dict()]))
            meta = metadata.get_metadata("203.0.113.10")
            self.assertEqual(set(meta), KEYS)
            for value in meta.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip())

    def test_repeated_failures(self, mock_get):
        errors = [requests.Timeout(), requests.ConnectionError(),
                  requests.HTTPError(), requests.TooManyRedirects(), ValueError()]
        for i in range(500):
            mock_get.side_effect = errors[i % len(errors)]
            self.assertEqual(set(metadata.get_metadata("1.2.3.4").values()), {NA})


if __name__ == "__main__":
    unittest.main()
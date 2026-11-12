"""test_detection.py - unit tests for detection.py (QA: Justin).

All tests use MOCKED (fake) API replies. No internet is used.
"""

import ipaddress
import os
import random
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

# Let the test find detection.py in the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import detection  # noqa: E402

V4 = "203.0.113.10"
V6 = "2001:db8::1"


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


@patch("detection.requests.get")
class TestDetection(unittest.TestCase):

    # ---------- happy path ----------
    def test_ipv4_found(self, mock_get):
        mock_get.return_value = fake_response({"ip": V4})
        self.assertEqual(detection.get_public_ipv4(), V4)

    def test_ipv6_found(self, mock_get):
        mock_get.return_value = fake_response({"ip": V6})
        self.assertEqual(detection.get_public_ipv6(), V6)

    def test_ipv4_uses_right_url_and_5s_timeout(self, mock_get):
        mock_get.return_value = fake_response({"ip": V4})
        detection.get_public_ipv4()
        mock_get.assert_called_once_with("https://api.ipify.org?format=json", timeout=5)

    def test_ipv6_uses_right_url_and_5s_timeout(self, mock_get):
        mock_get.return_value = fake_response({"ip": V6})
        detection.get_public_ipv6()
        mock_get.assert_called_once_with("https://api6.ipify.org?format=json", timeout=5)

    def test_whitespace_is_stripped(self, mock_get):
        mock_get.return_value = fake_response({"ip": "  " + V4 + " "})
        self.assertEqual(detection.get_public_ipv4(), V4)

    def test_ipv6_is_normalised(self, mock_get):
        mock_get.return_value = fake_response({"ip": "2001:0db8:0000:0000:0000:0000:0000:0001"})
        self.assertEqual(detection.get_public_ipv6(), "2001:db8::1")

    # ---------- IPv4 must never be IPv6 (and the reverse) ----------
    def test_ipv4_never_accepted_as_ipv6(self, mock_get):
        mock_get.return_value = fake_response({"ip": V4})
        self.assertIsNone(detection.get_public_ipv6())

    def test_ipv6_never_accepted_as_ipv4(self, mock_get):
        mock_get.return_value = fake_response({"ip": V6})
        self.assertIsNone(detection.get_public_ipv4())

    # ---------- failures: both functions must return None ----------
    def _both_none(self):
        self.assertIsNone(detection.get_public_ipv4())
        self.assertIsNone(detection.get_public_ipv6())

    def test_ipv6_unavailable_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()   # what "no IPv6" looks like
        self._both_none()

    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        self._both_none()

    def test_generic_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException()
        self._both_none()

    def test_http_429(self, mock_get):
        mock_get.return_value = fake_response(http_error=requests.HTTPError("429"))
        self._both_none()

    def test_http_500(self, mock_get):
        mock_get.return_value = fake_response(http_error=requests.HTTPError("500"))
        self._both_none()

    def test_bad_json(self, mock_get):
        mock_get.return_value = fake_response(json_error=ValueError("bad json"))
        self._both_none()

    # ---------- odd replies ----------
    def test_missing_ip_key(self, mock_get):
        mock_get.return_value = fake_response({"address": V4})
        self._both_none()

    def test_ip_is_null(self, mock_get):
        mock_get.return_value = fake_response({"ip": None})
        self._both_none()

    def test_ip_is_empty_string(self, mock_get):
        mock_get.return_value = fake_response({"ip": ""})
        self._both_none()

    def test_ip_is_garbage_text(self, mock_get):
        mock_get.return_value = fake_response({"ip": "not-an-ip"})
        self._both_none()

    def test_ip_out_of_range(self, mock_get):
        mock_get.return_value = fake_response({"ip": "999.1.1.1"})
        self._both_none()

    def test_ip_is_a_number(self, mock_get):
        mock_get.return_value = fake_response({"ip": 16909060})  # must not become 1.2.3.4
        self._both_none()

    def test_json_is_list(self, mock_get):
        mock_get.return_value = fake_response([V4])
        self._both_none()

    def test_json_is_null(self, mock_get):
        mock_get.return_value = fake_response(None)
        self._both_none()

    def test_json_is_plain_string(self, mock_get):
        mock_get.return_value = fake_response(V4)
        self._both_none()


@patch("detection.requests.get")
class TestStress(unittest.TestCase):
    """Throw 2000 random garbage replies at each function. It must never crash,
    and must only ever return None or an address of the RIGHT IP version."""

    def test_fuzz_never_crashes_and_never_mixes_versions(self, mock_get):
        rnd = random.Random(42)  # fixed seed = repeatable
        junk = [None, "", "x", 0, 1, -5, 3.14, True, False, [], {}, [1],
                {"a": 1}, "  ", "😀", V4, V6, "::1", "1.2.3.4", " 8.8.8.8 "]

        def payload():
            choice = rnd.randint(0, 2)
            if choice == 0:
                return rnd.choice(junk)
            if choice == 1:
                return {"ip": rnd.choice(junk)}
            return {"other": rnd.choice(junk)}

        for func, version in ((detection.get_public_ipv4, 4),
                              (detection.get_public_ipv6, 6)):
            for _ in range(2000):
                mock_get.return_value = fake_response(payload())
                result = func()
                if result is not None:
                    self.assertIsInstance(result, str)
                    self.assertEqual(ipaddress.ip_address(result).version, version)

    def test_repeated_failures(self, mock_get):
        errors = [requests.Timeout(), requests.ConnectionError(),
                  requests.HTTPError(), requests.TooManyRedirects(), ValueError()]
        for i in range(500):
            mock_get.side_effect = errors[i % len(errors)]
            self.assertIsNone(detection.get_public_ipv4())
            self.assertIsNone(detection.get_public_ipv6())


if __name__ == "__main__":
    unittest.main()
"""test_validation_extra.py - extra tests for validation.py validate_ip (QA: Justin).

Fake data only. No internet is used.
"""

import ipaddress
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validation import validate_ip  

V4 = "203.0.113.10"
V6 = "2001:db8::1"


class TestValidateIpExtra(unittest.TestCase):

    def test_valid_result_is_a_string_of_the_right_version(self):
        for text, version in ((V4, 4), (V6, 6), ("8.8.8.8", 4), ("::1", 6)):
            with self.subTest(text=text):
                result = validate_ip(text)
                self.assertIsInstance(result, str)
                self.assertEqual(ipaddress.ip_address(result).version, version)

    def test_ipv6_is_returned_in_lower_case(self):
        self.assertEqual(validate_ip("2001:DB8::ABCD"), "2001:db8::abcd")

    def test_validating_twice_gives_the_same_result(self):
        for text in (V4, V6, "  8.8.8.8 ", "2001:0db8:0000:0000:0000:0000:0000:0001"):
            with self.subTest(text=text):
                once = validate_ip(text)
                self.assertEqual(validate_ip(once), once)

    def test_unusual_types_return_none(self):
        for value in (b"8.8.8.8", b"\x08\x08\x08\x08", (8, 8, 8, 8), {"ip": V4},
                      {V4}, object(), True, False, float("nan"), 10 ** 30, -1):
            with self.subTest(value=repr(value)):
                self.assertIsNone(validate_ip(value))

    def test_port_prefix_and_names_are_rejected(self):
        for text in ("8.8.8.8:80", "2001:db8::/32", "localhost", "example.com",
                     "http://8.8.8.8", "8.8.8.8,", "1.2.3.4.5", "::g"):
            with self.subTest(text=text):
                self.assertIsNone(validate_ip(text))

    def test_control_characters_are_rejected(self):
        for text in ("8.8.8.8\x00", "\x008.8.8.8", "8.8.\x078.8", "8.8.8.8\x1b[0m"):
            with self.subTest(text=repr(text)):
                self.assertIsNone(validate_ip(text))

    def test_non_ascii_digits_are_rejected(self):
        self.assertIsNone(validate_ip("\uff18.\uff18.\uff18.\uff18"))  
        self.assertIsNone(validate_ip("\u0668.\u0668.\u0668.\u0668"))   

    def test_very_long_text_does_not_crash(self):
        for text in ("1" * 100000, "a" * 10000, "1." * 5000, ":" * 5000, V4 + "1" * 10000):
            with self.subTest(length=len(text)):
                self.assertIsNone(validate_ip(text))


class TestStress(unittest.TestCase):
    """Throw thousands of inputs at validate_ip. It must never raise."""

    def test_random_valid_ipv4_round_trips(self):
        rnd = random.Random(42)
        for _ in range(500):
            expected = str(ipaddress.IPv4Address(rnd.getrandbits(32)))
            self.assertEqual(validate_ip(expected), expected)
            self.assertEqual(validate_ip("  " + expected + "\t"), expected)

    def test_random_valid_ipv6_round_trips(self):
        rnd = random.Random(42)
        for _ in range(500):
            expected = str(ipaddress.IPv6Address(rnd.getrandbits(128)))
            self.assertEqual(validate_ip(expected), expected)
            self.assertEqual(validate_ip(expected.upper()), expected)

    def test_fuzz_never_raises_and_only_returns_real_addresses(self):
        rnd = random.Random(42)
        junk = [None, "", " ", "x", 0, 1, -5, 3.14, True, [], {}, b"x", "\U0001F600",
                V4, V6, "::1", " 8.8.8.8 ", "1.2.3", "256.1.1.1", "8.8.8.8/24",
                "::ffff:1.2.3.4", "1.2.3.4.5"]
        alphabet = "0123456789abcdefABCDEF.:/ %[]-"
        for _ in range(2000):
            if rnd.random() < 0.5:
                value = rnd.choice(junk)
            else:
                value = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 45)))
            result = validate_ip(value)
            if result is not None:
                self.assertIsInstance(result, str)
                self.assertEqual(str(ipaddress.ip_address(result)), result)


if __name__ == "__main__":
    unittest.main()
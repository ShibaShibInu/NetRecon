# Owner: Aaron Yumul (tests for validate_ip). No internet needed.
import unittest

from validation import validate_ip


class TestValidateIp(unittest.TestCase):
    def test_valid_ipv4(self):
        self.assertEqual(validate_ip("8.8.8.8"), "8.8.8.8")

    def test_valid_ipv6_is_shortened(self):
        self.assertEqual(validate_ip("2001:0db8:0000:0000:0000:0000:0000:0001"), "2001:db8::1")

    def test_spaces_are_removed(self):
        self.assertEqual(validate_ip("  1.1.1.1  "), "1.1.1.1")

    def test_private_address_is_still_valid(self):
        self.assertEqual(validate_ip("192.168.1.5"), "192.168.1.5")

    def test_bad_text(self):
        self.assertIsNone(validate_ip("abc"))

    def test_out_of_range(self):
        self.assertIsNone(validate_ip("256.1.1.1"))

    def test_too_few_parts(self):
        self.assertIsNone(validate_ip("1.2.3"))

    def test_empty_and_spaces(self):
        self.assertIsNone(validate_ip(""))
        self.assertIsNone(validate_ip("   "))

    def test_not_a_string(self):
        for value in (None, 123, 1.5, [], {}):
            self.assertIsNone(validate_ip(value))

    def test_injection_style_text(self):
        self.assertIsNone(validate_ip("8.8.8.8; rm -rf /"))
        self.assertIsNone(validate_ip("8.8.8.8/24"))


if __name__ == "__main__":
    unittest.main()

import unittest
from utils.contact_utils import normalize_indian_phone, mask_phone_number, validate_email_address

class TestContactUtils(unittest.TestCase):

    def test_normalize_indian_phone_valid(self):
        self.assertEqual(normalize_indian_phone("9876543210"), "+919876543210")
        self.assertEqual(normalize_indian_phone("09876543210"), "+919876543210")
        self.assertEqual(normalize_indian_phone("919876543210"), "+919876543210")
        self.assertEqual(normalize_indian_phone("+919876543210"), "+919876543210")
        self.assertEqual(normalize_indian_phone(" 9876-543-210 "), "+919876543210")

    def test_normalize_indian_phone_invalid(self):
        self.assertIsNone(normalize_indian_phone("12345"))
        self.assertIsNone(normalize_indian_phone("1876543210")) # Invalid start digit
        self.assertIsNone(normalize_indian_phone(""))
        self.assertIsNone(normalize_indian_phone(None))

    def test_mask_phone_number(self):
        self.assertEqual(mask_phone_number("9876543210"), "XXXXXX3210")
        self.assertEqual(mask_phone_number("+919876543210"), "XXXXXX3210")
        self.assertEqual(mask_phone_number(""), "")

    def test_validate_email_address(self):
        self.assertTrue(validate_email_address("employee@example.com"))
        self.assertTrue(validate_email_address("test.user+tag@domain.co.in"))
        self.assertFalse(validate_email_address("invalid-email"))
        self.assertFalse(validate_email_address("user@domain"))

if __name__ == '__main__':
    unittest.main()

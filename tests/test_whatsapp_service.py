import unittest
from services.whatsapp_service import send_payslip_whatsapp

class TestWhatsAppService(unittest.TestCase):

    def test_missing_phone_number(self):
        success, msg = send_payslip_whatsapp("", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(success)
        self.assertEqual(msg, "Phone number is not available for this employee. Please update Employee Master.")

    def test_invalid_phone_number(self):
        success, msg = send_payslip_whatsapp("123", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(success)
        self.assertEqual(msg, "Please enter a valid Indian mobile number.")

    def test_unconfigured_whatsapp_api(self):
        # With credentials missing from environment
        success, msg = send_payslip_whatsapp("9876543210", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(success)
        self.assertEqual(msg, "WhatsApp service is not configured. Please contact administrator.")

if __name__ == '__main__':
    unittest.main()

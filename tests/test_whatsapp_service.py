import os
import unittest
from unittest.mock import patch, MagicMock
from services.whatsapp_service import send_payslip_whatsapp, WhatsAppSendResult, test_whatsapp_api_configuration

class TestWhatsAppService(unittest.TestCase):

    def test_missing_phone_number(self):
        res = send_payslip_whatsapp("", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(res.success)
        self.assertEqual(res.stage, "PHONE_VALIDATION")
        self.assertEqual(res.message, "Phone number is not available for this employee. Please update Employee Master.")

    def test_invalid_phone_number(self):
        res = send_payslip_whatsapp("123", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(res.success)
        self.assertEqual(res.stage, "PHONE_VALIDATION")
        self.assertEqual(res.message, "Please enter a valid Indian mobile number.")

    def test_unconfigured_whatsapp_api(self):
        with patch.dict(os.environ, {'WHATSAPP_ACCESS_TOKEN': '', 'WHATSAPP_PHONE_NUMBER_ID': ''}):
            res = send_payslip_whatsapp("9876543210", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
            self.assertFalse(res.success)
            self.assertEqual(res.stage, "API_CONFIGURATION")
            self.assertEqual(res.message, "WhatsApp service is not configured. Please contact administrator.")

    @patch('services.whatsapp_service.requests.post')
    def test_media_upload_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "error": {
                "message": "Invalid OAuth access token",
                "type": "OAuthException",
                "code": 190
            }
        }
        mock_post.return_value = mock_resp

        with patch.dict(os.environ, {'WHATSAPP_ACCESS_TOKEN': 'test_token', 'WHATSAPP_PHONE_NUMBER_ID': '123456789'}):
            res = send_payslip_whatsapp("9876543210", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FAILED")
            self.assertEqual(res.stage, "MEDIA_UPLOAD")
            self.assertIn("Invalid or expired WhatsApp Access Token", res.message)

    @patch('services.whatsapp_service.requests.post')
    def test_message_send_failure(self, mock_post):
        # First call (media upload) succeeds, second call (message send) fails
        mock_upload_resp = MagicMock()
        mock_upload_resp.status_code = 200
        mock_upload_resp.json.return_value = {"id": "media_test_12345"}

        mock_send_resp = MagicMock()
        mock_send_resp.status_code = 400
        mock_send_resp.json.return_value = {
            "error": {
                "message": "Recipient phone number is not registered on WhatsApp",
                "code": 131030
            }
        }
        mock_post.side_effect = [mock_upload_resp, mock_send_resp]

        with patch.dict(os.environ, {'WHATSAPP_ACCESS_TOKEN': 'test_token', 'WHATSAPP_PHONE_NUMBER_ID': '123456789'}):
            res = send_payslip_whatsapp("9876543210", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
            self.assertFalse(res.success)
            self.assertEqual(res.status, "FAILED")
            self.assertEqual(res.stage, "MESSAGE_SEND")
            self.assertIn("not registered on WhatsApp", res.message)

    @patch('services.whatsapp_service.requests.post')
    def test_successful_send(self, mock_post):
        # Both calls succeed
        mock_upload_resp = MagicMock()
        mock_upload_resp.status_code = 200
        mock_upload_resp.json.return_value = {"id": "media_test_9999"}

        mock_send_resp = MagicMock()
        mock_send_resp.status_code = 200
        mock_send_resp.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
            "messages": [{"id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSR"} ]
        }
        mock_post.side_effect = [mock_upload_resp, mock_send_resp]

        with patch.dict(os.environ, {'WHATSAPP_ACCESS_TOKEN': 'test_token', 'WHATSAPP_PHONE_NUMBER_ID': '123456789'}):
            res = send_payslip_whatsapp("9876543210", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
            self.assertTrue(res.success)
            self.assertEqual(res.status, "SENT")
            self.assertEqual(res.stage, "MESSAGE_SEND")
            self.assertEqual(res.message_id, "wamid.HBgMOTE5ODc2NTQzMjEwFQIAERgSR")
            self.assertIn("Payslip sent successfully to WhatsApp", res.message)

    def test_tuple_unpacking_compatibility(self):
        # Verify backward compatibility with tuple unpacking: success, msg = send_payslip_whatsapp(...)
        success, msg = send_payslip_whatsapp("", "TEST EMP", "1001", "July 2026", b"pdf content", "test.pdf")
        self.assertFalse(success)
        self.assertIsInstance(msg, str)

if __name__ == '__main__':
    unittest.main()

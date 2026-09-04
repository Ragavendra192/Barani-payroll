import os
import json
import requests
from utils.contact_utils import normalize_indian_phone, mask_phone_number

class WhatsAppSendResult:
    """
    Structured outcome of a WhatsApp send operation.
    Supports 2-tuple unpacking for backward compatibility:
        success, message = send_payslip_whatsapp(...)
    And object/dict access for stage diagnostics:
        result.stage, result.message_id, result.to_dict()
    """
    def __init__(self, success: bool, message: str, status: str = 'FAILED', stage: str = None, message_id: str = None, error_details: str = None, http_status: int = None):
        self.success = bool(success)
        self.message = str(message)
        self.status = str(status)  # 'SENT', 'FAILED', 'SKIPPED', 'ALREADY_SENT'
        self.stage = stage         # 'PHONE_VALIDATION', 'API_CONFIGURATION', 'PDF_GENERATION', 'MEDIA_UPLOAD', 'MESSAGE_SEND'
        self.message_id = message_id
        self.error_details = error_details
        self.http_status = http_status

    def __iter__(self):
        return iter([self.success, self.message])

    def __getitem__(self, index):
        return [self.success, self.message][index]

    def to_dict(self):
        return {
            'success': self.success,
            'status': self.status,
            'stage': self.stage,
            'message': self.message,
            'message_id': self.message_id,
            'error_details': self.error_details,
            'http_status': self.http_status
        }

    def __repr__(self):
        return f"<WhatsAppSendResult success={self.success} status='{self.status}' stage='{self.stage}'>"

def is_whatsapp_configured():
    """Validates whether WhatsApp Cloud API credentials are configured in environment."""
    token = os.environ.get('WHATSAPP_ACCESS_TOKEN', '').strip()
    phone_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '').strip()
    if not token or not phone_id:
        return False
    if 'your_whatsapp' in token.lower() or 'your_phone' in phone_id.lower():
        return False
    return True

def send_payslip_whatsapp(phone_number, employee_name, employee_id, payroll_month, pdf_bytes, filename):
    """
    Sends official PDF payslip to employee via official Meta WhatsApp Business Cloud API.
    Performs stage-by-stage execution with detailed debug logging and structured diagnostic results.
    """
    masked_input = mask_phone_number(phone_number) if phone_number else '-'
    print("\n" + "=" * 60)
    print(f"[WHATSAPP DEBUG] Initiating send pipeline for Employee #{employee_id} ({employee_name})")
    print(f"[WHATSAPP DEBUG] Payroll Period: {payroll_month}")

    # Stage 1: Phone Number Presence Validation
    if not phone_number or str(phone_number).strip() in ('', '-', 'None'):
        print("[WHATSAPP DEBUG] Stage: PHONE_VALIDATION -> FAILED (Phone number missing in Employee Master)")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="Phone number is not available for this employee. Please update Employee Master.",
            status="FAILED",
            stage="PHONE_VALIDATION"
        )

    # Stage 2: Phone Number Normalization
    norm_phone = normalize_indian_phone(phone_number)
    if not norm_phone:
        print(f"[WHATSAPP DEBUG] Stage: PHONE_VALIDATION -> FAILED (Invalid format for {masked_input})")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="Please enter a valid Indian mobile number.",
            status="FAILED",
            stage="PHONE_VALIDATION"
        )

    masked_phone = mask_phone_number(norm_phone)
    recipient_phone = norm_phone.replace('+', '').strip()
    print(f"[WHATSAPP DEBUG] Stage: PHONE_VALIDATION -> SUCCESS (Recipient: {masked_phone})")

    # Stage 3: PDF Document Validation
    if not pdf_bytes or len(pdf_bytes) == 0:
        print("[WHATSAPP DEBUG] Stage: PDF_GENERATION -> FAILED (PDF payload is empty or None)")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="Payslip PDF could not be generated.",
            status="FAILED",
            stage="PDF_GENERATION"
        )
    print(f"[WHATSAPP DEBUG] Stage: PDF_GENERATION -> SUCCESS (File: {filename}, Size: {len(pdf_bytes)} bytes)")

    # Stage 4: API Credential Verification
    access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN', '').strip()
    phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '').strip()

    if not is_whatsapp_configured():
        print("[WHATSAPP DEBUG] Stage: API_CONFIGURATION -> FAILED (WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID missing/placeholder in .env)")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="WhatsApp service is not configured. Please contact administrator.",
            status="FAILED",
            stage="API_CONFIGURATION",
            error_details="WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID is missing or set to placeholder in .env"
        )
    print("[WHATSAPP DEBUG] Stage: API_CONFIGURATION -> SUCCESS (Credentials present)")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Stage 5: Upload PDF Document Media to WhatsApp Cloud API
    media_url = f"https://graph.facebook.com/v19.0/{phone_number_id}/media"
    files = {
        'file': (filename, pdf_bytes, 'application/pdf'),
    }
    data = {
        'messaging_product': 'whatsapp',
        'type': 'application/pdf'
    }

    try:
        print(f"[WHATSAPP DEBUG] Stage: MEDIA_UPLOAD -> POST {media_url}")
        media_resp = requests.post(media_url, headers=headers, data=data, files=files, timeout=30)
        print(f"[WHATSAPP DEBUG] Stage: MEDIA_UPLOAD -> HTTP {media_resp.status_code}")

        if media_resp.status_code != 200:
            err_code, err_msg = _extract_meta_error(media_resp)
            print(f"[WHATSAPP DEBUG] Stage: MEDIA_UPLOAD -> FAILED (Code: {err_code}, Message: {err_msg})")
            print("=" * 60 + "\n")
            return WhatsAppSendResult(
                success=False,
                message=f"WhatsApp document upload failed. ({err_msg})",
                status="FAILED",
                stage="MEDIA_UPLOAD",
                http_status=media_resp.status_code,
                error_details=f"HTTP {media_resp.status_code} - Code {err_code}: {err_msg}"
            )

        media_json = media_resp.json()
        media_id = media_json.get('id')
        if not media_id:
            print("[WHATSAPP DEBUG] Stage: MEDIA_UPLOAD -> FAILED (No media ID returned)")
            print("=" * 60 + "\n")
            return WhatsAppSendResult(
                success=False,
                message="WhatsApp document upload failed. Media ID was not returned by API.",
                status="FAILED",
                stage="MEDIA_UPLOAD",
                http_status=media_resp.status_code,
                error_details="No 'id' field in Meta media upload JSON response"
            )

        print(f"[WHATSAPP DEBUG] Stage: MEDIA_UPLOAD -> SUCCESS (Media ID: {media_id})")

        # Stage 6: Send WhatsApp Document Message
        message_url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        caption_text = (
            f"Hello {employee_name},\n\n"
            f"Your salary payslip for {payroll_month} is attached.\n\n"
            f"Employee ID: {employee_id}\n\n"
            f"Regards,\n"
            f"Payroll Department\n"
            f"Barani Hydraulics India Private Limited"
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": filename,
                "caption": caption_text
            }
        }

        print(f"[WHATSAPP DEBUG] Stage: MESSAGE_SEND -> POST {message_url}")
        msg_resp = requests.post(message_url, headers=headers, json=payload, timeout=30)
        print(f"[WHATSAPP DEBUG] Stage: MESSAGE_SEND -> HTTP {msg_resp.status_code}")

        if msg_resp.status_code in (200, 201):
            msg_json = msg_resp.json()
            messages = msg_json.get('messages', [])
            message_id = messages[0].get('id') if messages and isinstance(messages, list) else None
            print(f"[WHATSAPP DEBUG] Stage: MESSAGE_SEND -> SUCCESS (Message ID: {message_id})")
            print("=" * 60 + "\n")
            return WhatsAppSendResult(
                success=True,
                message=f"Payslip sent successfully to WhatsApp ({masked_phone}).",
                status="SENT",
                stage="MESSAGE_SEND",
                message_id=message_id,
                http_status=msg_resp.status_code
            )
        else:
            err_code, err_msg = _extract_meta_error(msg_resp)
            print(f"[WHATSAPP DEBUG] Stage: MESSAGE_SEND -> FAILED (Code: {err_code}, Message: {err_msg})")
            print("=" * 60 + "\n")
            return WhatsAppSendResult(
                success=False,
                message=f"Payslip PDF uploaded, but WhatsApp message could not be sent. ({err_msg})",
                status="FAILED",
                stage="MESSAGE_SEND",
                http_status=msg_resp.status_code,
                error_details=f"HTTP {msg_resp.status_code} - Code {err_code}: {err_msg}"
            )

    except requests.exceptions.Timeout:
        print("[WHATSAPP DEBUG] Network connection timed out during WhatsApp API request.")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="Network connection timed out while contacting WhatsApp service. Please check internet connection.",
            status="FAILED",
            stage="NETWORK_TIMEOUT"
        )
    except requests.exceptions.RequestException as req_err:
        print(f"[WHATSAPP DEBUG] Network/HTTP Exception: {req_err}")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message=f"Network error communicating with WhatsApp service: {str(req_err)}",
            status="FAILED",
            stage="NETWORK_ERROR",
            error_details=str(req_err)
        )
    except Exception as ex:
        print(f"[WHATSAPP DEBUG] Unexpected Exception: {ex}")
        print("=" * 60 + "\n")
        return WhatsAppSendResult(
            success=False,
            message="Payslip could not be sent due to an unexpected error. Please check WhatsApp configuration.",
            status="FAILED",
            stage="INTERNAL_ERROR",
            error_details=str(ex)
        )

def _extract_meta_error(response):
    """Safely extracts error code and user-friendly error message from Meta Graph API response."""
    try:
        data = response.json()
        err = data.get('error', {})
        code = err.get('code')
        msg = err.get('message', '')
        type_ = err.get('type', '')
        subcode = err.get('error_subcode')

        # Translate common Meta API error codes to informative descriptions
        if code == 190:
            return code, "Invalid or expired WhatsApp Access Token in .env"
        elif code == 100:
            return code, f"Invalid request parameter or Phone Number ID: {msg}"
        elif code == 131030:
            return code, "Recipient phone number is not registered on WhatsApp or cannot receive messages"
        elif code == 131047:
            return code, "Re-engagement message requires an approved template outside the 24-hour customer window"
        elif code == 131026:
            return code, "Message undeliverable to this phone number"
        elif msg:
            return code, msg
        else:
            return code, f"Meta API HTTP {response.status_code}"
    except Exception:
        return None, f"Meta API HTTP {response.status_code}: {response.text[:150]}"

def test_whatsapp_api_configuration():
    """
    Performs live diagnostic health check on WhatsApp Cloud API credentials.
    Queries GET https://graph.facebook.com/v19.0/{phone_number_id} to verify token & sender.
    """
    token = os.environ.get('WHATSAPP_ACCESS_TOKEN', '').strip()
    phone_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '').strip()

    if not is_whatsapp_configured():
        return {
            'configured': False,
            'valid': False,
            'status': 'UNCONFIGURED',
            'message': 'WhatsApp credentials are not configured or still set to placeholders in .env file.'
        }

    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f"https://graph.facebook.com/v19.0/{phone_id}"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'configured': True,
                'valid': True,
                'status': 'HEALTHY',
                'display_phone_number': data.get('display_phone_number', '-'),
                'verified_name': data.get('verified_name', '-'),
                'quality_rating': data.get('quality_rating', '-'),
                'message': f"WhatsApp Cloud API is ACTIVE. Sender: {data.get('verified_name', 'Verified Sender')} ({data.get('display_phone_number', phone_id)})."
            }
        else:
            code, msg = _extract_meta_error(resp)
            return {
                'configured': True,
                'valid': False,
                'status': 'INVALID_CREDENTIALS',
                'http_status': resp.status_code,
                'error_code': code,
                'message': f"Meta WhatsApp API returned HTTP {resp.status_code}: {msg}"
            }
    except Exception as e:
        return {
            'configured': True,
            'valid': False,
            'status': 'CONNECTION_ERROR',
            'message': f"Failed to connect to Meta WhatsApp API: {str(e)}"
        }

import os
import requests
from utils.contact_utils import normalize_indian_phone, mask_phone_number

def send_payslip_whatsapp(phone_number, employee_name, employee_id, payroll_month, pdf_bytes, filename):
    """
    Sends PDF payslip to employee via official WhatsApp Cloud API.
    Returns tuple: (success: bool, user_message: str)
    """
    # 1. Check phone number availability
    if not phone_number:
        return False, "Phone number is not available for this employee. Please update Employee Master."

    norm_phone = normalize_indian_phone(phone_number)
    if not norm_phone:
        return False, "Please enter a valid Indian mobile number."

    # Format phone number for WhatsApp API (digits only without leading +)
    recipient_phone = norm_phone.replace('+', '').strip()

    # 2. Check API Credentials from Environment
    access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')

    if not access_token or not phone_number_id:
        # Return clean user-facing error message without secrets
        return False, "WhatsApp service is not configured. Please contact administrator."

    # 3. Verify PDF Payload
    if not pdf_bytes:
        return False, "Payslip PDF could not be generated."

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # Step A: Upload PDF Document Media to WhatsApp Cloud API
        media_url = f"https://graph.facebook.com/v19.0/{phone_number_id}/media"
        files = {
            'file': (filename, pdf_bytes, 'application/pdf'),
        }
        data = {
            'messaging_product': 'whatsapp',
            'type': 'application/pdf'
        }

        media_resp = requests.post(media_url, headers=headers, data=data, files=files, timeout=30)
        if media_resp.status_code != 200:
            return False, "Unable to send payslip. Please try again."

        media_id = media_resp.json().get('id')
        if not media_id:
            return False, "Unable to send payslip. Please try again."

        # Step B: Send Document Message
        message_url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        caption_text = (
            f"Hello {employee_name},\n\n"
            f"Your salary payslip for {payroll_month} is attached.\n\n"
            f"Employee ID: {employee_id}\n\n"
            f"Regards,\n"
            f"Payroll Department"
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

        msg_resp = requests.post(message_url, headers=headers, json=payload, timeout=30)
        if msg_resp.status_code in (200, 201):
            masked = mask_phone_number(norm_phone)
            return True, f"Payslip sent successfully to WhatsApp ({masked})."
        else:
            return False, "Unable to send payslip. Please try again."

    except requests.exceptions.Timeout:
        return False, "Network connection failed. Please try again."
    except requests.exceptions.RequestException:
        return False, "Unable to send payslip. Please try again."
    except Exception:
        return False, "Payslip could not be sent. Please check the phone number and WhatsApp configuration."

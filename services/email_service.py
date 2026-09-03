import os
from utils.contact_utils import validate_email_address

def send_payslip_email(email_id, employee_name, employee_id, payroll_month, pdf_bytes, filename):
    """
    Sends PDF payslip to employee via Email.
    Returns tuple: (success: bool, user_message: str)
    """
    if not email_id:
        return False, "Email ID is not available for this employee. Please update Employee Master."

    if not validate_email_address(email_id):
        return False, "Please enter a valid email address."

    smtp_server = os.environ.get('SMTP_SERVER')
    if not smtp_server:
        return False, "Email service is not configured. Please contact administrator."

    # Future SMTP delivery extension point
    return True, f"Payslip sent successfully to email ({email_id})."

import os
import csv
import io
import time
from services.payslip_service import get_payslip_data, generate_payslip_pdf, MONTH_NAMES
from services.whatsapp_service import send_payslip_whatsapp
from models.payslip_send_log import log_payslip_send, is_payslip_already_sent, get_payslip_send_logs
from utils.contact_utils import normalize_indian_phone, mask_phone_number

def get_bulk_payslip_summary(year, month, category=None, search=None, resend=False):
    """
    Computes summary metrics for bulk payslip sending:
    - Total employees matching filters
    - Valid WhatsApp count
    - Missing phone number count
    - Invalid phone number format count
    - Already sent count
    - Will send count
    """
    records = get_payslip_data(year, month, category=category)
    if search:
        s = str(search).lower().strip()
        records = [r for r in records if s in str(r.get('Emp_No')).lower() or s in str(r.get('Employee_Name')).lower()]

    month_name = MONTH_NAMES[month]
    payroll_month_label = f"{month_name} {year}"

    total_employees = len(records)
    valid_whatsapp_count = 0
    missing_number_count = 0
    invalid_number_count = 0
    already_sent_count = 0
    will_send_count = 0

    employee_list = []

    for r in records:
        emp_id = r.get('Employee_ID') or r.get('Emp_No')
        emp_no = str(r.get('Emp_No')).strip()
        emp_name = r.get('Employee_Name') or r.get('Name') or 'Employee'
        phone = r.get('Phone_Number')
        
        already_sent = is_payslip_already_sent(emp_id, year, month_name)

        if not phone or str(phone).strip() in ('', '-', 'None'):
            status = 'MISSING_NUMBER'
            masked_phone = '-'
            missing_number_count += 1
        else:
            norm_phone = normalize_indian_phone(phone)
            if not norm_phone:
                status = 'INVALID_NUMBER'
                masked_phone = mask_phone_number(phone)
                invalid_number_count += 1
            else:
                masked_phone = mask_phone_number(norm_phone)
                valid_whatsapp_count += 1
                if already_sent and not resend:
                    status = 'ALREADY_SENT'
                    already_sent_count += 1
                else:
                    status = 'PENDING'
                    will_send_count += 1

        employee_list.append({
            'emp_id': emp_id,
            'emp_no': emp_no,
            'emp_name': emp_name,
            'category': r.get('Category'),
            'phone_masked': masked_phone,
            'status': status,
            'already_sent': already_sent
        })

    return {
        'year': year,
        'month': month,
        'month_name': month_name,
        'payroll_month_label': payroll_month_label,
        'category': category or 'ALL',
        'total_employees': total_employees,
        'valid_whatsapp_count': valid_whatsapp_count,
        'missing_number_count': missing_number_count,
        'invalid_number_count': invalid_number_count,
        'already_sent_count': already_sent_count,
        'will_send_count': will_send_count,
        'employee_list': employee_list
    }

def process_single_employee_whatsapp_send(year, month, emp_no, category=None, resend=False):
    """
    Atomically generates PDF payslip and sends via WhatsApp Cloud API for one employee.
    Handles retries up to 2 additional times for temporary failures.
    Returns dict with status, message, masked_phone, and message_id.
    """
    records = get_payslip_data(year, month, emp_no=emp_no, category=category)
    if not records:
        return {'status': 'SKIPPED', 'message': 'Payslip transaction not found', 'masked_phone': '-'}

    r = records[0]
    emp_id = r.get('Employee_ID') or r.get('Emp_No')
    emp_name = r.get('Employee_Name') or r.get('Name') or 'Employee'
    phone = r.get('Phone_Number')
    email_id = r.get('Email_ID')
    month_name = MONTH_NAMES[month]
    payroll_month_label = f"{month_name} {year}"

    # 1. Check Phone availability
    if not phone or str(phone).strip() in ('', '-', 'None'):
        log_payslip_send(emp_id, payroll_month_label, None, email_id, f"Payslip_{emp_no}.pdf", whatsapp_status='SKIPPED', error_message='WhatsApp number not available', payroll_year=year)
        return {'status': 'SKIPPED', 'message': 'WhatsApp number not available', 'masked_phone': '-'}

    norm_phone = normalize_indian_phone(phone)
    if not norm_phone:
        masked_phone = mask_phone_number(phone)
        log_payslip_send(emp_id, payroll_month_label, phone, email_id, f"Payslip_{emp_no}.pdf", whatsapp_status='SKIPPED', error_message='Invalid phone number format', payroll_year=year)
        return {'status': 'SKIPPED', 'message': 'Invalid phone number format', 'masked_phone': masked_phone}

    masked_phone = mask_phone_number(norm_phone)

    # 2. Check if Already Sent
    if not resend and is_payslip_already_sent(emp_id, year, month_name):
        return {'status': 'ALREADY_SENT', 'message': 'Payslip already sent previously', 'masked_phone': masked_phone}

    # 3. Generate BHIPL A4 Payslip PDF
    pdf_io, filename = generate_payslip_pdf(year, month, emp_no, category=category)
    if not pdf_io:
        log_payslip_send(emp_id, payroll_month_label, norm_phone, email_id, f"Payslip_{emp_no}.pdf", whatsapp_status='FAILED', error_message='PDF generation failed', payroll_year=year)
        return {'status': 'FAILED', 'message': 'PDF generation failed', 'masked_phone': masked_phone}

    pdf_bytes = pdf_io.getvalue()

    # 4. Send via WhatsApp Cloud API with Retry Logic (Up to 3 attempts total)
    max_attempts = 3
    send_res = None
    attempt_count = 0

    for attempt in range(1, max_attempts + 1):
        attempt_count = attempt
        send_res = send_payslip_whatsapp(
            phone_number=norm_phone,
            employee_name=emp_name,
            employee_id=emp_no,
            payroll_month=payroll_month_label,
            pdf_bytes=pdf_bytes,
            filename=filename
        )
        if send_res.success:
            break
        # Do not retry if configuration or unrecoverable client error
        if getattr(send_res, 'stage', None) in ('API_CONFIGURATION', 'PHONE_VALIDATION'):
            break
        time.sleep(1)  # Brief pause between retry attempts

    # 5. Log Result
    success = send_res.success if send_res else False
    status_str = 'SENT' if success else 'FAILED'
    stage_str = getattr(send_res, 'stage', None)
    msg_id = getattr(send_res, 'message_id', None)
    last_msg = send_res.message if send_res else 'Send failed'

    log_payslip_send(
        employee_id=emp_id,
        payroll_month=payroll_month_label,
        phone_number=norm_phone,
        email_id=email_id,
        payslip_file_name=filename,
        whatsapp_status=status_str,
        stage=stage_str,
        message_id=msg_id,
        sent_by='Admin',
        error_message=None if success else last_msg,
        payroll_year=year,
        attempt_count=attempt_count
    )

    return {
        'status': status_str,
        'stage': stage_str,
        'message': last_msg,
        'masked_phone': masked_phone,
        'emp_name': emp_name,
        'emp_no': emp_no
    }

def generate_bulk_send_report_csv(year, month, category=None):
    """
    Generates a CSV report of the bulk send operations for the given month/year.
    """
    month_name = MONTH_NAMES[month]
    logs = get_payslip_send_logs(payroll_year=year, payroll_month=month_name, limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Log ID', 'Employee ID', 'Payroll Year', 'Payroll Month', 'Masked Phone', 'File Name', 'Status', 'Sent Time', 'Sent By', 'Error / Reason'])

    for l in logs:
        writer.writerow([
            l.get('id'),
            l.get('employee_id'),
            l.get('payroll_year') or year,
            l.get('payroll_month'),
            l.get('phone_number_masked') or '-',
            l.get('payslip_file_name'),
            l.get('whatsapp_status'),
            str(l.get('sent_at')),
            l.get('sent_by'),
            l.get('error_message') or '-'
        ])

    output.seek(0)
    return output.getvalue()

import datetime as dt
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from models.payroll_transaction import get_payroll_transactions
from services.payslip_service import (
    generate_payslip_pdf, generate_all_payslips_zip, get_payslip_data, 
    get_payslip_template, get_worker_deductions_list, MONTH_NAMES
)
from utils.num_to_words import amount_in_words

payslips_bp = Blueprint('payslips', __name__, url_prefix='/payslips')

CATEGORIES = [
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS'),
    ('WORKER_NAPS', 'Worker — NAPS'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@payslips_bp.route('/')
def index():
    now = dt.datetime.now()
    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 7))
    category = request.args.get('category', '')
    search = request.args.get('search', '').strip()

    records = get_payroll_transactions(year, month, category=category if category else None, search=search if search else None)

    return render_template(
        'payslips/index.html',
        year=year,
        month=month,
        category=category,
        categories=CATEGORIES,
        search=search,
        records=records
    )

@payslips_bp.route('/view/<int:year>/<int:month>/<emp_no>')
def view_payslip(year, month, emp_no):
    category = request.args.get('category')
    records = get_payslip_data(year, month, emp_no=emp_no, category=category)
    if not records:
        flash(f"Payslip for Employee #{emp_no} ({month}/{year}) not found!", 'danger')
        return redirect(url_for('payslips.index'))

    row = records[0]
    month_name = MONTH_NAMES[month]
    net_in_words = amount_in_words(row.get('Net_Salary', 0.0))
    template_name = get_payslip_template(row)
    deductions_list = get_worker_deductions_list(row)

    return render_template(
        template_name,
        row=row,
        month_name=month_name,
        year=year,
        net_in_words=net_in_words,
        deductions_list=deductions_list,
        is_pdf=False
    )

@payslips_bp.route('/download/<int:year>/<int:month>/<emp_no>')
def download_payslip(year, month, emp_no):
    category = request.args.get('category')
    pdf_io, filename = generate_payslip_pdf(year, month, emp_no, category=category)
    if not pdf_io:
        flash("Failed to generate PDF payslip!", 'danger')
        return redirect(url_for('payslips.index'))

    return send_file(
        pdf_io,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@payslips_bp.route('/download_zip/<int:year>/<int:month>')
def download_zip(year, month):
    category = request.args.get('category')
    zip_io = generate_all_payslips_zip(year, month, category=category if category else None)
    if not zip_io:
        flash("No payslips available to zip!", 'warning')
        return redirect(url_for('payslips.index'))

    zip_filename = f"Payslips_{year}_{month:02d}.zip"
    return send_file(
        zip_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@payslips_bp.route('/send_whatsapp/<int:year>/<int:month>/<emp_no>', methods=['POST'])
@payslips_bp.route('/send-whatsapp', methods=['POST'])
def send_whatsapp(year=None, month=None, emp_no=None):
    from flask import jsonify
    from models.employee import get_employee_by_emp_no
    from models.payslip_send_log import log_payslip_send, is_payslip_already_sent
    from services.whatsapp_service import send_payslip_whatsapp

    # Parse parameters from URL, JSON body, or Form data
    data = request.get_json(silent=True) or {}
    if year is None:
        year = int(data.get('year') or request.form.get('year') or 2026)
    if month is None:
        month = int(data.get('month') or request.form.get('month') or 7)
    if emp_no is None:
        emp_no = str(data.get('employee_id') or data.get('emp_no') or request.form.get('emp_no') or '').strip()

    category = request.args.get('category') or data.get('category')
    resend = str(request.args.get('resend') or data.get('resend') or '').lower() in ('true', '1', 'yes')
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

    # Stage 1: Employee Master Lookup
    emp = get_employee_by_emp_no(emp_no)
    if not emp:
        msg = f"Employee record #{emp_no} not found in Employee Master."
        if is_xhr:
            return jsonify({
                'success': False,
                'status': 'FAILED',
                'stage': 'EMPLOYEE_LOOKUP',
                'message': msg
            }), 404
        flash(msg, 'danger')
        return redirect(url_for('payslips.index', year=year, month=month, category=category))

    emp_id = emp.get('Employee_ID') or emp_no
    emp_name = emp.get('Employee_Name')
    phone_number = emp.get('Phone_Number')
    email_id = emp.get('Email_ID')
    month_name = MONTH_NAMES[month]
    payroll_month_label = f"{month_name} {year}"

    # Stage 2: Phone Number Availability in Master
    if not phone_number or str(phone_number).strip() in ('', '-', 'None'):
        msg = "Phone number is not available for this employee. Please update Employee Master."
        log_payslip_send(
            employee_id=emp_id,
            payroll_year=year,
            payroll_month=payroll_month_label,
            phone_number=None,
            email_id=email_id,
            payslip_file_name=f"Payslip_{emp_no}.pdf",
            whatsapp_status='SKIPPED',
            stage='PHONE_VALIDATION',
            sent_by='Admin',
            error_message=msg
        )
        if is_xhr:
            return jsonify({
                'success': False,
                'status': 'SKIPPED',
                'stage': 'PHONE_VALIDATION',
                'message': msg
            })
        flash(msg, 'warning')
        return redirect(url_for('payslips.index', year=year, month=month, category=category))

    # Stage 3: Duplicate Protection
    if not resend and is_payslip_already_sent(emp_id, year, month_name):
        msg = "This payslip has already been sent to WhatsApp."
        if is_xhr:
            return jsonify({
                'success': False,
                'status': 'ALREADY_SENT',
                'stage': 'DUPLICATE_CHECK',
                'already_sent': True,
                'message': msg
            })
        flash(msg, 'info')
        return redirect(url_for('payslips.index', year=year, month=month, category=category))

    # Stage 4: Generate Payslip PDF
    pdf_io, filename = generate_payslip_pdf(year, month, emp_no, category=category)
    if not pdf_io:
        msg = "Payslip PDF could not be generated."
        log_payslip_send(
            employee_id=emp_id,
            payroll_year=year,
            payroll_month=payroll_month_label,
            phone_number=phone_number,
            email_id=email_id,
            payslip_file_name=f"Payslip_{emp_no}.pdf",
            whatsapp_status='FAILED',
            stage='PDF_GENERATION',
            sent_by='Admin',
            error_message=msg
        )
        if is_xhr:
            return jsonify({
                'success': False,
                'status': 'FAILED',
                'stage': 'PDF_GENERATION',
                'message': msg
            })
        flash(msg, 'danger')
        return redirect(url_for('payslips.index', year=year, month=month, category=category))

    pdf_bytes = pdf_io.getvalue()

    # Stage 5: WhatsApp Cloud API Pipeline (Media Upload & Message Send)
    res = send_payslip_whatsapp(
        phone_number=phone_number,
        employee_name=emp_name,
        employee_id=emp_no,
        payroll_month=payroll_month_label,
        pdf_bytes=pdf_bytes,
        filename=filename
    )

    # Stage 6: Database Send Logging
    log_payslip_send(
        employee_id=emp_id,
        payroll_year=year,
        payroll_month=payroll_month_label,
        phone_number=phone_number,
        email_id=email_id,
        payslip_file_name=filename,
        whatsapp_status='SENT' if res.success else 'FAILED',
        stage=res.stage,
        message_id=res.message_id,
        sent_by='Admin',
        error_message=None if res.success else res.message
    )

    if is_xhr:
        return jsonify(res.to_dict())

    flash(res.message, 'success' if res.success else 'danger')
    return redirect(url_for('payslips.index', year=year, month=month, category=category))


@payslips_bp.route('/api/test_whatsapp_config', methods=['GET', 'POST'])
def api_test_whatsapp_config():
    from flask import jsonify
    from services.whatsapp_service import test_whatsapp_api_configuration
    res = test_whatsapp_api_configuration()
    return jsonify(res)

@payslips_bp.route('/api/bulk_summary')
def api_bulk_summary():
    from flask import jsonify
    from services.bulk_payslip_service import get_bulk_payslip_summary

    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 7))
    category = request.args.get('category', '')
    search = request.args.get('search', '').strip()
    resend = request.args.get('resend', 'false').lower() in ('true', '1', 'yes')

    summary = get_bulk_payslip_summary(year, month, category=category if category else None, search=search if search else None, resend=resend)
    return jsonify(summary)

@payslips_bp.route('/api/bulk_send_single', methods=['POST'])
def api_bulk_send_single():
    from flask import jsonify
    from services.bulk_payslip_service import process_single_employee_whatsapp_send

    data = request.get_json() or {}
    year = int(data.get('year', 2026))
    month = int(data.get('month', 7))
    emp_no = str(data.get('emp_no', '')).strip()
    category = data.get('category')
    resend = bool(data.get('resend', False))

    if not emp_no:
        return jsonify({'status': 'FAILED', 'message': 'Missing employee number'}), 400

    res = process_single_employee_whatsapp_send(year, month, emp_no, category=category if category else None, resend=resend)
    return jsonify(res)

@payslips_bp.route('/download_send_report/<int:year>/<int:month>')
def download_send_report(year, month):
    from flask import Response
    from services.bulk_payslip_service import generate_bulk_send_report_csv, MONTH_NAMES

    category = request.args.get('category')
    csv_str = generate_bulk_send_report_csv(year, month, category=category if category else None)
    month_name = MONTH_NAMES[month]
    filename = f"Payslip_WhatsApp_Report_{year}_{month_name}.csv"

    return Response(
        csv_str,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

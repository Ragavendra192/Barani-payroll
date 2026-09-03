import os
import datetime as dt
import pandas as pd
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from models.employee import get_all_employees, get_employee_by_id, add_employee, update_employee, toggle_employee_status, bulk_import_employees
from models.payroll_transaction import get_payroll_transactions, get_payroll_attendance, save_payroll_batch
from models.payroll_period_settings import get_period_settings, save_period_settings
from models.payroll_period_settings import get_period_settings, save_period_settings, get_period_settings_info, calculate_month_working_days
from services.payroll_engine import calculate_payroll
from utils.payroll_calculation_engine import get_worker_calculation_trace, get_staff_pf_esi_calculation_trace
from utils.contact_utils import normalize_indian_phone, mask_phone_number

main_bp = Blueprint('main', __name__)

CATEGORIES = [
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS Apprentice'),
    ('WORKER_NAPS', 'Worker — NAPS Apprentice'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@main_bp.route('/api/attendance/month/<int:year>/<int:month>')
@main_bp.route('/api/payroll/attendance/<int:year>/<int:month>')
def api_get_attendance(year, month):
    period_info = get_period_settings_info(year, month)
    records = get_payroll_attendance(year, month)
    att_dict = {}
    for r in records:
        emp_id = str(r['Employee_ID'])
        emp_no = str(r.get('Emp_No') or emp_id)
        entry = {
            "present": float(r.get('Present_Days') or 0.0),
            "el": float(r.get('EL') or 0.0),
            "cl": float(r.get('CL') or 0.0),
            "sl": float(r.get('SL') or 0.0),
            "nh": float(r.get('NH') or 0.0),
            "ot_hours": float(r.get('Act_OT_Hrs') or 0.0)
        }
        att_dict[emp_id] = entry
        att_dict[emp_no] = entry

    return jsonify({
        "year": year,
        "month": month,
        "calendar_days": period_info['calendar_days'],
        "sunday_count": period_info['sunday_count'],
        "default_working_days": period_info['default_working_days'],
        "standard_working_days": period_info['standard_working_days'],
        "attendance": att_dict
    })

# ============================================================
# 0. REDIRECT ROOT TO MASTER PAGE (/)
# ============================================================
@main_bp.route('/')
def home():
    return redirect(url_for('main.master'))


# ============================================================
# 1. EMPLOYEE MASTER PAGE (/master)
# ============================================================
@main_bp.route('/master', methods=['GET', 'POST'])
def master():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'ALL')
    emp_type = request.args.get('employee_type', 'ALL')
    pay_cat = request.args.get('payroll_category', 'ALL')
    dept = request.args.get('department', 'ALL')
    status = request.args.get('status', 'Active')

    employees = get_all_employees(status=status if status != 'ALL' else None)

    if category and category != 'ALL':
        employees = [e for e in employees if e.get('Category') == category or f"{e.get('Employee_Type')}_{e.get('Payroll_Category')}" == category]
    if emp_type and emp_type != 'ALL':
        employees = [e for e in employees if e.get('Employee_Type') == emp_type]
    if pay_cat and pay_cat != 'ALL':
        employees = [e for e in employees if e.get('Payroll_Category') == pay_cat]
    if dept and dept != 'ALL':
        employees = [e for e in employees if e.get('Department') == dept]
    if search:
        s = search.lower()
        employees = [e for e in employees if s in str(e.get('Emp_No')).lower() or s in str(e.get('Employee_Name')).lower() or s in str(e.get('Emp_Name')).lower()]

    all_depts = sorted(list(set(e.get('Department') for e in get_all_employees(status=None) if e.get('Department'))))

    return render_template(
        'master.html',
        employees=employees,
        categories=CATEGORIES,
        selected_category=category,
        selected_type=emp_type,
        selected_pay_cat=pay_cat,
        selected_dept=dept,
        search=search,
        status=status,
        departments=all_depts
    )


@main_bp.route('/master/download-template', methods=['GET'])
def download_employee_template():
    """Download Employee Master Excel Template for HR."""
    template_path = os.path.join(current_app.root_path, 'static', 'Employee_Master_Import_Template.xlsx')
    if not os.path.exists(template_path):
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'Employee_Master_Import_Template.xlsx')
    
    return send_file(
        template_path,
        as_attachment=True,
        download_name='Employee_Master_Import_Template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@main_bp.route('/master/import', methods=['POST'])
def import_employees():
    """Process uploaded Excel file for Employee Master bulk import."""
    file = request.files.get('file')
    if not file or file.filename == '':
        flash("Please select an Excel file (.xlsx or .xls) to upload.", "danger")
        return redirect(url_for('main.master'))

    try:
        excel_bytes = file.read()
        xl = pd.ExcelFile(io.BytesIO(excel_bytes))
        sheet_name = 'Employee_Master' if 'Employee_Master' in xl.sheet_names else xl.sheet_names[0]
        df = pd.read_excel(xl, sheet_name=sheet_name)

        res = bulk_import_employees(df)

        if res['total'] == 0:
            flash("No valid employee rows found in the uploaded Excel file.", "warning")
        else:
            msg = f"Excel Import Complete: Total {res['total']} employees processed. ({res['inserted']} New Inserted, {res['updated']} Existing Updated)."
            flash(msg, "success")

        if res['errors']:
            for err in res['errors'][:5]:
                flash(err, "danger")
            if len(res['errors']) > 5:
                flash(f"... and {len(res['errors']) - 5} more row warnings.", "danger")

    except Exception as e:
        flash(f"Import Failed: Could not process Excel file. Error: {str(e)}", "danger")

    return redirect(url_for('main.master'))


MONTHS = [
    (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
]
YEARS = [2025, 2026, 2027, 2028]

# ============================================================
# 2. ATTENDANCE PAGE (/attendance)
# ============================================================
@main_bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    now = dt.datetime.now()
    if request.method == 'POST':
        year = int(request.form.get('year') or request.args.get('year') or 2026)
        month = int(request.form.get('month') or request.args.get('month') or 7)
    else:
        year = int(request.args.get('year') or request.form.get('year') or 2026)
        month = int(request.args.get('month') or request.form.get('month') or 7)
    
    category = request.form.get('category') or request.args.get('category') or 'ALL'
    emp_type = request.form.get('employee_type') or request.args.get('employee_type') or 'ALL'
    dept = request.form.get('department') or request.args.get('department') or 'ALL'
    search = request.form.get('search')
    if search is None:
        search = request.args.get('search', '')
    search = search.strip()

    action = request.form.get('action') or request.args.get('action')
    form_std_days = request.form.get('standard_days') or request.args.get('standard_days')

    # Get period info with calendar calculation
    period_info = get_period_settings_info(year, month)
    calendar_days = period_info['calendar_days']
    sunday_count = period_info['sunday_count']
    default_working_days = period_info['default_working_days']

    if action == 'apply_std_days' and form_std_days:
        try:
            val = float(form_std_days)
            if val <= 0:
                raise ValueError("Working days must be > 0")
            save_period_settings(year, month, val)
            standard_days = val
            flash(f"Working Days saved as {standard_days} for {month}/{year}!", "success")
            return redirect(url_for('main.attendance', year=year, month=month, category=category, employee_type=emp_type, department=dept, search=search))
        except Exception as e:
            flash(f"Invalid Working Days: {str(e)}", "danger")

    if form_std_days and float(form_std_days) > 0:
        standard_days = float(form_std_days)
    else:
        standard_days = period_info['standard_working_days']

    # Fetch active employees
    employees = get_all_employees(status='Active')
    if emp_type and emp_type.upper() != 'ALL':
        employees = [e for e in employees if e.get('Employee_Type') == emp_type]
    if category and category.upper() != 'ALL':
        employees = [e for e in employees if e.get('Category') == category or f"{e.get('Employee_Type')}_{e.get('Payroll_Category')}" == category]
    if dept and dept.upper() != 'ALL':
        employees = [e for e in employees if e.get('Department') == dept]
    if search:
        s = search.lower()
        employees = [e for e in employees if s in str(e.get('Emp_No')).lower() or s in str(e.get('Employee_Name')).lower()]

    existing_trans = get_payroll_transactions(year, month)
    trans_map = {t['Employee_ID']: t for t in existing_trans}

    if request.method == 'POST' and action == 'save_attendance':
        # Process and save attendance draft batch
        calculated_rows = []
        for emp in employees:
            emp_id = emp['Employee_ID']
            prefix = f"emp_{emp_id}_"
            present_days = float(request.form.get(f"{prefix}present_days", 0.0) or 0.0)
            nh_days = float(request.form.get(f"{prefix}nh", 0.0) or 0.0)
            el_days = float(request.form.get(f"{prefix}el", 0.0) or 0.0)
            cl_days = float(request.form.get(f"{prefix}cl", 0.0) or 0.0)
            sl_days = float(request.form.get(f"{prefix}sl", 0.0) or 0.0)
            act_ot = float(request.form.get(f"{prefix}act_ot", 0.0) or 0.0)

            att_dict = {'present_days': present_days, 'nh': nh_days, 'cl': cl_days, 'sl': sl_days, 'el': el_days, 'actual_ot_hours': act_ot}
            sal_dict = {'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
            
            # Preserve existing deductions if present
            existing_t = trans_map.get(emp_id) or {}
            ded_dict = {'arrears': float(existing_t.get('Arrears', 0.0) or 0.0), 'naps': float(existing_t.get('NAPS_Deduction', 0.0) or 0.0), 'lic': float(existing_t.get('LIC_Deduction', 0.0) or 0.0), 'advance': float(existing_t.get('Advance_Deduction', 0.0) or 0.0), 'accommodation': float(existing_t.get('Accommodation_Deduction', 0.0) or 0.0), 'other': float(existing_t.get('Other_Deduction', 0.0) or 0.0)}

            calc_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            calculated_rows.append(calc_res)

        try:
            save_period_settings(year, month, standard_days)
            save_payroll_batch(year, month, calculated_rows, standard_days=standard_days)
            flash(f"Attendance for {month}/{year} saved successfully!", "success")
            return redirect(url_for('main.attendance', year=year, month=month, category=category, employee_type=emp_type, department=dept, search=search))
        except Exception as e:
            flash(f"Error saving attendance: {str(e)}", "danger")

    elif request.method == 'POST' and action == 'import_excel':
        import_file = request.files.get('import_file')
        if not import_file or import_file.filename == '':
            flash('No file selected for import.', 'danger')
            return redirect(url_for('main.attendance', year=year, month=month))
        
        try:
            df = pd.read_excel(import_file)
            import_data = {}
            for _, r in df.iterrows():
                try:
                    eid = int(r.get('Emp ID', 0))
                    import_data[eid] = r
                except:
                    pass

            calculated_rows = []
            for emp in employees:
                emp_id = emp['Employee_ID']
                emp_no = int(emp['Emp_No'])
                r_data = import_data.get(emp_no, {})
                existing_t = trans_map.get(emp_id) or {}
                
                present_days = float(r_data.get('Present', standard_days)) if pd.notna(r_data.get('Present')) else float(existing_t.get('Present_Days', standard_days))
                nh_days = float(r_data.get('N/H', 0.0)) if pd.notna(r_data.get('N/H')) else float(existing_t.get('NH', 0.0))
                el_days = float(r_data.get('EL', 0.0)) if pd.notna(r_data.get('EL')) else float(existing_t.get('EL', 0.0))
                cl_days = float(r_data.get('CL', 0.0)) if pd.notna(r_data.get('CL')) else float(existing_t.get('CL', 0.0))
                sl_days = float(r_data.get('SL', 0.0)) if pd.notna(r_data.get('SL')) else float(existing_t.get('SL', 0.0))
                act_ot = float(r_data.get('OT Hours', 0.0)) if pd.notna(r_data.get('OT Hours')) else float(existing_t.get('Act_OT_Hrs', 0.0))

                att_dict = {'present_days': present_days, 'nh': nh_days, 'cl': cl_days, 'sl': sl_days, 'el': el_days, 'actual_ot_hours': act_ot}
                sal_dict = {'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
                
                ded_dict = {
                    'arrears': float(r_data.get('Arrears', 0.0)) if pd.notna(r_data.get('Arrears')) else float(existing_t.get('Arrears', 0.0)),
                    'naps': float(r_data.get('NAPS', 0.0)) if pd.notna(r_data.get('NAPS')) else float(existing_t.get('NAPS_Deduction', 0.0)),
                    'lic': float(r_data.get('LIC', 0.0)) if pd.notna(r_data.get('LIC')) else float(existing_t.get('LIC_Deduction', 0.0)),
                    'advance': float(r_data.get('Advance', 0.0)) if pd.notna(r_data.get('Advance')) else float(existing_t.get('Advance_Deduction', 0.0)),
                    'accommodation': float(r_data.get('Accommodation', 0.0)) if pd.notna(r_data.get('Accommodation')) else float(existing_t.get('Accommodation_Deduction', 0.0)),
                    'other': float(r_data.get('Other', 0.0)) if pd.notna(r_data.get('Other')) else float(existing_t.get('Other_Deduction', 0.0))
                }

                calc_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
                calculated_rows.append(calc_res)

            save_period_settings(year, month, standard_days)
            save_payroll_batch(year, month, calculated_rows, standard_days=standard_days)
            flash(f"Monthly data imported and saved successfully for {len(calculated_rows)} employees!", "success")
        except Exception as e:
            flash(f"Error importing excel: {str(e)}", "danger")
        return redirect(url_for('main.attendance', year=year, month=month, category=category, employee_type=emp_type, department=dept, search=search))

    elif action == 'download_template':
        data = []
        for emp in employees:
            emp_id = emp['Employee_ID']
            existing_t = trans_map.get(emp_id) or {}
            data.append({
                'Emp ID': emp['Emp_No'],
                'Employee Name': emp['Employee_Name'],
                'Type': emp.get('Employee_Type', ''),
                'Category': emp.get('Category', ''),
                'Company Working Days': standard_days,
                'Present': existing_t.get('Present_Days', standard_days),
                'N/H': existing_t.get('NH', 0.0),
                'EL': existing_t.get('EL', 0.0),
                'CL': existing_t.get('CL', 0.0),
                'SL': existing_t.get('SL', 0.0),
                'OT Hours': existing_t.get('Act_OT_Hrs', 0.0),
                'Arrears': existing_t.get('Arrears', 0.0),
                'NAPS': existing_t.get('NAPS_Deduction', 0.0),
                'LIC': existing_t.get('LIC_Deduction', 0.0),
                'Advance': existing_t.get('Advance_Deduction', 0.0),
                'Accommodation': existing_t.get('Accommodation_Deduction', 0.0),
                'Other': existing_t.get('Other_Deduction', 0.0)
            })
        df = pd.DataFrame(data)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Monthly_Input')
        out.seek(0)
        return send_file(out, download_name=f"Monthly_Input_Template_{month}_{year}.xlsx", as_attachment=True)

    # Read month-specific attendance records from PayrollAttendance
    att_records = get_payroll_attendance(year, month)
    att_map = {r['Employee_ID']: r for r in att_records}

    attendance_rows = []
    for emp in employees:
        emp_id = emp['Employee_ID']
        if emp_id in att_map:
            r = att_map[emp_id]
            pres = float(r.get('Present_Days') if r.get('Present_Days') is not None else 0.0)
            nh = float(r.get('NH') or 0.0)
            el = float(r.get('EL') or 0.0)
            cl = float(r.get('CL') or 0.0)
            sl = float(r.get('SL') or 0.0)
            act_ot = float(r.get('Act_OT_Hrs') or 0.0)
            tot_days = pres + nh + el + cl + sl
            lop = max(0.0, standard_days - tot_days)
            row = {
                'Employee_ID': emp_id,
                'Emp_No': emp['Emp_No'],
                'Employee_Name': emp['Employee_Name'],
                'Employee_Type': emp['Employee_Type'],
                'Category': emp.get('Category') or f"{emp.get('Employee_Type')}_{emp.get('Payroll_Category')}",
                'Department': emp.get('Department', ''),
                'Working_Days': standard_days,
                'Present_Days': pres,
                'NH': nh,
                'EL': el,
                'CL': cl,
                'SL': sl,
                'LOP_Days': lop,
                'Act_OT_Hrs': act_ot
            }
        else:
            # NEW MONTH WITH NO SAVED DATA -> RESET TO 0.0! (Do NOT load previous month!)
            row = {
                'Employee_ID': emp_id,
                'Emp_No': emp['Emp_No'],
                'Employee_Name': emp['Employee_Name'],
                'Employee_Type': emp['Employee_Type'],
                'Category': emp.get('Category') or f"{emp.get('Employee_Type')}_{emp.get('Payroll_Category')}",
                'Department': emp.get('Department', ''),
                'Working_Days': standard_days,
                'Present_Days': 0.0,
                'NH': 0.0,
                'EL': 0.0,
                'CL': 0.0,
                'SL': 0.0,
                'LOP_Days': standard_days,
                'Act_OT_Hrs': 0.0
            }
        attendance_rows.append(row)

    all_depts = sorted(list(set(e.get('Department') for e in get_all_employees(status=None) if e.get('Department'))))

    return render_template(
        'attendance.html',
        year=year,
        month=month,
        category=category,
        emp_type=emp_type,
        dept=dept,
        search=search,
        calendar_days=calendar_days,
        sunday_count=sunday_count,
        default_working_days=default_working_days,
        standard_days=standard_days,
        rows=attendance_rows,
        categories=CATEGORIES,
        departments=all_depts,
        months=MONTHS,
        years=YEARS
    )

# ============================================================
# 3. WAGES PAGE (/wages)
# ============================================================
@main_bp.route('/wages', methods=['GET', 'POST'])
def wages():
    now = dt.datetime.now()
    if request.method == 'POST':
        year = int(request.form.get('year') or request.args.get('year') or 2026)
        month = int(request.form.get('month') or request.args.get('month') or 7)
        category = request.form.get('category') if request.form.get('category') is not None else (request.args.get('category') or 'ALL')
        dept = request.form.get('department') if request.form.get('department') is not None else (request.args.get('department') or 'ALL')
        search = request.form.get('search')
        if search is None:
            search = request.args.get('search', '')
        search = search.strip()
    else:
        year = int(request.args.get('year') or 2026)
        month = int(request.args.get('month') or 7)
        category = request.args.get('category') or 'ALL'
        dept = request.args.get('department') or 'ALL'
        search = request.args.get('search', '').strip()

    action = request.form.get('action')
    form_std_days = request.form.get('standard_days') or request.args.get('standard_days')

    period_info = get_period_settings_info(year, month)
    standard_days = float(form_std_days) if form_std_days and float(form_std_days) > 0 else period_info['standard_working_days']

    # Fetch active employees (ORDERED BY STAFF FIRST, THEN WORKER)
    employees = get_all_employees(status='Active')
    
    # Category is ONLY a filter! Order STAFF first, WORKER second.
    if category and category.upper() != 'ALL':
        if category.upper() in ('STAFF', 'WORKER'):
            employees = [e for e in employees if e.get('Employee_Type') == category.upper()]
        else:
            employees = [e for e in employees if e.get('Category') == category or f"{e.get('Employee_Type')}_{e.get('Payroll_Category')}" == category]
    
    if dept and dept.upper() != 'ALL':
        employees = [e for e in employees if e.get('Department') == dept]
    if search:
        s = search.lower()
        employees = [e for e in employees if s in str(e.get('Emp_No')).lower() or s in str(e.get('Employee_Name')).lower()]

    existing_trans = get_payroll_transactions(year, month)
    trans_map = {t['Employee_ID']: t for t in existing_trans}
    has_saved_payroll = any(t.get('PayrollTransaction_ID') is not None for t in existing_trans)

    adv_balances = {}
    from db import get_db_connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Emp_No, ISNULL(SUM(Remaining_Amount), 0) FROM Advances GROUP BY Emp_No")
        adv_balances = {str(row[0]): float(row[1]) for row in cur.fetchall()}
        conn.close()
    except Exception as e:
        pass

    calculated_rows = []

    def get_f(key, default_val=0.0):
        val = request.form.get(key)
        if val is not None and str(val).strip() != '':
            try:
                return float(val)
            except Exception:
                pass
        return float(default_val or 0.0)

    if request.method == 'POST' and action in ('calculate', 'save'):
        for emp in employees:
            emp_id = emp['Employee_ID']
            prefix = f"emp_{emp_id}_"

            existing_t = trans_map.get(emp_id) or {}
            present_days = get_f(f"{prefix}present_days", existing_t.get('Present_Days', 0.0))
            nh_days = get_f(f"{prefix}nh", existing_t.get('NH', 0.0))
            el_days = get_f(f"{prefix}el", existing_t.get('EL', 0.0))
            cl_days = get_f(f"{prefix}cl", existing_t.get('CL', 0.0))
            sl_days = get_f(f"{prefix}sl", existing_t.get('SL', 0.0))
            act_ot = get_f(f"{prefix}act_ot", existing_t.get('Act_OT_Hrs', 0.0))

            att_dict = {'present_days': present_days, 'nh': nh_days, 'cl': cl_days, 'sl': sl_days, 'el': el_days, 'actual_ot_hours': act_ot}
            sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}

            ded_dict = {
                'arrears': get_f(f"{prefix}arrears", existing_t.get('Arrears', 0.0)),
                'naps': get_f(f"{prefix}naps", existing_t.get('NAPS_Deduction', 0.0)),
                'lic': get_f(f"{prefix}lic", existing_t.get('LIC_Deduction', emp.get('LIC', 0.0))),
                'advance': get_f(f"{prefix}advance", existing_t.get('Advance_Deduction', 0.0)),
                'accommodation': get_f(f"{prefix}accommodation", existing_t.get('Accommodation_Deduction', 0.0)),
                'other': get_f(f"{prefix}other", existing_t.get('Other_Deduction', 0.0))
            }

            calc_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            calc_res['Opening_Advance'] = adv_balances.get(str(emp['Emp_No']), 0.0)
            calculated_rows.append(calc_res)

        if action == 'save':
            try:
                save_period_settings(year, month, standard_days)
                save_payroll_batch(year, month, calculated_rows, standard_days=standard_days)
                flash(f"Wages Payroll for {month}/{year} saved successfully!", 'success')
                return redirect(url_for('main.wages', year=year, month=month, category=category, department=dept, search=search))
            except Exception as e:
                flash(f"Error saving wages: {str(e)}", 'danger')

    elif action == 'refresh_attendance' or has_saved_payroll:
        if action == 'refresh_attendance':
            flash(f"Attendance & Payroll data refreshed from SQL Server database for {month}/{year}!", 'success')
        for emp in employees:
            t = trans_map.get(emp['Employee_ID']) or {}
            present_days = float(t.get('Present_Days') if t.get('Present_Days') is not None else 0.0)
            nh_days = float(t.get('NH') or t.get('PH') or 0.0)
            el_days = float(t.get('EL') or t.get('PL') or 0.0)
            cl_days = float(t.get('CL') or 0.0)
            sl_days = float(t.get('SL') or 0.0)
            act_ot = float(t.get('Act_OT_Hrs') or t.get('Actual_OT_Hours') or 0.0)

            att_dict = {'present_days': present_days, 'nh': nh_days, 'cl': cl_days, 'sl': sl_days, 'el': el_days, 'actual_ot_hours': act_ot}
            sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}

            ded_dict = {
                'arrears': float(t.get('Arrears', 0.0) or 0.0),
                'naps': float(t.get('NAPS_Deduction', 0.0) or 0.0),
                'lic': float(t.get('LIC_Deduction', emp.get('LIC', 0.0)) or emp.get('LIC', 0.0)),
                'advance': float(t.get('Advance_Deduction', 0.0) or 0.0),
                'accommodation': float(t.get('Accommodation_Deduction', 0.0) or 0.0),
                'other': float(t.get('Other_Deduction', 0.0) or 0.0)
            }

            c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            c_res['Opening_Advance'] = adv_balances.get(str(emp['Emp_No']), 0.0)
            calculated_rows.append(c_res)
    else:
        # NEW MONTH WITH NO SAVED PAYROLL YET -> DO NOT SHOW PREVIOUS MONTH!
        calculated_rows = []

    tot_emp = len(calculated_rows)
    tot_gross = sum(float(r.get('Gross_Wages', 0.0) or 0.0) for r in calculated_rows)
    tot_pf = sum(float(r.get('PF_Deduction', 0.0) or 0.0) for r in calculated_rows)
    tot_esi = sum(float(r.get('ESI_Deduction', 0.0) or 0.0) for r in calculated_rows)
    tot_ded = sum(float(r.get('Total_Deduction', 0.0) or 0.0) for r in calculated_rows)
    tot_net = sum(float(r.get('Net_Salary', 0.0) or 0.0) for r in calculated_rows)

    all_depts = sorted(list(set(e.get('Department') for e in get_all_employees(status=None) if e.get('Department'))))

    return render_template(
        'wages.html',
        year=year,
        month=month,
        category=category,
        dept=dept,
        search=search,
        standard_days=standard_days,
        rows=calculated_rows,
        tot_emp=tot_emp,
        tot_gross=tot_gross,
        tot_pf=tot_pf,
        tot_esi=tot_esi,
        tot_ded=tot_ded,
        tot_net=tot_net,
        categories=CATEGORIES,
        departments=all_depts,
        months=MONTHS,
        years=YEARS
    )

@main_bp.route('/wages/download_excel/<int:year>/<int:month>')
def download_wages_excel(year, month):
    from flask import send_file
    from services.wages_excel_exporter import generate_wages_excel

    category = request.args.get('category', 'ALL')
    excel_io, filename = generate_wages_excel(year, month, category_filter=category)
    if not excel_io:
        flash("No payroll data available to export for this month.", 'warning')
        return redirect(url_for('main.wages', year=year, month=month, category=category))

    return send_file(
        excel_io,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# ============================================================
# 4. PAYSLIP PAGE (/payslip)
# ============================================================
@main_bp.route('/payslip')
def payslip():
    now = dt.datetime.now()
    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 7))
    category = request.args.get('category', '')
    search = request.args.get('search', '').strip()

    all_emps = get_all_employees(status=None)
    all_depts = sorted(list(set(e.get('Department') for e in all_emps if e.get('Department'))))
    records = get_payroll_transactions(year, month, category=category if category else None, search=search if search else None)

    # Attach contact info to records
    emp_map = {str(e.get('Emp_No')).strip(): e for e in all_emps}
    for r in records:
        emp_key = str(r.get('Emp_No')).strip()
        e_info = emp_map.get(emp_key) or {}
        r['Phone_Number'] = e_info.get('Phone_Number')
        phone_norm = normalize_indian_phone(e_info.get('Phone_Number'))
        r['Phone_Number_Masked'] = mask_phone_number(phone_norm) if phone_norm else '-'
        r['Email_ID'] = e_info.get('Email_ID')

    # Fetch send log stats
    from models.payslip_send_log import get_payslip_send_logs
    from services.payslip_service import MONTH_NAMES
    month_name = MONTH_NAMES[month]
    send_logs = get_payslip_send_logs(payroll_year=year, payroll_month=month_name, limit=1000)
    
    sent_count = len([l for l in send_logs if l.get('whatsapp_status') == 'SENT'])
    failed_count = len([l for l in send_logs if l.get('whatsapp_status') == 'FAILED'])
    skipped_count = len([l for l in send_logs if l.get('whatsapp_status') == 'SKIPPED'])

    return render_template(
        'payslip.html',
        year=year,
        month=month,
        category=category,
        search=search,
        records=records,
        categories=CATEGORIES,
        departments=all_depts,
        months=MONTHS,
        years=YEARS,
        sent_count=sent_count,
        failed_count=failed_count,
        skipped_count=skipped_count
    )

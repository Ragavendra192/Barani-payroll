import datetime as dt
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.employee import get_all_employees, get_employee_by_id
from models.payroll_transaction import get_payroll_transactions, save_payroll_batch
from models.payroll_period_settings import get_period_settings, save_period_settings
from services.payroll_engine import calculate_payroll
from utils.payroll_calculation_engine import get_worker_calculation_trace, get_staff_pf_esi_calculation_trace

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')

CATEGORIES = [
    ('ALL', 'All Categories (Staff & Worker)'),
    ('STAFF', 'All Staff Employees'),
    ('WORKER', 'All Worker Employees'),
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS Apprentice'),
    ('WORKER_NAPS', 'Worker — NAPS Apprentice'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@payroll_bp.route('/', methods=['GET', 'POST'])
def dynamic_payroll():
    now = dt.datetime.now()
    if request.method == 'POST':
        year = int(request.form.get('year') or request.args.get('year') or 2026)
        month = int(request.form.get('month') or request.args.get('month') or 7)
        raw_cat = request.form.get('category') or request.args.get('category') or 'ALL'
    else:
        year = int(request.args.get('year') or request.form.get('year') or 2026)
        month = int(request.args.get('month') or request.form.get('month') or 7)
        raw_cat = request.args.get('category') or request.form.get('category') or 'ALL'
    
    category = raw_cat.strip().upper()
    if not category:
        category = 'ALL'

    # Retrieve global Standard Working Days from PayrollPeriodSettings
    db_std_days = get_period_settings(year, month)
    form_std_days = request.form.get('standard_days') or request.args.get('standard_days')
    
    action = request.form.get('action')

    if action == 'apply_std_days' and form_std_days:
        try:
            val = float(form_std_days)
            if val <= 0:
                raise ValueError("Working days must be greater than 0")
            save_period_settings(year, month, val)
            standard_days = val
            flash(f"Standard Working Days set to {standard_days} globally for {month}/{year}!", "success")
            return redirect(url_for('payroll.dynamic_payroll', year=year, month=month, category=category, standard_days=standard_days))
        except Exception as e:
            flash(f"Invalid Standard Working Days input: {str(e)}", "danger")

    if form_std_days and float(form_std_days) > 0:
        standard_days = float(form_std_days)
    elif db_std_days is not None:
        standard_days = db_std_days
    else:
        standard_days = 26.0

    # Fetch active employees (ORDERED BY STAFF FIRST, THEN WORKER SECOND)
    if category in ('STAFF', 'WORKER'):
        employees = get_all_employees(employee_type=category, status='Active')
    elif category != 'ALL':
        employees = get_all_employees(category=category, status='Active')
    else:
        employees = get_all_employees(category=None, status='Active')

    # Check if saved transactions already exist for year/month
    existing_trans = get_payroll_transactions(year, month)
    trans_map = {t['Employee_ID']: t for t in existing_trans}

    calculated_rows = []
    validation_errors = []

    if request.method == 'POST' and action in ('calculate', 'save'):
        for emp in employees:
            emp_id = emp['Employee_ID']
            emp_no = emp.get('Emp_No', emp_id)
            emp_cat = emp.get('Category', 'STAFF_PF_ESI')
            prefix = f"emp_{emp_id}_"

            present_days = float(request.form.get(f"{prefix}present_days", standard_days) or standard_days)
            nh_days = float(request.form.get(f"{prefix}nh", 0.0) or 0.0)
            el_days = float(request.form.get(f"{prefix}el", 0.0) or 0.0)
            cl_days = float(request.form.get(f"{prefix}cl", 0.0) or 0.0)
            sl_days = float(request.form.get(f"{prefix}sl", 0.0) or 0.0)
            act_ot = float(request.form.get(f"{prefix}act_ot", 0.0) or 0.0)

            # Input Validation Rules
            if present_days > standard_days:
                validation_errors.append(f"Employee {emp_no} ({emp['Employee_Name']}): Present Days ({present_days}) cannot exceed Standard Working Days ({standard_days}).")
            if present_days < 0 or act_ot < 0 or cl_days < 0 or el_days < 0 or nh_days < 0 or sl_days < 0:
                validation_errors.append(f"Employee {emp_no} ({emp['Employee_Name']}): Attendance and OT inputs cannot be negative.")

            tot_days = present_days + nh_days + el_days + cl_days + sl_days

            att_dict = {
                'present_days': present_days,
                'nh': nh_days,
                'ph': nh_days,
                'cl': cl_days,
                'sl': sl_days,
                'el': el_days,
                'pl': el_days,
                'total_days': tot_days,
                'working_days': standard_days,
                'actual_ot_hours': act_ot,
                'ot_hours': min(act_ot, 50.0) if 'WORKER' in emp_cat else act_ot
            }

            sal_dict = {
                'Basic_DA': emp.get('Basic_DA', 0.0),
                'HRA': emp.get('HRA', 0.0),
                'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0),
                'Washing_Allowance': emp.get('Washing_Allowance', 0.0),
                'Other_Allowance': emp.get('Other_Allowance', 0.0),
                'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0),
                'OT_Rate': emp.get('OT_Rate', 56.25),
                'PF_Eligible': emp.get('PF_Eligible', True),
                'ESI_Eligible': emp.get('ESI_Eligible', True)
            }

            ded_dict = {
                'arrears': float(request.form.get(f"{prefix}arrears", 0.0) or 0.0),
                'naps': float(request.form.get(f"{prefix}naps", 0.0) or 0.0),
                'lic': float(request.form.get(f"{prefix}lic", emp.get('LIC', 0.0)) or emp.get('LIC', 0.0)),
                'advance': float(request.form.get(f"{prefix}advance", 0.0) or 0.0),
                'accommodation': float(request.form.get(f"{prefix}accommodation", 0.0) or 0.0),
                'other': float(request.form.get(f"{prefix}other", 0.0) or 0.0)
            }

            calc_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            calc_res['NH'] = nh_days
            calc_res['CL'] = cl_days
            calc_res['EL'] = el_days
            calc_res['SL'] = sl_days
            calculated_rows.append(calc_res)

        if validation_errors:
            for err in validation_errors:
                flash(err, 'danger')

        if action == 'save' and not validation_errors:
            try:
                # Save standard working days period setting
                save_period_settings(year, month, standard_days)
                save_payroll_batch(year, month, calculated_rows, standard_days=standard_days)
                flash(f"Payroll for {month}/{year} saved successfully! (Standard Days: {standard_days})", 'success')
                return redirect(url_for('payroll.dynamic_payroll', year=year, month=month, category=category, standard_days=standard_days))
            except Exception as e:
                flash(f"Error saving payroll: {str(e)}", 'danger')

    elif trans_map:
        for emp in employees:
            t = trans_map.get(emp['Employee_ID'])
            if t and float(t.get('Gross_Wages', 0.0) or 0.0) > 0.0:
                # Force global standard days on saved row
                t['Working_Days'] = standard_days
                calculated_rows.append(t)
            else:
                att_dict = {'present_days': standard_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': standard_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
                ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': float(emp.get('LIC', 0.0) or 0.0), 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
                sal_dict = {
                    'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0),
                    'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0),
                    'Washing_Allowance': emp.get('Washing_Allowance', 0.0),
                    'Other_Allowance': emp.get('Other_Allowance', 0.0),
                    'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25),
                    'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)
                }
                c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
                c_res['NH'] = 0.0
                c_res['CL'] = 0.0
                c_res['EL'] = 0.0
                c_res['SL'] = 0.0
                calculated_rows.append(c_res)
    else:
        for emp in employees:
            att_dict = {'present_days': standard_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': standard_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
            ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': float(emp.get('LIC', 0.0) or 0.0), 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
            sal_dict = {
                'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0),
                'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0),
                'Washing_Allowance': emp.get('Washing_Allowance', 0.0),
                'Other_Allowance': emp.get('Other_Allowance', 0.0),
                'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25),
                'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)
            }
            c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            c_res['NH'] = 0.0
            c_res['CL'] = 0.0
            c_res['EL'] = 0.0
            c_res['SL'] = 0.0
            calculated_rows.append(c_res)

    # Summary totals
    tot_gross = sum(r.get('Gross_Wages', 0.0) for r in calculated_rows)
    tot_ot = sum(r.get('OT_Wages', 0.0) + r.get('Special_OT_Amount', 0.0) for r in calculated_rows)
    tot_pf = sum(r.get('PF_Deduction', 0.0) for r in calculated_rows)
    tot_esi = sum(r.get('ESI_Deduction', 0.0) for r in calculated_rows)
    tot_ded = sum(r.get('Total_Deduction', 0.0) for r in calculated_rows)
    tot_net = sum(r.get('Net_Salary', 0.0) for r in calculated_rows)

    return render_template(
        'payroll/payroll_dynamic.html',
        year=year,
        month=month,
        category=category,
        categories=CATEGORIES,
        standard_days=standard_days,
        rows=calculated_rows,
        tot_gross=tot_gross,
        tot_ot=tot_ot,
        tot_pf=tot_pf,
        tot_esi=tot_esi,
        tot_ded=tot_ded,
        tot_net=tot_net,
        is_saved=bool(existing_trans),
        period_configured=bool(db_std_days is not None)
    )

@payroll_bp.route('/trace/<int:employee_id>', methods=['GET'])
def employee_trace(employee_id):
    """Returns step-by-step audit calculation trace JSON for debugging."""
    emp = get_employee_by_id(employee_id)
    if not emp:
        return jsonify({'error': 'Employee not found'}), 404

    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 7))
    emp_cat = emp.get('Category', '')
    std_days = float(request.args.get('standard_days', 27.0 if 'STAFF' in emp_cat else 26.0))

    sal_dict = {
        'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0),
        'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0),
        'Washing_Allowance': emp.get('Washing_Allowance', 0.0),
        'Other_Allowance': emp.get('Other_Allowance', 0.0),
        'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25),
        'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)
    }

    att_dict = {
        'present_days': float(request.args.get('present_days', std_days)),
        'nh': float(request.args.get('nh', 0.0)),
        'el': float(request.args.get('el', 0.0)),
        'cl': float(request.args.get('cl', 0.0)),
        'sl': float(request.args.get('sl', 0.0)),
        'actual_ot_hours': float(request.args.get('ot_hours', 0.0))
    }

    ded_dict = {
        'lic': float(request.args.get('lic', 0.0)),
        'advance': float(request.args.get('advance', 0.0)),
        'other': float(request.args.get('other', 0.0))
    }

    trace = get_calculation_trace(emp, sal_dict, att_dict, ded_dict, standard_days=std_days)

    if request.args.get('format') == 'json':
        return jsonify(trace)

    return render_template('payroll/payroll_trace.html', trace=trace, emp=emp, year=year, month=month, standard_days=std_days)

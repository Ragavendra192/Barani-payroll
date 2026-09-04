import datetime as dt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.employee import get_all_employees, get_employee_by_id, add_employee, update_employee, toggle_employee_status

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

CATEGORIES = [
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS'),
    ('WORKER_NAPS', 'Worker — NAPS'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@employees_bp.route('/')
def list_employees():
    category = request.args.get('category')
    emp_type = request.args.get('employee_type')
    pay_cat = request.args.get('payroll_category')
    search = request.args.get('search')
    status = request.args.get('status', 'Active')

    employees = get_all_employees(
        category=category,
        employee_type=emp_type,
        payroll_category=pay_cat,
        search=search,
        status=status if status != 'All' else None
    )

    return render_template(
        'employees/employee_list.html',
        employees=employees,
        categories=CATEGORIES,
        selected_category=category,
        selected_type=emp_type,
        selected_pay_cat=pay_cat,
        search=search,
        status=status
    )

@employees_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        doj_raw = request.form.get('DOJ', '').strip() or None
        if doj_raw:
            try:
                doj_dt = dt.datetime.strptime(doj_raw, "%Y-%m-%d").date()
                if doj_dt > dt.date.today():
                    flash("Date of Joining cannot be in the future.", 'danger')
                    return redirect(url_for('main.master'))
            except ValueError:
                pass

        data = {
            'Emp_No': request.form['Emp_No'].strip(),
            'ERP_Emp_No': request.form.get('ERP_Emp_No', '').strip(),
            'Emp_Code': request.form.get('Emp_Code', '').strip(),
            'Employee_Name': request.form['Employee_Name'].strip(),
            'Father_Name': request.form.get('Father_Name', '').strip(),
            'DOB': request.form.get('DOB', '').strip() or None,
            'Bank_Acc_No': request.form.get('Bank_Acc_No', '').strip(),
            'Bank_IFSC': request.form.get('Bank_IFSC', '').strip(),
            'Employee_Type': request.form['Employee_Type'],
            'Payroll_Category': request.form['Payroll_Category'],
            'Department': request.form.get('Department', '').strip(),
            'Designation': request.form.get('Designation', '').strip(),
            'Grade': request.form.get('Grade', '').strip(),
            'DOJ': doj_raw,
            'UAN_No': request.form.get('UAN_No', '').strip(),
            'ESI_No': request.form.get('ESI_No', '').strip(),
            'Phone_Number': request.form.get('Phone_Number', '').strip(),
            'Email_ID': request.form.get('Email_ID', '').strip(),
            'Fixed_Gross': float(request.form.get('Fixed_Gross', 0.0) or 0.0),
            'LIC': float(request.form.get('LIC', 0.0) or 0.0),
            'Basic_DA': float(request.form.get('Basic_DA', 0.0) or 0.0),
            'HRA': float(request.form.get('HRA', 0.0) or 0.0),
            'Conveyance_Allowance': float(request.form.get('Conveyance_Allowance', 0.0) or 0.0),
            'Washing_Allowance': float(request.form.get('Washing_Allowance', 0.0) or 0.0),
            'Other_Allowance': float(request.form.get('Other_Allowance', 0.0) or 0.0),
            'Per_Day_Wage': float(request.form.get('Per_Day_Wage', 0.0) or 0.0),
            'OT_Rate': float(request.form.get('OT_Rate', 56.25) or 56.25),
            'PF_Eligible': 'PF_Eligible' in request.form,
            'ESI_Eligible': 'ESI_Eligible' in request.form
        }
        try:
            add_employee(data)
            flash(f"Employee {data['Employee_Name']} added successfully!", 'success')
            return redirect(url_for('main.master'))
        except Exception as e:
            flash(f"Error adding employee: {str(e)}", 'danger')

    return redirect(url_for('main.master'))

@employees_bp.route('/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash("Employee not found!", 'danger')
        return redirect(url_for('main.master'))

    if request.method == 'POST':
        doj_raw = request.form.get('DOJ', '').strip() or None
        if doj_raw:
            try:
                doj_dt = dt.datetime.strptime(doj_raw, "%Y-%m-%d").date()
                if doj_dt > dt.date.today():
                    flash("Date of Joining cannot be in the future.", 'danger')
                    return redirect(url_for('main.master'))
            except ValueError:
                pass

        data = {
            'Emp_No': request.form.get('Emp_No', '').strip(),
            'Employee_Name': request.form['Employee_Name'].strip(),
            'Father_Name': request.form.get('Father_Name', '').strip(),
            'DOB': request.form.get('DOB', '').strip() or None,
            'Bank_Acc_No': request.form.get('Bank_Acc_No', '').strip(),
            'Bank_IFSC': request.form.get('Bank_IFSC', '').strip(),
            'Employee_Type': request.form['Employee_Type'],
            'Payroll_Category': request.form['Payroll_Category'],
            'ERP_Emp_No': request.form.get('ERP_Emp_No', '').strip(),
            'Emp_Code': request.form.get('Emp_Code', '').strip(),
            'Department': request.form.get('Department', '').strip(),
            'Designation': request.form.get('Designation', '').strip(),
            'Grade': request.form.get('Grade', '').strip(),
            'DOJ': doj_raw,
            'UAN_No': request.form.get('UAN_No', '').strip(),
            'ESI_No': request.form.get('ESI_No', '').strip(),
            'Phone_Number': request.form.get('Phone_Number', '').strip(),
            'Email_ID': request.form.get('Email_ID', '').strip(),
            'Status': request.form.get('Status', 'Active'),
            'Fixed_Gross': float(request.form.get('Fixed_Gross', 0.0) or 0.0),
            'LIC': float(request.form.get('LIC', 0.0) or 0.0),
            'Basic_DA': float(request.form.get('Basic_DA', 0.0) or 0.0),
            'HRA': float(request.form.get('HRA', 0.0) or 0.0),
            'Conveyance_Allowance': float(request.form.get('Conveyance_Allowance', 0.0) or 0.0),
            'Washing_Allowance': float(request.form.get('Washing_Allowance', 0.0) or 0.0),
            'Other_Allowance': float(request.form.get('Other_Allowance', 0.0) or 0.0),
            'Per_Day_Wage': float(request.form.get('Per_Day_Wage', 0.0) or 0.0),
            'OT_Rate': float(request.form.get('OT_Rate', 56.25) or 56.25),
            'PF_Eligible': 'PF_Eligible' in request.form,
            'ESI_Eligible': 'ESI_Eligible' in request.form
        }
        try:
            update_employee(employee_id, data)
            flash(f"Employee {data['Employee_Name']} updated successfully!", 'success')
            return redirect(url_for('main.master'))
        except Exception as e:
            flash(f"Error updating employee: {str(e)}", 'danger')

    return redirect(url_for('main.master'))

@employees_bp.route('/toggle/<int:employee_id>', methods=['POST'])
def toggle(employee_id):
    toggle_employee_status(employee_id)
    flash("Employee status updated!", 'info')
    return redirect(url_for('main.master'))

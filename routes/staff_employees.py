from flask import Blueprint, render_template, request, redirect, flash, url_for
from models.staff_employee import (
    get_all_staff_employees, get_staff_by_emp_no,
    add_staff_employee, update_staff_employee,
    toggle_staff_status, search_staff_employees
)

staff_employees_bp = Blueprint("staff_employees", __name__)

@staff_employees_bp.route("/employees/staff")
def list_employees():
    query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    
    if query:
        employees = search_staff_employees(query)
    else:
        employees = get_all_staff_employees(status_filter=status_filter if status_filter else None)

    return render_template("employees/staff_list.html", employees=employees, q=query, status_filter=status_filter)

@staff_employees_bp.route("/employees/staff/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        try:
            emp_no = request.form.get("Emp_No")
            if not emp_no:
                flash("Employee Number is required.", "danger")
                return render_template("employees/staff_form.html", employee=request.form, is_edit=False)

            existing = get_staff_by_emp_no(emp_no)
            if existing:
                flash(f"Employee Number {emp_no} already exists!", "danger")
                return render_template("employees/staff_form.html", employee=request.form, is_edit=False)

            add_staff_employee(request.form)
            flash(f"Staff employee {request.form.get('Emp_Name')} added successfully.", "success")
            return redirect(url_for("staff_employees.list_employees"))
        except Exception as e:
            flash(f"Failed to add employee: {e}", "danger")

    return render_template("employees/staff_form.html", employee=None, is_edit=False)

@staff_employees_bp.route("/employees/staff/edit/<int:emp_no>", methods=["GET", "POST"])
def edit_employee(emp_no):
    employee = get_staff_by_emp_no(emp_no)
    if not employee:
        flash(f"Employee #{emp_no} not found.", "danger")
        return redirect(url_for("staff_employees.list_employees"))

    if request.method == "POST":
        try:
            update_staff_employee(emp_no, request.form)
            flash(f"Staff employee #{emp_no} updated successfully.", "success")
            return redirect(url_for("staff_employees.list_employees"))
        except Exception as e:
            flash(f"Failed to update employee: {e}", "danger")

    return render_template("employees/staff_form.html", employee=employee, is_edit=True)

@staff_employees_bp.route("/employees/staff/toggle/<int:emp_no>", methods=["POST"])
def toggle_status(emp_no):
    employee = get_staff_by_emp_no(emp_no)
    if employee:
        new_status = "Inactive" if employee.get("Status") == "Active" else "Active"
        toggle_staff_status(emp_no, new_status)
        flash(f"Employee #{emp_no} status changed to {new_status}.", "info")
    return redirect(url_for("staff_employees.list_employees"))

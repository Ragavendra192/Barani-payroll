from flask import Blueprint, render_template, request, redirect, flash, url_for
from models.naps_employee import (
    get_all_naps_employees, get_naps_by_emp_no,
    add_naps_employee, update_naps_employee,
    toggle_naps_status, search_naps_employees
)

naps_employees_bp = Blueprint("naps_employees", __name__)

@naps_employees_bp.route("/employees/naps")
def list_employees():
    query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()

    if query:
        employees = search_naps_employees(query)
    else:
        employees = get_all_naps_employees(status_filter=status_filter if status_filter else None)

    return render_template("employees/naps_list.html", employees=employees, q=query, status_filter=status_filter)

@naps_employees_bp.route("/employees/naps/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        try:
            emp_no = request.form.get("Emp_No")
            if not emp_no:
                flash("NAPS Employee Number is required.", "danger")
                return render_template("employees/naps_form.html", employee=request.form, is_edit=False)

            existing = get_naps_by_emp_no(emp_no)
            if existing:
                flash(f"NAPS Employee Number {emp_no} already exists!", "danger")
                return render_template("employees/naps_form.html", employee=request.form, is_edit=False)

            add_naps_employee(request.form)
            flash(f"NAPS employee {request.form.get('Emp_Name')} added successfully.", "success")
            return redirect(url_for("naps_employees.list_employees"))
        except Exception as e:
            flash(f"Failed to add NAPS employee: {e}", "danger")

    return render_template("employees/naps_form.html", employee=None, is_edit=False)

@naps_employees_bp.route("/employees/naps/edit/<int:emp_no>", methods=["GET", "POST"])
def edit_employee(emp_no):
    employee = get_naps_by_emp_no(emp_no)
    if not employee:
        flash(f"NAPS Employee #{emp_no} not found.", "danger")
        return redirect(url_for("naps_employees.list_employees"))

    if request.method == "POST":
        try:
            update_naps_employee(emp_no, request.form)
            flash(f"NAPS employee #{emp_no} updated successfully.", "success")
            return redirect(url_for("naps_employees.list_employees"))
        except Exception as e:
            flash(f"Failed to update NAPS employee: {e}", "danger")

    return render_template("employees/naps_form.html", employee=employee, is_edit=True)

@naps_employees_bp.route("/employees/naps/toggle/<int:emp_no>", methods=["POST"])
def toggle_status(emp_no):
    employee = get_naps_by_emp_no(emp_no)
    if employee:
        new_status = "Inactive" if employee.get("Status") == "Active" else "Active"
        toggle_naps_status(emp_no, new_status)
        flash(f"NAPS Employee #{emp_no} status changed to {new_status}.", "info")
    return redirect(url_for("naps_employees.list_employees"))

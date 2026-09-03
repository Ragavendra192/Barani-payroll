import datetime as dt
from flask import Blueprint, render_template, request, flash, redirect, url_for
from models.staff_employee import get_all_staff_employees, get_staff_by_emp_no
from models.staff_payroll import get_staff_payroll_month, save_staff_payroll_batch
from services.staff_payroll_service import calculate_staff_payroll
from services.payroll_validation import validate_year_month, validate_working_days, validate_ot_hours, validate_deduction
from config import STANDARD_WORKING_DAYS

staff_payroll_bp = Blueprint("staff_payroll", __name__)

@staff_payroll_bp.route("/payroll/staff", methods=["GET", "POST"])
def manage_payroll():
    now = dt.datetime.now()
    selected_year = int(request.values.get("year", now.year))
    selected_month = int(request.values.get("month", now.month))
    standard_days = float(request.values.get("standard_days", STANDARD_WORKING_DAYS))

    action = request.form.get("action", "load")
    payroll_rows = []
    summary = None
    already_saved = False

    # Check if payroll already exists in DB for this month/year
    existing_payroll = get_staff_payroll_month(selected_year, selected_month)
    if existing_payroll:
        already_saved = True

    if request.method == "POST" or action == "load":
        valid, msg_or_ym = validate_year_month(selected_year, selected_month)
        if not valid:
            flash(msg_or_ym, "danger")
            return render_template(
                "payroll/staff_payroll.html",
                year=selected_year, month=selected_month,
                standard_days=standard_days, payroll_rows=[],
                summary=None, already_saved=False
            )

        employees = get_all_staff_employees(status_filter="Active")
        
        if not employees:
            flash("No active staff employees found in database.", "warning")

        # Map existing saved values if present
        saved_dict = {p["Emp_No"]: p for p in existing_payroll} if existing_payroll else {}

        if action == "load":
            for emp in employees:
                emp_no = emp["Emp_No"]
                saved = saved_dict.get(emp_no, {})
                w_days = float(saved.get("Working_Days", standard_days))
                ot_h = float(saved.get("OT_Hours", 0.0))
                other_ded = float(saved.get("Other_Deduction", 0.0))

                calc = calculate_staff_payroll(emp, w_days, ot_h, other_ded)
                payroll_rows.append(calc)

        elif action in ("calculate", "save"):
            # Read submitted form lists per employee
            emp_nos = request.form.getlist("emp_no[]")
            working_days_list = request.form.getlist("working_days[]")
            ot_hours_list = request.form.getlist("ot_hours[]")
            other_ded_list = request.form.getlist("other_deduction[]")

            for i, emp_no_str in enumerate(emp_nos):
                emp_no = int(emp_no_str)
                emp = get_staff_by_emp_no(emp_no)
                if not emp:
                    continue

                w_val = working_days_list[i] if i < len(working_days_list) else standard_days
                ot_val = ot_hours_list[i] if i < len(ot_hours_list) else 0.0
                ded_val = other_ded_list[i] if i < len(other_ded_list) else 0.0

                v_w, w_days = validate_working_days(w_val)
                v_ot, ot_h = validate_ot_hours(ot_val)
                v_ded, other_ded = validate_deduction(ded_val)

                if not v_w: w_days = standard_days
                if not v_ot: ot_h = 0.0
                if not v_ded: other_ded = 0.0

                calc = calculate_staff_payroll(emp, w_days, ot_h, other_ded)
                payroll_rows.append(calc)

            if action == "save":
                try:
                    save_staff_payroll_batch(selected_year, selected_month, payroll_rows)
                    month_name = dt.date(selected_year, selected_month, 1).strftime("%B")
                    flash(f"{month_name} {selected_year} Staff Payroll saved successfully.", "success")
                    already_saved = True
                except Exception as e:
                    flash(f"Error saving payroll: {e}", "danger")

    # Compute summary totals
    if payroll_rows:
        summary = {
            "total_employees": len(payroll_rows),
            "total_gross": round(sum(r["Gross_Salary"] for r in payroll_rows), 2),
            "total_ot": round(sum(r["OT_Amount"] for r in payroll_rows), 2),
            "total_pf": round(sum(r["PF"] for r in payroll_rows), 2),
            "total_esi": round(sum(r["ESI"] for r in payroll_rows), 2),
            "total_deduction": round(sum(r["Total_Deduction"] for r in payroll_rows), 2),
            "total_net": round(sum(r["Net_Salary"] for r in payroll_rows), 2),
        }

    return render_template(
        "payroll/staff_payroll.html",
        year=selected_year,
        month=selected_month,
        standard_days=standard_days,
        payroll_rows=payroll_rows,
        summary=summary,
        already_saved=already_saved
    )

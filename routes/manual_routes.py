from flask import Blueprint, render_template, request, redirect, flash
from db import get_db_connection
from models_manual import (
    add_manual_deduction,
    delete_manual_deduction,
    get_manual_deductions_for_employee,
)

manual_bp = Blueprint("manual", __name__)

# -------------------------------------------------
# HELPER
# -------------------------------------------------
def _fetchall_dict(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

# -------------------------------------------------
# 1️⃣ BULK LIST PAGE (ALL EMPLOYEES)
# URL: /manual-deductions/2025/12
# -------------------------------------------------
@manual_bp.route("/manual-deductions/<int:year>/<int:month>")
def manual_deduction_list(year, month):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.Emp_No,
            e.Emp_Name,
            e.Category,
            p.Gross_Wages,
            p.Net_Pay
        FROM PayrollHistory p
        JOIN EmployeeMaster e ON e.Emp_No = p.Emp_No
        WHERE p.Year = ? AND p.Month = ?
        ORDER BY e.Emp_No
    """, (year, month))

    employees = _fetchall_dict(cursor)
    conn.close()

    return render_template(
        "manual_deduction_list.html",
        employees=employees,
        year=year,
        month=month
    )

# -------------------------------------------------
# 2️⃣ REDIRECT TO DEBIT TAB (SINGLE EMP)
# URL: /manual-deductions/101/2025/12
# -------------------------------------------------
@manual_bp.route("/manual-deductions/<int:emp_no>/<int:year>/<int:month>")
def manual_redirect(emp_no, year, month):
    return redirect(f"/manual-deductions/debit/{emp_no}/{year}/{month}")

# -------------------------------------------------
# 3️⃣ DEBIT / CREDIT PAGE
# URL:
# /manual-deductions/debit/101/2025/12
# /manual-deductions/credit/101/2025/12
# -------------------------------------------------
@manual_bp.route(
    "/manual-deductions/<string:mode>/<int:emp_no>/<int:year>/<int:month>",
    methods=["GET", "POST"]
)
def manual_deductions(mode, emp_no, year, month):

    mode = mode.lower()
    if mode not in ("debit", "credit"):
        mode = "debit"

    print(f"[MANUAL DEDUCTIONS] Request: method={request.method}, mode={mode}, emp={emp_no}, year={year}, month={month}")

    if request.method == "POST":
        print(f"[MANUAL DEDUCTIONS] POST data: {dict(request.form)}")
        try:
            deduction_type = request.form.get("deduction_type")
            reason = request.form.get("reason", "")
            # apply_this_month checkbox: if checked -> Active, if unchecked -> Inactive (skip deduction this month)
            apply_flag = request.form.get("apply_this_month", None)
            status = "Active" if apply_flag in ("on", "true", "1", True) else "Inactive"

            transaction_type = request.form.get("transaction_type", "Debit")
            target = request.form.get("target")
            installments_str = request.form.get("installments")
            total_amount_str = request.form.get("total_amount")

            if not deduction_type:
                flash("Deduction Type is required", "warning")
                return redirect(f"/manual-deductions/{mode}/{emp_no}/{year}/{month}")

            if not total_amount_str:
                flash("Total Amount is required", "warning")
                return redirect(f"/manual-deductions/{mode}/{emp_no}/{year}/{month}")

            total_amount = float(total_amount_str)
            installments = int(installments_str) if installments_str else None

            # For installment-based entries, amount is calculated from total_amount / installments
            if installments and installments > 1:
                amount = round(total_amount / installments, 2)
            else:
                amount = total_amount
                installments = None

            # Show processing message for long-running operations
            if installments and installments > 1:
                flash(f"Processing {installments} installments... this may take a moment.", "info")

            add_manual_deduction(
                emp_no, year, month,
                deduction_type, amount, reason, status,
                transaction_type=transaction_type,
                target=target,
                installments=installments,
                total_amount=total_amount
            )

            flash("Manual entry saved successfully", "success")
            return redirect(f"/manual-deductions/{mode}/{emp_no}/{year}/{month}")
        except ValueError as ve:
            flash(f"Invalid input: {str(ve)}", "danger")
            return redirect(f"/manual-deductions/{mode}/{emp_no}/{year}/{month}")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            import traceback
            traceback.print_exc()
            return redirect(f"/manual-deductions/{mode}/{emp_no}/{year}/{month}")

    # GET DATA
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Emp_No, Emp_Name FROM EmployeeMaster ORDER BY Emp_No")
    employees = _fetchall_dict(cursor)
    conn.close()

    existing_df = get_manual_deductions_for_employee(emp_no, year, month)
    existing = existing_df.to_dict(orient="records") if existing_df is not None else []

    return render_template(
        "manual_deductions.html",
        mode=mode,
        emp_no=emp_no,
        year=year,
        month=month,
        employees=employees,
        existing=existing
    )

# -------------------------------------------------
# 4️⃣ DELETE
# -------------------------------------------------
@manual_bp.route("/manual-deductions/delete/<int:deduction_id>", methods=["POST"])
def manual_delete(deduction_id):
    delete_manual_deduction(deduction_id)
    return ("", 204)

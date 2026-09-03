from flask import Blueprint, render_template, request, flash

from models_attendance import get_attendance_summary
from models import save_payroll
from models_employee import get_all_employees
from utils.attendance_payroll_calc import calculate_attendance_payroll
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

attendance_payroll_bp = Blueprint("attendance_payroll", __name__)

@attendance_payroll_bp.route("/attendance/payroll", methods=["GET", "POST"])
def attendance_payroll():

    payroll = None
    year = None
    month = None

    if request.method == "POST":
        try:
            print("[payroll] POST received", flush=True)
            logging.info("[payroll] POST received")
            month = int(request.form["month"])
            year = int(request.form["year"])

            logging.info(f"[payroll] year={year} month={month}")
            print(f"[payroll] year={year} month={month}", flush=True)

            emp_df = get_all_employees()
            logging.info(f"[payroll] emp_df rows={len(emp_df)}")
            print(f"[payroll] emp_df rows={len(emp_df)}", flush=True)

            attendance_df = get_attendance_summary(year, month)
            logging.info(f"[payroll] attendance_df rows={len(attendance_df)}")
            print(f"[payroll] attendance_df rows={len(attendance_df)}", flush=True)

            if attendance_df.empty:
                flash("No attendance data found for selected month")
                return render_template("attendance_payroll.html", payroll=None, year=year, month=month)

            # attendance_df already contains employee fields (Category, Monthly_Salary, etc.)
            # so pass it directly to the payroll calculator to avoid duplicate-column suffixes.
            logging.info("[payroll] computing payroll (this may take a moment)")
            print("[payroll] computing payroll (this may take a moment)", flush=True)
            payroll = calculate_attendance_payroll(attendance_df, year=year, month=month)
            logging.info(f"[payroll] payroll computed rows={len(payroll)}")
            print(f"[payroll] payroll computed rows={len(payroll)}", flush=True)

            logging.info("[payroll] saving payroll to DB")
            print("[payroll] saving payroll to DB", flush=True)
            save_payroll(year, month, payroll)
            logging.info("[payroll] saved payroll to DB")
            print("[payroll] saved payroll to DB", flush=True)

            flash("Attendance payroll generated successfully")

        except Exception as e:
            logging.exception("[payroll] exception during payroll generation")
            flash(str(e))

    return render_template(
        "attendance_payroll.html",
        payroll=payroll,
        year=year,
        month=month
    )

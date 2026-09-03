import pandas as pd
import datetime as dt
import re
from flask import Blueprint, render_template, request, redirect, flash

from models_employee import get_employee_by_empno
from models_attendance import upsert_attendance

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance", methods=["GET", "POST"])
def upload_attendance():

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Please upload Attendance Excel file")
            return redirect("/attendance")

        try:
            raw_df = pd.read_excel(file, header=None)

            records = []
            current_emp = None
            in_table = False

            for _, row in raw_df.iterrows():
                row_values = [str(x).strip() for x in row if not pd.isna(x)]
                row_text = " ".join(row_values).lower()

                # ----------------------------------
                # 1️⃣ DETECT EMPLOYEE CODE
                # ----------------------------------
                if "employee code" in row_text:
                    nums = re.findall(r"\d+", row_text)
                    if nums:
                        emp_no = int(nums[0])
                        emp = get_employee_by_empno(emp_no)
                        if emp:
                            current_emp = emp
                        else:
                            current_emp = None
                    in_table = False
                    continue

                # ----------------------------------
                # 2️⃣ DETECT ATTENDANCE HEADER
                # ----------------------------------
                if "date" in row_text and "intime" in row_text and "outtime" in row_text:
                    in_table = True
                    continue

                # ----------------------------------
                # 3️⃣ PROCESS ATTENDANCE ROWS
                # ----------------------------------
                if in_table and current_emp and len(row_values) >= 3:
                    try:
                        work_date = pd.to_datetime(row_values[0]).date()
                        in_time = pd.to_datetime(row_values[1], errors="coerce")
                        out_time = pd.to_datetime(row_values[2], errors="coerce")

                        if pd.isna(in_time) or pd.isna(out_time):
                            continue

                        in_t = in_time.time()
                        out_t = out_time.time()

                        in_dt = dt.datetime.combine(work_date, in_t)
                        out_dt = dt.datetime.combine(work_date, out_t)

                        # Night shift
                        if out_dt < in_dt:
                            out_dt += dt.timedelta(days=1)

                        hours = round((out_dt - in_dt).total_seconds() / 3600, 2)
                        present = 1 if hours >= 4 else 0

                        ot = 0
                        if current_emp["Category"].upper() == "WORKER" and hours > 8:
                            ot = round(hours - 8, 2)

                        records.append({
                            "Emp_No": current_emp["Emp_No"],
                            "Work_Date": work_date,
                            "In_Time": in_t,
                            "Out_Time": out_t,
                            "Working_Hours": hours,
                            "Present": present,
                            "OT_Hours": ot
                        })

                    except:
                        continue

            if not records:
                raise Exception("No valid attendance data found")

            attendance_df = pd.DataFrame(records)
            upsert_attendance(attendance_df)

            flash(f"Attendance uploaded successfully ({len(records)} entries)")
            return redirect("/attendance")

        except Exception as e:
            flash(f"Upload failed: {e}")
            return redirect("/attendance")

    return render_template("attendance_upload.html")

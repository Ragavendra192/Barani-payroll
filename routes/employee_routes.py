import pandas as pd
from flask import Blueprint, render_template, request, redirect, flash

from models_employee import (
    upsert_employee_master,
    get_all_employees
)

employee_bp = Blueprint("employees", __name__)

# -------------------------------------------------
# Helper: Clean DOJ
# -------------------------------------------------
def clean_doj(value):
    try:
        if pd.isna(value) or value == "":
            return None
        return pd.to_datetime(value).date()
    except:
        return None


# -------------------------------------------------
# EMPLOYEE MASTER (BULK UPLOAD + LIST)
# -------------------------------------------------
@employee_bp.route("/employees", methods=["GET", "POST"])
def employees():

    # -----------------------------
    # POST → BULK UPLOAD
    # -----------------------------
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Please upload Employee Master Excel file")
            return redirect("/employees")

        try:
            # 🔹 Read Employee_Master sheet
            df = pd.read_excel(file, sheet_name="Employee_Master")

            # 🔹 Normalize column names
            df.columns = [c.strip() for c in df.columns]

            # 🔹 Fix DOJ conversion (IMPORTANT)
            if "DOJ" in df.columns:
                df["DOJ"] = df["DOJ"].apply(clean_doj)

            # 🔹 Required columns validation
            required_cols = [
                "Emp_No", "Emp_Name", "Department", "Category",
                "Basic", "DA", "HRA",
                "Washing_Allowance", "Conveyance", "Special_Allowance",
                "PF_Eligible", "ESI_Eligible"
            ]

            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                raise Exception(f"Missing columns: {', '.join(missing)}")

            # 🔹 Fill numeric NaN safely
            numeric_cols = [
                "Basic", "DA", "HRA",
                "Washing_Allowance", "Conveyance", "Special_Allowance",
                "PF_Eligible", "ESI_Eligible"
            ]
            for c in numeric_cols:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

            # 🔹 Ensure integer flags
            df["PF_Eligible"] = df["PF_Eligible"].astype(int)
            df["ESI_Eligible"] = df["ESI_Eligible"].astype(int)

            # 🔹 Save to DB (UPSERT)
            upsert_employee_master(df)

            flash("Employee Master uploaded successfully")

        except Exception as e:
            flash(f"Upload failed: {e}")

        return redirect("/employees")

    # -----------------------------
    # GET → LIST EMPLOYEES
    # -----------------------------
    employees = get_all_employees()
    return render_template("employees.html", employees=employees)

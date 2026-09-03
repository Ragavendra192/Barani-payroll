import io
import datetime as dt
import pandas as pd
from xhtml2pdf import pisa
from zipfile import ZipFile
from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, send_file
)

from models import get_payroll, get_archived_months

history_bp = Blueprint("history", __name__)


# --------------------------------------------------
# Helper
# --------------------------------------------------
def month_label(year, month):
    return dt.date(year, month, 1).strftime("%b %Y")


# --------------------------------------------------
# HISTORY HOME
# --------------------------------------------------
@history_bp.route("/history")
def history():
    months = get_archived_months()
    return render_template("history.html", months=months)
    # return render_template("history.html", records=records, months=get_archived_months())



# --------------------------------------------------
# VIEW MONTH PAYROLL
# --------------------------------------------------
@history_bp.route("/history/<int:year>/<int:month>")
def history_month(year, month):
    payroll = get_payroll(year, month)

    if payroll is None or payroll.empty:
        flash("No payroll data for this month.")
        return redirect(url_for("history.history"))

    return render_template(
        "history_view.html",
        payroll=payroll,
        month_label=month_label(year, month),
        year=year,
        month=month
    )


# --------------------------------------------------
# VIEW SINGLE PAYSLIP
# --------------------------------------------------

@history_bp.route("/payslip/<int:year>/<int:month>/<int:emp_no>")
def view_payslip(year, month, emp_no):
    payroll = get_payroll(year, month)
    row_df = payroll[payroll["Emp_No"] == emp_no]

    row = row_df.iloc[0].to_dict()   # ✅ REQUIRED
    row["Year"] = year
    row["Month"] = month

    return render_template(
        "payslip.html",
        row=row,
        month_label=month_label(year, month)
    )




# --------------------------------------------------
# DOWNLOAD PAYROLL SUMMARY EXCEL
# --------------------------------------------------
@history_bp.route("/download/summary/<int:year>/<int:month>")
def download_payroll_summary(year, month):
    payroll = get_payroll(year, month)

    if payroll is None or payroll.empty:
        flash("No payroll data available.")
        return redirect(url_for("main.index"))

    bio = io.BytesIO()
    
    # helper for month name
    month_name = dt.date(year, month, 1).strftime("%B %Y")
    
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Payroll_Summary")
        writer.sheets["Payroll_Summary"] = worksheet

        # Formats
        header_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D3D3D3', 'font_size': 10
        })
        title_fmt = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14
        })
        subtitle_fmt = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 12
        })
        data_fmt = workbook.add_format({'border': 1, 'font_size': 9})
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'font_size': 9})
        bold_num_fmt = workbook.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00', 'font_size': 10})

        # --- HEADERS ---
        # Row 0: Company Name
        worksheet.merge_range('A1:AN1', "BARANI HYDRAULICS INDIA PRIVATE LIMITED - UNIT - I", title_fmt)
        # Row 1: Subtitle
        worksheet.merge_range('A2:AN2', f"STAFF SALARY STATEMENT FOR THE MONTH OF {month_name.upper()}", subtitle_fmt)

        # Row 3: Group Headers
        # A-F: Basics
        worksheet.merge_range('G4:L4', 'Worked Days', header_fmt)
        worksheet.merge_range('M4:S4', 'Fixed Gross', header_fmt)
        worksheet.merge_range('T4:Z4', 'Earnings', header_fmt)
        worksheet.merge_range('AA4:AG4', 'Deductions', header_fmt)
        worksheet.merge_range('AJ4:AN4', 'Advance Tracking', header_fmt)

        cols = [
            "S.No", "Emp Code", "ERP Emp No", "UAN", "ESI No", "Name", # A-F
            "Present", "PH", "CL", "SL", "PL", "Total", # G-L
            "Basic", "DA", "HRA", "Washing", "Conv.", "Other", "Total", # M-S
            "Basic", "DA", "HRA", "Washing", "Conv.", "Other", "Gross Wages", # T-Z
            "PF", "ESI", "PT", "Mess", "LIC", "TDS", "Total Ded", # AA-AG
            "Sign", "NET Salary", # AH-AI
            "New Adv.", "Inst.", "Opening", "Clos. Adv.", "Sign" # AJ-AN
        ]
        
        for i, col_name in enumerate(cols):
            worksheet.write(4, i, col_name, header_fmt)

        # --- DATA ---
        for row_idx, r in payroll.iterrows():
            # Helper to get numeric value safely
            def fval(val):
                if val is None or pd.isna(val):
                    return 0.0
                return float(val)

            excel_row = 5 + row_idx
            # A-F
            worksheet.write(excel_row, 0, row_idx + 1, data_fmt)
            worksheet.write(excel_row, 1, r.get("Emp_No", ""), data_fmt)
            worksheet.write(excel_row, 2, r.get("Emp_No", ""), data_fmt) # ERP Emp No
            worksheet.write(excel_row, 3, r.get("UAN", ""), data_fmt)
            worksheet.write(excel_row, 4, r.get("ESI_No", ""), data_fmt)
            worksheet.write(excel_row, 5, r.get("Emp_Name", ""), data_fmt)

            # G-L (Worked Days)
            worksheet.write(excel_row, 6, fval(r.get("Present_Days")), data_fmt)
            worksheet.write(excel_row, 7, fval(r.get("PH")), data_fmt)
            worksheet.write(excel_row, 8, fval(r.get("CL")), data_fmt)
            worksheet.write(excel_row, 9, fval(r.get("SL")), data_fmt)
            worksheet.write(excel_row, 10, fval(r.get("PL")), data_fmt)
            
            total_days = fval(r.get("Present_Days")) + fval(r.get("PH")) + fval(r.get("CL")) + fval(r.get("SL")) + fval(r.get("PL"))
            worksheet.write(excel_row, 11, total_days, data_fmt)

            # M-S (Fixed Gross)
            # User requested Basic=40%, DA=20% of Base Gross
            base_gross = fval(r.get("Base_Gross"))
            f_basic = round(base_gross * 0.40, 2)
            f_da = round(base_gross * 0.20, 2)
            
            worksheet.write(excel_row, 12, f_basic, num_fmt)
            worksheet.write(excel_row, 13, f_da, num_fmt)
            worksheet.write(excel_row, 14, fval(r.get("Fixed_HRA")), num_fmt)
            worksheet.write(excel_row, 15, fval(r.get("Fixed_Washing")), num_fmt)
            worksheet.write(excel_row, 16, fval(r.get("Fixed_Conveyance")), num_fmt)
            worksheet.write(excel_row, 17, fval(r.get("Fixed_Other")), num_fmt)
            worksheet.write(excel_row, 18, base_gross, num_fmt)

            # T-Z (Earnings)
            # Basic and DA are pro-rated versions
            earned_basic_da = fval(r.get("Earned_Basic_DA"))
            # Split proportionally based on 40/60 and 20/60
            e_basic = round(earned_basic_da * (40/60), 2)
            e_da = round(earned_basic_da * (20/60), 2)

            worksheet.write(excel_row, 19, e_basic, num_fmt)
            worksheet.write(excel_row, 20, e_da, num_fmt)
            worksheet.write(excel_row, 21, fval(r.get("Earned_HRA")), num_fmt)
            worksheet.write(excel_row, 22, fval(r.get("Earned_Washing")), num_fmt)
            worksheet.write(excel_row, 23, fval(r.get("Earned_Conveyance")), num_fmt)
            worksheet.write(excel_row, 24, fval(r.get("Earned_Other")), num_fmt)
            worksheet.write(excel_row, 25, fval(r.get("Gross_Wages")), num_fmt)

            # AA-AG (Deductions)
            worksheet.write(excel_row, 26, fval(r.get("PF_Ded")), num_fmt)
            worksheet.write(excel_row, 27, fval(r.get("ESI_Ded")), num_fmt)
            worksheet.write(excel_row, 28, fval(r.get("PT")), num_fmt)
            worksheet.write(excel_row, 29, fval(r.get("Mess")), num_fmt)
            worksheet.write(excel_row, 30, fval(r.get("LIC")), num_fmt)
            worksheet.write(excel_row, 31, fval(r.get("TDS")), num_fmt)
            worksheet.write(excel_row, 32, fval(r.get("Total_Deductions")), num_fmt)

            # AH-AI (Sign & Net)
            worksheet.write(excel_row, 33, "", data_fmt) # Sign
            worksheet.write(excel_row, 34, r.get("Net_Pay", 0), bold_num_fmt)

            # AJ-AN (Advance)
            worksheet.write(excel_row, 35, fval(r.get("New_Advance")), num_fmt)
            worksheet.write(excel_row, 36, fval(r.get("Installment")), num_fmt)
            worksheet.write(excel_row, 37, fval(r.get("Opening_Advance")), num_fmt)
            worksheet.write(excel_row, 38, fval(r.get("Closing_Advance")), num_fmt)
            worksheet.write(excel_row, 39, "", data_fmt) # Sign

        # Column widths
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:C', 10)
        worksheet.set_column('D:E', 15)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:AN', 10)

    bio.seek(0)
    filename = f"Salary_Statement_{year}_{month:02d}.xlsx"

    return send_file(
        bio,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# --------------------------------------------------
# DOWNLOAD SINGLE PAYSLIP PDF
# --------------------------------------------------
@history_bp.route("/download/payslip/<int:year>/<int:month>/<int:emp_no>")
def download_single_payslip(year, month, emp_no):
    payroll = get_payroll(year, month)
    if payroll is None or payroll.empty:
        flash("No payroll data available.")
        return redirect(url_for("history.history"))

    row_df = payroll[payroll["Emp_No"] == emp_no]
    if row_df.empty:
        flash("Employee not found in payroll.")
        return redirect(url_for("history.history_month", year=year, month=month))

    row_dict = row_df.iloc[0].to_dict()
    row_dict["Year"] = year
    row_dict["Month"] = month

    base_gross = float(row_dict.get("Base_Gross") or 0)
    row_dict["Basic"] = round(base_gross * 0.40, 2)
    row_dict["DA"] = round(base_gross * 0.20, 2)

    earned_basic_da = float(row_dict.get("Earned_Basic_DA") or 0)
    row_dict["Earned_Basic"] = round(earned_basic_da * (40/60), 2)
    row_dict["Earned_DA"] = round(earned_basic_da * (20/60), 2)

    html = render_template(
        "payslip.html",
        row=row_dict,
        month_label=month_label(year, month),
        is_pdf=True
    )

    pdf_io = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_io)

    if pisa_status.err:
        flash("Error generating PDF payslip.")
        return redirect(url_for("history.history_month", year=year, month=month))

    pdf_io.seek(0)
    safe_name = str(row_dict.get("Emp_Name", "Employee")).replace(" ", "_")
    filename = f"Payslip_{emp_no}_{safe_name}_{year}_{month:02d}.pdf"

    return send_file(
        pdf_io,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


# --------------------------------------------------
# DOWNLOAD ALL PAYSLIPS ZIP
# --------------------------------------------------
@history_bp.route("/download/payslips/<int:year>/<int:month>")
def download_all_payslips(year, month):
    payroll = get_payroll(year, month)

    if payroll is None or payroll.empty:
        flash("No payroll data available.")
        return redirect(url_for("main.index"))

    zip_buffer = io.BytesIO()

    with ZipFile(zip_buffer, "w") as zipf:
        for _, row in payroll.iterrows():
            # Ensure Basic & DA split for the payslip (40/20)
            row_dict = row.to_dict()
            row_dict["Year"] = year
            row_dict["Month"] = month
            base_gross = float(row_dict.get("Base_Gross") or 0)
            
            # FIXED Constants
            row_dict["Basic"] = round(base_gross * 0.40, 2)
            row_dict["DA"] = round(base_gross * 0.20, 2)
            
            # EARNED pro-rated
            earned_basic_da = float(row_dict.get("Earned_Basic_DA") or 0)
            row_dict["Earned_Basic"] = round(earned_basic_da * (40/60), 2)
            row_dict["Earned_DA"] = round(earned_basic_da * (20/60), 2)

            # Render HTML
            html = render_template(
                "payslip.html",
                row=row_dict,
                month_label=month_label(year, month),
                is_pdf=True # Flag to hide nav/buttons
            )

            # Convert to PDF
            pdf_io = io.BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=pdf_io)
            
            if not pisa_status.err:
                safe_name = str(row_dict.get("Emp_Name", "Employee")).replace(" ", "_")
                filename = f"{row_dict.get('Emp_No', '0')}_{safe_name}.pdf"
                zipf.writestr(filename, pdf_io.getvalue())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"Payslips_{year}_{month:02d}.zip",
        mimetype="application/zip"
    )
from flask import request
from models import search_payroll_history


# --------------------------------------------------
# FILTERED HISTORY (SEARCH)
# --------------------------------------------------
@history_bp.route("/history/search")
def history_search():
    records = search_payroll_history(
        emp_no=request.args.get("emp_no", type=int),
        emp_name=request.args.get("emp_name"),
        dept=request.args.get("dept"),
        year=request.args.get("year", type=int),
        month=request.args.get("month", type=int),
        min_net_pay=request.args.get("min_net", type=float),
        max_net_pay=request.args.get("max_net", type=float),
    )

    return render_template(
        "history_filter.html",
        records=records
    )


# --------------------------------------------------
# DELETE MONTH PAYROLL + ATTENDANCE LOGS
# --------------------------------------------------
@history_bp.route("/history/delete/<int:year>/<int:month>", methods=["POST"])
def delete_history_month(year, month):
    from db import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Delete payroll rows for the month
        cur.execute("DELETE FROM PayrollHistory WHERE Year = ? AND Month = ?", (year, month))

        # Delete attendance logs for that month/year
        cur.execute("DELETE FROM AttendanceLogs WHERE MONTH(Work_Date) = ? AND YEAR(Work_Date) = ?", (month, year))

        # Delete manual deductions for that month
        cur.execute("DELETE FROM ManualDeductions WHERE Year = ? AND Month = ?", (year, month))

        conn.commit()
        flash(f"Deleted payroll and attendance data for {month:02d}/{year}", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Failed to delete data for {month:02d}/{year}: {e}", "danger")
    finally:
        conn.close()

    return ("", 204)


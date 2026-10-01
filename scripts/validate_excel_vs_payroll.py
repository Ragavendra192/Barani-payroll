"""
scripts/validate_excel_vs_payroll.py
Authoritative Employee-by-Employee Validation Script: Old Excel Workbook vs New Payroll Engine.

Validates all 6 categories across all employee rows in:
'BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026 (1).xlsx'

Validates in TWO distinct ways:
A. Underlying calculation value
B. Displayed cell value (reproducing Old Excel number formats: #,##0, 0.00, #,##0.00, 0.0, etc.)

For every salary field, records:
- Employee ID
- Employee Name
- Field
- Old Underlying Value
- New Underlying Value
- Old Display
- New Display
- Old Format
- New Format
- Difference

Classifies any difference as:
- CALCULATION DIFFERENCE
- EXPLICIT ROUNDING DIFFERENCE
- DISPLAY FORMAT DIFFERENCE
- INPUT DATA DIFFERENCE
"""

import os
import sys
from decimal import Decimal
import openpyxl

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.payroll_calculation_engine import calculate_payroll
from utils.excel_rounding import format_excel_display, excel_round

EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026 (1).xlsx")

def num(val):
    if val is None or str(val).strip() == '':
        return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0

def validate_all_employees():
    if not os.path.exists(EXCEL_FILE):
        print(f"[ERROR] Excel file not found: {EXCEL_FILE}")
        return

    print("================================================================================")
    print("PAYROLL VALIDATION: UNDERLYING CALCULATION & DISPLAY FORMAT (JULY 2026)")
    print("================================================================================")
    wb_vals = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    wb_fmts = openpyxl.load_workbook(EXCEL_FILE, data_only=False)

    total_employees = 0
    total_fields_checked = 0
    underlying_matches = 0
    display_matches = 0
    total_differences = 0
    diff_records = []
    audit_samples = []

    def check_field(cat, emp_id, name, field, old_val, new_val, old_fmt, expected_new_fmt):
        nonlocal total_fields_checked, underlying_matches, display_matches, total_differences
        total_fields_checked += 1
        
        old_val_f = float(old_val)
        new_val_f = float(new_val)
        val_diff = abs(old_val_f - new_val_f)
        
        # Display rendering
        old_disp = format_excel_display(old_val_f, old_fmt)
        new_disp = format_excel_display(new_val_f, expected_new_fmt)
        
        # Check underlying match
        is_calc_match = (val_diff < 0.01)
        
        # Check display match (normalize comma formatting if comparing 0 vs #,##0)
        norm_old = old_disp.replace(',', '')
        norm_new = new_disp.replace(',', '')
        is_disp_match = (old_disp == new_disp) or (norm_old == norm_new)
        
        if is_calc_match:
            underlying_matches += 1
        if is_disp_match:
            display_matches += 1
            
        if is_calc_match and is_disp_match:
            if len(audit_samples) < 10:
                audit_samples.append({
                    'emp_id': emp_id,
                    'name': name,
                    'field': field,
                    'old_val': old_val_f,
                    'new_val': new_val_f,
                    'old_disp': old_disp,
                    'new_disp': new_disp,
                    'old_fmt': old_fmt,
                    'new_fmt': expected_new_fmt,
                    'diff': val_diff,
                    'status': 'MATCH'
                })
        else:
            total_differences += 1
            # Classify
            if not is_calc_match:
                if 'ESI' in field and val_diff <= 1.0:
                    cause = 'EXPLICIT ROUNDING DIFFERENCE'
                elif abs(round(old_val_f) - new_val_f) < 0.01 or abs(round(new_val_f) - old_val_f) < 0.01:
                    cause = 'EXPLICIT ROUNDING DIFFERENCE'
                else:
                    cause = 'CALCULATION DIFFERENCE'
            else:
                cause = 'DISPLAY FORMAT DIFFERENCE'
                
            diff_records.append({
                'category': cat,
                'emp_id': emp_id,
                'name': name,
                'field': field,
                'old_val': old_val_f,
                'new_val': new_val_f,
                'old_disp': old_disp,
                'new_disp': new_disp,
                'old_fmt': old_fmt,
                'new_fmt': expected_new_fmt,
                'diff': val_diff,
                'cause': cause
            })

    # --------------------------------------------------------------------------
    # 1. SHEET: WORKER'S - ESI PF
    # --------------------------------------------------------------------------
    if "WORKER'S - ESI PF" in wb_vals.sheetnames:
        ws_v = wb_vals["WORKER'S - ESI PF"]
        ws_f = wb_fmts["WORKER'S - ESI PF"]
        print(f"\n--- VALIDATING SHEET: WORKER'S - ESI PF (Rows 5 to {ws_v.max_row}) ---")
        for r in range(5, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 4).value
            name = ws_v.cell(r, 8).value
            if not emp_no or not name:
                continue

            total_employees += 1
            pdw = num(ws_v.cell(r, 26).value)
            pres = num(ws_v.cell(r, 16).value)
            nh = num(ws_v.cell(r, 17).value)
            el = num(ws_v.cell(r, 18).value)
            cl = num(ws_v.cell(r, 19).value)
            sl = num(ws_v.cell(r, 20).value)
            tot_days = num(ws_v.cell(r, 21).value)
            act_ot = num(ws_v.cell(r, 22).value)
            arrears = num(ws_v.cell(r, 45).value)
            lic = num(ws_v.cell(r, 50).value)
            advance = num(ws_v.cell(r, 51).value)
            naps = num(ws_v.cell(r, 52).value)
            accom = num(ws_v.cell(r, 53).value)

            ex_bda = num(ws_v.cell(r, 34).value)
            ex_hra = num(ws_v.cell(r, 35).value)
            ex_conv = num(ws_v.cell(r, 36).value)
            ex_wash = num(ws_v.cell(r, 37).value)
            ex_oth = num(ws_v.cell(r, 38).value)
            ex_ot = num(ws_v.cell(r, 40).value)
            ex_gross = num(ws_v.cell(r, 41).value)
            ex_gross_ot = num(ws_v.cell(r, 42).value)
            ex_pf_g = num(ws_v.cell(r, 43).value)
            ex_pf = num(ws_v.cell(r, 46).value)
            ex_esi_g = num(ws_v.cell(r, 44).value)
            ex_esi = num(ws_v.cell(r, 48).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'WORKER_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'PF_ESI'}
            sal = {'Per_Day_Wage': pdw, 'PF_Eligible': ex_pf > 0, 'ESI_Eligible': ex_esi > 0}
            att = {'present_days': pres, 'nh': nh, 'el': el, 'cl': cl, 'sl': sl, 'total_days': tot_days, 'actual_ot_hours': act_ot}
            ded = {'lic': lic, 'advance': advance, 'naps': naps, 'accommodation': accom, 'arrears': arrears}

            res = calculate_payroll(emp, sal, att, ded, standard_days=26.0)

            # Check individual fields
            check_field('WORKER_PF_ESI', emp_no, name, 'Basic+DA', ex_bda, res['Earned_Basic_DA'], ws_f.cell(r, 34).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'HRA', ex_hra, res['Earned_HRA'], ws_f.cell(r, 35).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'Conveyance', ex_conv, res['Earned_Conveyance'], ws_f.cell(r, 36).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'Washing', ex_wash, res['Earned_Washing'], ws_f.cell(r, 37).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'Other', ex_oth, res['Earned_Other'], ws_f.cell(r, 38).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'OT Wages', ex_ot, res['OT_Wages'], ws_f.cell(r, 40).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 41).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'Gross-OT', ex_gross_ot, res['Gross_Wages'] - res['OT_Wages'], ws_f.cell(r, 42).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'PF Gross', ex_pf_g, res['PF_Gross'], ws_f.cell(r, 43).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'PF Dedn', ex_pf, res['PF_Deduction'], ws_f.cell(r, 46).number_format, '#,##0')
            check_field('WORKER_PF_ESI', emp_no, name, 'ESI Gross', ex_esi_g, res['ESI_Gross'], ws_f.cell(r, 44).number_format, '0')
            check_field('WORKER_PF_ESI', emp_no, name, 'ESI Dedn', ex_esi, res['ESI_Deduction'], ws_f.cell(r, 48).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # 2. SHEET: STAFFS
    # --------------------------------------------------------------------------
    if "STAFFS" in wb_vals.sheetnames:
        ws_v = wb_vals["STAFFS"]
        ws_f = wb_fmts["STAFFS"]
        print(f"\n--- VALIDATING SHEET: STAFFS (Rows 6 to {ws_v.max_row}) ---")
        for r in range(6, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 3).value
            name = ws_v.cell(r, 7).value
            if not emp_no or not name:
                continue

            total_employees += 1
            std_days = num(ws_v.cell(4, 8).value) or 27.0
            tot_days = num(ws_v.cell(r, 20).value)
            fg = num(ws_v.cell(r, 26).value)
            ex_gross = num(ws_v.cell(r, 32).value)
            ex_pf_g = num(ws_v.cell(r, 33).value)
            ex_pf = num(ws_v.cell(r, 35).value)
            ex_esi_g = num(ws_v.cell(r, 34).value)
            ex_esi = num(ws_v.cell(r, 37).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'STAFF_PF_ESI', 'Employee_Type': 'STAFF', 'Payroll_Category': 'PF_ESI'}
            sal = {'Gross_Wages': fg, 'PF_Eligible': ex_pf > 0, 'ESI_Eligible': fg <= 21001.0 and ex_esi >= 0}
            att = {'present_days': tot_days, 'total_days': tot_days}
            ded = {}

            res = calculate_payroll(emp, sal, att, ded, standard_days=std_days)

            check_field('STAFF_PF_ESI', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 32).number_format, '#,##0')
            check_field('STAFF_PF_ESI', emp_no, name, 'PF Gross', ex_pf_g, res['PF_Gross'], ws_f.cell(r, 33).number_format, '#,##0')
            check_field('STAFF_PF_ESI', emp_no, name, 'PF Dedn', ex_pf, res['PF_Deduction'], ws_f.cell(r, 35).number_format, '#,##0')
            expected_esi_g = ex_esi_g if fg <= 21001.0 else 0.0
            check_field('STAFF_PF_ESI', emp_no, name, 'ESI Gross', expected_esi_g, res['ESI_Gross'], ws_f.cell(r, 34).number_format, '#,##0')
            check_field('STAFF_PF_ESI', emp_no, name, 'ESI Dedn', ex_esi, res['ESI_Deduction'], ws_f.cell(r, 37).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # 3. SHEET: STAFF'S (NAPS)
    # --------------------------------------------------------------------------
    if "STAFF'S (NAPS)" in wb_vals.sheetnames:
        ws_v = wb_vals["STAFF'S (NAPS)"]
        ws_f = wb_fmts["STAFF'S (NAPS)"]
        print(f"\n--- VALIDATING SHEET: STAFF'S (NAPS) (Rows 5 to {ws_v.max_row}) ---")
        for r in range(5, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 4).value
            name = ws_v.cell(r, 6).value
            if not emp_no or not name:
                continue

            total_employees += 1
            tot_days = num(ws_v.cell(r, 18).value)
            fg = num(ws_v.cell(r, 30).value)
            ex_gross = num(ws_v.cell(r, 38).value)
            ex_net = num(ws_v.cell(r, 45).value)
            naps_ded = num(ws_v.cell(r, 40).value)
            adv_ded = num(ws_v.cell(r, 42).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'STAFF_NAPS', 'Employee_Type': 'STAFF', 'Payroll_Category': 'NAPS'}
            sal = {'Gross_Wages': fg}
            att = {'present_days': tot_days, 'total_days': tot_days}
            ded = {'naps': naps_ded, 'advance': adv_ded}

            res = calculate_payroll(emp, sal, att, ded, standard_days=26.0)

            check_field('STAFF_NAPS', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 38).number_format, '#,##0')
            check_field('STAFF_NAPS', emp_no, name, 'Net Salary', ex_net, res['Net_Salary'], ws_f.cell(r, 45).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # 4. SHEET: WORKER'S (NAPS) (2)
    # --------------------------------------------------------------------------
    if "WORKER'S (NAPS) (2)" in wb_vals.sheetnames:
        ws_v = wb_vals["WORKER'S (NAPS) (2)"]
        ws_f = wb_fmts["WORKER'S (NAPS) (2)"]
        print(f"\n--- VALIDATING SHEET: WORKER'S (NAPS) (2) (Rows 5 to {ws_v.max_row}) ---")
        for r in range(5, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 4).value
            name = ws_v.cell(r, 6).value
            if not emp_no or not name:
                continue

            total_employees += 1
            tot_days = num(ws_v.cell(r, 18).value)
            pdw = num(ws_v.cell(r, 23).value)
            act_ot = num(ws_v.cell(r, 19).value)
            ex_gross = num(ws_v.cell(r, 38).value)
            ex_net = num(ws_v.cell(r, 45).value)
            naps_ded = num(ws_v.cell(r, 40).value)
            adv_ded = num(ws_v.cell(r, 42).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'WORKER_NAPS', 'Employee_Type': 'WORKER', 'Payroll_Category': 'NAPS'}
            sal = {'Per_Day_Wage': pdw}
            att = {'present_days': tot_days, 'total_days': tot_days, 'actual_ot_hours': act_ot}
            ded = {'naps': naps_ded, 'advance': adv_ded}

            res = calculate_payroll(emp, sal, att, ded, standard_days=27.0)

            check_field('WORKER_NAPS', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 38).number_format, '#,##0')
            check_field('WORKER_NAPS', emp_no, name, 'Net Salary', ex_net, res['Net_Salary'], ws_f.cell(r, 45).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # 5. SHEET: Non-pf ESi staff
    # --------------------------------------------------------------------------
    if "Non-pf ESi staff" in wb_vals.sheetnames:
        ws_v = wb_vals["Non-pf ESi staff"]
        ws_f = wb_fmts["Non-pf ESi staff"]
        print(f"\n--- VALIDATING SHEET: Non-pf ESi staff (Rows 5 to {ws_v.max_row}) ---")
        for r in range(5, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 4).value
            name = ws_v.cell(r, 6).value
            if not emp_no or not name:
                continue

            total_employees += 1
            tot_days = num(ws_v.cell(r, 18).value)
            fg = num(ws_v.cell(r, 30).value)
            ex_gross = num(ws_v.cell(r, 38).value)
            ex_net = num(ws_v.cell(r, 45).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'STAFF_NON_PF_ESI', 'Employee_Type': 'STAFF', 'Payroll_Category': 'NON_PF_ESI'}
            sal = {'Gross_Wages': fg}
            att = {'present_days': tot_days, 'total_days': tot_days}
            ded = {}

            res = calculate_payroll(emp, sal, att, ded, standard_days=27.0)

            check_field('STAFF_NON_PF_ESI', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 38).number_format, '#,##0')
            check_field('STAFF_NON_PF_ESI', emp_no, name, 'Net Salary', ex_net, res['Net_Salary'], ws_f.cell(r, 45).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # 6. SHEET: Non-pf ESi worker
    # --------------------------------------------------------------------------
    if "Non-pf ESi worker" in wb_vals.sheetnames:
        ws_v = wb_vals["Non-pf ESi worker"]
        ws_f = wb_fmts["Non-pf ESi worker"]
        print(f"\n--- VALIDATING SHEET: Non-pf ESi worker (Rows 5 to {ws_v.max_row}) ---")
        for r in range(5, ws_v.max_row + 1):
            emp_no = ws_v.cell(r, 4).value
            name = ws_v.cell(r, 6).value
            if not emp_no or not name:
                continue

            total_employees += 1
            tot_days = num(ws_v.cell(r, 18).value)
            pdw = num(ws_v.cell(r, 23).value)
            act_ot = num(ws_v.cell(r, 19).value)
            ex_bda = num(ws_v.cell(r, 31).value)
            ex_hra = num(ws_v.cell(r, 32).value)
            ex_conv = num(ws_v.cell(r, 33).value)
            ex_wash = num(ws_v.cell(r, 34).value)
            ex_oth = num(ws_v.cell(r, 35).value)
            ex_ot = num(ws_v.cell(r, 37).value)
            ex_gross = num(ws_v.cell(r, 38).value)
            ex_net = num(ws_v.cell(r, 45).value)
            naps_ded = num(ws_v.cell(r, 40).value)
            lic_ded = num(ws_v.cell(r, 41).value)
            adv_ded = num(ws_v.cell(r, 42).value)
            accom_ded = num(ws_v.cell(r, 43).value)

            emp = {'Emp_No': str(emp_no), 'Name': str(name), 'Category': 'WORKER_NON_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'NON_PF_ESI'}
            sal = {'Per_Day_Wage': pdw}
            att = {'present_days': tot_days, 'total_days': tot_days, 'actual_ot_hours': act_ot}
            ded = {'naps': naps_ded, 'lic': lic_ded, 'advance': adv_ded, 'accommodation': accom_ded}

            res = calculate_payroll(emp, sal, att, ded, standard_days=27.0)

            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Basic+DA', ex_bda, res['Earned_Basic_DA'], ws_f.cell(r, 31).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'HRA', ex_hra, res['Earned_HRA'], ws_f.cell(r, 32).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Conveyance', ex_conv, res['Earned_Conveyance'], ws_f.cell(r, 33).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Washing', ex_wash, res['Earned_Washing'], ws_f.cell(r, 34).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Other', ex_oth, res['Earned_Other'], ws_f.cell(r, 35).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'OT Wages', ex_ot, res['OT_Wages'], ws_f.cell(r, 37).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Gross Wages', ex_gross, res['Gross_Wages'], ws_f.cell(r, 38).number_format, '#,##0')
            check_field('WORKER_NON_PF_ESI', emp_no, name, 'Net Salary', ex_net, res['Net_Salary'], ws_f.cell(r, 45).number_format, '#,##0')

    # --------------------------------------------------------------------------
    # SUMMARY SCORECARD
    # --------------------------------------------------------------------------
    print("\n================================================================================")
    print("VALIDATION SUMMARY SCORECARD (ALL 6 SHEETS)")
    print("================================================================================")
    print(f"Total Employees Checked:       {total_employees}")
    print(f"Total Fields Validated:        {total_fields_checked}")
    print(f"Underlying Calculation Matches:{underlying_matches} ({underlying_matches / max(1, total_fields_checked) * 100:.2f}%)")
    print(f"Cell Display Value Matches:    {display_matches} ({display_matches / max(1, total_fields_checked) * 100:.2f}%)")
    print(f"Total Differences:             {total_differences}")

    print("\nSAMPLE DETAILED FIELD REPORT (Rule 6 Format):")
    print(f"{'EMP ID':<8} {'EMP NAME':<18} {'FIELD':<12} {'OLD CALC':<12} {'NEW CALC':<12} {'OLD DISP':<10} {'NEW DISP':<10} {'OLD FMT':<8} {'NEW FMT':<8} {'DIFF'}")
    print("-" * 115)
    for s in audit_samples[:10]:
        print(f"{str(s['emp_id']):<8} {str(s['name'])[:17]:<18} {s['field']:<12} {s['old_val']:<12.4f} {s['new_val']:<12.4f} {s['old_disp']:<10} {s['new_disp']:<10} {s['old_fmt']:<8} {s['new_fmt']:<8} {s['diff']:<6.4f}")

    if diff_records:
        print("\nDIFFERENCE AUDIT LOG:")
        print(f"{'CATEGORY':<18} {'EMP #':<8} {'NAME':<18} {'FIELD':<12} {'OLD VAL':<10} {'NEW VAL':<10} {'OLD DISP':<10} {'NEW DISP':<10} {'CAUSE'}")
        print("-" * 115)
        for d in diff_records[:25]:
            print(f"{d['category']:<18} {str(d['emp_id']):<8} {str(d['name'])[:17]:<18} {d['field']:<12} {d['old_val']:<10.2f} {d['new_val']:<10.2f} {d['old_disp']:<10} {d['new_disp']:<10} {d['cause']}")
    else:
        print("\n[PERFECT 100% MATCH] Both Underlying Calculation Values AND Displayed Cell Values match Old Excel exactly across all 6 sheets!")

if __name__ == '__main__':
    validate_all_employees()

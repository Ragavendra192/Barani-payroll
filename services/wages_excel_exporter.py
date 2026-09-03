import io
import datetime as dt
import xlsxwriter
from models.employee import get_all_employees
from models.payroll_transaction import get_payroll_transactions
from models.payroll_period_settings import get_period_settings
from services.payroll_engine import calculate_payroll

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

CATEGORY_SHEET_NAMES = [
    ('STAFF_PF_ESI', 'Staff_PF_ESI', 'STAFF — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker_PF_ESI', 'WORKER — PF / ESI'),
    ('STAFF_NAPS', 'Staff_NAPS', 'STAFF — NAPS APPRENTICE'),
    ('WORKER_NAPS', 'Worker_NAPS', 'WORKER — NAPS APPRENTICE'),
    ('STAFF_NON_PF_ESI', 'Staff_Non_PF_ESI', 'STAFF — NON PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker_Non_PF_ESI', 'WORKER — NON PF / ESI')
]

def generate_wages_excel(year, month, category_filter='ALL'):
    """
    Generates a professionally formatted BHIPL Salary Statement Excel workbook
    for the selected year, month, and category filter.
    Returns (BytesIO, filename).
    """
    db_std_days = get_period_settings(year, month)
    standard_days = db_std_days if db_std_days else 26.0

    # Fetch saved payroll transactions for year/month
    existing_trans = get_payroll_transactions(year, month)
    trans_map = {t['Employee_ID']: t for t in existing_trans}

    # Fetch active employees
    employees = get_all_employees(status='Active')

    # Calculate or retrieve payroll rows for all active employees
    payroll_rows = []
    if trans_map:
        for emp in employees:
            t = trans_map.get(emp['Employee_ID'])
            if t and float(t.get('Gross_Wages', 0.0) or 0.0) > 0.0:
                t['Working_Days'] = standard_days
                payroll_rows.append(t)
            else:
                att_dict = {'present_days': standard_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': standard_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
                ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': 0.0, 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
                sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
                c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
                payroll_rows.append(c_res)
    else:
        for emp in employees:
            att_dict = {'present_days': standard_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': standard_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
            ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': 0.0, 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
            sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
            c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=standard_days)
            payroll_rows.append(c_res)

    month_name = MONTH_NAMES.get(month, f"Month_{month}")
    month_label = f"{month_name.upper()}-{year}"

    # Determine output filename
    if category_filter and category_filter.upper() != 'ALL':
        cat_clean = category_filter.strip().upper()
        filename = f"BHIPL_{cat_clean}_Statement_{month_name}_{year}.xlsx"
    else:
        filename = f"BHIPL_Payroll_Statement_{month_name}_{year}.xlsx"

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})

    # Styling formats
    fmt_title = wb.add_format({
        'bold': True, 'font_size': 14, 'font_name': 'Segoe UI',
        'align': 'center', 'valign': 'vcenter',
        'bg_color': '#1F4E79', 'font_color': '#FFFFFF'
    })
    fmt_subtitle = wb.add_format({
        'bold': True, 'font_size': 11, 'font_name': 'Segoe UI',
        'align': 'center', 'valign': 'vcenter',
        'bg_color': '#2F5597', 'font_color': '#FFFFFF'
    })
    fmt_group_header = wb.add_format({
        'bold': True, 'font_size': 10, 'font_name': 'Segoe UI',
        'align': 'center', 'valign': 'vcenter',
        'bg_color': '#D9E1F2', 'font_color': '#1F4E79', 'border': 1
    })
    fmt_col_header = wb.add_format({
        'bold': True, 'font_size': 9, 'font_name': 'Segoe UI',
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
        'bg_color': '#2F5597', 'font_color': '#FFFFFF', 'border': 1
    })
    
    fmt_text = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'valign': 'vcenter', 'border': 1})
    fmt_text_bold = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'bold': True, 'valign': 'vcenter', 'border': 1})
    fmt_center = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'align': 'center', 'valign': 'vcenter', 'border': 1})
    fmt_num = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '0.0'})
    fmt_currency = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'align': 'right', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.00'})
    fmt_currency_bold = wb.add_format({'font_size': 9, 'font_name': 'Segoe UI', 'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.00', 'bg_color': '#F2F2F2'})
    fmt_net_salary = wb.add_format({'font_size': 10, 'font_name': 'Segoe UI', 'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.00', 'bg_color': '#E2EFDA', 'font_color': '#375623'})

    fmt_total_label = wb.add_format({'bold': True, 'font_size': 10, 'font_name': 'Segoe UI', 'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 2})
    fmt_total_currency = wb.add_format({'bold': True, 'font_size': 10, 'font_name': 'Segoe UI', 'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 2, 'num_format': '#,##0.00'})

    # Group category rows
    category_groups = {}
    for code, sheet_name, cat_title in CATEGORY_SHEET_NAMES:
        category_groups[code] = {
            'sheet_name': sheet_name,
            'title': cat_title,
            'rows': []
        }

    for r in payroll_rows:
        c_code = r.get('Category') or f"{r.get('Employee_Type')}_{r.get('Payroll_Category')}"
        if c_code in category_groups:
            category_groups[c_code]['rows'].append(r)
        else:
            # Fallback grouping
            if 'STAFF' in c_code.upper():
                category_groups['STAFF_PF_ESI']['rows'].append(r)
            else:
                category_groups['WORKER_PF_ESI']['rows'].append(r)

    # Filter categories if specific category requested
    active_categories = []
    if category_filter and category_filter.upper() != 'ALL':
        raw_filter = category_filter.upper()
        if raw_filter in category_groups:
            active_categories = [raw_filter]
        elif raw_filter == 'STAFF':
            active_categories = ['STAFF_PF_ESI', 'STAFF_NAPS', 'STAFF_NON_PF_ESI']
        elif raw_filter == 'WORKER':
            active_categories = ['WORKER_PF_ESI', 'WORKER_NAPS', 'WORKER_NON_PF_ESI']
    else:
        active_categories = [code for code, _, _ in CATEGORY_SHEET_NAMES]

    sheets_created = 0

    for cat_code in active_categories:
        grp = category_groups[cat_code]
        rows = grp['rows']
        if not rows:
            continue

        sheets_created += 1
        ws = wb.add_worksheet(grp['sheet_name'])
        ws.set_landscape()
        ws.freeze_panes(4, 3)

        is_staff = 'STAFF' in cat_code.upper()

        if is_staff:
            # STAFF COLUMNS (35 Cols: A to AI)
            ws.merge_range('A1:AI1', 'BARANI HYDRAULICS INDIA PRIVATE LIMITED - UNIT - I', fmt_title)
            ws.merge_range('A2:AI2', f"{grp['title']} SALARY STATEMENT FOR THE MONTH OF {month_label}", fmt_subtitle)

            # Group headers
            ws.merge_range('A3:H3', 'EMPLOYEE DETAILS', fmt_group_header)
            ws.merge_range('I3:P3', 'WORKED DAYS', fmt_group_header)
            ws.merge_range('Q3:W3', 'FIXED SALARY STRUCTURE', fmt_group_header)
            ws.merge_range('X3:AD3', 'EARNINGS', fmt_group_header)
            ws.merge_range('AE3:AJ3', 'DEDUCTIONS', fmt_group_header)
            ws.write('AK3', 'NET SALARY', fmt_group_header)

            headers = [
                'S.No', 'Emp ID', 'Employee Name', 'Department', 'Designation', 'UAN No', 'ESI No', 'Category',
                'Working Days', 'Present', 'N/H', 'EL', 'CL', 'SL', 'Payable Days', 'OT Hours',
                'Fixed Gross', 'Basic+DA', 'Fixed HRA', 'Fixed Conv', 'Fixed Wash', 'Fixed Other', 'Gross Fixed',
                'Earned Basic+DA', 'Earned HRA', 'Earned Conv', 'Earned Wash', 'Earned Other', 'OT Wages', 'Earned Gross',
                'PF Dedn', 'ESI Dedn', 'LIC Dedn', 'Advance Dedn', 'Other Dedn', 'Total Dedn',
                'Net Salary'
            ]
            for col_idx, h in enumerate(headers):
                ws.write(3, col_idx, h, fmt_col_header)

            row_idx = 4
            for idx, r in enumerate(rows, start=1):
                ws.write(row_idx, 0, idx, fmt_center)
                ws.write(row_idx, 1, str(r.get('Emp_No', '')), fmt_text_bold)
                ws.write(row_idx, 2, str(r.get('Employee_Name') or r.get('Name', '')), fmt_text)
                ws.write(row_idx, 3, str(r.get('Department', '') or '-'), fmt_text)
                ws.write(row_idx, 4, str(r.get('Designation', '') or '-'), fmt_text)
                ws.write(row_idx, 5, str(r.get('UAN_No', '') or '-'), fmt_text)
                ws.write(row_idx, 6, str(r.get('ESI_No', '') or '-'), fmt_text)
                ws.write(row_idx, 7, str(r.get('Category', '')), fmt_center)

                ws.write(row_idx, 8, float(r.get('Working_Days', standard_days) or standard_days), fmt_num)
                ws.write(row_idx, 9, float(r.get('Present_Days', standard_days) or standard_days), fmt_num)
                ws.write(row_idx, 10, float(r.get('NH', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 11, float(r.get('EL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 12, float(r.get('CL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 13, float(r.get('SL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 14, float(r.get('Total_Days', standard_days) or standard_days), fmt_num)
                ws.write(row_idx, 15, float(r.get('Act_OT_Hrs', 0.0) or r.get('OT_Hours', 0.0) or 0.0), fmt_num)

                fg = float(r.get('Fixed_Gross', 0.0) or 0.0)
                ws.write(row_idx, 16, fg, fmt_currency)
                ws.write(row_idx, 17, float(r.get('Basic_DA', 0.0) or fg * 0.50), fmt_currency)
                ws.write(row_idx, 18, float(r.get('HRA', 0.0) or fg * 0.20), fmt_currency)
                ws.write(row_idx, 19, float(r.get('Conveyance_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 20, float(r.get('Washing_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 21, float(r.get('Other_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 22, fg, fmt_currency_bold)

                ws.write(row_idx, 23, float(r.get('Earned_Basic_DA', r.get('Basic_DA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 24, float(r.get('Earned_HRA', r.get('HRA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 25, float(r.get('Earned_Conveyance', r.get('Conveyance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 26, float(r.get('Earned_Washing', r.get('Washing_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 27, float(r.get('Earned_Other', r.get('Other_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 28, float(r.get('OT_Wages', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 29, float(r.get('Gross_Wages', 0.0) or 0.0), fmt_currency_bold)

                ws.write(row_idx, 30, float(r.get('PF_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 31, float(r.get('ESI_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 32, float(r.get('LIC_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 33, float(r.get('Advance_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 34, float(r.get('Other_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 35, float(r.get('Total_Deduction', 0.0) or 0.0), fmt_currency_bold)

                ws.write(row_idx, 36, float(r.get('Net_Salary', 0.0) or 0.0), fmt_net_salary)
                row_idx += 1

            # Total Row
            ws.merge_range(row_idx, 0, row_idx, 7, f"TOTAL ({len(rows)} Employees)", fmt_total_label)
            for c_i in range(8, 16):
                ws.write(row_idx, c_i, '', fmt_total_label)
            ws.write_formula(row_idx, 16, f"=SUM(Q5:Q{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 17, f"=SUM(R5:R{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 18, f"=SUM(S5:S{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 19, f"=SUM(T5:T{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 20, f"=SUM(U5:U{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 21, f"=SUM(V5:V{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 22, f"=SUM(W5:W{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 23, f"=SUM(X5:X{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 24, f"=SUM(Y5:Y{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 25, f"=SUM(Z5:Z{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 26, f"=SUM(AA5:AA{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 27, f"=SUM(AB5:AB{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 28, f"=SUM(AC5:AC{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 29, f"=SUM(AD5:AD{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 30, f"=SUM(AE5:AE{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 31, f"=SUM(AF5:AF{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 32, f"=SUM(AG5:AG{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 33, f"=SUM(AH5:AH{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 34, f"=SUM(AI5:AI{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 35, f"=SUM(AJ5:AJ{row_idx})", fmt_total_currency)
            ws.write_formula(row_idx, 36, f"=SUM(AK5:AK{row_idx})", fmt_total_currency)

            # Auto-fit column widths
            ws.set_column(0, 0, 6)   # S.No
            ws.set_column(1, 1, 10)  # Emp ID
            ws.set_column(2, 2, 24)  # Name
            ws.set_column(3, 4, 16)  # Dept & Desig
            ws.set_column(5, 6, 16)  # UAN & ESI
            ws.set_column(7, 7, 16)  # Category
            ws.set_column(8, 15, 10) # Attendance
            ws.set_column(16, 36, 14) # Currency columns

        else:
            # WORKER COLUMNS (54 Cols: A to BB)
            ws.merge_range('A1:BB1', 'BARANI HYDRAULICS INDIA PRIVATE LIMITED - UNIT - I', fmt_title)
            ws.merge_range('A2:BB2', f"{grp['title']} SALARY STATEMENT FOR THE MONTH OF {month_label}", fmt_subtitle)

            ws.merge_range('A3:H3', 'EMPLOYEE DETAILS', fmt_group_header)
            ws.merge_range('I3:S3', 'WORKED DAYS & OT', fmt_group_header)
            ws.merge_range('T3:AA3', 'FIXED SALARY', fmt_group_header)
            ws.merge_range('AB3:AI3', 'EARNINGS', fmt_group_header)
            ws.merge_range('AJ3:AM3', 'STATUTORY GROSS & ARREARS', fmt_group_header)
            ws.merge_range('AN3:AW3', 'DEDUCTIONS', fmt_group_header)
            ws.write('AX3', 'NET SALARY', fmt_group_header)
            ws.merge_range('AY3:BB3', 'ADVANCE TRACKING', fmt_group_header)

            headers = [
                'S.No', 'Emp ID', 'Employee Name', 'Department', 'Designation', 'UAN No', 'ESI No', 'Category',
                'Working Days', 'Present', 'N/H', 'EL', 'CL', 'SL', 'Payable Days', 'Act OT Hrs', 'Reg OT', 'Spl OT', 'OT Hrs (/2)',
                'Per Day Wage', 'Basic+DA', 'HRA', 'Convey Allow', 'Washing Allow', 'Other Allow', 'OT Hrs Wage', 'Gross Fixed',
                'Earned Basic+DA', 'Earned HRA', 'Earned Conv', 'Earned Wash', 'Earned Other', 'Reg OT Wages', 'Spl OT Wages', 'Earned Gross',
                'Gross-OT', 'PF Gross', 'ESI Gross', 'Arrears',
                'PF Dedn', 'Acc PF Dedn', 'ESI Dedn', 'Acc ESI Dedn', 'LIC', 'Advance Dedn', 'NAPS Dedn', 'Accomdn', 'Other Dedn', 'Total Dedn',
                'Net Salary',
                'New Advance', 'Installment', 'Opening Advance', 'Closing Advance'
            ]
            for col_idx, h in enumerate(headers):
                ws.write(3, col_idx, h, fmt_col_header)

            row_idx = 4
            for idx, r in enumerate(rows, start=1):
                ws.write(row_idx, 0, idx, fmt_center)
                ws.write(row_idx, 1, str(r.get('Emp_No', '')), fmt_text_bold)
                ws.write(row_idx, 2, str(r.get('Employee_Name') or r.get('Name', '')), fmt_text)
                ws.write(row_idx, 3, str(r.get('Department', '') or '-'), fmt_text)
                ws.write(row_idx, 4, str(r.get('Designation', '') or '-'), fmt_text)
                ws.write(row_idx, 5, str(r.get('UAN_No', '') or '-'), fmt_text)
                ws.write(row_idx, 6, str(r.get('ESI_No', '') or '-'), fmt_text)
                ws.write(row_idx, 7, str(r.get('Category', '')), fmt_center)

                ws.write(row_idx, 8, float(r.get('Working_Days', standard_days) or standard_days), fmt_num)
                ws.write(row_idx, 9, float(r.get('Present_Days', standard_days) or standard_days), fmt_num)
                ws.write(row_idx, 10, float(r.get('NH', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 11, float(r.get('EL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 12, float(r.get('CL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 13, float(r.get('SL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 14, float(r.get('Total_Days', standard_days) or standard_days), fmt_num)

                act_ot = float(r.get('Act_OT_Hrs', 0.0) or r.get('OT_Hours', 0.0) or 0.0)
                reg_ot = min(act_ot, 50.0)
                spl_ot = max(0.0, act_ot - 50.0)
                ot_hrs_display = act_ot / 2.0
                
                ws.write(row_idx, 15, act_ot, fmt_num)
                ws.write(row_idx, 16, reg_ot, fmt_num)
                ws.write(row_idx, 17, spl_ot, fmt_num)
                ws.write(row_idx, 18, ot_hrs_display, fmt_num)

                pdw = float(r.get('Per_Day_Wage', 0.0) or 0.0)
                fg = pdw * standard_days
                
                ws.write(row_idx, 19, pdw, fmt_currency)
                ws.write(row_idx, 20, fg * 0.50, fmt_currency)
                ws.write(row_idx, 21, fg * 0.20, fmt_currency)
                ws.write(row_idx, 22, fg * 0.10, fmt_currency)
                ws.write(row_idx, 23, fg * 0.10, fmt_currency)
                ws.write(row_idx, 24, fg * 0.10, fmt_currency)
                ws.write(row_idx, 25, pdw / 8.0 if pdw else 0.0, fmt_currency)
                ws.write(row_idx, 26, fg, fmt_currency_bold)

                ws.write(row_idx, 27, float(r.get('Earned_Basic_DA', r.get('Basic_DA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 28, float(r.get('Earned_HRA', r.get('HRA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 29, float(r.get('Earned_Conveyance', r.get('Conveyance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 30, float(r.get('Earned_Washing', r.get('Washing_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 31, float(r.get('Earned_Other', r.get('Other_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 32, float(r.get('OT_Wages', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 33, float(r.get('Special_OT_Amount', 0.0) or 0.0), fmt_currency)
                
                earned_gross = float(r.get('Gross_Wages', 0.0) or 0.0)
                ot_wages = float(r.get('OT_Wages', 0.0) or 0.0)
                spl_ot_wages = float(r.get('Special_OT_Amount', 0.0) or 0.0)
                gross_minus_ot = earned_gross - ot_wages - spl_ot_wages
                
                ws.write(row_idx, 34, earned_gross, fmt_currency_bold)
                ws.write(row_idx, 35, gross_minus_ot, fmt_currency)
                ws.write(row_idx, 36, float(r.get('PF_Eligible_Gross', 0.0) or 0.0), fmt_currency)
                
                esi_gross = float(r.get('ESI_Eligible_Gross', 0.0) or 0.0)
                ws.write(row_idx, 37, esi_gross, fmt_currency)
                ws.write(row_idx, 38, float(r.get('Arrears', 0.0) or 0.0), fmt_currency)

                pf_dedn = float(r.get('PF_Deduction', 0.0) or 0.0)
                esi_dedn = float(r.get('ESI_Deduction', 0.0) or 0.0)
                
                ws.write(row_idx, 39, pf_dedn, fmt_currency)
                ws.write(row_idx, 40, pf_dedn, fmt_currency)
                ws.write(row_idx, 41, esi_dedn, fmt_currency)
                ws.write(row_idx, 42, round(esi_gross * 0.0325, 2), fmt_currency)
                ws.write(row_idx, 43, float(r.get('LIC_Deduction', 0.0) or 0.0), fmt_currency)
                adv_dedn = float(r.get('Advance_Deduction', 0.0) or 0.0)
                ws.write(row_idx, 44, adv_dedn, fmt_currency)
                ws.write(row_idx, 45, float(r.get('NAPS_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 46, float(r.get('Accommodation_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 47, float(r.get('Other_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 48, float(r.get('Total_Deduction', 0.0) or 0.0), fmt_currency_bold)

                ws.write(row_idx, 49, float(r.get('Net_Salary', 0.0) or 0.0), fmt_net_salary)
                
                open_adv = float(r.get('Opening_Advance', 0.0) or 0.0)
                ws.write(row_idx, 50, 0.0, fmt_currency) # New Advance
                ws.write(row_idx, 51, adv_dedn, fmt_currency) # Installment
                ws.write(row_idx, 52, open_adv, fmt_currency)
                ws.write(row_idx, 53, open_adv + adv_dedn, fmt_currency)
                
                row_idx += 1

            # Total Row
            ws.merge_range(row_idx, 0, row_idx, 7, f"TOTAL ({len(rows)} Employees)", fmt_total_label)
            for c_i in range(8, 19):
                ws.write(row_idx, c_i, '', fmt_total_label)
            
            from xlsxwriter.utility import xl_col_to_name
            for c_i in range(19, 54):
                col_letter = xl_col_to_name(c_i)
                ws.write_formula(row_idx, c_i, f"=SUM({col_letter}5:{col_letter}{row_idx})", fmt_total_currency)

            ws.set_column(0, 0, 6)   # S.No
            ws.set_column(1, 1, 10)  # Emp ID
            ws.set_column(2, 2, 24)  # Name
            ws.set_column(3, 4, 16)  # Dept & Desig
            ws.set_column(5, 6, 16)  # UAN & ESI
            ws.set_column(7, 7, 16)  # Category
            ws.set_column(8, 18, 10) # Attendance & OT
            ws.set_column(19, 53, 14) # Currency columns

    wb.close()
    output.seek(0)
    return output, filename

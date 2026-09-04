import io
import datetime as dt
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
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
    from models.payroll_period_settings import get_period_settings_info
    period_info = get_period_settings_info(year, month)
    worker_working_days = period_info.get('worker_working_days', 26.0)
    staff_working_days = period_info.get('staff_working_days', 26.0)

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
            emp_is_staff = (emp.get('Employee_Type') == 'STAFF')
            emp_std_days = staff_working_days if emp_is_staff else worker_working_days

            if t and float(t.get('Gross_Wages', 0.0) or 0.0) > 0.0:
                t['Working_Days'] = emp_std_days
                uan = str(t.get('UAN_No') or t.get('UAN') or emp.get('UAN_No') or emp.get('UAN') or '').strip()
                esi = str(t.get('ESI_No') or emp.get('ESI_No') or '').strip()
                t['UAN_No'] = uan
                t['ESI_No'] = esi
                t['Department'] = t.get('Department') or emp.get('Department') or ''
                t['Designation'] = t.get('Designation') or emp.get('Designation') or ''

                # Ensure Fixed_Gross and components
                fg = float(t.get('Fixed_Gross') or emp.get('Fixed_Gross', 0.0) or 0.0)
                pdw = float(t.get('Per_Day_Wage') or emp.get('Per_Day_Wage', 0.0) or 0.0)
                if fg == 0.0 and pdw > 0.0:
                    fg = round(pdw * emp_std_days, 2)
                t['Fixed_Gross'] = fg
                t['Per_Day_Wage'] = pdw

                tot_days = float(t.get('Total_Days', emp_std_days) or emp_std_days)
                std_days = float(t.get('Working_Days', emp_std_days) or emp_std_days) or 26.0

                f_bda = float(t.get('Basic_DA') or emp.get('Basic_DA', 0.0) or (fg * 0.50))
                f_hra = float(t.get('HRA') or emp.get('HRA', 0.0) or (fg * 0.20))
                f_conv = float(t.get('Conveyance_Allowance') or emp.get('Conveyance_Allowance', 0.0) or (fg * 0.10))
                f_wash = float(t.get('Washing_Allowance') or emp.get('Washing_Allowance', 0.0) or (fg * 0.10))
                f_other = float(t.get('Other_Allowance') or emp.get('Other_Allowance', 0.0) or (fg * 0.10))

                t['Basic_DA'] = f_bda
                t['HRA'] = f_hra
                t['Conveyance_Allowance'] = f_conv
                t['Washing_Allowance'] = f_wash
                t['Other_Allowance'] = f_other

                # Check if earned slabs are 0 (e.g. older saved transactions)
                e_hra = float(t.get('Earned_HRA', t.get('HRA_Earned', 0.0)) or 0.0)
                if e_hra == 0.0 and fg > 0.0 and std_days > 0.0:
                    t['Earned_Basic_DA'] = round((f_bda / std_days) * tot_days, 2)
                    t['Earned_HRA'] = round((f_hra / std_days) * tot_days, 2)
                    t['Earned_Conveyance'] = round((f_conv / std_days) * tot_days, 2)
                    t['Earned_Washing'] = round((f_wash / std_days) * tot_days, 2)
                    t['Earned_Other'] = round((f_other / std_days) * tot_days, 2)
                else:
                    t['Earned_Basic_DA'] = float(t.get('Earned_Basic_DA', t.get('Basic_DA_Earned', 0.0)) or 0.0)
                    t['Earned_HRA'] = e_hra
                    t['Earned_Conveyance'] = float(t.get('Earned_Conveyance', t.get('Conveyance_Earned', 0.0)) or 0.0)
                    t['Earned_Washing'] = float(t.get('Earned_Washing', t.get('Washing_Allowance_Earned', 0.0)) or 0.0)
                    t['Earned_Other'] = float(t.get('Earned_Other', t.get('Other_Allowance_Earned', 0.0)) or 0.0)

                payroll_rows.append(t)
            else:
                att_dict = {'present_days': emp_std_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': emp_std_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
                ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': 0.0, 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
                sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
                c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=emp_std_days)
                c_res['Working_Days'] = emp_std_days
                c_res['UAN_No'] = str(emp.get('UAN_No') or emp.get('UAN') or '').strip()
                c_res['ESI_No'] = str(emp.get('ESI_No') or '').strip()
                c_res['Department'] = emp.get('Department') or ''
                c_res['Designation'] = emp.get('Designation') or ''
                payroll_rows.append(c_res)
    else:
        for emp in employees:
            emp_is_staff = (emp.get('Employee_Type') == 'STAFF')
            emp_std_days = staff_working_days if emp_is_staff else worker_working_days
            att_dict = {'present_days': emp_std_days, 'nh': 0.0, 'cl': 0.0, 'el': 0.0, 'sl': 0.0, 'total_days': emp_std_days, 'actual_ot_hours': 0.0, 'ot_hours': 0.0}
            ded_dict = {'arrears': 0.0, 'naps': 0.0, 'lic': 0.0, 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}
            sal_dict = {'Fixed_Gross': emp.get('Fixed_Gross', 0.0), 'Basic_DA': emp.get('Basic_DA', 0.0), 'HRA': emp.get('HRA', 0.0), 'Conveyance_Allowance': emp.get('Conveyance_Allowance', 0.0), 'Washing_Allowance': emp.get('Washing_Allowance', 0.0), 'Other_Allowance': emp.get('Other_Allowance', 0.0), 'Per_Day_Wage': emp.get('Per_Day_Wage', 0.0), 'OT_Rate': emp.get('OT_Rate', 56.25), 'PF_Eligible': emp.get('PF_Eligible', True), 'ESI_Eligible': emp.get('ESI_Eligible', True)}
            c_res = calculate_payroll(emp, sal_dict, att_dict, ded_dict, standard_days=emp_std_days)
            c_res['Working_Days'] = emp_std_days
            c_res['UAN_No'] = str(emp.get('UAN_No') or emp.get('UAN') or '').strip()
            c_res['ESI_No'] = str(emp.get('ESI_No') or '').strip()
            c_res['Department'] = emp.get('Department') or ''
            c_res['Designation'] = emp.get('Designation') or ''
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
            # STAFF COLUMNS (39 Cols: A to AM)
            ws.merge_range('A1:AM1', 'BARANI HYDRAULICS INDIA PRIVATE LIMITED - UNIT - 1', fmt_title)
            ws.merge_range('A2:AM2', f"{grp['title']} SALARY STATEMENT FOR THE MONTH OF {month_label}", fmt_subtitle)

            # Group headers
            ws.merge_range('A3:H3', 'EMPLOYEE DETAILS', fmt_group_header)
            ws.merge_range('I3:P3', 'WORKED DAYS', fmt_group_header)
            ws.merge_range('Q3:W3', 'FIXED SALARY STRUCTURE', fmt_group_header)
            ws.merge_range('X3:AD3', 'EARNINGS', fmt_group_header)
            ws.merge_range('AE3:AF3', 'STATUTORY GROSS', fmt_group_header)
            ws.merge_range('AG3:AL3', 'DEDUCTIONS', fmt_group_header)
            ws.write('AM3', 'NET SALARY', fmt_group_header)

            headers = [
                'S.No', 'Emp ID', 'Employee Name', 'Department', 'Designation', 'UAN No', 'ESI No', 'Category',
                'Working Days', 'Present', 'N/H', 'EL', 'CL', 'SL', 'Payable Days', 'OT Hours',
                'Gross', 'Basic+DA', 'HRA', 'Conv', 'Washing Allow', 'Other Allow', 'Gross Wages',
                'Basic+DA', 'HRA', 'Conv', 'Wash Allow', 'Other Allow', 'OT Wages', 'Gross Wages',
                'PF Gross', 'ESI Gross',
                'PF Dedn', 'ESI Dedn', 'LIC Dedn', 'Advance Dedn', 'Other Dedn', 'Total Dedn',
                'Net Salary'
            ]
            for col_idx, h in enumerate(headers):
                ws.write(3, col_idx, h, fmt_col_header)

            row_idx = 4
            default_emp_days = staff_working_days if 'STAFF' in cat_code else worker_working_days
            for idx, r in enumerate(rows, start=1):
                ws.write(row_idx, 0, idx, fmt_center)
                ws.write(row_idx, 1, str(r.get('Emp_No', '')), fmt_text_bold)
                ws.write(row_idx, 2, str(r.get('Employee_Name') or r.get('Name', '')), fmt_text)
                ws.write(row_idx, 3, str(r.get('Department', '') or '-'), fmt_text)
                ws.write(row_idx, 4, str(r.get('Designation', '') or '-'), fmt_text)
                uan_str = str(r.get('UAN_No') or r.get('UAN') or '').strip()
                esi_str = str(r.get('ESI_No') or '').strip()
                ws.write(row_idx, 5, uan_str if uan_str and uan_str not in ('0', 'None', 'nan') else '-', fmt_text)
                ws.write(row_idx, 6, esi_str if esi_str and esi_str not in ('0', 'None', 'nan') else '-', fmt_text)
                ws.write(row_idx, 7, str(r.get('Category', '')), fmt_center)

                ws.write(row_idx, 8, float(r.get('Working_Days', default_emp_days) or default_emp_days), fmt_num)
                ws.write(row_idx, 9, float(r.get('Present_Days', default_emp_days) or default_emp_days), fmt_num)
                ws.write(row_idx, 10, float(r.get('NH', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 11, float(r.get('EL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 12, float(r.get('CL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 13, float(r.get('SL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 14, float(r.get('Total_Days', default_emp_days) or default_emp_days), fmt_num)
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

                # Statutory Gross
                ws.write(row_idx, 30, float(r.get('PF_Eligible_Gross', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 31, float(r.get('ESI_Eligible_Gross', 0.0) or 0.0), fmt_currency)

                # Deductions
                ws.write(row_idx, 32, float(r.get('PF_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 33, float(r.get('ESI_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 34, float(r.get('LIC_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 35, float(r.get('Advance_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 36, float(r.get('Other_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 37, float(r.get('Total_Deduction', 0.0) or 0.0), fmt_currency_bold)

                ws.write(row_idx, 38, float(r.get('Net_Salary', 0.0) or 0.0), fmt_net_salary)
                row_idx += 1

            # Total Row
            ws.merge_range(row_idx, 0, row_idx, 7, f"TOTAL ({len(rows)} Employees)", fmt_total_label)
            for c_i in range(8, 16):
                ws.write(row_idx, c_i, '', fmt_total_label)
            for c_i in range(16, 39):
                col_letter = xl_col_to_name(c_i)
                ws.write_formula(row_idx, c_i, f"=SUM({col_letter}5:{col_letter}{row_idx})", fmt_total_currency)

            # Auto-fit column widths
            ws.set_column(0, 0, 6)   # S.No
            ws.set_column(1, 1, 10)  # Emp ID
            ws.set_column(2, 2, 24)  # Name
            ws.set_column(3, 4, 16)  # Dept & Desig
            ws.set_column(5, 6, 16)  # UAN & ESI
            ws.set_column(7, 7, 16)  # Category
            ws.set_column(8, 15, 10) # Attendance
            ws.set_column(16, 38, 14) # Currency columns

        else:
            # WORKER COLUMNS (52 Cols: A to AZ)
            ws.merge_range('A1:AZ1', 'BARANI HYDRAULICS INDIA PRIVATE LIMITED - UNIT - 1', fmt_title)
            ws.merge_range('A2:AZ2', f"{grp['title']} SALARY STATEMENT FOR THE MONTH OF {month_label}", fmt_subtitle)

            ws.merge_range('A3:H3', 'EMPLOYEE DETAILS', fmt_group_header)
            ws.merge_range('I3:S3', 'WORKED DAYS & OT', fmt_group_header)
            ws.merge_range('T3:AA3', 'FIXED SALARY', fmt_group_header)
            ws.merge_range('AB3:AI3', 'EARNINGS', fmt_group_header)
            ws.merge_range('AJ3:AM3', 'STATUTORY GROSS & ARREARS', fmt_group_header)
            ws.merge_range('AN3:AU3', 'DEDUCTIONS', fmt_group_header)
            ws.write('AV3', 'NET SALARY', fmt_group_header)
            ws.merge_range('AW3:AZ3', 'ADVANCE TRACKING', fmt_group_header)

            headers = [
                'S.No', 'Emp ID', 'Employee Name', 'Department', 'Designation', 'UAN No', 'ESI No', 'Category',
                'Working Days', 'Present', 'N/H', 'EL', 'CL', 'SL', 'Payable Days', 'Act OT Hrs', 'OT', 'SPL', 'OT Hrs (/2)',
                'Per Day Wage', 'Basic+DA', 'HRA', 'Convey Allow', 'Washing Allow', 'Other Allow', 'OT Hrs Wage', 'Gross Wages',
                'Basic+DA', 'HRA', 'Conv', 'Wash Allow', 'Other Allow', 'Spl Allowance', 'OT Wages', 'Gross Wages',
                'Gross-OT', 'PF Gross', 'ESI Gross', 'Arrears',
                'PF Dedn', 'ESI Dedn', 'LIC', 'Advance Dedn', 'NAPS Dedn', 'Accomdn', 'Other Dedn', 'Total Dedn',
                'Net Salary',
                'New Advance', 'Installment', 'Opening Advance', 'Closing Advance'
            ]
            for col_idx, h in enumerate(headers):
                ws.write(3, col_idx, h, fmt_col_header)

            row_idx = 4
            default_emp_days = staff_working_days if 'STAFF' in cat_code else worker_working_days
            for idx, r in enumerate(rows, start=1):
                ws.write(row_idx, 0, idx, fmt_center)
                ws.write(row_idx, 1, str(r.get('Emp_No', '')), fmt_text_bold)
                ws.write(row_idx, 2, str(r.get('Employee_Name') or r.get('Name', '')), fmt_text)
                ws.write(row_idx, 3, str(r.get('Department', '') or '-'), fmt_text)
                ws.write(row_idx, 4, str(r.get('Designation', '') or '-'), fmt_text)
                uan_str = str(r.get('UAN_No') or r.get('UAN') or '').strip()
                esi_str = str(r.get('ESI_No') or '').strip()
                ws.write(row_idx, 5, uan_str if uan_str and uan_str not in ('0', 'None', 'nan') else '-', fmt_text)
                ws.write(row_idx, 6, esi_str if esi_str and esi_str not in ('0', 'None', 'nan') else '-', fmt_text)
                ws.write(row_idx, 7, str(r.get('Category', '')), fmt_center)

                ws.write(row_idx, 8, float(r.get('Working_Days', default_emp_days) or default_emp_days), fmt_num)
                ws.write(row_idx, 9, float(r.get('Present_Days', default_emp_days) or default_emp_days), fmt_num)
                ws.write(row_idx, 10, float(r.get('NH', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 11, float(r.get('EL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 12, float(r.get('CL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 13, float(r.get('SL', 0.0) or 0.0), fmt_num)
                ws.write(row_idx, 14, float(r.get('Total_Days', default_emp_days) or default_emp_days), fmt_num)

                act_ot = float(r.get('Act_OT_Hrs', 0.0) or r.get('OT_Hours', 0.0) or 0.0)
                reg_ot = min(act_ot, 50.0)
                spl_ot = max(0.0, act_ot - 50.0)
                ot_hrs_display = reg_ot / 2.0
                
                ws.write(row_idx, 15, act_ot, fmt_num)
                ws.write(row_idx, 16, reg_ot, fmt_num)
                ws.write(row_idx, 17, spl_ot, fmt_num)
                ws.write(row_idx, 18, ot_hrs_display, fmt_num)

                pdw = float(r.get('Per_Day_Wage', 0.0) or 0.0)
                fg = float(r.get('Fixed_Gross', 0.0) or (pdw * default_emp_days))
                
                ws.write(row_idx, 19, pdw, fmt_currency)
                ws.write(row_idx, 20, float(r.get('Basic_DA', 0.0) or fg * 0.50), fmt_currency)
                ws.write(row_idx, 21, float(r.get('HRA', 0.0) or fg * 0.20), fmt_currency)
                ws.write(row_idx, 22, float(r.get('Conveyance_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 23, float(r.get('Washing_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 24, float(r.get('Other_Allowance', 0.0) or fg * 0.10), fmt_currency)
                ws.write(row_idx, 25, pdw / 8.0 if pdw else (fg / (standard_days * 8.0) if standard_days else 0.0), fmt_currency)
                ws.write(row_idx, 26, fg, fmt_currency_bold)

                ws.write(row_idx, 27, float(r.get('Earned_Basic_DA', r.get('Basic_DA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 28, float(r.get('Earned_HRA', r.get('HRA_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 29, float(r.get('Earned_Conveyance', r.get('Conveyance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 30, float(r.get('Earned_Washing', r.get('Washing_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 31, float(r.get('Earned_Other', r.get('Other_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 32, float(r.get('Special_OT_Amount', r.get('Special_Allowance_Earned', 0.0)) or 0.0), fmt_currency)
                ws.write(row_idx, 33, float(r.get('OT_Wages', 0.0) or 0.0), fmt_currency)
                
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
                ws.write(row_idx, 40, esi_dedn, fmt_currency)
                ws.write(row_idx, 41, float(r.get('LIC_Deduction', 0.0) or 0.0), fmt_currency)
                adv_dedn = float(r.get('Advance_Deduction', 0.0) or 0.0)
                ws.write(row_idx, 42, adv_dedn, fmt_currency)
                ws.write(row_idx, 43, float(r.get('NAPS_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 44, float(r.get('Accommodation_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 45, float(r.get('Other_Deduction', 0.0) or 0.0), fmt_currency)
                ws.write(row_idx, 46, float(r.get('Total_Deduction', 0.0) or 0.0), fmt_currency_bold)

                ws.write(row_idx, 47, float(r.get('Net_Salary', 0.0) or 0.0), fmt_net_salary)
                
                open_adv = float(r.get('Opening_Advance', 0.0) or 0.0)
                ws.write(row_idx, 48, 0.0, fmt_currency) # New Advance
                ws.write(row_idx, 49, adv_dedn, fmt_currency) # Installment
                ws.write(row_idx, 50, open_adv, fmt_currency)
                ws.write(row_idx, 51, open_adv + adv_dedn, fmt_currency)
                
                row_idx += 1

            # Total Row
            ws.merge_range(row_idx, 0, row_idx, 7, f"TOTAL ({len(rows)} Employees)", fmt_total_label)
            for c_i in range(8, 19):
                ws.write(row_idx, c_i, '', fmt_total_label)
            
            for c_i in range(19, 52):
                col_letter = xl_col_to_name(c_i)
                ws.write_formula(row_idx, c_i, f"=SUM({col_letter}5:{col_letter}{row_idx})", fmt_total_currency)

            ws.set_column(0, 0, 6)   # S.No
            ws.set_column(1, 1, 10)  # Emp ID
            ws.set_column(2, 2, 24)  # Name
            ws.set_column(3, 4, 16)  # Dept & Desig
            ws.set_column(5, 6, 16)  # UAN & ESI
            ws.set_column(7, 7, 16)  # Category
            ws.set_column(8, 18, 10) # Attendance & OT
            ws.set_column(19, 51, 14) # Currency columns

    wb.close()
    output.seek(0)
    return output, filename

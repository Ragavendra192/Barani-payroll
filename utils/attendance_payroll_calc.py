import pandas as pd
from utils.payroll_calculation_engine import calculate_payroll
from models_manual import get_manual_deductions

def calculate_attendance_payroll(df, year=None, month=None):
    """
    DataFrame wrapper around the authoritative payroll calculation engine.
    Applies utils.payroll_calculation_engine.calculate_payroll for each employee row.
    """
    df = df.copy()

    calculated_rows = []
    for _, row in df.iterrows():
        emp_dict = {
            'Employee_ID': row.get('Employee_ID'),
            'Emp_No': row.get('Emp_No'),
            'Name': row.get('Name'),
            'Category': row.get('Category'),
            'Employee_Type': row.get('Employee_Type'),
            'Payroll_Category': row.get('Payroll_Category')
        }

        sal_dict = {
            'Basic': row.get('Basic', 0.0),
            'DA': row.get('DA', 0.0),
            'HRA': row.get('HRA', 0.0),
            'Washing_Allowance': row.get('Washing_Allowance', 0.0),
            'Conveyance_Allowance': row.get('Conveyance', row.get('Conveyance_Allowance', 0.0)),
            'Special_Allowance': row.get('Special_Allowance', 0.0),
            'Other_Allowance': row.get('Other_Allowance', 0.0),
            'Gross_Wages': row.get('Monthly_Salary', row.get('Gross_Wages', 0.0)),
            'Per_Day_Wage': row.get('Daily_Wage', row.get('Per_Day_Wage', 0.0)),
            'PF_Eligible': row.get('PF_Eligible', True),
            'ESI_Eligible': row.get('ESI_Eligible', True)
        }

        att_dict = {
            'present_days': row.get('Present_Days', 0.0),
            'ph': row.get('PH', 0.0),
            'cl': row.get('CL', 0.0),
            'sl': row.get('SL', 0.0),
            'pl': row.get('PL', 0.0),
            'total_days': row.get('Total_Worked_Days'),
            'actual_ot_hours': row.get('Total_OT_Hours', row.get('Act_OT_Hrs', 0.0))
        }

        ded_dict = {
            'pt': row.get('PT', 0.0),
            'mess': row.get('Mess', 0.0),
            'lic': row.get('LIC', 0.0),
            'tds': row.get('TDS', 0.0),
            'naps': row.get('NAPS_Deduction', row.get('NAPS', 0.0)),
            'advance': row.get('Advance_Deduction', row.get('Advance', 0.0)),
            'accommodation': row.get('Accommodation_Deduction', 0.0),
            'other': row.get('Other_Deduction', 0.0),
            'arrears': row.get('Arrears', 0.0)
        }

        calc_res = calculate_payroll(emp_dict, sal_dict, att_dict, ded_dict)
        calculated_rows.append(calc_res)

    res_df = pd.DataFrame(calculated_rows)
    return res_df

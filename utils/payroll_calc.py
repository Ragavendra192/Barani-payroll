import pandas as pd
from utils.payroll_calculation_engine import calculate_payroll

def compute_payroll(emp, sal, att, ded):
    """
    DataFrame compute_payroll wrapper delegating to central calculation engine.
    """
    df = emp.merge(sal, on="Emp_No", how="left")
    df = df.merge(att, on="Emp_No", how="left")
    df = df.merge(ded, on="Emp_No", how="left")

    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(0)

    calc_results = []
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
            'Conveyance_Allowance': row.get('Conveyance', 0.0),
            'Special_Allowance': row.get('Special_Allowance', 0.0),
            'Gross_Wages': row.get('Gross_Wages', 0.0),
            'Per_Day_Wage': row.get('Per_Day_Wage', row.get('Daily_Wage', 0.0)),
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
            'actual_ot_hours': row.get('Total_OT_Hours', row.get('OT_Hours', 0.0))
        }
        ded_dict = {
            'pt': row.get('PT', 0.0),
            'mess': row.get('Mess', 0.0),
            'lic': row.get('LIC', 0.0),
            'tds': row.get('TDS', 0.0),
            'naps': row.get('NAPS', 0.0),
            'advance': row.get('Advance', 0.0),
            'accommodation': row.get('Accommodation', 0.0),
            'other': row.get('Other_Deduction', 0.0),
            'arrears': row.get('Arrears', 0.0)
        }
        res = calculate_payroll(emp_dict, sal_dict, att_dict, ded_dict)
        calc_results.append(res)

    return pd.DataFrame(calc_results)

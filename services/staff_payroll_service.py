from utils.payroll_calculation_engine import calculate_payroll

def calculate_staff_payroll(employee, working_days, ot_hours, other_deduction):
    """
    Staff/Worker payroll calculation helper delegating to central calculation engine.
    """
    emp_dict = {
        'Employee_ID': employee.get('Emp_ID') or employee.get('id'),
        'Emp_No': employee.get('Emp_No'),
        'Name': employee.get('Emp_Name') or employee.get('Name'),
        'Category': employee.get('Category'),
        'Employee_Type': employee.get('Employee_Type', 'STAFF'),
        'Payroll_Category': employee.get('Payroll_Category', 'PF_ESI')
    }

    sal_dict = {
        'Basic': employee.get('Basic', 0.0),
        'DA': employee.get('DA', 0.0),
        'HRA': employee.get('HRA', 0.0),
        'Washing_Allowance': employee.get('Washing_Allowance', 0.0),
        'Conveyance_Allowance': employee.get('Conveyance', 0.0),
        'Special_Allowance': employee.get('Special_Allowance', 0.0),
        'Gross_Wages': employee.get('Base_Gross', 0.0),
        'Per_Day_Wage': employee.get('Per_Day_Wage', 0.0),
        'PF_Eligible': employee.get('PF_Eligible', True),
        'ESI_Eligible': employee.get('ESI_Eligible', True)
    }

    att_dict = {
        'present_days': float(working_days or 0.0),
        'total_days': float(working_days or 0.0),
        'actual_ot_hours': float(ot_hours or 0.0)
    }

    ded_dict = {
        'other': float(other_deduction or 0.0)
    }

    res = calculate_payroll(emp_dict, sal_dict, att_dict, ded_dict)

    return {
        "Emp_No": employee["Emp_No"],
        "Emp_Name": res["Name"],
        "Department": employee.get("Department"),
        "Designation": employee.get("Designation"),
        "Working_Days": float(working_days or 0),
        "OT_Hours": float(ot_hours or 0),
        "Other_Deduction": float(other_deduction or 0),
        "Basic_Earned": res["Earned_Basic"],
        "DA_Earned": res["Earned_DA"],
        "HRA_Earned": res["Earned_HRA"],
        "Washing_Earned": res["Earned_Washing"],
        "Conveyance_Earned": res["Earned_Conveyance"],
        "Special_Allowance_Earned": res["Earned_Special"],
        "OT_Amount": res["OT_Wages"] + res["Special_OT_Amount"],
        "Gross_Salary": res["Gross_Wages"],
        "PF": res["PF_Deduction"],
        "ESI": res["ESI_Deduction"],
        "Total_Deduction": res["Total_Deduction"],
        "Net_Salary": res["Net_Salary"]
    }

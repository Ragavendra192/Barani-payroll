from utils.payroll_calculation_engine import calculate_payroll

def calculate_naps_payroll(employee, working_days, ot_hours, other_deduction):
    """
    NAPS Apprentice calculation helper delegating to central calculation engine.
    """
    emp_type = employee.get('Employee_Type', 'STAFF')
    cat = f"{emp_type.upper()}_NAPS"

    emp_dict = {
        'Employee_ID': employee.get('NAPS_ID') or employee.get('id'),
        'Emp_No': employee.get('Emp_No'),
        'Name': employee.get('Emp_Name') or employee.get('Name'),
        'Category': cat,
        'Employee_Type': emp_type,
        'Payroll_Category': 'NAPS'
    }

    sal_dict = {
        'Gross_Wages': employee.get('Stipend', 0.0),
        'Basic_DA': employee.get('Stipend', 0.0),
        'Per_Day_Wage': employee.get('Per_Day_Wage', 0.0),
        'PF_Eligible': False,
        'ESI_Eligible': False
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
        "NAPS_ID": employee.get("NAPS_ID", employee.get("Emp_No")),
        "Emp_No": employee["Emp_No"],
        "Emp_Name": res["Name"],
        "Department": employee.get("Department"),
        "Designation": employee.get("Designation"),
        "Working_Days": float(working_days or 0),
        "OT_Hours": float(ot_hours or 0),
        "Stipend_Earned": res["Earned_Basic_DA"],
        "OT_Amount": res["OT_Wages"] + res["Special_OT_Amount"],
        "Gross_Amount": res["Gross_Wages"],
        "PF": 0.0,
        "ESI": 0.0,
        "Other_Deduction": float(other_deduction or 0),
        "Total_Deduction": res["Total_Deduction"],
        "Net_Amount": res["Net_Salary"]
    }

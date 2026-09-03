import io
import pandas as pd
from models.payroll_transaction import get_payroll_transactions

def generate_monthly_salary_statement_excel(year, month):
    """
    Generates a 6-sheet Excel Workbook reproducing the exact BHIPL Unit-I Salary Statement format:
      1. STAFFS (STAFF_PF_ESI)
      2. WORKER'S - ESI PF (WORKER_PF_ESI)
      3. STAFF'S (NAPS) (STAFF_NAPS)
      4. WORKER'S (NAPS) (WORKER_NAPS)
      5. Non-pf ESi staff (STAFF_NON_PF_ESI)
      6. Non-pf ESi worker (WORKER_NON_PF_ESI)
    """
    output = io.BytesIO()
    
    category_sheets = [
        ("STAFFS", "STAFF_PF_ESI"),
        ("WORKER'S - ESI PF", "WORKER_PF_ESI"),
        ("STAFF'S (NAPS)", "STAFF_NAPS"),
        ("WORKER'S (NAPS)", "WORKER_NAPS"),
        ("Non-pf ESi staff", "STAFF_NON_PF_ESI"),
        ("Non-pf ESi worker", "WORKER_NON_PF_ESI")
    ]

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_title, cat in category_sheets:
            records = get_payroll_transactions(year, month, category=cat)
            
            if not records:
                # Add empty dataframe with standard columns
                df = pd.DataFrame(columns=[
                    "Emp No", "ERP Emp No", "Name", "Department", "Designation",
                    "Working Days", "OT Hours", "Per Day Wage",
                    "Basic + DA (Earned)", "HRA (Earned)", "Conveyance (Earned)", "Washing (Earned)", "Other (Earned)",
                    "Special Allowance", "OT Wages", "Gross Wages",
                    "PF", "ESI", "NAPS", "LIC", "Advance", "Accommodation", "Other Dedn", "Total Dedn", "Net Salary"
                ])
            else:
                formatted_rows = []
                for r in records:
                    formatted_rows.append({
                        "Emp No": r.get('Emp_No'),
                        "ERP Emp No": r.get('ERP_Emp_No') or r.get('Emp_No'),
                        "Emp Code": r.get('Emp_Code'),
                        "Name": r.get('Employee_Name'),
                        "Department": r.get('Department'),
                        "Designation": r.get('Designation'),
                        "Grade": r.get('Grade'),
                        "Present Days": r.get('Present_Days', 0.0),
                        "Total Days": r.get('Total_Days', 0.0),
                        "Working Days": r.get('Working_Days', 0.0),
                        "OT Hours": r.get('OT_Hours', 0.0),
                        "Per Day Wage": r.get('Per_Day_Wage', 0.0),
                        "Basic + DA (Earned)": r.get('Basic_DA_Earned', 0.0),
                        "HRA (Earned)": r.get('HRA_Earned', 0.0),
                        "Conveyance (Earned)": r.get('Conveyance_Earned', 0.0),
                        "Washing (Earned)": r.get('Washing_Allowance_Earned', 0.0),
                        "Other (Earned)": r.get('Other_Allowance_Earned', 0.0),
                        "Special Allowance": r.get('Special_Allowance_Earned', 0.0),
                        "OT Wages": r.get('OT_Wages', 0.0),
                        "Gross Wages": r.get('Gross_Wages', 0.0),
                        "PF": r.get('PF_Deduction', 0.0),
                        "ESI": r.get('ESI_Deduction', 0.0),
                        "NAPS": r.get('NAPS_Deduction', 0.0),
                        "LIC": r.get('LIC_Deduction', 0.0),
                        "Advance": r.get('Advance_Deduction', 0.0),
                        "Accommodation": r.get('Accommodation_Deduction', 0.0),
                        "Arrears": r.get('Arrears', 0.0),
                        "Total Dedn": r.get('Total_Deduction', 0.0),
                        "Net Salary": r.get('Net_Salary', 0.0)
                    })
                df = pd.DataFrame(formatted_rows)
            
            df.to_excel(writer, sheet_name=sheet_title, index=False)

    output.seek(0)
    return output

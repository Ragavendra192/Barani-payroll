import pandas as pd
from db import get_db_connection

def get_staff_payroll_month(year, month):
    conn = get_db_connection()
    query = """
        SELECT p.*, e.Emp_Name, e.Department, e.Designation, e.DOJ, e.UAN, e.ESI_No
        FROM StaffPayroll p
        JOIN StaffEmployees e ON e.Emp_No = p.Emp_No
        WHERE p.Year = ? AND p.Month = ?
        ORDER BY p.Emp_No
    """
    df = pd.read_sql(query, conn, params=[year, month])
    conn.close()
    return df.to_dict("records")

def get_staff_payroll_by_emp(year, month, emp_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, e.Emp_Name, e.Department, e.Designation, e.DOJ, e.UAN, e.ESI_No
        FROM StaffPayroll p
        JOIN StaffEmployees e ON e.Emp_No = p.Emp_No
        WHERE p.Year = ? AND p.Month = ? AND p.Emp_No = ?
    """, (year, month, emp_no))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cols = [c[0] for c in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
    return data

def save_staff_payroll_batch(year, month, records):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for r in records:
        cursor.execute("""
            MERGE StaffPayroll AS t
            USING (SELECT ? AS Year, ? AS Month, ? AS Emp_No) AS s
            ON t.Year = s.Year AND t.Month = s.Month AND t.Emp_No = s.Emp_No
            WHEN MATCHED THEN
                UPDATE SET
                    Working_Days = ?,
                    OT_Hours = ?,
                    Other_Deduction = ?,
                    Basic_Earned = ?,
                    DA_Earned = ?,
                    HRA_Earned = ?,
                    Washing_Earned = ?,
                    Conveyance_Earned = ?,
                    Special_Allowance_Earned = ?,
                    OT_Amount = ?,
                    Gross_Salary = ?,
                    PF = ?,
                    ESI = ?,
                    Total_Deduction = ?,
                    Net_Salary = ?,
                    Updated_At = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (
                    Year, Month, Emp_No,
                    Working_Days, OT_Hours, Other_Deduction,
                    Basic_Earned, DA_Earned, HRA_Earned,
                    Washing_Earned, Conveyance_Earned, Special_Allowance_Earned,
                    OT_Amount, Gross_Salary, PF, ESI,
                    Total_Deduction, Net_Salary, Created_At, Updated_At
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE());
        """, (
            year, month, int(r["Emp_No"]),
            
            float(r.get("Working_Days", 0)),
            float(r.get("OT_Hours", 0)),
            float(r.get("Other_Deduction", 0)),
            float(r.get("Basic_Earned", 0)),
            float(r.get("DA_Earned", 0)),
            float(r.get("HRA_Earned", 0)),
            float(r.get("Washing_Earned", 0)),
            float(r.get("Conveyance_Earned", 0)),
            float(r.get("Special_Allowance_Earned", 0)),
            float(r.get("OT_Amount", 0)),
            float(r.get("Gross_Salary", 0)),
            float(r.get("PF", 0)),
            float(r.get("ESI", 0)),
            float(r.get("Total_Deduction", 0)),
            float(r.get("Net_Salary", 0)),
            
            year, month, int(r["Emp_No"]),
            float(r.get("Working_Days", 0)),
            float(r.get("OT_Hours", 0)),
            float(r.get("Other_Deduction", 0)),
            float(r.get("Basic_Earned", 0)),
            float(r.get("DA_Earned", 0)),
            float(r.get("HRA_Earned", 0)),
            float(r.get("Washing_Earned", 0)),
            float(r.get("Conveyance_Earned", 0)),
            float(r.get("Special_Allowance_Earned", 0)),
            float(r.get("OT_Amount", 0)),
            float(r.get("Gross_Salary", 0)),
            float(r.get("PF", 0)),
            float(r.get("ESI", 0)),
            float(r.get("Total_Deduction", 0)),
            float(r.get("Net_Salary", 0))
        ))
    
    conn.commit()
    conn.close()

def delete_staff_payroll_month(year, month):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM StaffPayroll WHERE Year = ? AND Month = ?", (year, month))
    conn.commit()
    conn.close()

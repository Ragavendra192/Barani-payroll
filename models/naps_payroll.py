import pandas as pd
from db import get_db_connection

def get_naps_payroll_month(year, month):
    conn = get_db_connection()
    query = """
        SELECT p.*, n.Emp_Name, n.Department, n.Designation, n.DOJ
        FROM NAPSPayroll p
        JOIN NAPS n ON n.NAPS_ID = p.NAPS_ID
        WHERE p.Year = ? AND p.Month = ?
        ORDER BY p.Emp_No
    """
    df = pd.read_sql(query, conn, params=[year, month])
    conn.close()
    return df.to_dict("records")

def get_naps_payroll_by_emp(year, month, emp_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, n.Emp_Name, n.Department, n.Designation, n.DOJ
        FROM NAPSPayroll p
        JOIN NAPS n ON n.NAPS_ID = p.NAPS_ID
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

def save_naps_payroll_batch(year, month, records):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for r in records:
        cursor.execute("""
            MERGE NAPSPayroll AS t
            USING (SELECT ? AS Year, ? AS Month, ? AS NAPS_ID) AS s
            ON t.Year = s.Year AND t.Month = s.Month AND t.NAPS_ID = s.NAPS_ID
            WHEN MATCHED THEN
                UPDATE SET
                    Emp_No = ?,
                    Working_Days = ?,
                    OT_Hours = ?,
                    Stipend_Earned = ?,
                    OT_Amount = ?,
                    Gross_Amount = ?,
                    PF = ?,
                    ESI = ?,
                    Other_Deduction = ?,
                    Total_Deduction = ?,
                    Net_Amount = ?,
                    Updated_At = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (
                    Year, Month, NAPS_ID, Emp_No,
                    Working_Days, OT_Hours, Stipend_Earned,
                    OT_Amount, Gross_Amount, PF, ESI,
                    Other_Deduction, Total_Deduction, Net_Amount,
                    Created_At, Updated_At
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE());
        """, (
            year, month, int(r["NAPS_ID"]),
            
            int(r["Emp_No"]),
            float(r.get("Working_Days", 0)),
            float(r.get("OT_Hours", 0)),
            float(r.get("Stipend_Earned", 0)),
            float(r.get("OT_Amount", 0)),
            float(r.get("Gross_Amount", 0)),
            float(r.get("PF", 0)),
            float(r.get("ESI", 0)),
            float(r.get("Other_Deduction", 0)),
            float(r.get("Total_Deduction", 0)),
            float(r.get("Net_Amount", 0)),
            
            year, month, int(r["NAPS_ID"]), int(r["Emp_No"]),
            float(r.get("Working_Days", 0)),
            float(r.get("OT_Hours", 0)),
            float(r.get("Stipend_Earned", 0)),
            float(r.get("OT_Amount", 0)),
            float(r.get("Gross_Amount", 0)),
            float(r.get("PF", 0)),
            float(r.get("ESI", 0)),
            float(r.get("Other_Deduction", 0)),
            float(r.get("Total_Deduction", 0)),
            float(r.get("Net_Amount", 0))
        ))
    
    conn.commit()
    conn.close()

def delete_naps_payroll_month(year, month):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM NAPSPayroll WHERE Year = ? AND Month = ?", (year, month))
    conn.commit()
    conn.close()

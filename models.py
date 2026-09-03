import pandas as pd
from db import get_db_connection
def save_payroll(year, month, df):
    conn = get_db_connection()
    cursor = conn.cursor()

    for _, r in df.iterrows():
        cursor.execute("""
                MERGE dbo.PayrollHistory AS t
                USING (SELECT ? AS Year, ? AS Month, ? AS Emp_No) s
                ON t.Year = s.Year AND t.Month = s.Month AND t.Emp_No = s.Emp_No
                WHEN MATCHED THEN
                    UPDATE SET
                        Emp_Name = ?, Department = ?, Category = ?,
                        Basic = ?, DA = ?, HRA = ?, Washing_Allowance = ?, Conveyance = ?, Special_Allowance = ?,
                        OT_Amount = ?, Gross_Wages = ?, PF_Ded = ?, ESI_Ded = ?, Manual_Deductions = ?,
                        Total_Deductions = ?, Net_Pay = ?,
                        PH = ?, CL = ?, SL = ?, PL = ?,
                        Fixed_Basic_DA = ?, Fixed_HRA = ?, Fixed_Washing = ?, Fixed_Conveyance = ?, Fixed_Other = ?,
                        Earned_Basic_DA = ?, Earned_HRA = ?, Earned_Washing = ?, Earned_Conveyance = ?, Earned_Other = ?,
                        PT = ?, Mess = ?, LIC = ?, TDS = ?,
                        New_Advance = ?, Installment = ?, Opening_Advance = ?, Closing_Advance = ?
                WHEN NOT MATCHED THEN
                    INSERT (
                        Year, Month, Emp_No,
                        Emp_Name, Department, Category,
                        Basic, DA, HRA, Washing_Allowance, Conveyance, Special_Allowance,
                        OT_Amount, Gross_Wages, PF_Ded, ESI_Ded, Manual_Deductions,
                        Total_Deductions, Net_Pay,
                        PH, CL, SL, PL,
                        Fixed_Basic_DA, Fixed_HRA, Fixed_Washing, Fixed_Conveyance, Fixed_Other,
                        Earned_Basic_DA, Earned_HRA, Earned_Washing, Earned_Conveyance, Earned_Other,
                        PT, Mess, LIC, TDS,
                        New_Advance, Installment, Opening_Advance, Closing_Advance
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                        # match keys
                        year, month, int(r.get("Emp_No", 0)),

                        # update values
                        r.get("Emp_Name", ""), r.get("Department", ""), r.get("Category", ""),
                        float(r.get("Basic", 0)), float(r.get("DA", 0)), float(r.get("HRA", 0)),
                        float(r.get("Washing_Allowance", 0)), float(r.get("Conveyance", 0)), float(r.get("Special_Allowance", 0)),
                        float(r.get("OT_Amount", 0)), float(r.get("Gross_Wages", 0)), float(r.get("PF_Ded", 0)), float(r.get("ESI_Ded", 0)),
                        float(r.get("Manual_Deductions", 0)), float(r.get("Total_Deductions", 0)), float(r.get("Net_Pay", 0)),
                        float(r.get("PH", 0)), float(r.get("CL", 0)), float(r.get("SL", 0)), float(r.get("PL", 0)),
                        float(r.get("Fixed_Basic_DA", 0)), float(r.get("Fixed_HRA", 0)), float(r.get("Fixed_Washing", 0)), float(r.get("Fixed_Conveyance", 0)), float(r.get("Fixed_Other", 0)),
                        float(r.get("Earned_Basic_DA", 0)), float(r.get("Earned_HRA", 0)), float(r.get("Earned_Washing", 0)), float(r.get("Earned_Conveyance", 0)), float(r.get("Earned_Other", 0)),
                        float(r.get("PT", 0)), float(r.get("Mess", 0)), float(r.get("LIC", 0)), float(r.get("TDS", 0)),
                        float(r.get("New_Advance", 0)), float(r.get("Installment", 0)), float(r.get("Opening_Advance", 0)), float(r.get("Closing_Advance", 0)),

                        # insert keys (Year, Month, Emp_No)
                        year, month, int(r.get("Emp_No", 0)),
                        # insert values
                        r.get("Emp_Name", ""), r.get("Department", ""), r.get("Category", ""),
                        float(r.get("Basic", 0)), float(r.get("DA", 0)), float(r.get("HRA", 0)),
                        float(r.get("Washing_Allowance", 0)), float(r.get("Conveyance", 0)), float(r.get("Special_Allowance", 0)),
                        float(r.get("OT_Amount", 0)), float(r.get("Gross_Wages", 0)), float(r.get("PF_Ded", 0)), float(r.get("ESI_Ded", 0)),
                        float(r.get("Manual_Deductions", 0)), float(r.get("Total_Deductions", 0)), float(r.get("Net_Pay", 0)),
                        float(r.get("PH", 0)), float(r.get("CL", 0)), float(r.get("SL", 0)), float(r.get("PL", 0)),
                        float(r.get("Fixed_Basic_DA", 0)), float(r.get("Fixed_HRA", 0)), float(r.get("Fixed_Washing", 0)), float(r.get("Fixed_Conveyance", 0)), float(r.get("Fixed_Other", 0)),
                        float(r.get("Earned_Basic_DA", 0)), float(r.get("Earned_HRA", 0)), float(r.get("Earned_Washing", 0)), float(r.get("Earned_Conveyance", 0)), float(r.get("Earned_Other", 0)),
                        float(r.get("PT", 0)), float(r.get("Mess", 0)), float(r.get("LIC", 0)), float(r.get("TDS", 0)),
                        float(r.get("New_Advance", 0)), float(r.get("Installment", 0)), float(r.get("Opening_Advance", 0)), float(r.get("Closing_Advance", 0))
                ))

    conn.commit()
    conn.close()




def get_payroll(year, month):
    conn = get_db_connection()
    query = """
SELECT
  ISNULL(p.ReceiptNumber, p.ID) AS ReceiptNumber,
  p.Emp_No, p.Emp_Name, p.Department, p.Category,
  p.Basic, p.DA, p.HRA, p.Washing_Allowance, p.Conveyance, p.Special_Allowance,
  p.PH, p.CL, p.SL, p.PL,
  p.Gross_Wages, p.PF_Ded, p.ESI_Ded, p.Manual_Deductions, p.Total_Deductions, p.Net_Pay,
  p.Fixed_Basic_DA, p.Fixed_HRA, p.Fixed_Washing, p.Fixed_Conveyance, p.Fixed_Other,
  p.Earned_Basic_DA, p.Earned_HRA, p.Earned_Washing, p.Earned_Conveyance, p.Earned_Other,
  p.PT, p.Mess, p.LIC, p.TDS,
  p.New_Advance, p.Installment, p.Opening_Advance, p.Closing_Advance,
  p.OT_Amount, p.DOJ, p.UAN, p.ESI_No,
  ISNULL(a.Advance, 0) AS Advance_Manual,
  ISNULL(l.Loan, 0) AS Loan_Manual
FROM PayrollHistory p
LEFT JOIN (
    SELECT Emp_No, ISNULL(SUM(Amount),0) AS Advance
    FROM ManualDeductions
    WHERE Year = ? AND Month = ? AND Deduction_Type LIKE 'Advance%'
    GROUP BY Emp_No
) a ON p.Emp_No = a.Emp_No
LEFT JOIN (
    SELECT Emp_No, ISNULL(SUM(Amount),0) AS Loan
    FROM ManualDeductions
    WHERE Year = ? AND Month = ? AND Deduction_Type LIKE 'Loan%'
    GROUP BY Emp_No
) l ON p.Emp_No = l.Emp_No
WHERE p.Year = ? AND p.Month = ?
ORDER BY p.Emp_No
"""
    params = [year, month, year, month, year, month]
    return pd.read_sql(query, conn, params=params)

def get_archived_months():
    """
    Returns list of (Year, Month) tuples
    Example: [(2025, 11), (2025, 10)]
    """
    conn = get_db_connection()
    query = """
        SELECT DISTINCT Year, Month
        FROM PayrollHistory
        ORDER BY Year DESC, Month DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()

    return [(int(r.Year), int(r.Month)) for _, r in df.iterrows()]


def search_payroll_history(
    emp_no=None,
    emp_name=None,
    dept=None,
    year=None,
    month=None,
    min_net_pay=None,
    max_net_pay=None
):
    conn = get_db_connection()

    query = """
        SELECT
            Year,
            Month,
            Emp_No,
            Emp_Name,
            Department,
            Category,
            Gross_Wages,
            Net_Pay
        FROM PayrollHistory
        WHERE 1=1
    """
    params = []

    if year:
        query += " AND Year = ?"
        params.append(year)

    if month:
        query += " AND Month = ?"
        params.append(month)

    if emp_no:
        query += " AND Emp_No = ?"
        params.append(emp_no)

    if emp_name:
        query += " AND Emp_Name LIKE ?"
        params.append(f"%{emp_name}%")

    if dept:
        query += " AND Department LIKE ?"
        params.append(f"%{dept}%")

    if min_net_pay is not None:
        query += " AND Net_Pay >= ?"
        params.append(min_net_pay)

    if max_net_pay is not None:
        query += " AND Net_Pay <= ?"
        params.append(max_net_pay)

    query += " ORDER BY Year DESC, Month DESC, Emp_No"

    df = pd.read_sql(query, conn, params=params)
    conn.close()

    return df.to_dict("records")

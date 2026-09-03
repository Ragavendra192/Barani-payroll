import pandas as pd
from db import get_db_connection

def get_archived_payroll_months():
    conn = get_db_connection()
    query = """
        SELECT DISTINCT Year, Month FROM (
            SELECT Year, Month FROM StaffPayroll
            UNION
            SELECT Year, Month FROM NAPSPayroll
            UNION
            SELECT Year, Month FROM PayrollHistory
        ) AS Months
        ORDER BY Year DESC, Month DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return [(int(r.Year), int(r.Month)) for _, r in df.iterrows()]

def search_payroll_history(emp_type=None, year=None, month=None, emp_no=None, emp_name=None, dept=None):
    conn = get_db_connection()
    records = []

    # 1. Staff Payroll search
    if emp_type in (None, "All", "Staff", "staff"):
        q_staff = """
            SELECT
                p.Year, p.Month, p.Emp_No, e.Emp_Name, e.Department,
                'Staff' AS Emp_Type, p.Gross_Salary AS Gross, p.Total_Deduction AS Deduction, p.Net_Salary AS Net_Pay
            FROM StaffPayroll p
            JOIN StaffEmployees e ON e.Emp_No = p.Emp_No
            WHERE 1=1
        """
        params_s = []
        if year:
            q_staff += " AND p.Year = ?"
            params_s.append(year)
        if month:
            q_staff += " AND p.Month = ?"
            params_s.append(month)
        if emp_no:
            q_staff += " AND p.Emp_No = ?"
            params_s.append(emp_no)
        if emp_name:
            q_staff += " AND e.Emp_Name LIKE ?"
            params_s.append(f"%{emp_name}%")
        if dept:
            q_staff += " AND e.Department LIKE ?"
            params_s.append(f"%{dept}%")

        df_s = pd.read_sql(q_staff, conn, params=params_s if params_s else None)
        records.extend(df_s.to_dict("records"))

    # 2. NAPS Payroll search
    if emp_type in (None, "All", "NAPS", "naps"):
        q_naps = """
            SELECT
                p.Year, p.Month, p.Emp_No, n.Emp_Name, n.Department,
                'NAPS' AS Emp_Type, p.Gross_Amount AS Gross, p.Total_Deduction AS Deduction, p.Net_Amount AS Net_Pay
            FROM NAPSPayroll p
            JOIN NAPS n ON n.NAPS_ID = p.NAPS_ID
            WHERE 1=1
        """
        params_n = []
        if year:
            q_naps += " AND p.Year = ?"
            params_n.append(year)
        if month:
            q_naps += " AND p.Month = ?"
            params_n.append(month)
        if emp_no:
            q_naps += " AND p.Emp_No = ?"
            params_n.append(emp_no)
        if emp_name:
            q_naps += " AND n.Emp_Name LIKE ?"
            params_n.append(f"%{emp_name}%")
        if dept:
            q_naps += " AND n.Department LIKE ?"
            params_n.append(f"%{dept}%")

        df_n = pd.read_sql(q_naps, conn, params=params_n if params_n else None)
        records.extend(df_n.to_dict("records"))

    # 3. Legacy Payroll History fallback (if no modern Staff/NAPS record matched)
    if not records and emp_type in (None, "All", "Legacy", "Staff", "staff"):
        q_leg = """
            SELECT
                Year, Month, Emp_No, Emp_Name, Department,
                ISNULL(Category, 'Legacy') AS Emp_Type, Gross_Wages AS Gross, Total_Deductions AS Deduction, Net_Pay
            FROM PayrollHistory
            WHERE 1=1
        """
        params_l = []
        if year:
            q_leg += " AND Year = ?"
            params_l.append(year)
        if month:
            q_leg += " AND Month = ?"
            params_l.append(month)
        if emp_no:
            q_leg += " AND Emp_No = ?"
            params_l.append(emp_no)
        if emp_name:
            q_leg += " AND Emp_Name LIKE ?"
            params_l.append(f"%{emp_name}%")
        if dept:
            q_leg += " AND Department LIKE ?"
            params_l.append(f"%{dept}%")

        df_l = pd.read_sql(q_leg, conn, params=params_l if params_l else None)
        records.extend(df_l.to_dict("records"))

    conn.close()
    return records

def get_dashboard_summary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM StaffEmployees WHERE Status = 'Active'")
    active_staff = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM NAPS WHERE Status = 'Active'")
    active_naps = cur.fetchone()[0] or 0

    # Latest month payroll totals
    cur.execute("""
        SELECT TOP 1 Year, Month FROM (
            SELECT Year, Month FROM StaffPayroll
            UNION
            SELECT Year, Month FROM NAPSPayroll
            UNION
            SELECT Year, Month FROM PayrollHistory
        ) AS Months
        ORDER BY Year DESC, Month DESC
    """)
    row_latest = cur.fetchone()
    
    current_year = row_latest[0] if row_latest else None
    current_month = row_latest[1] if row_latest else None

    current_gross = 0.0
    current_deduction = 0.0
    current_net = 0.0
    current_emp_count = 0

    if current_year and current_month:
        # Sum staff payroll
        cur.execute("""
            SELECT COUNT(*), ISNULL(SUM(Gross_Salary),0), ISNULL(SUM(Total_Deduction),0), ISNULL(SUM(Net_Salary),0)
            FROM StaffPayroll WHERE Year = ? AND Month = ?
        """, (current_year, current_month))
        c_s, g_s, d_s, n_s = cur.fetchone()

        # Sum NAPS payroll
        cur.execute("""
            SELECT COUNT(*), ISNULL(SUM(Gross_Amount),0), ISNULL(SUM(Total_Deduction),0), ISNULL(SUM(Net_Amount),0)
            FROM NAPSPayroll WHERE Year = ? AND Month = ?
        """, (current_year, current_month))
        c_n, g_n, d_n, n_n = cur.fetchone()

        # If no redesigned staff/naps payroll for this month, sum legacy
        if c_s == 0 and c_n == 0:
            cur.execute("""
                SELECT COUNT(*), ISNULL(SUM(Gross_Wages),0), ISNULL(SUM(Total_Deductions),0), ISNULL(SUM(Net_Pay),0)
                FROM PayrollHistory WHERE Year = ? AND Month = ?
            """, (current_year, current_month))
            c_l, g_l, d_l, n_l = cur.fetchone()
            current_emp_count = c_l
            current_gross = float(g_l)
            current_deduction = float(d_l)
            current_net = float(n_l)
        else:
            current_emp_count = c_s + c_n
            current_gross = float(g_s) + float(g_n)
            current_deduction = float(d_s) + float(d_n)
            current_net = float(n_s) + float(n_n)

    conn.close()

    return {
        "active_staff": active_staff,
        "active_naps": active_naps,
        "current_year": current_year,
        "current_month": current_month,
        "current_emp_count": current_emp_count,
        "current_gross": current_gross,
        "current_deduction": current_deduction,
        "current_net": current_net
    }

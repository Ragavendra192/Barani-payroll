import pandas as pd
from db import get_db_connection


# -------------------------------------------------
# SAVE / UPSERT ATTENDANCE
# -------------------------------------------------
def upsert_attendance(df):
    conn = get_db_connection()
    cursor = conn.cursor()

    for _, r in df.iterrows():
        cursor.execute("""
            MERGE AttendanceLogs AS t
            USING (
                SELECT ? AS Emp_No, ? AS Work_Date
            ) AS s
            ON t.Emp_No = s.Emp_No AND t.Work_Date = s.Work_Date
            WHEN MATCHED THEN
              UPDATE SET
                In_Time = ?,
                Out_Time = ?,
                Working_Hours = ?,
                Present = ?,
                OT_Hours = ?
            WHEN NOT MATCHED THEN
              INSERT (
                Emp_No, Work_Date,
                In_Time, Out_Time,
                Working_Hours, Present, OT_Hours
              )
              VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            int(r.Emp_No),
            r.Work_Date,

            r.In_Time,
            r.Out_Time,
            float(r.Working_Hours),
            int(r.Present),
            float(r.OT_Hours),

            int(r.Emp_No),
            r.Work_Date,
            r.In_Time,
            r.Out_Time,
            float(r.Working_Hours),
            int(r.Present),
            float(r.OT_Hours),
        ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# FETCH ATTENDANCE SUMMARY (FOR MODE-2 PAYROLL)
# -------------------------------------------------
def get_attendance_summary(year, month):
    conn = get_db_connection()
    query = """
        SELECT
            e.Emp_No,
            e.Emp_Name,
            e.Category,
            e.Daily_Wage,
            e.Monthly_Salary,
            e.Basic,
            e.DA,
            e.HRA,
            e.Washing_Allowance,
            e.Conveyance,
            e.Special_Allowance,
            e.PF_Eligible,
            e.ESI_Eligible,
            COUNT(CASE WHEN a.Present = 1 THEN 1 END) AS Present_Days,
            SUM(ISNULL(a.PH,0)) AS PH,
            SUM(ISNULL(a.CL,0)) AS CL,
            SUM(ISNULL(a.SL,0)) AS SL,
            SUM(ISNULL(a.PL,0)) AS PL,
            SUM(a.Working_Hours) AS Total_Working_Hours,
            SUM(a.OT_Hours) AS Total_OT_Hours
        FROM AttendanceLogs a
        JOIN EmployeeMaster e ON e.Emp_No = a.Emp_No
        WHERE MONTH(a.Work_Date) = ? AND YEAR(a.Work_Date) = ?
        GROUP BY
            e.Emp_No, e.Emp_Name, e.Category,
            e.Daily_Wage, e.Monthly_Salary,
            e.Basic, e.DA, e.HRA,
            e.Washing_Allowance, e.Conveyance, e.Special_Allowance,
            e.PF_Eligible, e.ESI_Eligible
        ORDER BY e.Emp_No
    """
    df = pd.read_sql(query, conn, params=[month, year])
    conn.close()
    return df


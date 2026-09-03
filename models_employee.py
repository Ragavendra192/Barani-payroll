import pandas as pd
from db import get_db_connection


# -------------------------------------------------
# UPSERT EMPLOYEE MASTER (BULK)
# -------------------------------------------------
def upsert_employee_master(df):
    conn = get_db_connection()
    cursor = conn.cursor()

    for _, r in df.iterrows():
        cursor.execute("""
        MERGE EmployeeMaster AS t
        USING (SELECT ? AS Emp_No) s
        ON t.Emp_No = s.Emp_No
        WHEN MATCHED THEN
          UPDATE SET
            Emp_Name = ?,
            Department = ?,
            Category = ?,
            DOJ = ?,
            Basic = ?,
            DA = ?,
            HRA = ?,
            Washing_Allowance = ?,
            Conveyance = ?,
            Special_Allowance = ?,
            PF_Eligible = ?,
            ESI_Eligible = ?,
            UAN = ?,
            ESI_No = ?
        WHEN NOT MATCHED THEN
          INSERT (
            Emp_No, Emp_Name, Department, Category, DOJ,
            Basic, DA, HRA,
            Washing_Allowance, Conveyance, Special_Allowance,
            PF_Eligible, ESI_Eligible,
            UAN, ESI_No
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            # match
            int(r.Emp_No),

            # update
            r.Emp_Name,
            r.Department,
            r.Category,
            r.get("DOJ"),
            float(r.Basic),
            float(r.DA),
            float(r.HRA),
            float(r.Washing_Allowance),
            float(r.Conveyance),
            float(r.Special_Allowance),
            int(r.PF_Eligible),
            int(r.ESI_Eligible),
            r.get("UAN"),
            r.get("ESI_No"),

            # insert
            int(r.Emp_No),
            r.Emp_Name,
            r.Department,
            r.Category,
            r.get("DOJ"),
            float(r.Basic),
            float(r.DA),
            float(r.HRA),
            float(r.Washing_Allowance),
            float(r.Conveyance),
            float(r.Special_Allowance),
            int(r.PF_Eligible),
            int(r.ESI_Eligible),
            r.get("UAN"),
            r.get("ESI_No"),
        ))

    conn.commit()
    conn.close()


# -------------------------------------------------
# GET ALL EMPLOYEES
# -------------------------------------------------
def get_all_employees():
    conn = get_db_connection()
    df = pd.read_sql(
        "SELECT * FROM EmployeeMaster ORDER BY Emp_No",
        conn
    )
    conn.close()
    return df


# -------------------------------------------------
# GET SINGLE EMPLOYEE (REQUIRED FOR ATTENDANCE)
# -------------------------------------------------
def get_employee_by_empno(emp_no):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT Emp_No, Category FROM EmployeeMaster WHERE Emp_No = ?",
        emp_no
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "Emp_No": row.Emp_No,
        "Category": row.Category
    }
def get_employee_by_cardno(card_no):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT Emp_No, Category
        FROM EmployeeMaster
        WHERE Card_No=?
    """, card_no)

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "Emp_No": row[0],
        "Category": row[1]
    }

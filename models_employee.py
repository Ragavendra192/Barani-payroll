import pandas as pd
from db import get_db_connection


# -------------------------------------------------
# UPSERT EMPLOYEE MASTER (BULK)
# -------------------------------------------------
def upsert_employee_master(df):
    from models.employee import bulk_import_employees
    return bulk_import_employees(df)


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

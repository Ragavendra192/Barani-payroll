import pandas as pd
from db import get_db_connection

def get_all_staff_employees(status_filter=None):
    conn = get_db_connection()
    query = "SELECT * FROM StaffEmployees"
    params = []
    if status_filter:
        query += " WHERE Status = ?"
        params.append(status_filter)
    query += " ORDER BY Emp_No"
    df = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df.to_dict("records")

def get_staff_by_emp_no(emp_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM StaffEmployees WHERE Emp_No = ?", (emp_no,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cols = [c[0] for c in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
    return data

def add_staff_employee(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO StaffEmployees (
            Emp_No, Emp_Name, Department, Designation, DOJ,
            Basic, DA, HRA, Washing_Allowance, Conveyance, Special_Allowance,
            PF_Eligible, ESI_Eligible, UAN, ESI_No, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(data["Emp_No"]),
        data["Emp_Name"],
        data.get("Department"),
        data.get("Designation"),
        data.get("DOJ"),
        float(data.get("Basic", 0)),
        float(data.get("DA", 0)),
        float(data.get("HRA", 0)),
        float(data.get("Washing_Allowance", 0)),
        float(data.get("Conveyance", 0)),
        float(data.get("Special_Allowance", 0)),
        1 if data.get("PF_Eligible") in (1, True, "1", "on") else 0,
        1 if data.get("ESI_Eligible") in (1, True, "1", "on") else 0,
        data.get("UAN"),
        data.get("ESI_No"),
        data.get("Status", "Active")
    ))
    conn.commit()
    conn.close()

def update_staff_employee(emp_no, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE StaffEmployees SET
            Emp_Name = ?,
            Department = ?,
            Designation = ?,
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
            ESI_No = ?,
            Status = ?,
            Updated_At = GETDATE()
        WHERE Emp_No = ?
    """, (
        data["Emp_Name"],
        data.get("Department"),
        data.get("Designation"),
        data.get("DOJ"),
        float(data.get("Basic", 0)),
        float(data.get("DA", 0)),
        float(data.get("HRA", 0)),
        float(data.get("Washing_Allowance", 0)),
        float(data.get("Conveyance", 0)),
        float(data.get("Special_Allowance", 0)),
        1 if data.get("PF_Eligible") in (1, True, "1", "on") else 0,
        1 if data.get("ESI_Eligible") in (1, True, "1", "on") else 0,
        data.get("UAN"),
        data.get("ESI_No"),
        data.get("Status", "Active"),
        int(emp_no)
    ))
    conn.commit()
    conn.close()

def toggle_staff_status(emp_no, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE StaffEmployees SET Status = ?, Updated_At = GETDATE() WHERE Emp_No = ?", (status, emp_no))
    conn.commit()
    conn.close()

def search_staff_employees(search_term):
    conn = get_db_connection()
    query = """
        SELECT * FROM StaffEmployees
        WHERE CAST(Emp_No AS NVARCHAR) LIKE ? OR Emp_Name LIKE ? OR Department LIKE ? OR Designation LIKE ?
        ORDER BY Emp_No
    """
    term = f"%{search_term}%"
    df = pd.read_sql(query, conn, params=[term, term, term, term])
    conn.close()
    return df.to_dict("records")

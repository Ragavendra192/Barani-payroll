import pandas as pd
from db import get_db_connection

def get_all_naps_employees(status_filter=None):
    conn = get_db_connection()
    query = "SELECT * FROM NAPS"
    params = []
    if status_filter:
        query += " WHERE Status = ?"
        params.append(status_filter)
    query += " ORDER BY Emp_No"
    df = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df.to_dict("records")

def get_naps_by_emp_no(emp_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM NAPS WHERE Emp_No = ?", (emp_no,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cols = [c[0] for c in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
    return data

def get_naps_by_id(naps_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM NAPS WHERE NAPS_ID = ?", (naps_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cols = [c[0] for c in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
    return data

def add_naps_employee(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO NAPS (
            Emp_No, Emp_Name, Department, Designation, DOJ,
            Stipend, PF_Eligible, ESI_Eligible, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(data["Emp_No"]),
        data["Emp_Name"],
        data.get("Department"),
        data.get("Designation"),
        data.get("DOJ"),
        float(data.get("Stipend", 0)),
        1 if data.get("PF_Eligible") in (1, True, "1", "on") else 0,
        1 if data.get("ESI_Eligible") in (1, True, "1", "on") else 0,
        data.get("Status", "Active")
    ))
    conn.commit()
    conn.close()

def update_naps_employee(emp_no, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE NAPS SET
            Emp_Name = ?,
            Department = ?,
            Designation = ?,
            DOJ = ?,
            Stipend = ?,
            PF_Eligible = ?,
            ESI_Eligible = ?,
            Status = ?,
            Updated_At = GETDATE()
        WHERE Emp_No = ?
    """, (
        data["Emp_Name"],
        data.get("Department"),
        data.get("Designation"),
        data.get("DOJ"),
        float(data.get("Stipend", 0)),
        1 if data.get("PF_Eligible") in (1, True, "1", "on") else 0,
        1 if data.get("ESI_Eligible") in (1, True, "1", "on") else 0,
        data.get("Status", "Active"),
        int(emp_no)
    ))
    conn.commit()
    conn.close()

def toggle_naps_status(emp_no, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE NAPS SET Status = ?, Updated_At = GETDATE() WHERE Emp_No = ?", (status, emp_no))
    conn.commit()
    conn.close()

def search_naps_employees(search_term):
    conn = get_db_connection()
    query = """
        SELECT * FROM NAPS
        WHERE CAST(Emp_No AS NVARCHAR) LIKE ? OR Emp_Name LIKE ? OR Department LIKE ? OR Designation LIKE ?
        ORDER BY Emp_No
    """
    term = f"%{search_term}%"
    df = pd.read_sql(query, conn, params=[term, term, term, term])
    conn.close()
    return df.to_dict("records")

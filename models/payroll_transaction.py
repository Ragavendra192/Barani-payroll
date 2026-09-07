import time
from decimal import Decimal
import pandas as pd
from db import get_db_connection

_ATTENDANCE_COLS_CHECKED = False

def ensure_attendance_columns():
    """Ensure CL, EL, SL, and LOP_Days columns exist in PayrollAttendance and LOP_Deduction in PayrollTransaction."""
    global _ATTENDANCE_COLS_CHECKED
    if _ATTENDANCE_COLS_CHECKED:
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollAttendance' AND COLUMN_NAME = 'CL')
            BEGIN
                ALTER TABLE PayrollAttendance ADD CL DECIMAL(5,2) DEFAULT 0.0, EL DECIMAL(5,2) DEFAULT 0.0;
            END
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollAttendance' AND COLUMN_NAME = 'SL')
            BEGIN
                ALTER TABLE PayrollAttendance ADD SL DECIMAL(5,2) DEFAULT 0.0;
            END
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollAttendance' AND COLUMN_NAME = 'LOP_Days')
            BEGIN
                ALTER TABLE PayrollAttendance ADD LOP_Days DECIMAL(5,2) DEFAULT 0.0;
            END
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollTransaction' AND COLUMN_NAME = 'LOP_Deduction')
            BEGIN
                ALTER TABLE PayrollTransaction ADD LOP_Deduction DECIMAL(18,2) DEFAULT 0.0;
            END
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollTransaction' AND COLUMN_NAME = 'Opening_Advance')
            BEGIN
                ALTER TABLE PayrollTransaction ADD Opening_Advance DECIMAL(18,2) DEFAULT 0.0, New_Advance DECIMAL(18,2) DEFAULT 0.0, Closing_Advance DECIMAL(18,2) DEFAULT 0.0;
            END
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PayrollTransaction' AND COLUMN_NAME = 'TDS_Deduction')
            BEGIN
                ALTER TABLE PayrollTransaction ADD TDS_Deduction DECIMAL(18,2) DEFAULT 0.0;
            END
        """)
        conn.commit()
        conn.close()
        _ATTENDANCE_COLS_CHECKED = True
    except Exception as e:
        print(f"[ATTENDANCE COLUMN NOTICE]: {e}")

def get_payroll_transactions(year, month, category=None, emp_type=None, search=None, max_retries=3):
    """Retrieve monthly payroll transactions with CL/EL/SL/NH leaves and WITH (NOLOCK) hints."""
    ensure_attendance_columns()
    query = """
        SELECT 
            t.PayrollTransaction_ID, p.PayrollPeriod_ID, m.Employee_ID,
            m.Emp_No, ISNULL(m.Employee_Name, m.Emp_Name) AS Employee_Name,
            m.Emp_Code, m.ERP_Emp_No, m.Department, m.Designation, m.Grade, m.DOJ, m.Rejoin_DOJ,
            ISNULL(NULLIF(m.UAN_No, ''), ISNULL(m.UAN, '')) AS UAN_No,
            ISNULL(m.ESI_No, '') AS ESI_No,
            ISNULL(t.Employee_Type, m.Employee_Type) AS Employee_Type,
            ISNULL(t.Payroll_Category, m.Payroll_Category) AS Payroll_Category,
            ISNULL(t.Category, CASE WHEN m.Category IS NOT NULL AND m.Category != '' THEN m.Category ELSE UPPER(m.Employee_Type) + '_' + UPPER(m.Payroll_Category) END) AS Category,
            a.Present_Days, ISNULL(a.Normal_Holiday, 0.0) AS NH, ISNULL(a.CL, 0.0) AS CL, ISNULL(a.EL, 0.0) AS EL, ISNULL(a.SL, 0.0) AS SL,
            ISNULL(a.LOP_Days, 0.0) AS LOP_Days, ISNULL(t.LOP_Deduction, 0.0) AS LOP_Deduction,
            ISNULL(a.Total_Days, 0.0) AS Total_Days, ISNULL(a.Working_Days, p.Standard_Working_Days) AS Working_Days,
            a.Actual_OT_Hours AS Act_OT_Hrs, a.OT_Hours, a.Special_OT_Hours,
            ISNULL(m.Fixed_Gross, 0.0) AS Fixed_Gross,
            t.Basic_DA, t.HRA, t.Conveyance_Allowance, t.Washing_Allowance, t.Other_Allowance, t.Per_Day_Wage,
            t.Basic_DA_Earned, t.HRA_Earned, t.Conveyance_Earned, t.Washing_Allowance_Earned, t.Other_Allowance_Earned,
            t.Special_Allowance_Earned, t.OT_Wages, t.Gross_Wages,
            t.PF_Gross, t.ESI_Gross, t.PF_Deduction, t.Accounts_PF_Deduction, t.ESI_Deduction, t.Accounts_ESI_Deduction,
            t.Arrears, t.NAPS_Deduction, t.LIC_Deduction, ISNULL(t.TDS_Deduction, 0.0) AS TDS_Deduction, t.Advance_Deduction, t.Accommodation_Deduction, t.Other_Deduction,
            ISNULL(t.Opening_Advance, 0.0) AS Opening_Advance,
            ISNULL(t.New_Advance, 0.0) AS New_Advance,
            ISNULL(t.Closing_Advance, 0.0) AS Closing_Advance,
            t.Total_Deduction, t.Net_Salary,
            p.Payroll_Year, p.Payroll_Month, p.Standard_Working_Days
        FROM PayrollPeriod p WITH (NOLOCK)
        JOIN EmployeeMaster m WITH (NOLOCK) ON ISNULL(m.Status, 'Active') = 'Active'
        LEFT JOIN PayrollAttendance a WITH (NOLOCK) ON a.PayrollPeriod_ID = p.PayrollPeriod_ID AND a.Employee_ID = m.Employee_ID
        LEFT JOIN PayrollTransaction t WITH (NOLOCK) ON t.PayrollPeriod_ID = p.PayrollPeriod_ID AND t.Employee_ID = m.Employee_ID
        WHERE p.Payroll_Year = ? AND p.Payroll_Month = ?
    """
    params = [year, month]

    if category and category.upper() != 'ALL':
        if category.upper() in ('STAFF', 'WORKER'):
            query += " AND (t.Employee_Type = ? OR m.Employee_Type = ?)"
            params.extend([category.upper(), category.upper()])
        else:
            query += " AND (t.Category = ? OR m.Category = ?)"
            params.extend([category, category])
    if emp_type:
        query += " AND (t.Employee_Type = ? OR m.Employee_Type = ?)"
        params.extend([emp_type, emp_type])
    if search:
        query += " AND (m.Emp_No LIKE ? OR m.Employee_Name LIKE ? OR m.Emp_Name LIKE ? OR m.Department LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += """ ORDER BY 
        CASE WHEN UPPER(ISNULL(t.Employee_Type, m.Employee_Type)) LIKE '%STAFF%' THEN 1 ELSE 2 END,
        ISNULL(t.Category, m.Category),
        CASE WHEN ISNUMERIC(m.Emp_No) = 1 THEN CAST(m.Emp_No AS INT) ELSE 999999 END,
        m.Emp_No
    """

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            cols = [column[0] for column in cur.description]
            records = [dict(zip(cols, row)) for row in cur.fetchall()]
            conn.close()
            for r in records:
                pdw = float(r.get('Per_Day_Wage') or 0.0)
                std = float(r.get('Working_Days') or r.get('Standard_Working_Days') or 26.0)
                fg = float(r.get('Fixed_Gross') or 0.0)
                if fg == 0.0 and pdw > 0.0:
                    r['Fixed_Gross'] = round(pdw * std, 2)
                r['Earned_Basic_DA'] = float(r.get('Basic_DA_Earned') or r.get('Earned_Basic_DA') or 0.0)
                r['Basic_DA_Earned'] = r['Earned_Basic_DA']
                r['Earned_HRA'] = float(r.get('HRA_Earned') or r.get('Earned_HRA') or 0.0)
                r['HRA_Earned'] = r['Earned_HRA']
                r['Earned_Conveyance'] = float(r.get('Conveyance_Earned') or r.get('Earned_Conveyance') or 0.0)
                r['Conveyance_Earned'] = r['Earned_Conveyance']
                r['Earned_Washing'] = float(r.get('Washing_Allowance_Earned') or r.get('Earned_Washing') or 0.0)
                r['Washing_Allowance_Earned'] = r['Earned_Washing']
                r['Earned_Other'] = float(r.get('Other_Allowance_Earned') or r.get('Earned_Other') or 0.0)
                r['Other_Allowance_Earned'] = r['Earned_Other']
                r['Earned_Special'] = float(r.get('Special_Allowance_Earned') or r.get('Earned_Special') or 0.0)
                r['Special_Allowance_Earned'] = r['Earned_Special']
            return records
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise e

def get_payroll_attendance(year, month, max_retries=3):
    """Retrieve monthly attendance records directly from PayrollAttendance joined with PayrollPeriod."""
    ensure_attendance_columns()
    query = """
        SELECT 
            a.PayrollAttendance_ID, a.PayrollPeriod_ID, a.Employee_ID,
            m.Emp_No, ISNULL(m.Employee_Name, m.Emp_Name) AS Employee_Name,
            a.Present_Days, ISNULL(a.Normal_Holiday, 0.0) AS NH, ISNULL(a.CL, 0.0) AS CL, ISNULL(a.EL, 0.0) AS EL, ISNULL(a.SL, 0.0) AS SL,
            ISNULL(a.LOP_Days, 0.0) AS LOP_Days,
            ISNULL(a.Total_Days, 0.0) AS Total_Days, ISNULL(a.Working_Days, p.Standard_Working_Days) AS Working_Days,
            a.Actual_OT_Hours AS Act_OT_Hrs, a.OT_Hours, a.Special_OT_Hours,
            p.Payroll_Year, p.Payroll_Month, p.Standard_Working_Days
        FROM PayrollAttendance a WITH (NOLOCK)
        JOIN PayrollPeriod p WITH (NOLOCK) ON a.PayrollPeriod_ID = p.PayrollPeriod_ID
        JOIN EmployeeMaster m WITH (NOLOCK) ON a.Employee_ID = m.Employee_ID
        WHERE p.Payroll_Year = ? AND p.Payroll_Month = ?
    """
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, [year, month])
            cols = [column[0] for column in cur.description]
            records = [dict(zip(cols, row)) for row in cur.fetchall()]
            conn.close()
            return records
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            return []

def save_payroll_batch(year, month, records, standard_days=26.0, max_retries=3):
    """Batch upsert payroll transactions and attendance into SQL Server with deadlock retries."""
    ensure_attendance_columns()
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get or create PayrollPeriod
            cur.execute("SELECT PayrollPeriod_ID FROM PayrollPeriod WITH (NOLOCK) WHERE Payroll_Year = ? AND Payroll_Month = ?", (year, month))
            row_period = cur.fetchone()
            if row_period:
                period_id = row_period[0]
                cur.execute("UPDATE PayrollPeriod SET Standard_Working_Days = ?, Status = 'CALCULATED', Updated_At = GETDATE() WHERE PayrollPeriod_ID = ?", (standard_days, period_id))
            else:
                cur.execute("INSERT INTO PayrollPeriod (Payroll_Year, Payroll_Month, Standard_Working_Days, Status) OUTPUT INSERTED.PayrollPeriod_ID VALUES (?, ?, ?, 'CALCULATED')", (year, month, standard_days))
                row_new = cur.fetchone()
                if row_new and row_new[0]:
                    period_id = row_new[0]
                else:
                    raise ValueError(f"Failed to retrieve PayrollPeriod_ID for {month}/{year}")

            attendance_params = []
            transaction_params = []

            for r in records:
                emp_id = r['Employee_ID']
                pres_days = float(r.get('Present_Days', standard_days))
                nh_days = float(r.get('NH', r.get('PH', r.get('Normal_Holiday', 0.0))))
                cl_days = float(r.get('CL', 0.0))
                sl_days = float(r.get('SL', 0.0))
                el_days = float(r.get('EL', r.get('PL', 0.0)))
                tot_days = float(r.get('Total_Days', r.get('Total_Worked_Days', pres_days + nh_days + cl_days + sl_days + el_days)))
                work_days = float(r.get('Working_Days', standard_days))
                lop_days = float(r.get('LOP_Days', max(0.0, work_days - tot_days)))
                lop_ded = float(r.get('LOP_Deduction', 0.0))
                act_ot = float(r.get('Act_OT_Hrs', r.get('OT_Hours', 0.0)))
                ot_h = float(r.get('OT_Hours', 0.0))
                spl_ot = float(r.get('Special_OT_Hours', 0.0))

                attendance_params.append((
                    period_id, emp_id, pres_days, nh_days, cl_days, sl_days, el_days, lop_days, tot_days, work_days, act_ot, ot_h, spl_ot,
                    period_id, emp_id, pres_days, nh_days, cl_days, sl_days, el_days, lop_days, tot_days, work_days, act_ot, ot_h, spl_ot
                ))

                transaction_params.append((
                    period_id, emp_id,
                    r['Employee_Type'], r['Payroll_Category'], r['Category'],
                    r.get('Basic_DA', r.get('Fixed_Basic_DA', 0.0)), r.get('HRA', r.get('Fixed_HRA', 0.0)), r.get('Conveyance_Allowance', r.get('Fixed_Conveyance', 0.0)),
                    r.get('Washing_Allowance', r.get('Fixed_Washing', 0.0)), r.get('Other_Allowance', r.get('Fixed_Other', 0.0)), r.get('Special_Allowance', r.get('Fixed_Special', 0.0)),
                    r.get('Per_Day_Wage', 0.0), r.get('OT_Hours', 0.0), r.get('OT_Rate', 0.0), r.get('OT_Wages', 0.0),
                    r.get('Basic_DA_Earned', r.get('Earned_Basic_DA', 0.0)), r.get('HRA_Earned', r.get('Earned_HRA', 0.0)), r.get('Conveyance_Earned', r.get('Earned_Conveyance', 0.0)),
                    r.get('Washing_Allowance_Earned', r.get('Earned_Washing', 0.0)), r.get('Other_Allowance_Earned', r.get('Earned_Other', 0.0)), r.get('Special_Allowance_Earned', r.get('Earned_Special', 0.0)),
                    r.get('Gross_Wages', 0.0), r.get('PF_Gross', 0.0), r.get('ESI_Gross', 0.0),
                    r.get('PF_Deduction', 0.0), r.get('Accounts_PF_Deduction', 0.0),
                    r.get('ESI_Deduction', 0.0), r.get('Accounts_ESI_Deduction', 0.0),
                    r.get('Arrears', 0.0), r.get('NAPS_Deduction', 0.0), r.get('LIC_Deduction', 0.0), r.get('TDS_Deduction', r.get('TDS', 0.0)),
                    r.get('Advance_Deduction', 0.0), r.get('Accommodation_Deduction', 0.0), r.get('Other_Deduction', 0.0),
                    float(r.get('Opening_Advance', 0.0) or 0.0), float(r.get('New_Advance', 0.0) or 0.0), float(r.get('Closing_Advance', 0.0) or 0.0),
                    lop_ded, r.get('Total_Deduction', 0.0), r.get('Net_Salary', 0.0),

                    period_id, emp_id,
                    r['Employee_Type'], r['Payroll_Category'], r['Category'],
                    r.get('Basic_DA', r.get('Fixed_Basic_DA', 0.0)), r.get('HRA', r.get('Fixed_HRA', 0.0)), r.get('Conveyance_Allowance', r.get('Fixed_Conveyance', 0.0)),
                    r.get('Washing_Allowance', r.get('Fixed_Washing', 0.0)), r.get('Other_Allowance', r.get('Fixed_Other', 0.0)), r.get('Special_Allowance', r.get('Fixed_Special', 0.0)),
                    r.get('Per_Day_Wage', 0.0), r.get('OT_Hours', 0.0), r.get('OT_Rate', 0.0), r.get('OT_Wages', 0.0),
                    r.get('Basic_DA_Earned', r.get('Earned_Basic_DA', 0.0)), r.get('HRA_Earned', r.get('Earned_HRA', 0.0)), r.get('Conveyance_Earned', r.get('Earned_Conveyance', 0.0)),
                    r.get('Washing_Allowance_Earned', r.get('Earned_Washing', 0.0)), r.get('Other_Allowance_Earned', r.get('Earned_Other', 0.0)), r.get('Special_Allowance_Earned', r.get('Earned_Special', 0.0)),
                    r.get('Gross_Wages', 0.0), r.get('PF_Gross', 0.0), r.get('ESI_Gross', 0.0),
                    r.get('PF_Deduction', 0.0), r.get('Accounts_PF_Deduction', 0.0),
                    r.get('ESI_Deduction', 0.0), r.get('Accounts_ESI_Deduction', 0.0),
                    r.get('Arrears', 0.0), r.get('NAPS_Deduction', 0.0), r.get('LIC_Deduction', 0.0), r.get('TDS_Deduction', r.get('TDS', 0.0)),
                    r.get('Advance_Deduction', 0.0), r.get('Accommodation_Deduction', 0.0), r.get('Other_Deduction', 0.0),
                    float(r.get('Opening_Advance', 0.0) or 0.0), float(r.get('New_Advance', 0.0) or 0.0), float(r.get('Closing_Advance', 0.0) or 0.0),
                    lop_ded, r.get('Total_Deduction', 0.0), r.get('Net_Salary', 0.0)
                ))

            cur.fast_executemany = True

            if attendance_params:
                cur.executemany("""
                    MERGE PayrollAttendance AS t
                    USING (SELECT ? AS PayrollPeriod_ID, ? AS Employee_ID) AS s
                    ON t.PayrollPeriod_ID = s.PayrollPeriod_ID AND t.Employee_ID = s.Employee_ID
                    WHEN MATCHED THEN
                        UPDATE SET Present_Days=?, Normal_Holiday=?, CL=?, SL=?, EL=?, LOP_Days=?, Total_Days=?, Working_Days=?, Actual_OT_Hours=?, OT_Hours=?, Special_OT_Hours=?
                    WHEN NOT MATCHED THEN
                        INSERT (PayrollPeriod_ID, Employee_ID, Present_Days, Normal_Holiday, CL, SL, EL, LOP_Days, Total_Days, Working_Days, Actual_OT_Hours, OT_Hours, Special_OT_Hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, attendance_params)

            if transaction_params:
                cur.executemany("""
                    MERGE PayrollTransaction AS t
                    USING (SELECT ? AS PayrollPeriod_ID, ? AS Employee_ID) AS s
                    ON t.PayrollPeriod_ID = s.PayrollPeriod_ID AND t.Employee_ID = s.Employee_ID
                    WHEN MATCHED THEN
                        UPDATE SET
                            Employee_Type=?, Payroll_Category=?, Category=?,
                            Basic_DA=?, HRA=?, Conveyance_Allowance=?, Washing_Allowance=?, Other_Allowance=?, Special_Allowance=?,
                            Per_Day_Wage=?, OT_Hours=?, OT_Rate=?, OT_Wages=?,
                            Basic_DA_Earned=?, HRA_Earned=?, Conveyance_Earned=?, Washing_Allowance_Earned=?, Other_Allowance_Earned=?, Special_Allowance_Earned=?,
                            Gross_Wages=?, PF_Gross=?, ESI_Gross=?, PF_Deduction=?, Accounts_PF_Deduction=?, ESI_Deduction=?, Accounts_ESI_Deduction=?,
                            Arrears=?, NAPS_Deduction=?, LIC_Deduction=?, TDS_Deduction=?, Advance_Deduction=?, Accommodation_Deduction=?, Other_Deduction=?,
                            Opening_Advance=?, New_Advance=?, Closing_Advance=?,
                            LOP_Deduction=?, Total_Deduction=?, Net_Salary=?, Updated_At=GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (
                            PayrollPeriod_ID, Employee_ID, Employee_Type, Payroll_Category, Category,
                            Basic_DA, HRA, Conveyance_Allowance, Washing_Allowance, Other_Allowance, Special_Allowance,
                            Per_Day_Wage, OT_Hours, OT_Rate, OT_Wages,
                            Basic_DA_Earned, HRA_Earned, Conveyance_Earned, Washing_Allowance_Earned, Other_Allowance_Earned, Special_Allowance_Earned,
                            Gross_Wages, PF_Gross, ESI_Gross, PF_Deduction, Accounts_PF_Deduction, ESI_Deduction, Accounts_ESI_Deduction,
                            Arrears, NAPS_Deduction, LIC_Deduction, TDS_Deduction, Advance_Deduction, Accommodation_Deduction, Other_Deduction,
                            Opening_Advance, New_Advance, Closing_Advance,
                            LOP_Deduction, Total_Deduction, Net_Salary, Created_At, Updated_At
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?, GETDATE(), GETDATE()
                        );
                """, transaction_params)

            conn.commit()

            # Update Advances table remaining balances and record any new advances
            try:
                for r in records:
                    emp_no = r.get('Emp_No') or r.get('Emp_Code')
                    if not emp_no:
                        continue

                    # 1. Record New Advance if entered
                    new_adv = float(r.get('New_Advance', 0.0) or 0.0)
                    if new_adv > 0:
                        cur.execute("SELECT COUNT(*) FROM Advances WHERE (Emp_No = ? OR CAST(Emp_No AS NVARCHAR) = ?) AND Start_Year = ? AND Start_Month = ? AND Total_Amount = ?", (emp_no, str(emp_no), year, month, new_adv))
                        if cur.fetchone()[0] == 0:
                            cur.execute("""
                                INSERT INTO Advances (Emp_No, Start_Year, Start_Month, Total_Amount, Installments, Monthly_Amount, Remaining_Amount, Status, Note, Created_At)
                                VALUES (?, ?, ?, ?, 1, ?, ?, 'Active', 'New Advance via Attendance', GETDATE())
                            """, (emp_no, year, month, new_adv, new_adv, new_adv))

                    # 2. Deduct from Active Advances
                    adv_ded = float(r.get('Advance_Deduction', 0.0) or 0.0)
                    if adv_ded > 0:
                        cur.execute("SELECT Id, Remaining_Amount FROM Advances WHERE (Emp_No = ? OR CAST(Emp_No AS NVARCHAR) = ?) AND Status = 'Active' ORDER BY Created_At ASC", (emp_no, str(emp_no)))
                        adv_rows = cur.fetchall()
                        rem_ded = Decimal(str(adv_ded))
                        for adv_id, rem_amt in adv_rows:
                            rem_amt_dec = Decimal(str(rem_amt or 0))
                            if rem_amt_dec > Decimal('0.00'):
                                deduct_now = min(rem_amt_dec, rem_ded)
                                new_rem = rem_amt_dec - deduct_now
                                rem_ded -= deduct_now
                                new_status = 'Completed' if new_rem <= Decimal('0.00') else 'Active'
                                cur.execute("UPDATE Advances SET Remaining_Amount = ?, Status = ? WHERE Id = ?", (float(new_rem), new_status, adv_id))
                                if rem_ded <= Decimal('0.00'):
                                    break
                conn.commit()
            except Exception as adv_err:
                print(f"[ADVANCES UPDATE NOTICE]: {adv_err}")

            conn.close()
            return True
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise e

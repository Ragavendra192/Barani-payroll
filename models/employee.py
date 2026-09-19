import calendar
import datetime as dt
import pandas as pd
from db import get_db_connection
from utils.contact_utils import normalize_indian_phone, mask_phone_number
from decimal import Decimal, ROUND_HALF_UP

def round_half_rupee(val):
    """
    Rounds value to nearest integer with >= 0.50 rounding up, < 0.50 rounding down.
    Returns float (e.g. 5080.40 -> 5080.0, 2540.50 -> 2541.0).
    """
    if val is None:
        return 0.0
    try:
        d = Decimal(str(round(float(val), 4)))
        return float(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except Exception:
        return 0.0

_CONTACT_COLS_CHECKED = False

def init_employee_contact_columns():
    """Ensure Phone_Number, Email_ID, Fixed_Gross, Father_Name, DOB, Bank_Acc_No, and Bank_IFSC columns exist on EmployeeMaster and EmployeeSalaryMaster tables."""
    global _CONTACT_COLS_CHECKED
    if _CONTACT_COLS_CHECKED:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Phone_Number'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Phone_Number VARCHAR(20) NULL;
            END
            
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Email_ID'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Email_ID VARCHAR(255) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Fixed_Gross'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Fixed_Gross DECIMAL(18, 2) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeSalaryMaster') AND name = 'Fixed_Gross'
            )
            BEGIN
                ALTER TABLE EmployeeSalaryMaster ADD Fixed_Gross DECIMAL(18, 2) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Father_Name'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Father_Name VARCHAR(255) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'DOB'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD DOB VARCHAR(20) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Bank_Acc_No'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Bank_Acc_No VARCHAR(50) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'Bank_IFSC'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD Bank_IFSC VARCHAR(20) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeMaster') AND name = 'LIC'
            )
            BEGIN
                ALTER TABLE EmployeeMaster ADD LIC DECIMAL(18, 2) NULL;
            END

            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('EmployeeSalaryMaster') AND name = 'LIC'
            )
            BEGIN
                ALTER TABLE EmployeeSalaryMaster ADD LIC DECIMAL(18, 2) NULL;
            END
        """)
        conn.commit()
        _CONTACT_COLS_CHECKED = True
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

# Execute schema migration check on module import
init_employee_contact_columns()

def calculate_experience_str(doj):
    """Calculates calendar-aware experience string from DOJ to today's date."""
    if not doj or pd.isna(doj):
        return "-"
    
    if isinstance(doj, str):
        doj_str = doj.strip()
        if not doj_str:
            return "-"
        try:
            doj_date = dt.datetime.strptime(doj_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                doj_date = dt.datetime.strptime(doj_str, "%d-%m-%Y").date()
            except ValueError:
                return "-"
    elif isinstance(doj, dt.datetime):
        doj_date = doj.date()
    elif isinstance(doj, dt.date):
        doj_date = doj
    else:
        return "-"

    today = dt.date.today()
    if doj_date > today:
        return "Future Date"

    years = today.year - doj_date.year
    months = today.month - doj_date.month
    days = today.day - doj_date.day

    if days < 0:
        months -= 1
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        _, days_in_prev = calendar.monthrange(prev_year, prev_month)
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    if years > 0:
        if months > 0:
            return f"{years} Year{'s' if years > 1 else ''} {months} Month{'s' if months > 1 else ''}"
        else:
            return f"{years} Year{'s' if years > 1 else ''}"
    elif months > 0:
        return f"{months} Month{'s' if months > 1 else ''}"
    elif days > 0:
        return f"{days} Day{'s' if days > 1 else ''}"
    else:
        return "0 Days"

def get_all_employees(category=None, employee_type=None, payroll_category=None, search=None, status='Active'):
    """Fetch employees from EmployeeMaster with optional 6-category filtering."""
    conn = get_db_connection()
    query = """
        SELECT 
            m.Employee_ID, m.Emp_No, m.ERP_Emp_No, m.Emp_Code,
            ISNULL(m.Employee_Name, m.Emp_Name) AS Employee_Name,
            m.Employee_Type, m.Payroll_Category, m.Category,
            m.Department, m.Designation, m.Grade, m.DOJ, m.Rejoin_DOJ,
            m.Father_Name, m.DOB, ISNULL(m.Bank_Acc_No, m.Bank_Account) AS Bank_Acc_No, m.Bank_IFSC,
            m.UAN_No, m.ESI_No, m.Status,
            m.Phone_Number, m.Email_ID,
            ISNULL(s.Fixed_Gross, m.Fixed_Gross) AS Fixed_Gross,
            s.Basic_DA, s.HRA, s.Conveyance_Allowance, s.Washing_Allowance, s.Other_Allowance,
            s.Per_Day_Wage, s.OT_Rate, s.PF_Eligible, s.ESI_Eligible,
            ISNULL(s.LIC, ISNULL(m.LIC, 0.0)) AS LIC
        FROM EmployeeMaster m
        LEFT JOIN EmployeeSalaryMaster s ON m.Employee_ID = s.Employee_ID AND s.Active = 1
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND m.Status = ?"
        params.append(status)
    if category and category.upper() != 'ALL':
        query += " AND m.Category = ?"
        params.append(category)
    if employee_type:
        query += " AND m.Employee_Type = ?"
        params.append(employee_type)
    if payroll_category:
        query += " AND m.Payroll_Category = ?"
        params.append(payroll_category)
    if search:
        query += " AND (m.Emp_No LIKE ? OR m.Employee_Name LIKE ? OR m.Emp_Name LIKE ? OR m.Department LIKE ? OR m.Father_Name LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    query += """ ORDER BY 
        CASE WHEN ISNUMERIC(m.Emp_No) = 1 THEN CAST(m.Emp_No AS INT) ELSE 999999 END,
        m.Emp_No
    """
    
    df = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    records = df.to_dict(orient='records')
    for r in records:
        r['Phone_Number_Masked'] = mask_phone_number(r.get('Phone_Number'))
        r['Experience_Formatted'] = calculate_experience_str(r.get('DOJ'))
        # Auto-compute Fixed_Gross if missing
        if not r.get('Fixed_Gross') or float(r.get('Fixed_Gross') or 0.0) == 0:
            b_da = float(r.get('Basic_DA') or 0.0)
            hra = float(r.get('HRA') or 0.0)
            conv = float(r.get('Conveyance_Allowance') or 0.0)
            wash = float(r.get('Washing_Allowance') or 0.0)
            other = float(r.get('Other_Allowance') or 0.0)
            p_day = float(r.get('Per_Day_Wage') or 0.0)
            if (b_da + hra + conv + wash + other) > 0:
                r['Fixed_Gross'] = round(b_da + hra + conv + wash + other, 2)
            elif p_day > 0:
                r['Fixed_Gross'] = round(p_day * 26.0, 2)
    return records

def get_employee_by_id(employee_id):
    """Fetch single employee details by Employee_ID."""
    conn = get_db_connection()
    query = """
        SELECT 
            m.Employee_ID, m.Emp_No, m.ERP_Emp_No, m.Emp_Code,
            ISNULL(m.Employee_Name, m.Emp_Name) AS Employee_Name,
            m.Employee_Type, m.Payroll_Category, m.Category,
            m.Department, m.Designation, m.Grade, m.DOJ, m.Rejoin_DOJ,
            m.Father_Name, m.DOB, ISNULL(m.Bank_Acc_No, m.Bank_Account) AS Bank_Acc_No, m.Bank_IFSC,
            m.UAN_No, m.ESI_No, m.Status,
            m.Phone_Number, m.Email_ID,
            ISNULL(s.Fixed_Gross, m.Fixed_Gross) AS Fixed_Gross,
            s.Basic_DA, s.HRA, s.Conveyance_Allowance, s.Washing_Allowance, s.Other_Allowance,
            s.Per_Day_Wage, s.OT_Rate, s.PF_Eligible, s.ESI_Eligible,
            ISNULL(s.LIC, ISNULL(m.LIC, 0.0)) AS LIC
        FROM EmployeeMaster m
        LEFT JOIN EmployeeSalaryMaster s ON m.Employee_ID = s.Employee_ID AND s.Active = 1
        WHERE m.Employee_ID = ?
    """
    df = pd.read_sql(query, conn, params=[employee_id])
    conn.close()
    records = df.to_dict(orient='records')
    if records:
        rec = records[0]
        rec['Phone_Number_Masked'] = mask_phone_number(rec.get('Phone_Number'))
        rec['Experience_Formatted'] = calculate_experience_str(rec.get('DOJ'))
        if not rec.get('Fixed_Gross') or float(rec.get('Fixed_Gross') or 0.0) == 0:
            b_da = float(rec.get('Basic_DA') or 0.0)
            hra = float(rec.get('HRA') or 0.0)
            conv = float(rec.get('Conveyance_Allowance') or 0.0)
            wash = float(rec.get('Washing_Allowance') or 0.0)
            other = float(rec.get('Other_Allowance') or 0.0)
            p_day = float(rec.get('Per_Day_Wage') or 0.0)
            if (b_da + hra + conv + wash + other) > 0:
                rec['Fixed_Gross'] = round(b_da + hra + conv + wash + other, 2)
            elif p_day > 0:
                rec['Fixed_Gross'] = round(p_day * 26.0, 2)
        return rec
    return None

def get_employee_by_emp_no(emp_no):
    """Fetch single employee details by Emp_No."""
    conn = get_db_connection()
    query = """
        SELECT 
            m.Employee_ID, m.Emp_No, m.ERP_Emp_No, m.Emp_Code,
            ISNULL(m.Employee_Name, m.Emp_Name) AS Employee_Name,
            m.Employee_Type, m.Payroll_Category, m.Category,
            m.Department, m.Designation, m.Grade, m.DOJ, m.Rejoin_DOJ,
            m.Father_Name, m.DOB, ISNULL(m.Bank_Acc_No, m.Bank_Account) AS Bank_Acc_No, m.Bank_IFSC,
            m.UAN_No, m.ESI_No, m.Status,
            m.Phone_Number, m.Email_ID,
            ISNULL(s.Fixed_Gross, m.Fixed_Gross) AS Fixed_Gross,
            s.Basic_DA, s.HRA, s.Conveyance_Allowance, s.Washing_Allowance, s.Other_Allowance,
            s.Per_Day_Wage, s.OT_Rate, s.PF_Eligible, s.ESI_Eligible,
            ISNULL(s.LIC, ISNULL(m.LIC, 0.0)) AS LIC
        FROM EmployeeMaster m
        LEFT JOIN EmployeeSalaryMaster s ON m.Employee_ID = s.Employee_ID AND s.Active = 1
        WHERE m.Emp_No = ?
    """
    df = pd.read_sql(query, conn, params=[emp_no])
    conn.close()
    records = df.to_dict(orient='records')
    if records:
        rec = records[0]
        rec['Phone_Number_Masked'] = mask_phone_number(rec.get('Phone_Number'))
        rec['Experience_Formatted'] = calculate_experience_str(rec.get('DOJ'))
        if not rec.get('Fixed_Gross') or float(rec.get('Fixed_Gross') or 0.0) == 0:
            b_da = float(rec.get('Basic_DA') or 0.0)
            hra = float(rec.get('HRA') or 0.0)
            conv = float(rec.get('Conveyance_Allowance') or 0.0)
            wash = float(rec.get('Washing_Allowance') or 0.0)
            other = float(rec.get('Other_Allowance') or 0.0)
            p_day = float(rec.get('Per_Day_Wage') or 0.0)
            if (b_da + hra + conv + wash + other) > 0:
                rec['Fixed_Gross'] = round(b_da + hra + conv + wash + other, 2)
            elif p_day > 0:
                rec['Fixed_Gross'] = round(p_day * 26.0, 2)
        return rec
    return None

import numpy as np

def safe_float(val, default=0.0):
    """Safely convert any cell value, string, or numpy NaN to float."""
    if val is None or pd.isna(val):
        return float(default)
    try:
        s = str(val).strip().replace(',', '')
        if s == '' or s.lower() in ['nan', 'none', 'null', '-']:
            return float(default)
        f = float(s)
        if pd.isna(f) or np.isnan(f):
            return float(default)
        return float(f)
    except (ValueError, TypeError):
        return float(default)

def add_employee(data):
    """Add a new employee and fixed salary structure."""
    conn = get_db_connection()
    cur = conn.cursor()

    emp_type = str(data.get('Employee_Type') or 'STAFF').strip().upper()
    if 'WORK' in emp_type:
        emp_type = 'WORKER'
    else:
        emp_type = 'STAFF'

    pay_cat = str(data.get('Payroll_Category') or 'PF_ESI').strip().upper()
    if 'NAPS' in pay_cat:
        pay_cat = 'NAPS'
    elif 'NON' in pay_cat:
        pay_cat = 'NON_PF_ESI'
    else:
        pay_cat = 'PF_ESI'

    category = f"{emp_type}_{pay_cat}"
    norm_phone = normalize_indian_phone(data.get('Phone_Number'))

    fixed_gross = safe_float(data.get('Fixed_Gross'))
    b_da = safe_float(data.get('Basic_DA'))
    basic = safe_float(data.get('Basic'))
    da = safe_float(data.get('DA'))
    hra = safe_float(data.get('HRA'))
    conv = safe_float(data.get('Conveyance_Allowance') if data.get('Conveyance_Allowance') is not None else data.get('Conveyance'))
    wash = safe_float(data.get('Washing_Allowance'))
    other = safe_float(data.get('Other_Allowance') if data.get('Other_Allowance') is not None else data.get('Special_Allowance'))
    per_day_wage = safe_float(data.get('Per_Day_Wage') if data.get('Per_Day_Wage') is not None else data.get('Daily_Wage'))
    lic = safe_float(data.get('LIC'))

    if emp_type == 'WORKER':
        if per_day_wage > 0:
            fixed_gross = round(per_day_wage * 26.0, 2)
            daily_wage = per_day_wage
        elif fixed_gross > 0:
            per_day_wage = round(fixed_gross / 26.0, 2)
            daily_wage = per_day_wage
        else:
            daily_wage = 0.0

        components_sum = b_da + hra + conv + wash + other
        if components_sum == 0 and fixed_gross > 0:
            b_da = round_half_rupee(fixed_gross * 0.50)
            hra = round_half_rupee(fixed_gross * 0.20)
            conv = round_half_rupee(fixed_gross * 0.10)
            wash = round_half_rupee(fixed_gross * 0.10)
            other = round_half_rupee(fixed_gross * 0.10)

        if basic == 0 and da == 0 and b_da > 0:
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)
        elif basic + da > 0 and b_da == 0:
            b_da = round(basic + da, 2)

        ot_rate = safe_float(data.get('OT_Rate'))
        if ot_rate <= 0:
            ot_rate = round(per_day_wage / 8.0, 2) if per_day_wage > 0 else 56.25

    else:  # STAFF
        per_day_wage = 0.0
        daily_wage = 0.0

        if basic + da > 0 and b_da == 0:
            b_da = round(basic + da, 2)
        elif b_da > 0 and basic + da == 0:
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)

        components_sum = b_da + hra + conv + wash + other
        if fixed_gross > 0 and components_sum == 0:
            b_da = round_half_rupee(fixed_gross * 0.50)
            hra = round_half_rupee(fixed_gross * 0.20)
            conv = round_half_rupee(fixed_gross * 0.10)
            wash = round_half_rupee(fixed_gross * 0.10)
            other = round_half_rupee(fixed_gross * 0.10)
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)
        elif fixed_gross == 0 and components_sum > 0:
            fixed_gross = round(components_sum, 2)

        ot_rate = safe_float(data.get('OT_Rate'))

    bank_acc = (data.get('Bank_Acc_No') or data.get('Bank_Account') or '').strip()
    father_name = (data.get('Father_Name') or '').strip()
    dob = (data.get('DOB') or '').strip() or None
    bank_ifsc = (data.get('Bank_IFSC') or '').strip()
    status_str = data.get('Status', 'Active')
    is_active_bit = 0 if str(status_str).strip().lower() in ['inactive', '0', 'no', 'disabled', 'false'] else 1

    pf_bit = 1 if data.get('PF_Eligible') in [True, 1, '1', 'YES', 'True', 'true'] else 0
    esi_bit = 1 if data.get('ESI_Eligible') in [True, 1, '1', 'YES', 'True', 'true'] else 0

    try:
        emp_no_val = int(str(data['Emp_No']).strip())
    except Exception:
        emp_no_val = data['Emp_No']

    cur.execute("""
        INSERT INTO EmployeeMaster (
            Emp_No, ERP_Emp_No, Emp_Code, Emp_Name, Employee_Name,
            Employee_Type, Payroll_Category, Category,
            Department, Designation, Grade, DOJ, Father_Name, DOB,
            Bank_Acc_No, Bank_Account, Bank_IFSC,
            UAN_No, UAN, ESI_No, Status, Is_Active,
            Phone_Number, Email_ID, Fixed_Gross, Monthly_Salary,
            Basic, DA, HRA, Washing_Allowance, Conveyance, Special_Allowance,
            Daily_Wage, PF_Eligible, ESI_Eligible, LIC
        ) 
        OUTPUT INSERTED.Employee_ID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        emp_no_val, str(data.get('ERP_Emp_No') or data['Emp_No']).strip(), str(data.get('Emp_Code') or data['Emp_No']).strip(),
        str(data['Employee_Name']).strip(), str(data['Employee_Name']).strip(),
        emp_type, pay_cat, category,
        data.get('Department'), data.get('Designation'), data.get('Grade'),
        data.get('DOJ'), father_name, dob,
        bank_acc, bank_acc, bank_ifsc,
        data.get('UAN_No'), data.get('UAN_No'), data.get('ESI_No'),
        status_str, is_active_bit,
        norm_phone, data.get('Email_ID'), fixed_gross, fixed_gross,
        basic, da, hra, wash, conv, other,
        daily_wage, pf_bit, esi_bit, lic
    ))
    employee_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO EmployeeSalaryMaster (
            Employee_ID, Basic_DA, HRA, Conveyance_Allowance, Washing_Allowance,
            Other_Allowance, Per_Day_Wage, OT_Rate, PF_Eligible, ESI_Eligible, Fixed_Gross, LIC, Active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        employee_id,
        b_da, hra, conv, wash, other,
        per_day_wage, ot_rate,
        pf_bit, esi_bit,
        fixed_gross, lic
    ))

    conn.commit()
    conn.close()
    return employee_id

def update_employee(employee_id, data):
    """Update employee master details and salary structure."""
    conn = get_db_connection()
    cur = conn.cursor()

    emp_type = str(data.get('Employee_Type') or 'STAFF').strip().upper()
    if 'WORK' in emp_type:
        emp_type = 'WORKER'
    else:
        emp_type = 'STAFF'

    pay_cat = str(data.get('Payroll_Category') or 'PF_ESI').strip().upper()
    if 'NAPS' in pay_cat:
        pay_cat = 'NAPS'
    elif 'NON' in pay_cat:
        pay_cat = 'NON_PF_ESI'
    else:
        pay_cat = 'PF_ESI'

    category = f"{emp_type}_{pay_cat}"
    norm_phone = normalize_indian_phone(data.get('Phone_Number'))

    fixed_gross = safe_float(data.get('Fixed_Gross'))
    b_da = safe_float(data.get('Basic_DA'))
    basic = safe_float(data.get('Basic'))
    da = safe_float(data.get('DA'))
    hra = safe_float(data.get('HRA'))
    conv = safe_float(data.get('Conveyance_Allowance') if data.get('Conveyance_Allowance') is not None else data.get('Conveyance'))
    wash = safe_float(data.get('Washing_Allowance'))
    other = safe_float(data.get('Other_Allowance') if data.get('Other_Allowance') is not None else data.get('Special_Allowance'))
    per_day_wage = safe_float(data.get('Per_Day_Wage') if data.get('Per_Day_Wage') is not None else data.get('Daily_Wage'))
    lic = safe_float(data.get('LIC'))

    if emp_type == 'WORKER':
        if per_day_wage > 0:
            fixed_gross = round(per_day_wage * 26.0, 2)
            daily_wage = per_day_wage
        elif fixed_gross > 0:
            per_day_wage = round(fixed_gross / 26.0, 2)
            daily_wage = per_day_wage
        else:
            daily_wage = 0.0

        components_sum = b_da + hra + conv + wash + other
        if per_day_wage > 0:
            if components_sum == 0 or abs(components_sum - per_day_wage) > 0.5:
                b_da = round_half_rupee(per_day_wage * 0.50)
                hra = round_half_rupee(per_day_wage * 0.20)
                conv = round_half_rupee(per_day_wage * 0.10)
                wash = round_half_rupee(per_day_wage * 0.10)
                other = round_half_rupee(per_day_wage * 0.10)
                basic = round_half_rupee(b_da * 0.50)
                da = round_half_rupee(b_da * 0.50)
        elif components_sum == 0 and fixed_gross > 0:
            b_da = round_half_rupee(fixed_gross * 0.50)
            hra = round_half_rupee(fixed_gross * 0.20)
            conv = round_half_rupee(fixed_gross * 0.10)
            wash = round_half_rupee(fixed_gross * 0.10)
            other = round_half_rupee(fixed_gross * 0.10)

        if basic == 0 and da == 0 and b_da > 0:
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)
        elif basic + da > 0 and b_da == 0:
            b_da = round(basic + da, 2)

        ot_rate = safe_float(data.get('OT_Rate'))
        if ot_rate <= 0:
            ot_rate = round(per_day_wage / 8.0, 2) if per_day_wage > 0 else 56.25

    else:  # STAFF
        per_day_wage = 0.0
        daily_wage = 0.0

        if basic + da > 0 and b_da == 0:
            b_da = round(basic + da, 2)
        elif b_da > 0 and basic + da == 0:
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)

        components_sum = b_da + hra + conv + wash + other
        if fixed_gross > 0 and components_sum == 0:
            b_da = round_half_rupee(fixed_gross * 0.50)
            hra = round_half_rupee(fixed_gross * 0.20)
            conv = round_half_rupee(fixed_gross * 0.10)
            wash = round_half_rupee(fixed_gross * 0.10)
            other = round_half_rupee(fixed_gross * 0.10)
            basic = round_half_rupee(b_da * 0.50)
            da = round_half_rupee(b_da * 0.50)
        elif fixed_gross == 0 and components_sum > 0:
            fixed_gross = round(components_sum, 2)

        ot_rate = safe_float(data.get('OT_Rate'))

    bank_acc = (data.get('Bank_Acc_No') or data.get('Bank_Account') or '').strip()
    father_name = (data.get('Father_Name') or '').strip()
    dob = (data.get('DOB') or '').strip() or None
    bank_ifsc = (data.get('Bank_IFSC') or '').strip()
    status_str = data.get('Status', 'Active')
    is_active_bit = 0 if str(status_str).strip().lower() in ['inactive', '0', 'no', 'disabled', 'false'] else 1

    pf_bit = 1 if data.get('PF_Eligible') in [True, 1, '1', 'YES', 'True', 'true'] else 0
    esi_bit = 1 if data.get('ESI_Eligible') in [True, 1, '1', 'YES', 'True', 'true'] else 0

    cur.execute("""
        UPDATE EmployeeMaster SET
            Emp_No = ISNULL(NULLIF(?, ''), Emp_No),
            Emp_Name = ?, Employee_Name = ?, Employee_Type = ?, Payroll_Category = ?, Category = ?,
            ERP_Emp_No = ?, Emp_Code = ?, Department = ?, Designation = ?, Grade = ?,
            DOJ = ?, Father_Name = ?, DOB = ?, Bank_Acc_No = ?, Bank_Account = ?, Bank_IFSC = ?,
            UAN_No = ?, UAN = ?, ESI_No = ?, Status = ?, Is_Active = ?,
            Phone_Number = ISNULL(?, Phone_Number), Email_ID = ?,
            Fixed_Gross = ?, Monthly_Salary = ?,
            Basic = ?, DA = ?, HRA = ?, Washing_Allowance = ?, Conveyance = ?, Special_Allowance = ?,
            Daily_Wage = ?, PF_Eligible = ?, ESI_Eligible = ?, LIC = ?,
            Updated_At = GETDATE()
        WHERE Employee_ID = ?
    """, (
        str(data.get('Emp_No') or '').strip(),
        str(data['Employee_Name']).strip(), str(data['Employee_Name']).strip(), emp_type, pay_cat, category,
        str(data.get('ERP_Emp_No') or data.get('Emp_No') or '').strip(), str(data.get('Emp_Code') or data.get('Emp_No') or '').strip(),
        data.get('Department'), data.get('Designation'), data.get('Grade'),
        data.get('DOJ'), father_name, dob,
        bank_acc, bank_acc, bank_ifsc,
        data.get('UAN_No'), data.get('UAN_No'), data.get('ESI_No'),
        status_str, is_active_bit,
        norm_phone, data.get('Email_ID'),
        fixed_gross, fixed_gross,
        basic, da, hra, wash, conv, other,
        daily_wage, pf_bit, esi_bit, lic,
        employee_id
    ))

    cur.execute("SELECT 1 FROM EmployeeSalaryMaster WHERE Employee_ID = ? AND Active = 1", (employee_id,))
    if cur.fetchone():
        cur.execute("""
            UPDATE EmployeeSalaryMaster SET
                Basic_DA = ?, HRA = ?, Conveyance_Allowance = ?, Washing_Allowance = ?,
                Other_Allowance = ?, Per_Day_Wage = ?, OT_Rate = ?, PF_Eligible = ?, ESI_Eligible = ?,
                Fixed_Gross = ?, LIC = ?
            WHERE Employee_ID = ? AND Active = 1
        """, (
            b_da, hra, conv, wash, other,
            per_day_wage, ot_rate,
            pf_bit, esi_bit,
            fixed_gross, lic,
            employee_id
        ))
    else:
        cur.execute("""
            INSERT INTO EmployeeSalaryMaster (
                Employee_ID, Basic_DA, HRA, Conveyance_Allowance, Washing_Allowance,
                Other_Allowance, Per_Day_Wage, OT_Rate, PF_Eligible, ESI_Eligible, Fixed_Gross, LIC, Active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            employee_id,
            b_da, hra, conv, wash, other,
            per_day_wage, ot_rate,
            pf_bit, esi_bit,
            fixed_gross, lic
        ))

    conn.commit()
    conn.close()

def toggle_employee_status(employee_id):
    """Toggle employee status between Active and Inactive."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE EmployeeMaster 
        SET Status = CASE WHEN Status = 'Active' THEN 'Inactive' ELSE 'Active' END,
            Is_Active = CASE WHEN Status = 'Active' THEN 0 ELSE 1 END,
            Updated_At = GETDATE()
        WHERE Employee_ID = ?
    """, (employee_id,))
    conn.commit()
    conn.close()


def parse_excel_date(val):
    """Parses date from Excel cell into YYYY-MM-DD string."""
    if pd.isna(val) or val is None or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null", "-"]:
        return None
    if isinstance(val, (dt.datetime, dt.date)):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_bool_flag(val, default_true=True):
    """Parses boolean eligibility flag (YES/NO, 1/0, TRUE/FALSE)."""
    if pd.isna(val) or val is None or str(val).strip() == "" or str(val).strip().lower() in ["nan", "none", "null"]:
        return default_true
    s = str(val).strip().upper()
    if s in ["YES", "Y", "TRUE", "1", "ELIGIBLE"]:
        return True
    elif s in ["NO", "N", "FALSE", "0", "NOT ELIGIBLE"]:
        return False
    return default_true


def bulk_import_employees(df):
    """
    Import or bulk upsert employees from DataFrame into EmployeeMaster & EmployeeSalaryMaster.
    Supports flexible column aliases, Workers Daily/Per-Day wages, and Staff salary structures.
    Returns summary dictionary with inserted, updated, total, and error list.
    """
    if df is None or df.empty:
        return {"total": 0, "inserted": 0, "updated": 0, "errors": ["Uploaded file contains no data."]}

    # Normalize DataFrame column names: strip and uppercase
    col_dict = {c: str(c).strip().upper().replace("_", " ") for c in df.columns}

    # Comprehensive column alias dictionary
    alias_map = {
        "EMP_NO": ["EMP_NO", "EMP NO", "EMPNO", "EMP CODE", "EMP_CODE", "EMPLOYEE CODE", "EMP_ID", "EMPLOYEE_ID", "EMP ID", "ID", "CARD NO", "CARD_NO"],
        "EMPLOYEE_NAME": ["EMPLOYEE_NAME", "EMPLOYEE NAME", "EMP_NAME", "EMP NAME", "NAME", "EMPLOYEE"],
        "EMPLOYEE_TYPE": ["EMPLOYEE_TYPE", "EMPLOYEE TYPE", "TYPE", "EMP_TYPE", "EMP TYPE"],
        "PAYROLL_CATEGORY": ["PAYROLL_CATEGORY", "PAYROLL CATEGORY", "PAYROLL CAT", "PAYROLL_CAT", "CAT"],
        "CATEGORY": ["CATEGORY", "EMP_CATEGORY", "EMPLOYEE CATEGORY"],
        "STATUS": ["STATUS", "EMP_STATUS", "EMPLOYEE_STATUS", "ACTIVE", "IS_ACTIVE", "STATE"],
        "DEPARTMENT": ["DEPARTMENT", "DEPT", "DEP"],
        "DESIGNATION": ["DESIGNATION", "DESIG", "ROLE", "TITLE", "POSITION"],
        "GRADE": ["GRADE", "LEVEL"],
        "DOJ": ["DOJ", "DATE OF JOINING", "JOINING DATE", "DATE_OF_JOINING", "JOIN_DATE"],
        "DOB": ["DOB", "DATE OF BIRTH", "BIRTH DATE", "DATE_OF_BIRTH"],
        "FATHER_NAME": ["FATHER_NAME", "FATHER NAME", "FATHER/HUSBAND NAME", "FATHER HUSBAND NAME", "FATHER", "HUSBAND NAME"],
        "BANK_ACC_NO": ["BANK_ACC_NO", "BANK ACC NO", "BANK ACCOUNT", "ACCOUNT NO", "BANK_ACCOUNT", "ACC NO", "A/C NO", "ACCOUNT NUMBER", "BANK ACCOUNT NO"],
        "BANK_IFSC": ["BANK_IFSC", "BANK IFSC", "IFSC", "IFSC CODE", "IFSC_CODE"],
        "UAN_NO": ["UAN_NO", "UAN NO", "UAN", "UAN NUMBER", "PF NO", "PF NUMBER"],
        "ESI_NO": ["ESI_NO", "ESI NO", "ESI", "ESI NUMBER", "ESIC", "ESIC NO"],
        "PHONE_NUMBER": ["PHONE_NUMBER", "PHONE NUMBER", "PHONE", "MOBILE", "MOBILE NO", "MOBILE NUMBER", "CONTACT"],
        "EMAIL_ID": ["EMAIL_ID", "EMAIL ID", "EMAIL", "MAIL", "MAIL ID", "E-MAIL"],
        "FIXED_GROSS": ["FIXED_GROSS", "FIXED GROSS", "GROSS", "GROSS SALARY", "FIXED_SALARY", "SALARY", "MONTHLY SALARY", "GROSS WAGES"],
        "BASIC_DA": ["BASIC_DA", "BASIC DA", "BASIC + DA", "BASIC+DA", "BASIC & DA"],
        "BASIC": ["BASIC", "BASIC SALARY", "BASIC_SALARY", "BASIC PAY"],
        "DA": ["DA", "DEARNESS ALLOWANCE", "D.A", "D.A."],
        "HRA": ["HRA", "HOUSE RENT ALLOWANCE", "H.R.A", "H.R.A."],
        "CONVEYANCE_ALLOWANCE": ["CONVEYANCE_ALLOWANCE", "CONVEYANCE", "CONVEYANCE ALLOWANCE", "CONV ALLOWANCE", "CONV"],
        "WASHING_ALLOWANCE": ["WASHING_ALLOWANCE", "WASHING", "WASHING ALLOWANCE", "WASH ALLOWANCE", "WASH"],
        "OTHER_ALLOWANCE": ["OTHER_ALLOWANCE", "OTHER ALLOWANCE", "SPECIAL ALLOWANCE", "SPECIAL_ALLOWANCE", "OTHER", "SPL ALLOWANCE", "SPL_ALLOWANCE"],
        "PER_DAY_WAGE": ["PER_DAY_WAGE", "PER DAY WAGE", "DAILY WAGE", "DAY WAGE", "DAILY_WAGE", "PER_DAY", "PER DAY", "RATE/DAY", "WAGE PER DAY", "RATE PER DAY"],
        "OT_RATE": ["OT_RATE", "OT RATE", "OVERTIME RATE", "OT RATE/HR"],
        "PF_ELIGIBLE": ["PF_ELIGIBLE", "PF ELIGIBLE", "PF", "PF YES/NO"],
        "ESI_ELIGIBLE": ["ESI_ELIGIBLE", "ESI ELIGIBLE", "ESI", "ESI YES/NO"],
        "LIC": ["LIC", "LIC AMOUNT", "LIC DEDUCTION", "LIC_DEDUCTION"]
    }

    def get_row_val(row, target_key):
        aliases = alias_map.get(target_key, [])
        for orig_col, norm_col in col_dict.items():
            if norm_col in [a.replace("_", " ") for a in aliases]:
                val = row[orig_col]
                if not pd.isna(val):
                    return val
        return None

    total = 0
    inserted = 0
    updated = 0
    errors = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel 1-based header is row 1
        emp_no_raw = get_row_val(row, "EMP_NO")
        if emp_no_raw is None or str(emp_no_raw).strip() == "":
            emp_no_raw = row.iloc[0] if len(row) > 0 else None

        if pd.isna(emp_no_raw) or str(emp_no_raw).strip() == "" or str(emp_no_raw).strip().lower() in ["nan", "none"]:
            continue  # Skip blank rows

        emp_no = str(emp_no_raw).strip()
        if emp_no.endswith(".0") and emp_no[:-2].isdigit():
            emp_no = emp_no[:-2]

        emp_name_raw = get_row_val(row, "EMPLOYEE_NAME")
        if emp_name_raw is None or pd.isna(emp_name_raw) or str(emp_name_raw).strip() == "":
            emp_name_raw = row.iloc[1] if len(row) > 1 else None

        if pd.isna(emp_name_raw) or str(emp_name_raw).strip() == "" or str(emp_name_raw).strip().lower() in ["nan", "none"]:
            errors.append(f"Row {row_num}: Missing Employee Name for Emp_No '{emp_no}'. Skipped.")
            continue

        emp_name = str(emp_name_raw).strip()
        total += 1

        # Extract wage & numeric fields early using safe_float
        per_day_wage = safe_float(get_row_val(row, "PER_DAY_WAGE"))
        fixed_gross = safe_float(get_row_val(row, "FIXED_GROSS"))
        basic_da = safe_float(get_row_val(row, "BASIC_DA"))
        basic_val = safe_float(get_row_val(row, "BASIC"))
        da_val = safe_float(get_row_val(row, "DA"))
        hra = safe_float(get_row_val(row, "HRA"))
        conv = safe_float(get_row_val(row, "CONVEYANCE_ALLOWANCE"))
        wash = safe_float(get_row_val(row, "WASHING_ALLOWANCE"))
        other = safe_float(get_row_val(row, "OTHER_ALLOWANCE"))
        ot_rate_val = safe_float(get_row_val(row, "OT_RATE"))
        lic_val = safe_float(get_row_val(row, "LIC"))

        # Smart Category and Employee_Type parsing
        raw_emp_type = str(get_row_val(row, "EMPLOYEE_TYPE") or "").strip().upper()
        raw_pay_cat = str(get_row_val(row, "PAYROLL_CATEGORY") or "").strip().upper()
        raw_cat = str(get_row_val(row, "CATEGORY") or "").strip().upper()

        emp_type = ""
        pay_cat = ""

        if "WORKER" in raw_cat:
            emp_type = "WORKER"
        elif "STAFF" in raw_cat:
            emp_type = "STAFF"

        if "NAPS" in raw_cat:
            pay_cat = "NAPS"
        elif "NON" in raw_cat:
            pay_cat = "NON_PF_ESI"
        elif "PF" in raw_cat or "ESI" in raw_cat:
            pay_cat = "PF_ESI"

        if not emp_type:
            if "WORK" in raw_emp_type:
                emp_type = "WORKER"
            elif "STAFF" in raw_emp_type:
                emp_type = "STAFF"
            elif "WORK" in raw_pay_cat:
                emp_type = "WORKER"
            elif "STAFF" in raw_pay_cat:
                emp_type = "STAFF"
            elif per_day_wage > 0:
                emp_type = "WORKER"
            else:
                emp_type = "STAFF"

        if not pay_cat:
            if "NAPS" in raw_pay_cat:
                pay_cat = "NAPS"
            elif "NON" in raw_pay_cat:
                pay_cat = "NON_PF_ESI"
            else:
                pay_cat = "PF_ESI"

        dept = str(get_row_val(row, "DEPARTMENT") or "General").strip()
        desig = str(get_row_val(row, "DESIGNATION") or "Employee").strip()
        grade_val = get_row_val(row, "GRADE")
        grade = str(grade_val).strip() if grade_val and not pd.isna(grade_val) else None

        doj = parse_excel_date(get_row_val(row, "DOJ"))
        dob = parse_excel_date(get_row_val(row, "DOB"))

        # Parse Status
        status_raw = get_row_val(row, "STATUS")
        status_clean = "Active"
        if status_raw is not None and not pd.isna(status_raw):
            s_val = str(status_raw).strip().lower()
            if s_val in ["inactive", "no", "0", "disabled", "false"]:
                status_clean = "Inactive"

        def clean_import_str(val):
            if val is None or pd.isna(val):
                return ""
            s = str(val).strip()
            if s.endswith(".0") and s[:-2].isdigit():
                s = s[:-2]
            if s.lower() in ["nan", "none", "null"]:
                return ""
            return s

        father_name = clean_import_str(get_row_val(row, "FATHER_NAME"))
        bank_acc = clean_import_str(get_row_val(row, "BANK_ACC_NO"))
        bank_ifsc = clean_import_str(get_row_val(row, "BANK_IFSC"))
        uan_no = clean_import_str(get_row_val(row, "UAN_NO"))
        esi_no = clean_import_str(get_row_val(row, "ESI_NO"))
        phone = clean_import_str(get_row_val(row, "PHONE_NUMBER"))
        email = clean_import_str(get_row_val(row, "EMAIL_ID"))

        is_pf = parse_bool_flag(get_row_val(row, "PF_ELIGIBLE"), default_true=(pay_cat == "PF_ESI"))
        is_esi = parse_bool_flag(get_row_val(row, "ESI_ELIGIBLE"), default_true=(pay_cat == "PF_ESI"))

        # Consolidate Basic + DA
        if basic_val + da_val > 0 and basic_da == 0:
            basic_da = basic_val + da_val

        emp_data = {
            'Emp_No': emp_no,
            'ERP_Emp_No': emp_no,
            'Emp_Code': emp_no,
            'Employee_Name': emp_name,
            'Father_Name': father_name,
            'DOB': dob,
            'Bank_Acc_No': bank_acc,
            'Bank_IFSC': bank_ifsc,
            'Employee_Type': emp_type,
            'Payroll_Category': pay_cat,
            'Department': dept,
            'Designation': desig,
            'Grade': grade,
            'Status': status_clean,
            'DOJ': doj,
            'UAN_No': uan_no,
            'ESI_No': esi_no,
            'Phone_Number': phone,
            'Email_ID': email,
            'Fixed_Gross': fixed_gross,
            'Basic_DA': basic_da,
            'Basic': basic_val,
            'DA': da_val,
            'HRA': hra,
            'Conveyance_Allowance': conv,
            'Washing_Allowance': wash,
            'Other_Allowance': other,
            'Per_Day_Wage': per_day_wage,
            'OT_Rate': ot_rate_val,
            'PF_Eligible': is_pf,
            'ESI_Eligible': is_esi,
            'LIC': lic_val
        }

        try:
            existing = get_employee_by_emp_no(emp_no)
            if existing:
                update_employee(existing['Employee_ID'], emp_data)
                updated += 1
            else:
                add_employee(emp_data)
                inserted += 1
        except Exception as e:
            errors.append(f"Row {row_num} (Emp_No {emp_no}): Error saving - {str(e)}")

    return {
        "total": total,
        "inserted": inserted,
        "updated": updated,
        "errors": errors
    }



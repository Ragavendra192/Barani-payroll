import time
import datetime as dt
import calendar
import pandas as pd
from db import get_db_connection

def calculate_month_working_days(year, month):
    """
    Calculate calendar_days, sunday_count, and default_working_days for any given year & month.
    Formula: Default Working Days = Calendar Days - Sunday Count
    """
    calendar_days = calendar.monthrange(year, month)[1]
    cal = calendar.Calendar(firstweekday=0)
    sunday_count = sum(1 for day in cal.itermonthdays2(year, month) if day[0] != 0 and day[1] == 6)
    default_working_days = float(calendar_days - sunday_count)
    return {
        'calendar_days': calendar_days,
        'sunday_count': sunday_count,
        'default_working_days': default_working_days
    }

_PERIOD_SETTINGS_TABLE_CHECKED = False

def init_period_settings_table():
    """Initializes the PayrollPeriodSettings table in SQL Server with additional columns."""
    global _PERIOD_SETTINGS_TABLE_CHECKED
    if _PERIOD_SETTINGS_TABLE_CHECKED:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PayrollPeriodSettings')
    BEGIN
        CREATE TABLE PayrollPeriodSettings (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            PayrollYear INT NOT NULL,
            PayrollMonth INT NOT NULL,
            PayrollMonthStr NVARCHAR(20) NOT NULL,
            CalendarDays INT NULL,
            SundayCount INT NULL,
            DefaultWorkingDays DECIMAL(5,2) NULL,
            StandardWorkingDays DECIMAL(5,2) NOT NULL DEFAULT 26.0,
            WorkerWorkingDays DECIMAL(5,2) NULL DEFAULT 26.0,
            StaffWorkingDays DECIMAL(5,2) NULL,
            IsActive BIT DEFAULT 1,
            CreatedBy NVARCHAR(100) DEFAULT 'Admin',
            CreatedAt DATETIME DEFAULT GETDATE(),
            UpdatedBy NVARCHAR(100) DEFAULT 'Admin',
            UpdatedAt DATETIME DEFAULT GETDATE(),
            CONSTRAINT UQ_PayrollPeriodSettings UNIQUE (PayrollYear, PayrollMonth)
        );
    END;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayrollPeriodSettings') AND name = 'CalendarDays')
    BEGIN
        ALTER TABLE PayrollPeriodSettings ADD CalendarDays INT NULL;
        ALTER TABLE PayrollPeriodSettings ADD SundayCount INT NULL;
        ALTER TABLE PayrollPeriodSettings ADD DefaultWorkingDays DECIMAL(5,2) NULL;
    END;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayrollPeriodSettings') AND name = 'WorkerWorkingDays')
    BEGIN
        ALTER TABLE PayrollPeriodSettings ADD WorkerWorkingDays DECIMAL(5,2) NULL;
    END;

    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayrollPeriodSettings') AND name = 'StaffWorkingDays')
    BEGIN
        ALTER TABLE PayrollPeriodSettings ADD StaffWorkingDays DECIMAL(5,2) NULL;
    END;
    """
    cur.execute(create_table_sql)
    conn.commit()
    conn.close()
    _PERIOD_SETTINGS_TABLE_CHECKED = True

def get_period_settings_info(year, month, max_retries=3):
    """
    Fetch full period settings (CalendarDays, SundayCount, DefaultWorkingDays, StandardWorkingDays, WorkerWorkingDays, StaffWorkingDays).
    If not saved in DB, automatically computes defaults:
      - Worker Working Days: default 26.0
      - Staff Working Days: default CalendarDays - SundayCount
    """
    init_period_settings_table()
    calc = calculate_month_working_days(year, month)
    
    query = """
        SELECT CalendarDays, SundayCount, DefaultWorkingDays, StandardWorkingDays, WorkerWorkingDays, StaffWorkingDays
        FROM PayrollPeriodSettings WITH (NOLOCK)
        WHERE PayrollYear = ? AND PayrollMonth = ? AND IsActive = 1
    """
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, [year, month])
            row = cur.fetchone()
            conn.close()
            if row:
                cal_days = row[0] if row[0] is not None else calc['calendar_days']
                sun_count = row[1] if row[1] is not None else calc['sunday_count']
                def_days = float(row[2]) if row[2] is not None else calc['default_working_days']
                std_days = float(row[3]) if row[3] is not None else 26.0
                worker_days = float(row[4]) if row[4] is not None else 26.0
                staff_days = float(row[5]) if row[5] is not None else def_days

                return {
                    'calendar_days': cal_days,
                    'sunday_count': sun_count,
                    'default_working_days': def_days,
                    'worker_working_days': worker_days,
                    'staff_working_days': staff_days,
                    'standard_working_days': std_days
                }

            return {
                'calendar_days': calc['calendar_days'],
                'sunday_count': calc['sunday_count'],
                'default_working_days': calc['default_working_days'],
                'worker_working_days': 26.0,
                'staff_working_days': calc['default_working_days'],
                'standard_working_days': 26.0
            }
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            return {
                'calendar_days': calc['calendar_days'],
                'sunday_count': calc['sunday_count'],
                'default_working_days': calc['default_working_days'],
                'worker_working_days': 26.0,
                'staff_working_days': calc['default_working_days'],
                'standard_working_days': 26.0
            }

def get_period_settings(year, month, emp_type=None, max_retries=3):
    """
    Fetch period working days for a given year and month.
    If emp_type == 'STAFF', returns Staff working days.
    If emp_type == 'WORKER', returns Worker working days (default 26.0).
    """
    info = get_period_settings_info(year, month, max_retries=max_retries)
    if emp_type:
        emp_type_str = str(emp_type).upper()
        if 'STAFF' in emp_type_str:
            return info['staff_working_days']
        elif 'WORKER' in emp_type_str:
            return info['worker_working_days']
    return info['worker_working_days']

def save_period_settings(year, month, worker_days=None, staff_days=None, standard_days=None, user='Admin', max_retries=3):
    """
    Save or update WorkerWorkingDays, StaffWorkingDays, StandardWorkingDays, CalendarDays, SundayCount, DefaultWorkingDays.
    Supports backwards compatibility with legacy positional arguments:
      - save_period_settings(year, month, standard_days) -> sets worker_days = standard_days
      - save_period_settings(year, month, worker_days, staff_days) -> sets both
    """
    init_period_settings_table()
    month_str = f"{year}-{month:02d}"
    calc = calculate_month_working_days(year, month)

    # Handle legacy call where single standard_days was passed as 3rd positional argument
    if worker_days is not None and staff_days is None and standard_days is None:
        try:
            val = float(worker_days)
            worker_days_val = val
            # Check existing staff days or default to calc['default_working_days']
            existing_info = get_period_settings_info(year, month)
            staff_days_val = existing_info.get('staff_working_days', calc['default_working_days'])
        except Exception:
            worker_days_val = 26.0
            staff_days_val = calc['default_working_days']
    else:
        worker_days_val = float(worker_days) if worker_days is not None else (float(standard_days) if standard_days is not None else 26.0)
        staff_days_val = float(staff_days) if staff_days is not None else calc['default_working_days']

    if worker_days_val <= 0:
        raise ValueError("Worker Working Days must be a positive number")
    if staff_days_val <= 0:
        raise ValueError("Staff Working Days must be a positive number")

    upsert_sql = """
    IF EXISTS (SELECT 1 FROM PayrollPeriodSettings WITH (NOLOCK) WHERE PayrollYear = ? AND PayrollMonth = ?)
    BEGIN
        UPDATE PayrollPeriodSettings
        SET CalendarDays = ?,
            SundayCount = ?,
            DefaultWorkingDays = ?,
            StandardWorkingDays = ?,
            WorkerWorkingDays = ?,
            StaffWorkingDays = ?,
            UpdatedBy = ?,
            UpdatedAt = GETDATE()
        WHERE PayrollYear = ? AND PayrollMonth = ?
    END
    ELSE
    BEGIN
        INSERT INTO PayrollPeriodSettings (
            PayrollYear, PayrollMonth, PayrollMonthStr, CalendarDays, SundayCount, DefaultWorkingDays,
            StandardWorkingDays, WorkerWorkingDays, StaffWorkingDays,
            IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, GETDATE(), ?, GETDATE())
    END
    """
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(upsert_sql, (
                year, month,
                calc['calendar_days'], calc['sunday_count'], calc['default_working_days'], worker_days_val, worker_days_val, staff_days_val, user, year, month,
                year, month, month_str, calc['calendar_days'], calc['sunday_count'], calc['default_working_days'], worker_days_val, worker_days_val, staff_days_val, user, user
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            raise e

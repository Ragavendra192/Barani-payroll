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
    """
    cur.execute(create_table_sql)
    conn.commit()
    conn.close()
    _PERIOD_SETTINGS_TABLE_CHECKED = True

def get_period_settings_info(year, month, max_retries=3):
    """
    Fetch full period settings (CalendarDays, SundayCount, DefaultWorkingDays, StandardWorkingDays).
    If not saved in DB, automatically computes defaults.
    """
    init_period_settings_table()
    calc = calculate_month_working_days(year, month)
    
    query = """
        SELECT CalendarDays, SundayCount, DefaultWorkingDays, StandardWorkingDays
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
            if row and row[3] is not None:
                return {
                    'calendar_days': row[0] if row[0] is not None else calc['calendar_days'],
                    'sunday_count': row[1] if row[1] is not None else calc['sunday_count'],
                    'default_working_days': float(row[2]) if row[2] is not None else calc['default_working_days'],
                    'standard_working_days': float(row[3])
                }
            return {
                'calendar_days': calc['calendar_days'],
                'sunday_count': calc['sunday_count'],
                'default_working_days': calc['default_working_days'],
                'standard_working_days': calc['default_working_days']
            }
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            return {
                'calendar_days': calc['calendar_days'],
                'sunday_count': calc['sunday_count'],
                'default_working_days': calc['default_working_days'],
                'standard_working_days': calc['default_working_days']
            }

def get_period_settings(year, month, max_retries=3):
    """
    Fetch period settings (StandardWorkingDays) for a given year and month.
    Returns: StandardWorkingDays float or None if not configured.
    """
    info = get_period_settings_info(year, month, max_retries=max_retries)
    return info['standard_working_days']

def save_period_settings(year, month, standard_days, user='Admin', max_retries=3):
    """
    Save or update StandardWorkingDays, CalendarDays, SundayCount, DefaultWorkingDays for a given year and month.
    """
    init_period_settings_table()
    month_str = f"{year}-{month:02d}"
    std_days_val = float(standard_days)
    calc = calculate_month_working_days(year, month)

    if std_days_val <= 0:
        raise ValueError("Standard Working Days must be a positive number")

    upsert_sql = """
    IF EXISTS (SELECT 1 FROM PayrollPeriodSettings WITH (NOLOCK) WHERE PayrollYear = ? AND PayrollMonth = ?)
    BEGIN
        UPDATE PayrollPeriodSettings
        SET CalendarDays = ?,
            SundayCount = ?,
            DefaultWorkingDays = ?,
            StandardWorkingDays = ?,
            UpdatedBy = ?,
            UpdatedAt = GETDATE()
        WHERE PayrollYear = ? AND PayrollMonth = ?
    END
    ELSE
    BEGIN
        INSERT INTO PayrollPeriodSettings (
            PayrollYear, PayrollMonth, PayrollMonthStr, CalendarDays, SundayCount, DefaultWorkingDays, StandardWorkingDays,
            IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, GETDATE(), ?, GETDATE())
    END
    """
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(upsert_sql, (
                year, month,
                calc['calendar_days'], calc['sunday_count'], calc['default_working_days'], std_days_val, user, year, month,
                year, month, month_str, calc['calendar_days'], calc['sunday_count'], calc['default_working_days'], std_days_val, user, user
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if '1205' in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            raise e

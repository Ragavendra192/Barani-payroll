import pandas as pd
from db import get_db_connection
from utils.contact_utils import mask_phone_number

_LOG_TABLE_CHECKED = False

def init_payslip_send_log_table():
    """Create PayslipSendLog table if it does not exist and ensure columns exist."""
    global _LOG_TABLE_CHECKED
    if _LOG_TABLE_CHECKED:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PayslipSendLog')
            BEGIN
                CREATE TABLE PayslipSendLog (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    employee_id INT NOT NULL,
                    payroll_year INT NULL,
                    payroll_month VARCHAR(50) NOT NULL,
                    channel VARCHAR(50) NOT NULL DEFAULT 'WhatsApp',
                    phone_number_masked VARCHAR(20) NULL,
                    email_id VARCHAR(255) NULL,
                    payslip_file_name VARCHAR(255) NOT NULL,
                    whatsapp_status VARCHAR(50) NOT NULL DEFAULT 'NOT_SENT',
                    email_status VARCHAR(50) NOT NULL DEFAULT 'NOT_SENT',
                    message_id VARCHAR(255) NULL,
                    attempt_count INT NOT NULL DEFAULT 1,
                    sent_at DATETIME NOT NULL DEFAULT GETDATE(),
                    sent_by VARCHAR(100) NOT NULL DEFAULT 'Admin',
                    error_message VARCHAR(500) NULL
                );
            END
            ELSE
            BEGIN
                IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayslipSendLog') AND name = 'payroll_year')
                    ALTER TABLE PayslipSendLog ADD payroll_year INT NULL;

                IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayslipSendLog') AND name = 'channel')
                    ALTER TABLE PayslipSendLog ADD channel VARCHAR(50) NOT NULL DEFAULT 'WhatsApp';

                IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayslipSendLog') AND name = 'message_id')
                    ALTER TABLE PayslipSendLog ADD message_id VARCHAR(255) NULL;

                IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('PayslipSendLog') AND name = 'attempt_count')
                    ALTER TABLE PayslipSendLog ADD attempt_count INT NOT NULL DEFAULT 1;
            END
        """)
        conn.commit()
        _LOG_TABLE_CHECKED = True
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

# Auto-initialize table schema on import
init_payslip_send_log_table()

def log_payslip_send(employee_id, payroll_month, phone_number, email_id, payslip_file_name, whatsapp_status='NOT_SENT', email_status='NOT_SENT', sent_by='Admin', error_message=None, payroll_year=None, channel='WhatsApp', message_id=None, attempt_count=1):
    """Inserts a new record into PayslipSendLog table."""
    masked_phone = mask_phone_number(phone_number) if phone_number else '-'
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO PayslipSendLog (
                employee_id, payroll_year, payroll_month, channel, phone_number_masked, email_id,
                payslip_file_name, whatsapp_status, email_status, message_id, attempt_count, sent_at, sent_by, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?)
        """, (
            employee_id, payroll_year, payroll_month, channel, masked_phone, email_id,
            payslip_file_name, whatsapp_status, email_status, message_id, attempt_count, sent_by, error_message
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()

def is_payslip_already_sent(employee_id, payroll_year, payroll_month):
    """Checks if payslip has already been successfully sent via WhatsApp for a given month/year."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM PayslipSendLog WITH (NOLOCK)
            WHERE employee_id = ? AND (payroll_year = ? OR payroll_month LIKE ?) AND whatsapp_status = 'SENT'
        """, (employee_id, payroll_year, f"%{payroll_month}%"))
        count = cur.fetchone()[0]
        return count > 0
    except Exception:
        return False
    finally:
        conn.close()

def get_payslip_send_logs(employee_id=None, payroll_month=None, payroll_year=None, limit=500):
    """Fetch communication log records."""
    conn = get_db_connection()
    query = "SELECT TOP (?) * FROM PayslipSendLog WHERE 1=1"
    params = [limit]
    if employee_id:
        query += " AND employee_id = ?"
        params.append(employee_id)
    if payroll_year:
        query += " AND payroll_year = ?"
        params.append(payroll_year)
    if payroll_month:
        query += " AND payroll_month LIKE ?"
        params.append(f"%{payroll_month}%")
    query += " ORDER BY id DESC"

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df.to_dict(orient='records')

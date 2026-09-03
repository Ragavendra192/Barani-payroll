import pandas as pd
from db import get_db_connection


def _column_exists(conn, table_name, column_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
    """, (table_name, column_name))
    return cur.fetchone() is not None


def _ensure_loan_advance_tables(conn):
    """Create Loans and Advances tables if they do not exist."""
    cur = conn.cursor()
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Loans') AND type in (N'U'))
    CREATE TABLE Loans (
        Id INT IDENTITY PRIMARY KEY,
        Emp_No INT NOT NULL,
        Start_Year INT NOT NULL,
        Start_Month INT NOT NULL,
        Total_Amount DECIMAL(12,2) NOT NULL,
        Installments INT NOT NULL,
        Monthly_Amount DECIMAL(12,2) NOT NULL,
        Remaining_Amount DECIMAL(12,2) NOT NULL,
        Status NVARCHAR(50) DEFAULT 'Active',
        Note NVARCHAR(400),
        Created_At DATETIME DEFAULT GETDATE()
    )
    """)

    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Advances') AND type in (N'U'))
    CREATE TABLE Advances (
        Id INT IDENTITY PRIMARY KEY,
        Emp_No INT NOT NULL,
        Start_Year INT NOT NULL,
        Start_Month INT NOT NULL,
        Total_Amount DECIMAL(12,2) NOT NULL,
        Installments INT NOT NULL,
        Monthly_Amount DECIMAL(12,2) NOT NULL,
        Remaining_Amount DECIMAL(12,2) NOT NULL,
        Status NVARCHAR(50) DEFAULT 'Active',
        Note NVARCHAR(400),
        Created_At DATETIME DEFAULT GETDATE()
    )
    """)
    conn.commit()


def _recalculate_and_update_payroll(emp_no, year, month):
    """
    Update PayrollHistory for the employee by recalculating 
    manual deductions total and Net Pay.
    """
    import logging
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the total of all active manual deductions for this employee/month
        if _column_exists(conn, 'ManualDeductions', 'Status'):
            cursor.execute("""
                SELECT ISNULL(SUM(Amount), 0)
                FROM ManualDeductions
                WHERE Emp_No = ? AND Year = ? AND Month = ? AND (Status IS NULL OR Status = 'Active')
            """, (emp_no, year, month))
        else:
            cursor.execute("""
                SELECT ISNULL(SUM(Amount), 0)
                FROM ManualDeductions
                WHERE Emp_No = ? AND Year = ? AND Month = ?
            """, (emp_no, year, month))
        
        manual_deductions_total = cursor.fetchone()[0] or 0.0
        print(f"[PAYROLL UPDATE] Emp {emp_no}, Year {year}, Month {month}: Manual deductions total = {manual_deductions_total}")
        
        # Fetch the current payroll record
        cursor.execute("""
            SELECT Gross_Wages, PF_Ded, ESI_Ded
            FROM PayrollHistory
            WHERE Emp_No = ? AND Year = ? AND Month = ?
        """, (emp_no, year, month))
        
        payroll_row = cursor.fetchone()
        
        if not payroll_row:
            print(f"[PAYROLL UPDATE] No payroll record found for Emp {emp_no}, {year}-{month}")
            conn.close()
            return  # No payroll record to update
        
        gross_wages, pf_ded, esi_ded = payroll_row
        print(f"[PAYROLL UPDATE] Fetched: Gross={gross_wages}, PF={pf_ded}, ESI={esi_ded}")
        
        # Recalculate totals
        total_deductions = float(pf_ded or 0) + float(esi_ded or 0) + float(manual_deductions_total)
        net_pay = float(gross_wages or 0) - total_deductions
        
        print(f"[PAYROLL UPDATE] Calculated: Total_Deductions={total_deductions}, Net_Pay={net_pay}")
        
        # Update PayrollHistory with new manual deductions and recalculated totals
        # Some deployments may not have Manual_Deductions column on PayrollHistory
        # — detect and issue an appropriate UPDATE accordingly.
        payroll_has_manual = _column_exists(conn, 'PayrollHistory', 'Manual_Deductions')

        if payroll_has_manual:
            cursor.execute("""
                UPDATE PayrollHistory
                SET Manual_Deductions = ?, Total_Deductions = ?, Net_Pay = ?
                WHERE Emp_No = ? AND Year = ? AND Month = ?
            """, (manual_deductions_total, total_deductions, net_pay, emp_no, year, month))
        else:
            cursor.execute("""
                UPDATE PayrollHistory
                SET Total_Deductions = ?, Net_Pay = ?
                WHERE Emp_No = ? AND Year = ? AND Month = ?
            """, (total_deductions, net_pay, emp_no, year, month))

        rows_affected = cursor.rowcount
        print(f"[PAYROLL UPDATE] UPDATE executed: {rows_affected} rows affected (manual column present: {payroll_has_manual})")
        
        conn.commit()
        print(f"[PAYROLL UPDATE] COMMITTED to database")
        conn.close()
    except Exception as e:
        print(f"[PAYROLL UPDATE ERROR] Exception in _recalculate_and_update_payroll: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def get_manual_deductions_for_employee(emp_no, year, month):
    """Return all manual deduction rows for a single employee."""
    conn = get_db_connection()
    cols = ["Id", "Emp_No", "Year", "Month", "Deduction_Type", "Amount", "Reason"]
    if _column_exists(conn, 'ManualDeductions', 'Status'):
        cols.append('Status')

    query = f"SELECT {', '.join(cols)} FROM ManualDeductions WHERE Emp_No = ? AND Year = ? AND Month = ?"
    df = pd.read_sql(query, conn, params=[emp_no, year, month])
    conn.close()
    return df


def get_manual_deductions(year, month):
    """Return aggregated manual deductions per Emp_No for given month as DataFrame.

    This is used by payroll calculation to subtract manual deductions from net pay.
    Returns DataFrame with columns: Emp_No, Manual_Deductions
    """
    conn = get_db_connection()

    # If Status column exists, only include Active/null statuses (excludes 'Credit' audit rows). Otherwise sum all.
    if _column_exists(conn, 'ManualDeductions', 'Status'):
        query = """
            SELECT Emp_No, ISNULL(SUM(Amount),0) AS Manual_Deductions
            FROM ManualDeductions
            WHERE Year = ? AND Month = ? AND (Status IS NULL OR Status = 'Active' OR Status = 'Credit')
            GROUP BY Emp_No
        """
    else:
        query = """
            SELECT Emp_No, ISNULL(SUM(Amount),0) AS Manual_Deductions
            FROM ManualDeductions
            WHERE Year = ? AND Month = ?
            GROUP BY Emp_No
        """

    df = pd.read_sql(query, conn, params=[year, month])
    conn.close()
    return df


def add_manual_deduction(emp_no, year, month, dtype, amount, reason, status='Active',
                         transaction_type=None, target=None, installments=None, total_amount=None):
    """Add a manual deduction or credit.

    - For simple debit (default), insert a ManualDeductions row for the given year/month.
    - For a credit (`transaction_type=='Credit'`), add the amount to the specified payroll column
      (if exists) or to `Gross_Wages`, then recalculate payroll.
    - For debits with `installments` and `total_amount`, create monthly deduction rows
      for the next `installments` months splitting `total_amount` equally.
    """
    print(f"[ADD DEDUCTION] Starting: Emp {emp_no}, Year {year}, Month {month}, Amount {amount}, txn={transaction_type}, installments={installments}")

    # Handle credits: apply directly to payroll component
    if transaction_type and transaction_type.lower() == 'credit':
        print(f"[ADD DEDUCTION] Processing as CREDIT")
        conn = get_db_connection()
        cursor = conn.cursor()
        # Decide target column
        target_col = target or 'Gross_Wages'
        # sanitize simple column name (no injection expected since from UI)
        # if column exists in PayrollHistory, update it; otherwise update Gross_Wages
        if not _column_exists(conn, 'PayrollHistory', target_col):
            target_col = 'Gross_Wages'

        # Build dynamic SQL safely (column name can't be parameterized)
        sql = f"UPDATE PayrollHistory SET {target_col} = ISNULL({target_col},0) + ? WHERE Emp_No = ? AND Year = ? AND Month = ?"
        cursor.execute(sql, (amount, emp_no, year, month))
        conn.commit()
        conn.close()

        # Insert a small audit record into ManualDeductions so the credit appears in the UI
        try:
            log_conn = get_db_connection()
            log_cur = log_conn.cursor()
            has_status = _column_exists(log_conn, 'ManualDeductions', 'Status')
            has_created = _column_exists(log_conn, 'ManualDeductions', 'Created_At')
            dtype_note = f"Credit - {dtype or 'Allowance'}"
            note_text = reason or f"Credit applied to {target_col}"

            if has_status and has_created:
                log_cur.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status, Created_At)
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (emp_no, year, month, dtype_note, 0.00, note_text, 'Active'))
            elif has_status and not has_created:
                log_cur.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (emp_no, year, month, dtype_note, 0.00, note_text, 'Active'))
            else:
                log_cur.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (emp_no, year, month, dtype_note, 0.00, note_text))

            log_conn.commit()
            log_conn.close()
            print(f"[ADD DEDUCTION] Inserted audit credit row into ManualDeductions for Emp {emp_no}")
        except Exception as e:
            print(f"[ADD DEDUCTION] Warning: could not insert audit credit row: {e}")

        # Recalculate totals after applying credit
        print(f"[ADD DEDUCTION] Applied credit to {target_col}, calling payroll recalculation")
        _recalculate_and_update_payroll(emp_no, year, month)
        return

    # Handle debit with installments (create rows across months)
    # Normalize installments and total_amount if provided
    if installments:
        try:
            installments = int(installments)
            if installments < 1:
                installments = None
        except Exception:
            installments = None
    
    if total_amount:
        try:
            total_amount = float(total_amount)
        except Exception:
            total_amount = None

    # If installments > 1, create multiple rows across months
    if installments and installments > 1 and total_amount:
        print(f"[ADD DEDUCTION] Processing as INSTALLMENTS (count={installments}, total={total_amount})")
        monthly_amount = round(total_amount / installments, 2)

        # Ensure tables exist ONCE before the loop
        try:
            _ensure_loan_advance_tables(get_db_connection())
        except Exception as e:
            print(f"[ADD DEDUCTION] Warning: Could not ensure tables: {e}")

        conn = get_db_connection()
        cursor = conn.cursor()
        has_status = _column_exists(conn, 'ManualDeductions', 'Status')
        has_created = _column_exists(conn, 'ManualDeductions', 'Created_At')

        # Insert master record into Loans or Advances table for tracking
        table_name = None
        if dtype and dtype.lower().startswith('loan'):
            table_name = 'Loans'
        elif dtype and dtype.lower().startswith('advance'):
            table_name = 'Advances'

        master_id = None
        if table_name:
            try:
                cursor.execute(f"INSERT INTO {table_name} (Emp_No, Start_Year, Start_Month, Total_Amount, Installments, Monthly_Amount, Remaining_Amount, Note) OUTPUT INSERTED.Id VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (emp_no, year, month, total_amount, installments, monthly_amount, total_amount, reason))
                result = cursor.fetchone()
                master_id = result[0] if result else None
                print(f"[ADD DEDUCTION] Created master record: {table_name} Id={master_id}")
            except Exception as e:
                # if table missing or insert fails, continue with per-installment insert
                print(f"[ADD DEDUCTION] Warning: Could not insert master record: {e}")
                master_id = None

        # Insert one row per installment, starting at provided year/month and advancing months
        y = int(year)
        m = int(month)
        for i in range(installments):
            ins_year = y + ((m - 1 + i) // 12)
            ins_month = ((m - 1 + i) % 12) + 1
            note = f"Schedule:{total_amount};part:{i+1}/{installments}" + (f";{reason}" if reason else "")
            if master_id:
                note = f"{note};master_id:{master_id}"

            if has_status and has_created:
                cursor.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status, Created_At)
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (emp_no, ins_year, ins_month, dtype, monthly_amount, note, status))
            elif has_status and not has_created:
                cursor.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (emp_no, ins_year, ins_month, dtype, monthly_amount, note, status))
            else:
                cursor.execute("""
                    INSERT INTO ManualDeductions
                    (Emp_No, Year, Month, Deduction_Type, Amount, Reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (emp_no, ins_year, ins_month, dtype, monthly_amount, note))
            
            print(f"[ADD DEDUCTION] Inserted installment {i+1}/{installments} for {ins_year}/{ins_month}")

        conn.commit()
        conn.close()
        print(f"[ADD DEDUCTION] Committed {installments} installment rows")

        # NOW recalculate payroll for each installment month (after closing insert connection)
        print(f"[ADD DEDUCTION] Recalculating payroll for all installment months...")
        for i in range(installments):
            ins_year = y + ((m - 1 + i) // 12)
            ins_month = ((m - 1 + i) % 12) + 1
            try:
                _recalculate_and_update_payroll(emp_no, ins_year, ins_month)
            except Exception as e:
                print(f"[ADD DEDUCTION] Warning: Payroll recalc failed for {emp_no}/{ins_year}/{ins_month}: {e}")

        print(f"[ADD DEDUCTION] Completed installment creation; master_id={master_id}")
        return

    # Default single-row insert (debit or credit without installments)
    print(f"[ADD DEDUCTION] Processing as SINGLE ROW insert")
    conn = get_db_connection()
    cursor = conn.cursor()
    has_status = _column_exists(conn, 'ManualDeductions', 'Status')
    has_created = _column_exists(conn, 'ManualDeductions', 'Created_At')
    # If this is a Loan or Advance and a total_amount was provided, create a master tracking row
    master_id = None
    table_name = None
    if dtype and dtype.lower().startswith('loan'):
        table_name = 'Loans'
    elif dtype and dtype.lower().startswith('advance'):
        table_name = 'Advances'

    if table_name and total_amount:
        try:
            # ensure tables exist
            _ensure_loan_advance_tables(conn)
            monthly_amount = float(amount)
            total_amt = float(total_amount)
            cursor.execute(f"INSERT INTO {table_name} (Emp_No, Start_Year, Start_Month, Total_Amount, Installments, Monthly_Amount, Remaining_Amount, Note) OUTPUT INSERTED.Id VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (emp_no, year, month, total_amt, 1, monthly_amount, max(total_amt - monthly_amount, 0.0), reason))
            res = cursor.fetchone()
            master_id = res[0] if res else None
            print(f"[ADD DEDUCTION] Created master record for single payment: {table_name} Id={master_id}")
        except Exception as e:
            print(f"[ADD DEDUCTION] Warning: Could not create master record for single loan/advance: {e}")

    if has_status and has_created:
        cursor.execute("""
            INSERT INTO ManualDeductions
            (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status, Created_At)
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (emp_no, year, month, dtype, amount, reason, status))
    elif has_status and not has_created:
        cursor.execute("""
            INSERT INTO ManualDeductions
            (Emp_No, Year, Month, Deduction_Type, Amount, Reason, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emp_no, year, month, dtype, amount, reason, status))
    else:
        # no Status column
        cursor.execute("""
            INSERT INTO ManualDeductions
            (Emp_No, Year, Month, Deduction_Type, Amount, Reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (emp_no, year, month, dtype, amount, reason))

    conn.commit()
    print(f"[ADD DEDUCTION] Inserted single row into ManualDeductions table")
    conn.close()
    
    # Auto-update PayrollHistory with new manual deductions
    print(f"[ADD DEDUCTION] Now calling _recalculate_and_update_payroll...")
    _recalculate_and_update_payroll(emp_no, year, month)
    print(f"[ADD DEDUCTION] Completed successfully")


def update_manual_deduction(deduction_id, dtype, amount, reason, status):
    print(f"[UPDATE DEDUCTION] Starting: Deduction ID {deduction_id}, Amount {amount}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get emp_no, year, month before updating
    cursor.execute("""
        SELECT Emp_No, Year, Month FROM ManualDeductions WHERE Id = ?
    """, (deduction_id,))
    result = cursor.fetchone()
    emp_no, year, month = result if result else (None, None, None)
    print(f"[UPDATE DEDUCTION] Found: Emp {emp_no}, Year {year}, Month {month}")
    
    if _column_exists(conn, 'ManualDeductions', 'Status'):
        cursor.execute("""
            UPDATE ManualDeductions
            SET Deduction_Type = ?, Amount = ?, Reason = ?, Status = ?
            WHERE Id = ?
        """, (dtype, amount, reason, status, deduction_id))
    else:
        cursor.execute("""
            UPDATE ManualDeductions
            SET Deduction_Type = ?, Amount = ?, Reason = ?
            WHERE Id = ?
        """, (dtype, amount, reason, deduction_id))

    conn.commit()
    print(f"[UPDATE DEDUCTION] Updated ManualDeductions table")
    conn.close()
    
    # Auto-update PayrollHistory with updated manual deductions
    if emp_no and year and month:
        print(f"[UPDATE DEDUCTION] Calling _recalculate_and_update_payroll...")
        _recalculate_and_update_payroll(emp_no, year, month)
        print(f"[UPDATE DEDUCTION] Completed")
    else:
        print(f"[UPDATE DEDUCTION] WARNING: Could not find emp_no/year/month for recalculation")


def delete_manual_deduction(deduction_id):
    print(f"[DELETE DEDUCTION] Starting: Deduction ID {deduction_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get emp_no, year, month before deleting
    cursor.execute("""
        SELECT Emp_No, Year, Month FROM ManualDeductions WHERE Id = ?
    """, (deduction_id,))
    result = cursor.fetchone()
    emp_no, year, month = result if result else (None, None, None)
    print(f"[DELETE DEDUCTION] Found: Emp {emp_no}, Year {year}, Month {month}")
    
    cursor.execute("DELETE FROM ManualDeductions WHERE Id = ?", (deduction_id,))
    conn.commit()
    print(f"[DELETE DEDUCTION] Deleted from ManualDeductions table")
    conn.close()
    
    # Auto-update PayrollHistory to recalculate without this deduction
    if emp_no and year and month:
        print(f"[DELETE DEDUCTION] Calling _recalculate_and_update_payroll...")
        _recalculate_and_update_payroll(emp_no, year, month)
        print(f"[DELETE DEDUCTION] Completed")
    else:
        print(f"[DELETE DEDUCTION] WARNING: Could not find emp_no/year/month for recalculation")


def get_total_manual_deduction(emp_no, year, month):
    conn = get_db_connection()
    cursor = conn.cursor()
    if _column_exists(conn, 'ManualDeductions', 'Status'):
        cursor.execute("""
            SELECT ISNULL(SUM(Amount),0)
            FROM ManualDeductions
            WHERE Emp_No = ? AND Year = ? AND Month = ? AND (Status IS NULL OR Status = 'Active')
        """, (emp_no, year, month))
    else:
        cursor.execute("""
            SELECT ISNULL(SUM(Amount),0)
            FROM ManualDeductions
            WHERE Emp_No = ? AND Year = ? AND Month = ?
        """, (emp_no, year, month))
    total = cursor.fetchone()[0]
    conn.close()
    return float(total)

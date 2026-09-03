#!/usr/bin/env python
import sys
sys.path.insert(0, 'e:\\payroll_app')

from db import get_db_connection
from models_manual import _recalculate_and_update_payroll

conn = get_db_connection()
cursor = conn.cursor()

# Get all unique employees with manual deductions in Dec 2025
cursor.execute("""
    SELECT DISTINCT Emp_No, Year, Month
    FROM ManualDeductions
    WHERE Year = 2025 AND Month = 12
""")

records = cursor.fetchall()
conn.close()

print(f"\nRecalculating PayrollHistory for {len(records)} employee(s)...\n")

for emp_no, year, month in records:
    print(f"Processing Emp {emp_no}, {year}-{month}...")
    _recalculate_and_update_payroll(emp_no, year, month)

print("\n✓ All PayrollHistory records updated!")

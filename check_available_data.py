#!/usr/bin/env python
import sys
sys.path.insert(0, 'e:\\payroll_app')

from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("\nPayroll data available for:")
cursor.execute("""
    SELECT DISTINCT Year, Month
    FROM PayrollHistory
    ORDER BY Year DESC, Month DESC
""")

for row in cursor.fetchall():
    print(f"  {row[0]}-{row[1]:02d}")

print("\nManual deductions available for:")
cursor.execute("""
    SELECT DISTINCT Year, Month
    FROM ManualDeductions
    ORDER BY Year DESC, Month DESC
""")

for row in cursor.fetchall():
    print(f"  {row[0]}-{row[1]:02d}")

conn.close()

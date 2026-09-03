#!/usr/bin/env python
import sys
sys.path.insert(0, 'e:\\payroll_app')

from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("\n" + "="*100)
print("PAYROLL HISTORY TABLE STRUCTURE")
print("="*100)
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'PayrollHistory'
    ORDER BY ORDINAL_POSITION
""")

print(f"{'Column Name':<30} {'Data Type':<20}")
print("-" * 100)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]:<20}")

conn.close()

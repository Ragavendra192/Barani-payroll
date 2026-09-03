#!/usr/bin/env python
import sys
sys.path.insert(0, 'e:\\payroll_app')

from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("Adding Manual_Deductions column to PayrollHistory...")

# First check if column already exists
cursor.execute("""
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'PayrollHistory' AND COLUMN_NAME = 'Manual_Deductions'
""")

if cursor.fetchone():
    print("Column already exists!")
else:
    # Add the column with default value 0
    cursor.execute("""
        ALTER TABLE PayrollHistory
        ADD Manual_Deductions DECIMAL(10,2) DEFAULT 0
    """)
    conn.commit()
    print("✓ Column added successfully!")

conn.close()

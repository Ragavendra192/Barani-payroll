#!/usr/bin/env python
import pyodbc

# Connect to database
conn_str = (
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=LAPTOP-5NKR2M6K;'
    'Database=payroll;'
    'Trusted_Connection=yes;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("\n" + "="*100)
print("MANUAL DEDUCTIONS TABLE (Dec 2025)")
print("="*100)
cursor.execute('''
    SELECT Emp_No, Deduction_Type, Amount, Year, Month
    FROM ManualDeductions
    WHERE Year = 2025 AND Month = 12
    ORDER BY Emp_No
''')
print(f"{'Emp_No':<8} {'Deduction_Type':<20} {'Amount':<12} {'Year':<6} {'Month':<6}")
print("-" * 100)
for row in cursor.fetchall():
    print(f"{row[0]:<8} {str(row[1]):<20} {row[2]:<12.2f} {row[3]:<6} {row[4]:<6}")

print("\n" + "="*100)
print("PAYROLL HISTORY TABLE (Dec 2025)")
print("="*100)
cursor.execute('''
    SELECT Emp_No, Gross_Wages, Manual_Deductions, Total_Deductions, Net_Pay, Year, Month
    FROM PayrollHistory
    WHERE Year = 2025 AND Month = 12
    ORDER BY Emp_No
''')
print(f"{'Emp_No':<8} {'Gross':<12} {'Manual_Ded':<12} {'Total_Ded':<12} {'Net_Pay':<12} {'Year':<6} {'Month':<6}")
print("-" * 100)
for row in cursor.fetchall():
    print(f"{row[0]:<8} {row[1]:<12.2f} {row[2]:<12.2f} {row[3]:<12.2f} {row[4]:<12.2f} {row[5]:<6} {row[6]:<6}")

conn.close()
print("\nDone.")

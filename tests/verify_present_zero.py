import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import io
import pandas as pd
from app import app
from models.payroll_transaction import get_payroll_transactions, get_payroll_attendance
from services.wages_excel_exporter import generate_wages_excel

client = app.test_client()

# 1. Test POST save_attendance with 0 present days for employee 182
post_data = {
    'year': '2026',
    'month': '7',
    'action': 'save_attendance',
    'emp_182_present_days': '0',
    'emp_182_nh': '0',
    'emp_182_coff': '0',
    'emp_182_el': '0',
    'emp_182_cl': '0',
    'emp_182_sl': '0',
    'emp_182_act_ot': '0'
}
resp = client.post('/attendance', data=post_data, follow_redirects=True)
assert resp.status_code == 200, f'Status was {resp.status_code}'
print('[PASS] POST /attendance returned 200')

# 2. Verify attendance and transaction in DB
trans = get_payroll_transactions(2026, 7)
t182 = [t for t in trans if t['Employee_ID'] == 182][0]
print(f"Employee 182 DB Trans: Present={t182['Present_Days']}, Total={t182['Total_Days']}, Working={t182['Working_Days']}, Net={t182['Net_Salary']}")
assert float(t182['Present_Days']) == 0.0, f"Expected 0.0, got {t182['Present_Days']}"
assert float(t182['Total_Days']) == 0.0, f"Expected 0.0, got {t182['Total_Days']}"
print('[PASS] DB Trans Present and Total are strictly 0.0')

# 3. Verify Wages Excel Exporter outputs 0.0 for Present and Payable Days
excel_io, name = generate_wages_excel(2026, 7)
xl = pd.ExcelFile(excel_io)
found = False
for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet, skiprows=3)
    row = df[df['Emp ID'] == 1.0] # 182 has Emp_No 1
    if not row.empty:
        found = True
        p_val = float(row['Present'].iloc[0])
        w_val = float(row['Working Days'].iloc[0])
        pay_val = float(row['Payable Days'].iloc[0])
        print(f"Sheet {sheet}: Emp 1: Working Days={w_val}, Present={p_val}, Payable Days={pay_val}")
        assert p_val == 0.0, f"Excel Present was {p_val}, expected 0.0!"
        assert pay_val == 0.0, f"Excel Payable Days was {pay_val}, expected 0.0!"
        print('[PASS] Wages Excel Exporter outputs 0.0 for Present and Payable Days!')
        break
assert found, 'Employee 1 not found in excel sheets'
print('ALL VERIFICATION CHECKS PASSED!')

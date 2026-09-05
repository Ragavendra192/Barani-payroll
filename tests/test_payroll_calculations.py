import unittest
from decimal import Decimal
from utils.payroll_calculation_engine import (
    calculate_payroll,
    money,
    calculate_attendance,
    calculate_ot,
    calculate_pf,
    calculate_esi
)

class TestPayrollCalculationsEngine(unittest.TestCase):

    def setUp(self):
        self.staff_pf_esi_emp = {
            'Employee_ID': '1001',
            'Emp_No': '1001',
            'Name': 'KRISHNAN.A.P',
            'Category': 'STAFF_PF_ESI',
            'Employee_Type': 'STAFF',
            'Payroll_Category': 'PF_ESI'
        }

        self.worker_pf_esi_emp = {
            'Employee_ID': '10002',
            'Emp_No': '10002',
            'Name': 'D.ZAHEER HUSSAIN',
            'Category': 'WORKER_PF_ESI',
            'Employee_Type': 'WORKER',
            'Payroll_Category': 'PF_ESI'
        }

        self.worker_naps_emp = {
            'Employee_ID': '10154',
            'Emp_No': '10154',
            'Name': 'E.ESSAKIRAJA',
            'Category': 'WORKER_NAPS',
            'Employee_Type': 'WORKER',
            'Payroll_Category': 'NAPS'
        }

        self.worker_non_pf_emp = {
            'Employee_ID': '10041',
            'Emp_No': '10041',
            'Name': 'D.JESU BALAN',
            'Category': 'WORKER_NON_PF_ESI',
            'Employee_Type': 'WORKER',
            'Payroll_Category': 'NON_PF_ESI'
        }

    # Test Case 1: Full Attendance (Staff PF/ESI)
    def test_01_full_attendance(self):
        sal = {'Gross_Wages': 63600.0}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {'lic': 344.0}
        res = calculate_payroll(self.staff_pf_esi_emp, sal, att, ded, standard_days=27.0)
        
        self.assertEqual(res['Gross_Wages'], 63600.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 2144.0)
        self.assertEqual(res['Net_Salary'], 61456.0)

    # Test Case 2: Partial Attendance (Staff PF/ESI - No LOP Deducted)
    def test_02_partial_attendance(self):
        sal = {'Gross_Wages': 27000.0}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {}
        res = calculate_payroll(self.staff_pf_esi_emp, sal, att, ded, standard_days=27.0)
        
        self.assertEqual(res['Gross_Wages'], 27000.0)
        self.assertEqual(res['LOP_Days'], 0.0)
        self.assertEqual(res['LOP_Deduction'], 0.0)
        self.assertEqual(res['PF_Gross'], 15000.0) # min(27000 * 80%, 15000)
        self.assertEqual(res['PF_Deduction'], 1800.0)

    # Test Case 3-7: Leave & Attendance Components (PH, CL, SL, PL)
    def test_03_leave_and_attendance_components(self):
        att = {
            'present_days': 20.0,
            'ph': 1.0,
            'cl': 2.0,
            'sl': 1.0,
            'pl': 2.0
        }
        res_att = calculate_attendance(att)
        self.assertEqual(res_att['total_worked_days'], 26.0)
        self.assertEqual(res_att['lop_days'], 0.0)

    # Test Case 8-9: Capped OT & Special OT (Worker)
    def test_08_overtime_capped_and_special(self):
        ot_res = calculate_ot(65.5, 906.0) # Per day wage 906 -> OT Rate 113.25
        self.assertEqual(ot_res['capped_ot_hours'], 50.0)
        self.assertEqual(ot_res['special_ot_hours'], 15.5)
        self.assertEqual(ot_res['ot_rate'], 113.25)
        self.assertEqual(ot_res['ot_wages'], 5663.00)
        self.assertEqual(ot_res['special_ot_amount'], 1755.00)

    # Test Case 10: Statutory PF Capping
    def test_10_pf_calculation_capping(self):
        pf_gross, pf_ded, acc_pf = calculate_pf(Decimal('63600.00'), Decimal('31800.00'), Decimal('12720.00'), Decimal('0.00'), is_staff=True)
        self.assertEqual(pf_gross, Decimal('15000.00'))
        self.assertEqual(pf_ded, Decimal('1800.00'))

    # Test Case 11: ESI Calculation & Eligibility Limit
    def test_11_esi_calculation_limit(self):
        esi_g, esi_d, _ = calculate_esi(Decimal('18000.00'), Decimal('18000.00'), is_staff=True)
        self.assertEqual(esi_g, Decimal('16200.00')) # 90% of 18000
        self.assertEqual(esi_d, Decimal('122.00')) # round_half(16200 * 0.0075) = round_half(121.5) = 122

        # Exceeding 21000 fixed gross limit
        esi_g2, esi_d2, _ = calculate_esi(Decimal('25000.00'), Decimal('25000.00'), is_staff=True)
        self.assertEqual(esi_d2, Decimal('0.00'))

    # Test Case 12: NAPS Category (PF & ESI zero)
    def test_12_naps_employee(self):
        sal = {'Gross_Wages': 17000.0}
        att = {'present_days': 26.0, 'total_days': 26.0}
        ded = {'naps': 1500.0}
        res = calculate_payroll({'Category': 'STAFF_NAPS'}, sal, att, ded, standard_days=26.0)
        
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['NAPS_Deduction'], 1500.0)
        self.assertEqual(res['Net_Salary'], 15500.0)

    # Test Case 13-17: Multiple Manual Deductions & Advances
    def test_13_multiple_deductions_and_advance(self):
        sal = {'Per_Day_Wage': 1110.0}
        att = {'present_days': 21.5, 'total_days': 23.5, 'actual_ot_hours': 34.5}
        ded = {'lic': 275.0, 'advance': 7000.0}
        res = calculate_payroll(self.worker_pf_esi_emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Gross_Wages'], 30874.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['LIC_Deduction'], 275.0)
        self.assertEqual(res['Advance_Deduction'], 7000.0)
        self.assertEqual(res['Total_Deduction'], 9075.0)
        self.assertEqual(res['Net_Salary'], 21799.0)

    # Test Case 18: Zero OT (Worker)
    def test_18_zero_ot(self):
        sal = {'Per_Day_Wage': 906.0}
        att = {'present_days': 27.0, 'total_days': 27.0, 'actual_ot_hours': 0.0}
        ded = {}
        res = calculate_payroll(self.worker_non_pf_emp, sal, att, ded, standard_days=27.0)

        self.assertEqual(res['OT_Wages'], 0.0)
        self.assertEqual(res['Special_OT_Amount'], 0.0)
        self.assertEqual(res['Gross_Wages'], 24461.0)

    # Test Case 19: Non-PF/ESI Employee
    def test_19_non_pf_esi_employee(self):
        sal = {'Gross_Wages': 55000.0}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {}
        res = calculate_payroll({'Category': 'STAFF_NON_PF_ESI'}, sal, att, ded, standard_days=27.0)

        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Net_Salary'], 55000.0)

    # Test Case 20: Decimal Money Helper Precision
    def test_20_money_precision_helper(self):
        self.assertEqual(money(10.005), Decimal('10.01'))
        self.assertEqual(money('10.004'), Decimal('10.00'))
        self.assertEqual(money(None), Decimal('0.00'))

    # Test Case 21: Automatic LIC Deduction from Employee Master
    def test_21_lic_master_auto_deduction(self):
        emp_with_lic = {
            'Employee_ID': '1099',
            'Emp_No': '1099',
            'Name': 'LIC TEST EMP',
            'Category': 'STAFF_PF_ESI',
            'Employee_Type': 'STAFF',
            'Payroll_Category': 'PF_ESI',
            'LIC': 500.0
        }
        sal = {'Gross_Wages': 30000.0}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {'lic': float(emp_with_lic.get('LIC', 0.0))}
        res = calculate_payroll(emp_with_lic, sal, att, ded, standard_days=27.0)

        self.assertEqual(res['LIC_Deduction'], 500.0)
        self.assertEqual(res['Total_Deduction'], 2300.0) # PF 1800 + LIC 500
        self.assertEqual(res['Net_Salary'], 27700.0)

    # Test Case 22: Worker Wages Excel Exporter SPL Amount & Spl Allowance Columns
    def test_22_worker_wages_excel_spl_amount_column(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='WORKER_PF_ESI')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        self.assertIn('Worker_PF_ESI', wb.sheetnames)
        ws = wb['Worker_PF_ESI']
        
        # Check header row (row 4, 1-indexed)
        header_vals = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
        
        self.assertIn('Spl Allowance', header_vals)
        self.assertIn('SPL Amount', header_vals)
        self.assertIn('OT Wages', header_vals)
        
        spl_allow_idx = header_vals.index('Spl Allowance')
        spl_amt_idx = header_vals.index('SPL Amount')
        ot_wages_idx = header_vals.index('OT Wages')
        
        # Verify strict order: Spl Allowance < SPL Amount < OT Wages
        self.assertEqual(spl_amt_idx, spl_allow_idx + 1)
        self.assertEqual(ot_wages_idx, spl_amt_idx + 1)

    # Test Case 23: Staff Wages Excel Advance Tracking Columns
    def test_23_staff_wages_excel_advance_tracking_columns(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='STAFF_PF_ESI')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        self.assertIn('Staff_PF_ESI', wb.sheetnames)
        ws = wb['Staff_PF_ESI']
        
        # Check header row (row 4, 1-indexed)
        header_vals = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
        
        self.assertIn('New Advance', header_vals)
        self.assertIn('Installment', header_vals)
        self.assertIn('Opening Advance', header_vals)
        self.assertIn('Closing Advance', header_vals)
        
        new_adv_idx = header_vals.index('New Advance')
        inst_idx = header_vals.index('Installment')
        open_adv_idx = header_vals.index('Opening Advance')
        close_adv_idx = header_vals.index('Closing Advance')
        
        # Verify strict order: New Advance -> Installment -> Opening Advance -> Closing Advance
        self.assertEqual(inst_idx, new_adv_idx + 1)
        self.assertEqual(open_adv_idx, inst_idx + 1)
        self.assertEqual(close_adv_idx, open_adv_idx + 1)

    # Test Case 24: Employee Details with DOJ and Year of Experience
    def test_24_employee_details_doj_experience_columns(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='ALL')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            first_10_headers = [ws.cell(row=4, column=c).value for c in range(1, 11)]
            expected_10 = [
                'S.No', 'Emp ID', 'UAN No', 'ESI No', 'Employee Name',
                'Department', 'Date of Joining', 'Year of Experience', 'Designation', 'Category'
            ]
            self.assertEqual(first_10_headers, expected_10, f"Mismatch in headers for sheet {sheetname}")

    # Test Case 22: Worker Wages Excel Exporter SPL Amount & Spl Allowance Columns
    def test_22_worker_wages_excel_spl_amount_column(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='WORKER_PF_ESI')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        self.assertIn('Worker_PF_ESI', wb.sheetnames)
        ws = wb['Worker_PF_ESI']
        
        # Check header row (row 4, 1-indexed)
        header_vals = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
        
        self.assertIn('Spl Allowance', header_vals)
        self.assertIn('SPL Amount', header_vals)
        self.assertIn('OT Wages', header_vals)
        
        spl_allow_idx = header_vals.index('Spl Allowance')
        spl_amt_idx = header_vals.index('SPL Amount')
        ot_wages_idx = header_vals.index('OT Wages')
        
        # Verify strict order: Spl Allowance < SPL Amount < OT Wages
        self.assertEqual(spl_amt_idx, spl_allow_idx + 1)
        self.assertEqual(ot_wages_idx, spl_amt_idx + 1)

    # Test Case 23: Staff Wages Excel Advance Tracking Columns
    def test_23_staff_wages_excel_advance_tracking_columns(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='STAFF_PF_ESI')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        self.assertIn('Staff_PF_ESI', wb.sheetnames)
        ws = wb['Staff_PF_ESI']
        
        # Check header row (row 4, 1-indexed)
        header_vals = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
        
        self.assertIn('New Advance', header_vals)
        self.assertIn('Installment', header_vals)
        self.assertIn('Opening Advance', header_vals)
        self.assertIn('Closing Advance', header_vals)
        
        new_adv_idx = header_vals.index('New Advance')
        inst_idx = header_vals.index('Installment')
        open_adv_idx = header_vals.index('Opening Advance')
        close_adv_idx = header_vals.index('Closing Advance')
        
        # Verify strict order: New Advance -> Installment -> Opening Advance -> Closing Advance
        self.assertEqual(inst_idx, new_adv_idx + 1)
        self.assertEqual(open_adv_idx, inst_idx + 1)
        self.assertEqual(close_adv_idx, open_adv_idx + 1)

    # Test Case 24: Employee Details with DOJ and Year of Experience
    def test_24_employee_details_doj_experience_columns(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        
        excel_io, fname = generate_wages_excel(2026, 7, category_filter='ALL')
        self.assertIsNotNone(excel_io)
        
        wb = openpyxl.load_workbook(excel_io)
        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            first_10_headers = [ws.cell(row=4, column=c).value for c in range(1, 11)]
            expected_10 = [
                'S.No', 'Emp ID', 'UAN No', 'ESI No', 'Employee Name',
                'Department', 'Date of Joining', 'Year of Experience', 'Designation', 'Category'
            ]
            self.assertEqual(first_10_headers, expected_10, f"Mismatch in headers for sheet {sheetname}")

if __name__ == '__main__':
    unittest.main()

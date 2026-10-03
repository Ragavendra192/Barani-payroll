import unittest
import openpyxl
from decimal import Decimal

from utils.payroll_calculation_engine import calculate_attendance, calculate_payroll
from services.excel_service import generate_attendance_template_excel

class TestCompOffFeature(unittest.TestCase):

    def test_staff_comp_off_in_attendance(self):
        att = {
            'present_days': 20.0,
            'nh': 1.0,
            'el': 1.0,
            'c_off': 2.0,
            'sl': 1.0,
            'cl': 1.0
        }
        res = calculate_attendance(att, is_worker=False, standard_days=27.0)
        self.assertEqual(res['present_days'], 20.0)
        self.assertEqual(res['ph'], 1.0)
        self.assertEqual(res['el'], 1.0)
        self.assertEqual(res['c_off'], 2.0)
        self.assertEqual(res['sl'], 1.0)
        self.assertEqual(res['cl'], 1.0)
        # Total Worked Days = 20 + 1 + 1 + 2 + 1 + 1 = 26.0
        self.assertEqual(res['total_worked_days'], 26.0)

    def test_worker_comp_off_ignored(self):
        att = {
            'present_days': 20.0,
            'nh': 1.0,
            'el': 1.0,
            'c_off': 2.0,  # Worker should NOT receive comp-off
            'sl': 1.0,
            'cl': 1.0
        }
        res = calculate_attendance(att, is_worker=True, standard_days=26.0)
        self.assertEqual(res['present_days'], 20.0)
        self.assertEqual(res['c_off'], 0.0)
        # Total Worked Days = 20 + 1 + 1 + 0 + 1 + 1 = 24.0
        self.assertEqual(res['total_worked_days'], 24.0)

    def test_excel_template_columns_and_formula(self):
        sample_employees = [
            {
                'Employee_ID': 1,
                'Emp_No': '1001',
                'Employee_Name': 'Staff User',
                'Employee_Type': 'STAFF',
                'Category': 'STAFF_PF_ESI'
            },
            {
                'Employee_ID': 2,
                'Emp_No': '101',
                'Employee_Name': 'Worker User',
                'Employee_Type': 'WORKER',
                'Category': 'WORKER_PF_ESI'
            }
        ]
        excel_buf = generate_attendance_template_excel(
            year=2026,
            month=7,
            employees=sample_employees,
            worker_working_days=26.0,
            staff_working_days=27.0
        )
        wb = openpyxl.load_workbook(excel_buf, data_only=False)
        ws = wb.active

        headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
        
        # Verify C-Off is directly after N/H and before EL
        nh_idx = headers.index('N/H') + 1
        coff_idx = headers.index('C-Off') + 1
        el_idx = headers.index('EL') + 1
        cl_idx = headers.index('CL') + 1
        sl_idx = headers.index('SL') + 1
        tot_idx = headers.index('Total Present Days') + 1

        self.assertEqual(coff_idx, nh_idx + 1, "C-Off must be immediately after N/H")
        self.assertEqual(el_idx, coff_idx + 1, "EL must be immediately after C-Off")
        self.assertEqual(cl_idx, el_idx + 1, "CL must be immediately after EL")
        self.assertEqual(sl_idx, cl_idx + 1, "SL must be immediately after CL")
        self.assertEqual(tot_idx, sl_idx + 1, "Total Present Days must be immediately after SL")

        # Verify formula in row 2 (Staff row)
        tot_cell_r2 = ws.cell(row=2, column=tot_idx).value
        # Formula: =Present + NH + C-Off + EL + SL + CL
        self.assertIn('+', tot_cell_r2)
        self.assertTrue(tot_cell_r2.startswith('='))
        
        # Verify Closing Advance formula exists and is valid
        close_adv_idx = headers.index('Closing Advance') + 1
        close_cell_r2 = ws.cell(row=2, column=close_adv_idx).value
        self.assertTrue(close_cell_r2.startswith('=MAX(0,'))

    def test_wages_excel_headers(self):
        import openpyxl
        from services.wages_excel_exporter import generate_wages_excel
        from unittest.mock import patch

        mock_employees = [
            {
                'Employee_ID': 1, 'Emp_No': '1001', 'Employee_Name': 'Staff Test',
                'Employee_Type': 'STAFF', 'Category': 'STAFF_PF_ESI', 'Fixed_Gross': 30000.0,
                'Basic_DA': 15000.0, 'HRA': 6000.0, 'Conveyance_Allowance': 3000.0,
                'Washing_Allowance': 3000.0, 'Other_Allowance': 3000.0, 'Department': 'Admin',
                'Designation': 'Manager', 'DOJ': None, 'LIC': 0.0, 'PF_Eligible': True, 'ESI_Eligible': True
            },
            {
                'Employee_ID': 2, 'Emp_No': '101', 'Employee_Name': 'Worker Test',
                'Employee_Type': 'WORKER', 'Category': 'WORKER_PF_ESI', 'Fixed_Gross': 15000.0,
                'Basic_DA': 7500.0, 'HRA': 3000.0, 'Conveyance_Allowance': 1500.0,
                'Washing_Allowance': 1500.0, 'Other_Allowance': 1500.0, 'Department': 'Machining',
                'Designation': 'Operator', 'DOJ': None, 'LIC': 0.0, 'PF_Eligible': True, 'ESI_Eligible': True,
                'Per_Day_Wage': 576.92
            }
        ]
        mock_trans = [
            {
                'Employee_ID': 1, 'Present_Days': 24.0, 'NH': 1.0, 'C_Off': 1.0, 'EL': 1.0, 'CL': 0.0, 'SL': 0.0,
                'Act_OT_Hrs': 0.0, 'Gross_Wages': 30000.0, 'Working_Days': 27.0
            },
            {
                'Employee_ID': 2, 'Present_Days': 24.0, 'NH': 1.0, 'C_Off': 0.0, 'EL': 0.0, 'CL': 0.0, 'SL': 0.0,
                'Act_OT_Hrs': 10.0, 'Gross_Wages': 15000.0, 'Working_Days': 26.0
            }
        ]

        with patch('services.wages_excel_exporter.get_all_employees', return_value=mock_employees), \
             patch('services.wages_excel_exporter.get_payroll_transactions', return_value=mock_trans), \
             patch('models.payroll_period_settings.get_period_settings_info', return_value={'worker_working_days': 26.0, 'staff_working_days': 27.0}):
            excel_io, filename = generate_wages_excel(2026, 7)
            wb = openpyxl.load_workbook(excel_io, data_only=False)
            
            # Check Staff_PF_ESI sheet
            ws_staff = wb['Staff_PF_ESI']
            headers_staff = [ws_staff.cell(row=4, column=c).value for c in range(1, ws_staff.max_column + 1)]
            nh_pos = headers_staff.index('N/H')
            coff_pos = headers_staff.index('C-Off')
            el_pos = headers_staff.index('EL')
            self.assertEqual(coff_pos, nh_pos + 1, "Staff C-Off must be immediately after N/H")
            self.assertEqual(el_pos, coff_pos + 1, "Staff EL must be immediately after C-Off")

            # Check Worker_PF_ESI sheet
            ws_worker = wb['Worker_PF_ESI']
            headers_worker = [ws_worker.cell(row=4, column=c).value for c in range(1, ws_worker.max_column + 1)]
            nh_pos_w = headers_worker.index('N/H')
            coff_pos_w = headers_worker.index('C-Off')
            el_pos_w = headers_worker.index('EL')
            self.assertEqual(coff_pos_w, nh_pos_w + 1, "Worker C-Off must be immediately after N/H")
            self.assertEqual(el_pos_w, coff_pos_w + 1, "Worker EL must be immediately after C-Off")

if __name__ == '__main__':
    unittest.main()

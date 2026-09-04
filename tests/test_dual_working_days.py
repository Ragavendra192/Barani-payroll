import unittest
import pandas as pd
from models.payroll_period_settings import (
    init_period_settings_table,
    get_period_settings_info,
    get_period_settings,
    save_period_settings,
    calculate_month_working_days
)
from utils.payroll_calculation_engine import calculate_payroll
from services.excel_service import generate_attendance_template_excel
from services.wages_excel_exporter import generate_wages_excel

class TestDualWorkingDays(unittest.TestCase):

    def setUp(self):
        init_period_settings_table()
        self.test_year = 2026
        self.test_month = 8  # August 2026 has 31 days, 5 Sundays -> 26 working days default

    def test_01_default_period_settings(self):
        """Test default working days calculation when not saved in DB."""
        calc = calculate_month_working_days(self.test_year, self.test_month)
        self.assertEqual(calc['calendar_days'], 31)
        self.assertEqual(calc['sunday_count'], 5)
        self.assertEqual(calc['default_working_days'], 26.0)

        # Test fetching info
        info = get_period_settings_info(self.test_year, self.test_month)
        self.assertEqual(info['calendar_days'], 31)
        self.assertEqual(info['sunday_count'], 5)
        self.assertIn('worker_working_days', info)
        self.assertIn('staff_working_days', info)

    def test_02_save_and_retrieve_custom_dual_working_days(self):
        """Test saving custom worker days (e.g. 25.5) and staff days (e.g. 27.0)."""
        save_period_settings(self.test_year, self.test_month, worker_days=25.5, staff_days=27.0)
        
        info = get_period_settings_info(self.test_year, self.test_month)
        self.assertEqual(info['worker_working_days'], 25.5)
        self.assertEqual(info['staff_working_days'], 27.0)

        # Test get_period_settings with emp_type filter
        self.assertEqual(get_period_settings(self.test_year, self.test_month, emp_type='STAFF'), 27.0)
        self.assertEqual(get_period_settings(self.test_year, self.test_month, emp_type='WORKER'), 25.5)

    def test_03_payroll_calculation_with_separate_working_days(self):
        """Verify payroll calculation produces correct earned salaries for Worker vs Staff."""
        staff_emp = {
            'Employee_ID': 998,
            'Emp_No': 'ST998',
            'Employee_Name': 'Test Staff',
            'Employee_Type': 'STAFF',
            'Category': 'STAFF_PF_ESI',
            'Payroll_Category': 'PF_ESI',
            'Fixed_Gross': 27000.0,
            'Basic_DA': 13500.0,
            'HRA': 5400.0,
            'Conveyance_Allowance': 2700.0,
            'Washing_Allowance': 2700.0,
            'Other_Allowance': 2700.0,
            'Per_Day_Wage': 0.0,
            'OT_Rate': 0.0,
            'PF_Eligible': True,
            'ESI_Eligible': True
        }
        worker_emp = {
            'Employee_ID': 999,
            'Emp_No': 'WK999',
            'Employee_Name': 'Test Worker',
            'Employee_Type': 'WORKER',
            'Category': 'WORKER_PF_ESI',
            'Payroll_Category': 'PF_ESI',
            'Fixed_Gross': 15600.0,
            'Basic_DA': 7800.0,
            'HRA': 3120.0,
            'Conveyance_Allowance': 1560.0,
            'Washing_Allowance': 1560.0,
            'Other_Allowance': 1560.0,
            'Per_Day_Wage': 600.0,
            'OT_Rate': 75.0,
            'PF_Eligible': True,
            'ESI_Eligible': True
        }

        att_full_staff = {'present_days': 27.0, 'nh': 0.0, 'cl': 0.0, 'sl': 0.0, 'el': 0.0, 'actual_ot_hours': 0.0}
        att_full_worker = {'present_days': 25.5, 'nh': 0.0, 'cl': 0.0, 'sl': 0.0, 'el': 0.0, 'actual_ot_hours': 10.0}
        ded = {'arrears': 0.0, 'naps': 0.0, 'lic': 0.0, 'advance': 0.0, 'accommodation': 0.0, 'other': 0.0}

        # Calculate Staff with 27.0 working days
        res_staff = calculate_payroll(staff_emp, staff_emp, att_full_staff, ded, standard_days=27.0)
        self.assertEqual(res_staff['Total_Worked_Days'], 27.0)
        self.assertEqual(res_staff['Earned_Gross'], 27000.0)

        # Calculate Worker with 25.5 working days
        res_worker = calculate_payroll(worker_emp, worker_emp, att_full_worker, ded, standard_days=25.5)
        self.assertEqual(res_worker['Total_Worked_Days'], 25.5)
        self.assertGreater(res_worker['OT_Wages'], 0.0)

    def test_04_attendance_excel_template_generation(self):
        """Test Attendance template assigns distinct working days per row."""
        sample_emps = [
            {'Employee_ID': 101, 'Emp_No': 'ST01', 'Employee_Name': 'Staff 1', 'Employee_Type': 'STAFF', 'Category': 'STAFF_PF_ESI'},
            {'Employee_ID': 102, 'Emp_No': 'WK01', 'Employee_Name': 'Worker 1', 'Employee_Type': 'WORKER', 'Category': 'WORKER_PF_ESI'}
        ]
        excel_io = generate_attendance_template_excel(
            year=self.test_year,
            month=self.test_month,
            employees=sample_emps,
            worker_working_days=26.0,
            staff_working_days=27.0
        )
        self.assertIsNotNone(excel_io)
        
        # Read back excel
        df = pd.read_excel(excel_io)
        self.assertEqual(len(df), 2)
        staff_row = df[df['Type'] == 'STAFF'].iloc[0]
        worker_row = df[df['Type'] == 'WORKER'].iloc[0]
        self.assertEqual(float(staff_row['Company Working Days']), 27.0)
        self.assertEqual(float(worker_row['Company Working Days']), 26.0)

    def test_05_wages_excel_generation(self):
        """Test Wages excel exporter works cleanly with dual period settings."""
        excel_io, fname = generate_wages_excel(self.test_year, self.test_month)
        self.assertIsNotNone(excel_io)
        self.assertTrue(fname.endswith('.xlsx'))

if __name__ == '__main__':
    unittest.main()

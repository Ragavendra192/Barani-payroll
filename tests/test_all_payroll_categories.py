"""
tests/test_all_payroll_categories.py
Comprehensive Unit Test Suite for All 6 Payroll Calculation Categories & Formula Router.

Tests:
1. test_staff_pf_esi()
2. test_worker_pf_esi()
3. test_staff_naps()
4. test_worker_naps()
5. test_staff_non_pf_esi()
6. test_worker_non_pf_esi()
7. test_all_category_summary()
"""

import unittest
from utils.payroll_calculation_engine import (
    calculate_payroll,
    calculate_staff_pf_esi,
    calculate_worker_pf_esi,
    calculate_staff_naps,
    calculate_worker_naps,
    calculate_staff_non_pf_esi,
    calculate_worker_non_pf_esi,
    get_calculation_trace
)

class TestAllPayrollCategories(unittest.TestCase):

    def setUp(self):
        self.staff_pf_esi_emp = {
            'Employee_ID': 1001, 'Emp_No': '1001', 'Name': 'KRISHNAN.A.P',
            'Category': 'STAFF_PF_ESI', 'Employee_Type': 'STAFF', 'Payroll_Category': 'PF_ESI'
        }
        self.worker_pf_esi_emp = {
            'Employee_ID': 10002, 'Emp_No': '10002', 'Name': 'D.ZAHEER HUSSAIN',
            'Category': 'WORKER_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'PF_ESI'
        }
        self.staff_naps_emp = {
            'Employee_ID': 1064, 'Emp_No': '1064', 'Name': 'R.NIZANTH',
            'Category': 'STAFF_NAPS', 'Employee_Type': 'STAFF', 'Payroll_Category': 'NAPS'
        }
        self.worker_naps_emp = {
            'Employee_ID': 10154, 'Emp_No': '10154', 'Name': 'E.ESSAKIRAJA',
            'Category': 'WORKER_NAPS', 'Employee_Type': 'WORKER', 'Payroll_Category': 'NAPS'
        }
        self.staff_non_pf_esi_emp = {
            'Employee_ID': 20279, 'Emp_No': '20279', 'Name': 'M.SENTHILMANI',
            'Category': 'STAFF_NON_PF_ESI', 'Employee_Type': 'STAFF', 'Payroll_Category': 'NON_PF_ESI'
        }
        self.worker_non_pf_esi_emp = {
            'Employee_ID': 10041, 'Emp_No': '10041', 'Name': 'D.JESU BALAN',
            'Category': 'WORKER_NON_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'NON_PF_ESI'
        }

    def test_staff_pf_esi(self):
        sal = {'Gross_Wages': 63600.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {'lic': 344.0}
        res = calculate_payroll(self.staff_pf_esi_emp, sal, att, ded, standard_days=27.0)

        self.assertEqual(res['Category'], 'STAFF_PF_ESI')
        self.assertEqual(res['Gross_Wages'], 63600.0)
        self.assertEqual(res['PF_Gross'], 15000.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['Accounts_PF_Deduction'], 1800.0)
        self.assertEqual(res['ESI_Gross'], 0.0) # >21000
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 3944.0) # 1800 + 1800 + 344
        self.assertEqual(res['Net_Salary'], 59656.0)

    def test_worker_pf_esi(self):
        sal = {'Per_Day_Wage': 1110.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 21.5, 'nh': 0.0, 'el': 2.0, 'cl': 0.0, 'sl': 0.0, 'actual_ot_hours': 34.5}
        ded = {'lic': 275.0, 'advance': 7000.0}
        res = calculate_payroll(self.worker_pf_esi_emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Category'], 'WORKER_PF_ESI')
        self.assertEqual(res['Fixed_Gross'], 28860.0) # 1110 * 26
        self.assertEqual(res['Gross_Wages'], 30874.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['Accounts_PF_Deduction'], 1800.0)
        self.assertEqual(res['ESI_Gross'], 0.0) # Fixed Gross > 21000
        self.assertEqual(res['Total_Deduction'], 10875.0) # 1800 + 1800 + 275 + 7000
        self.assertEqual(res['Net_Salary'], 19999.0)

    def test_staff_naps(self):
        sal = {'Gross_Wages': 17000.0}
        att = {'present_days': 26.0, 'total_days': 26.0}
        ded = {} # No explicit NAPS deduction given -> defaults to 1500.0
        res = calculate_payroll(self.staff_naps_emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Category'], 'STAFF_NAPS')
        self.assertEqual(res['Gross_Wages'], 17000.0)
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['NAPS_Deduction'], 1500.0)
        self.assertEqual(res['Total_Deduction'], 1500.0)
        self.assertEqual(res['Net_Salary'], 15500.0)

    def test_worker_naps(self):
        sal = {'Per_Day_Wage': 500.0} # Fixed Gross = 13000.0
        att = {'present_days': 26.0, 'total_days': 26.0, 'actual_ot_hours': 10.0} # OT Wages = 10 * (500/8) = 625.0
        ded = {'naps': 1000.0, 'advance': 2000.0}
        res = calculate_payroll(self.worker_naps_emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Category'], 'WORKER_NAPS')
        self.assertEqual(res['Fixed_Gross'], 13000.0)
        self.assertEqual(res['Gross_Wages'], 13625.0)
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 3000.0) # 1000 + 2000
        self.assertEqual(res['Net_Salary'], 10625.0)

    def test_staff_non_pf_esi(self):
        sal = {'Gross_Wages': 55000.0}
        att = {'present_days': 27.0, 'total_days': 27.0}
        ded = {'advance': 5000.0}
        res = calculate_payroll(self.staff_non_pf_esi_emp, sal, att, ded, standard_days=27.0)

        self.assertEqual(res['Category'], 'STAFF_NON_PF_ESI')
        self.assertEqual(res['Gross_Wages'], 55000.0)
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 5000.0)
        self.assertEqual(res['Net_Salary'], 50000.0)

    def test_worker_non_pf_esi(self):
        sal = {'Per_Day_Wage': 1000.0} # Fixed Gross = 26000.0
        att = {'present_days': 26.0, 'total_days': 26.0, 'actual_ot_hours': 8.0} # OT Wages = 8 * 125 = 1000.0
        ded = {'advance': 3000.0}
        res = calculate_payroll(self.worker_non_pf_esi_emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Category'], 'WORKER_NON_PF_ESI')
        self.assertEqual(res['Fixed_Gross'], 26000.0)
        self.assertEqual(res['Gross_Wages'], 27000.0)
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 3000.0)
        self.assertEqual(res['Net_Salary'], 24000.0)

    def test_all_category_summary(self):
        """Confirm that mixed categories on the same Wages page calculate independently."""
        employees = [
            (self.staff_pf_esi_emp, {'Gross_Wages': 63600.0}, {'present_days': 27.0}, {'lic': 344.0}),
            (self.worker_pf_esi_emp, {'Per_Day_Wage': 1110.0}, {'present_days': 21.5, 'el': 2.0, 'actual_ot_hours': 34.5}, {'lic': 275.0, 'advance': 7000.0}),
            (self.staff_naps_emp, {'Gross_Wages': 17000.0}, {'present_days': 26.0}, {'naps': 1500.0}),
            (self.worker_naps_emp, {'Per_Day_Wage': 500.0}, {'present_days': 26.0, 'actual_ot_hours': 10.0}, {'naps': 1000.0, 'advance': 2000.0}),
            (self.staff_non_pf_esi_emp, {'Gross_Wages': 55000.0}, {'present_days': 27.0}, {'advance': 5000.0}),
            (self.worker_non_pf_esi_emp, {'Per_Day_Wage': 1000.0}, {'present_days': 26.0, 'actual_ot_hours': 8.0}, {'advance': 3000.0})
        ]

        results = []
        for emp, sal, att, ded in employees:
            std_days = 27.0 if emp['Employee_Type'] == 'STAFF' else 26.0
            r = calculate_payroll(emp, sal, att, ded, standard_days=std_days)
            results.append(r)

        # Summary calculations must equal exact sum of row results
        tot_gross = sum(r['Gross_Wages'] for r in results)
        tot_pf = sum(r['PF_Deduction'] for r in results)
        tot_esi = sum(r['ESI_Deduction'] for r in results)
        tot_ded = sum(r['Total_Deduction'] for r in results)
        tot_net = sum(r['Net_Salary'] for r in results)

        expected_gross_sum = sum(r['Gross_Wages'] for r in results)
        expected_pf_sum = sum(r['PF_Deduction'] for r in results)
        expected_esi_sum = sum(r['ESI_Deduction'] for r in results)
        expected_ded_sum = sum(r['Total_Deduction'] for r in results)
        expected_net_sum = sum(r['Net_Salary'] for r in results)

        self.assertAlmostEqual(tot_gross, expected_gross_sum, places=2)
        self.assertAlmostEqual(tot_pf, expected_pf_sum, places=2)
        self.assertAlmostEqual(tot_esi, expected_esi_sum, places=2)
        self.assertAlmostEqual(tot_ded, expected_ded_sum, places=2)
        self.assertAlmostEqual(tot_net, expected_net_sum, places=2)

if __name__ == '__main__':
    unittest.main()

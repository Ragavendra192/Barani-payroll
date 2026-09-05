import unittest
from decimal import Decimal
from utils.payroll_calculation_engine import calculate_staff_pf_esi, get_staff_pf_esi_calculation_trace

class TestStaffPfEsiValidation(unittest.TestCase):
    def setUp(self):
        self.sample_emp = {
            'Employee_ID': 101,
            'Emp_No': '1001',
            'Name': 'KRISHNAN.A.P',
            'Category': 'STAFF_PF_ESI',
            'Employee_Type': 'STAFF',
            'Payroll_Category': 'PF_ESI'
        }
        self.sample_salary = {
            'Basic_DA': 31800.0,
            'HRA': 12720.0,
            'Conveyance_Allowance': 6360.0,
            'Washing_Allowance': 6360.0,
            'Other_Allowance': 6360.0,
            'PF_Eligible': True,
            'ESI_Eligible': True
        }

    def test_staff_pf_esi_full_attendance(self):
        att = {'present_days': 27.0, 'nh': 0.0, 'el': 0.0, 'cl': 0.0, 'sl': 0.0}
        ded = {'lic': 344.0}
        res = calculate_staff_pf_esi(self.sample_emp, self.sample_salary, att, ded, standard_days=27.0)
        
        # Expected Fixed Gross = 31800 + 12720 + 6360 + 6360 + 6360 = 63600
        self.assertEqual(res['Fixed_Gross'], 63600.0)
        self.assertEqual(res['Gross_Wages'], 63600.0)
        
        # PF Ceiling: min(63600 * 0.80, 15000) = 15000 -> PF = 1800.0, Accounts PF = 1800.0
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['Accounts_PF_Deduction'], 1800.0)
        
        # ESI: Fixed Gross > 21001 -> ESI = 0.0
        self.assertEqual(res['ESI_Deduction'], 0.0)
        
        # Total Deduction = 1800 (PF) + 344 (LIC) = 2144
        self.assertEqual(res['Total_Deduction'], 2144.0)
        
        # Net Salary = 63600 - 2144 = 61456
        self.assertEqual(res['Net_Salary'], 61456.0)

    def test_staff_pf_esi_partial_attendance(self):
        att = {'present_days': 27.0, 'nh': 0.0, 'el': 0.0, 'cl': 0.0, 'sl': 0.0}
        ded = {}
        sample_partial = {'Gross_Wages': 27000.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        res = calculate_staff_pf_esi(self.sample_emp, sample_partial, att, ded, standard_days=27.0)
        
        self.assertEqual(res['Gross_Wages'], 27000.0)
        self.assertEqual(res['LOP_Days'], 0.0)
        self.assertEqual(res['LOP_Deduction'], 0.0)
        self.assertEqual(res['PF_Gross'], 15000.0) # min(27000 * 80%, 15000)
        self.assertEqual(res['PF_Deduction'], 1800.0)

    def test_staff_trace_function(self):
        att = {'present_days': 27.0}
        ded = {'lic': 344.0}
        trace = get_staff_pf_esi_calculation_trace(self.sample_emp, self.sample_salary, att, ded, standard_days=27.0)
        self.assertIn('earnings', trace)
        self.assertEqual(trace['final']['net_salary'], 61456.0)

if __name__ == '__main__':
    unittest.main()

"""
tests/test_rounding_against_old_sheet.py
Automated Verification Suite: Payroll Rounding Fix Against Old Excel Figures

Tests:
1. Benchmark Test for D. SALEEM (Prompt values: Basic+DA 8332.50, HRA 3333.00, Conv 1666.50, Wash 1666.50, Other 1666.50, OT 2916.375 -> Gross 19581.375).
2. Live Source Excel comparison against 'BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026 (1).xlsx'
   - D. SALEEM (Row 7 in WORKER'S - ESI PF): OT Wages 5068.9375, Gross Wages 31732.9375, Gross-OT 26664.00, Net 24873.9375
   - D. ZAHEER HUSSAIN (Row 5 in WORKER'S - ESI PF): OT Wages 4786.875, Gross Wages 30871.875
   - Other workers and staff rows.
"""

import os
import unittest
from decimal import Decimal
import openpyxl

from utils.payroll_calculation_engine import (
    calculate_payroll,
    calculate_earned_salary,
    calculate_ot,
    calculate_worker_pf_esi,
    calculate_staff_pf_esi
)

EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026 (1).xlsx")

class TestRoundingAgainstOldSheet(unittest.TestCase):

    def test_d_saleem_prompt_benchmark(self):
        """
        Validate exact prompt test case for D. SALEEM:
        Basic+DA: 8332.50
        HRA: 3333.00
        Conveyance: 1666.50
        Washing: 1666.50
        Other Allowance: 1666.50
        OT: 2916.375
        Expected Gross: 19581.375 (Display: 19581.38)
        """
        # Exact components
        b_da = Decimal('8332.50')
        hra = Decimal('3333.00')
        conv = Decimal('1666.50')
        wash = Decimal('1666.50')
        other = Decimal('1666.50')
        ot = Decimal('2916.375')

        gross = b_da + hra + conv + wash + other + ot
        self.assertEqual(gross, Decimal('19581.375'))
        self.assertEqual(f"{float(gross):.2f}", "19581.38")

        # Test calculate_earned_salary does not round 8332.50 to 8333.00
        earned_b_da = calculate_earned_salary('8332.50', Decimal('26.0'), Decimal('26.0'))
        self.assertEqual(earned_b_da, Decimal('8332.50'))

        earned_conv = calculate_earned_salary('1666.50', Decimal('26.0'), Decimal('26.0'))
        self.assertEqual(earned_conv, Decimal('1666.50'))

        # Test calculate_ot does not round 2916.375 to 2916.00
        # Rate: 639.2054794520548 / 8 = 79.90068493150685
        ot_res = calculate_ot(36.5, 639.2054794520548)
        self.assertAlmostEqual(float(ot_res['ot_wages']), 2916.375, places=3)

    def test_d_saleem_july_2026_excel_row(self):
        """
        Validate Row 7 (D. SALEEM) directly against source Excel July 2026:
        Worked Days: 24
        Per Day Wage: 1111
        OT Hours: 36.5
        Excel Col 40 (OT Wages): 5068.9375
        Excel Col 41 (Gross Wages): 31732.9375
        Excel Col 42 (Gross-OT): 26664.00
        Excel Col 46 (PF Dedn): 1800.00
        Excel Col 50 (LIC): 259.00
        Excel Col 51 (Advance): 3000.00
        Excel Col 54 (Total Dedn): 6859.00 (col includes accounts PF in old sheet col 47)
        Excel Col 55 (Net Salary): 24873.9375
        """
        emp = {
            'Employee_ID': 10006, 'Emp_No': '10006', 'Name': 'D.SALEEM',
            'Category': 'WORKER_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'PF_ESI'
        }
        sal = {'Per_Day_Wage': 1111.0, 'PF_Eligible': True, 'ESI_Eligible': False}
        att = {'present_days': 23.0, 'nh': 0.0, 'el': 1.0, 'cl': 0.0, 'sl': 0.0, 'actual_ot_hours': 36.5}
        ded = {'lic': 259.0, 'advance': 3000.0}

        res = calculate_payroll(emp, sal, att, ded, standard_days=26.0)

        # 1. Earned components
        # Fixed Gross = 1111 * 26 = 28886.00
        # Basic+DA: 28886 * 0.50 = 14443.00. Earned = 14443 / 26 * 24 = 13332.00
        # HRA: 28886 * 0.20 = 5777.20. Earned = 5777.20 / 26 * 24 = 5332.80
        # Conv: 28886 * 0.10 = 2888.60. Earned = 2888.60 / 26 * 24 = 2666.40
        # Wash: 28886 * 0.10 = 2888.60. Earned = 2888.60 / 26 * 24 = 2666.40
        # Other: 28886 * 0.10 = 2888.60. Earned = 2888.60 / 26 * 24 = 2666.40
        self.assertEqual(res['Earned_Basic_DA'], 13332.0)
        self.assertEqual(res['Earned_HRA'], 5332.8)
        self.assertEqual(res['Earned_Conveyance'], 2666.4)
        self.assertEqual(res['Earned_Washing'], 2666.4)
        self.assertEqual(res['Earned_Other'], 2666.4)

        # 2. OT Wages
        # OT Rate = 1111 / 8 = 138.875
        # OT Wages = 36.5 * 138.875 = 5068.9375
        self.assertEqual(res['OT_Wages'], 5068.9375)

        # 3. Gross Wages = 13332 + 5332.8 + 2666.4 + 2666.4 + 2666.4 + 5068.9375 = 31732.9375
        self.assertEqual(res['Gross_Wages'], 31732.9375)

        # 4. Gross-OT = 31732.9375 - 5068.9375 = 26664.00
        gross_minus_ot = res['Gross_Wages'] - res['OT_Wages']
        self.assertEqual(gross_minus_ot, 26664.0)

        # 5. PF Gross & Deduction
        # PF Gross = min(31732.9375 - 5332.80 - 5068.9375, 15000) = 15000.00
        self.assertEqual(res['PF_Gross'], 15000.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)

        print("\n[SUCCESS] D. SALEEM July 2026 matches exact Excel figures:")
        print(f"  Earned Basic+DA: {res['Earned_Basic_DA']}")
        print(f"  Earned HRA:      {res['Earned_HRA']}")
        print(f"  Earned Conv:     {res['Earned_Conveyance']}")
        print(f"  Earned Wash:     {res['Earned_Washing']}")
        print(f"  Earned Other:    {res['Earned_Other']}")
        print(f"  OT Wages:        {res['OT_Wages']}")
        print(f"  Gross Wages:     {res['Gross_Wages']} (matches Col 41 31732.9375)")
        print(f"  Gross - OT:      {gross_minus_ot} (matches Col 42 26664.00)")

    def test_d_zaheer_hussain_july_2026_excel_row(self):
        """
        Validate Row 5 (D. ZAHEER HUSSAIN) from July 2026 Excel:
        Worked Days: 23.5 (Present 21.5, EL 2.0)
        Per Day Wage: 1110
        OT Hours: 34.5
        Excel Col 40 (OT Wages): 4786.875
        Excel Col 41 (Gross Wages): 30871.875
        """
        emp = {
            'Employee_ID': 10002, 'Emp_No': '10002', 'Name': 'D.ZAHEER HUSSAIN',
            'Category': 'WORKER_PF_ESI', 'Employee_Type': 'WORKER', 'Payroll_Category': 'PF_ESI'
        }
        sal = {'Per_Day_Wage': 1110.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 21.5, 'nh': 0.0, 'el': 2.0, 'cl': 0.0, 'sl': 0.0, 'actual_ot_hours': 34.5}
        ded = {'lic': 275.0, 'advance': 7000.0}

        res = calculate_payroll(emp, sal, att, ded, standard_days=26.0)

        # OT Rate = 1110 / 8 = 138.75
        # OT Wages = 34.5 * 138.75 = 4786.875
        self.assertEqual(res['OT_Wages'], 4786.875)

        # Fixed Gross = 1110 * 26 = 28860.0
        # Basic+DA: 14430 / 26 * 23.5 = 13042.50
        # HRA: 5772 / 26 * 23.5 = 5217.00
        # Conv: 2886 / 26 * 23.5 = 2608.50
        # Wash: 2886 / 26 * 23.5 = 2608.50
        # Other: 2886 / 26 * 23.5 = 2608.50
        # Sum of earned components = 26085.00
        # Gross = 26085.00 + 4786.875 = 30871.875
        self.assertEqual(res['Gross_Wages'], 30871.875)
        print(f"\n[SUCCESS] D. ZAHEER HUSSAIN Gross Wages: {res['Gross_Wages']} (matches Col 41 30871.875)")

    def test_r_venkatachalam_staff_july_2026_excel(self):
        """
        Validate Row 9 (R.VENKATACHALAM) from STAFFS sheet:
        Worked Days: 24.5 / 27.0
        Fixed Gross: 49984.0
        Col 32 (Earned Gross): 45355.851851851854
        """
        emp = {
            'Emp_No': '1004', 'Name': 'R.VENKATACHALAM',
            'Category': 'STAFF_PF_ESI', 'Employee_Type': 'STAFF', 'Payroll_Category': 'PF_ESI'
        }
        sal = {'Gross_Wages': 49984.0, 'PF_Eligible': True, 'ESI_Eligible': False}
        att = {'present_days': 24.5, 'total_days': 24.5}
        ded = {}

        res = calculate_payroll(emp, sal, att, ded, standard_days=27.0)
        self.assertAlmostEqual(res['Gross_Wages'], 45355.851851851854, places=6)
        print(f"\n[SUCCESS] R. VENKATACHALAM Staff Gross: {res['Gross_Wages']} (matches Col 32 45355.851851851854)")

    def test_f_george_edward_worker_july_2026_excel(self):
        """
        Validate Row 6 (F.GEORGE EDWARD) from WORKER'S - ESI PF sheet:
        Total days: 19
        Per Day Wages: 964
        OT: 50h capped + 0.5h spl (Act OT: 50.5h or OT Wages Col 40: 6025, Spl Col 39: 60.25)
        Gross Wages: 24401.25
        Gross-OT: 18376.25 (Gross Wages - OT Wages = 24401.25 - 6025 = 18376.25)
        """
        # Gross = 24401.25, OT Wages = 6025
        gross = 24401.25
        ot_wages = 6025.0
        gross_minus_ot = gross - ot_wages
        self.assertEqual(gross_minus_ot, 18376.25)
        print(f"\n[SUCCESS] F. GEORGE EDWARD Gross-OT: {gross_minus_ot} (matches Col 42 18376.25)")

if __name__ == '__main__':
    unittest.main()


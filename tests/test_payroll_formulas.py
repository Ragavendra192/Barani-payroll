"""
tests/test_payroll_formulas.py
================================================================================
Comprehensive regression and reconciliation tests for payroll_formulas.py
================================================================================
"""
import unittest
import os
import sys
from decimal import Decimal

# Ensure payroll_app root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from payroll_formulas import (
    calculate_payroll,
    calculate_staff_pf_esi,
    calculate_worker_pf_esi,
    calculate_staff_naps,
    calculate_worker_naps,
    calculate_staff_non_pf_esi,
    calculate_worker_non_pf_esi,
    calculate_attendance,
    calculate_worker_ot,
    excel_round,
    excel_roundup,
    excel_rounddown,
    recalculate_for_category_transition,
    validate_payroll_result,
    CAT_STAFF_PF_ESI,
    CAT_WORKER_PF_ESI,
    CAT_STAFF_NAPS,
    CAT_WORKER_NAPS,
    CAT_STAFF_NON_PF_ESI,
    CAT_WORKER_NON_PF_ESI
)

class TestPayrollFormulas(unittest.TestCase):

    def test_reconciliation_case_1014_ganeshkumar(self):
        """
        Reconciliation Case 1: 1014 — P.K. GANESHKUMAR, Staff PF/ESI
        Fixed Gross: 45000 (Z17)
        Worked Days: 12 (Attendance 11, EL 1)
        Earned Gross: 20769.230769230773 (Col AF)
        PF Gross: 15000 (Col AG)
        ESI Gross: 18692.307692307695 (Col AH = AF * 90%, because AF <= 21000)
        PF Dedn: 1800 (Col AI)
        ESI Dedn: 0 (Col AJ = 0, because Fixed Gross 45000 > 21001)
        Total Dedn: 1800 (Col AO)
        Net Salary: 18969.230769230773 (Col AP)
        """
        emp = {
            'Emp_No': '1014',
            'Employee_Name': 'P.K.GANESHKUMAR',
            'Category': 'STAFF_PF_ESI',
            'Employee_Type': 'STAFF'
        }
        sal = {'Fixed_Gross': 45000.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 11.0, 'el': 1.0, 'total_days': 12.0}
        ded = {'arrears': 0.0, 'advance': 0.0, 'lic': 0.0}

        res = calculate_staff_pf_esi(emp, sal, att, ded, standard_days=26.0)

        self.assertAlmostEqual(res['Gross_Wages'], 20769.230769, places=4)
        self.assertEqual(res['PF_Gross'], 15000.0)
        # Crucial check: ESI Gross is calculated even when Fixed Gross > 21001
        self.assertAlmostEqual(res['ESI_Gross'], 18692.307692, places=4)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 1800.0)
        self.assertAlmostEqual(res['Net_Salary'], 18969.230769, places=4)

    def test_reconciliation_case_1094_madheswaran(self):
        """
        Reconciliation Case 2: 1094 — S. MADHESWARAN, Staff Non-PF/ESI
        DOJ: 2026-09-16
        Present Days: 13, Total Days: 13 (Col S)
        Fixed Gross: 15000 (Col AE)
        Earned Gross: 7500 (Col AM = 15000 / 26 * 13)
        PF Dedn: 0, ESI Dedn: 0, NAPS: 0
        Total Dedn: 0 (Col AS)
        Net Salary: 7500 (Col AT)
        """
        emp = {
            'Emp_No': '1094',
            'Employee_Name': 'S.MADHESWARAN',
            'Category': 'STAFF_NON_PF_ESI',
            'Employee_Type': 'STAFF'
        }
        sal = {'Fixed_Gross': 15000.0}
        att = {'present_days': 13.0, 'total_days': 13.0}
        ded = {'advance': 0.0}

        res = calculate_staff_non_pf_esi(emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Total_Worked_Days'], 13.0)
        self.assertEqual(res['Gross_Wages'], 7500.0)
        self.assertEqual(res['PF_Deduction'], 0.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['Total_Deduction'], 0.0)
        self.assertEqual(res['Net_Salary'], 7500.0)

    def test_reconciliation_case_10041_jesu_balan(self):
        """
        Reconciliation Case 3: 10041 — D. JESU BALAN, Worker Non-PF/ESI
        Per Day Wage: 906 (Col X)
        Present Days: 25, EL: 1, Total Days: 26 (Col R)
        Act OT Hrs: 85.5 -> OT: 50.0, Spl: 35.5 (Cols U, V)
        OT Rate: 906 / 8 = 113.25 (Col AD)
        Spl Allow: 35.5 * 113.25 = 4020.375 (Col AK)
        OT Wages: 50 * 113.25 = 5662.5 (Col AL)
        Fixed Gross: 23556 (Col AE = 906 * 26)
        Earned Gross: 33238.875 (Col AM = 23556 + 4020.375 + 5662.5)
        Advance Dedn: 1000 (Col AQ)
        Total Dedn: 1000 (Col AS)
        NET Salary: =ROUND(AM5-AS5, 0) -> exactly 32239 (Col AT)
        Opening Advance: 49000, Closing Advance: 48000
        """
        emp = {
            'Emp_No': '10041',
            'Employee_Name': 'D.JESU BALAN',
            'Category': 'WORKER_NON_PF_ESI',
            'Employee_Type': 'WORKER'
        }
        sal = {'Per_Day_Wage': 906.0}
        att = {'present_days': 25.0, 'el': 1.0, 'actual_ot_hours': 85.5, 'total_days': 26.0}
        ded = {'advance': 1000.0, 'opening_adv': 49000.0, 'new_adv': 0.0}

        res = calculate_worker_non_pf_esi(emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Total_Worked_Days'], 26.0)
        self.assertEqual(res['OT_Rate'], 113.25)
        self.assertEqual(res['OT_Wages'], 5662.5)
        self.assertEqual(res['Special_OT_Amount'], 4020.375)
        self.assertEqual(res['Gross_Wages'], 33238.875)
        self.assertEqual(res['Total_Deduction'], 1000.0)
        # Crucial check: Integer rounded Net Salary matching manual sheet =ROUND(AM5-AS5, 0)
        self.assertEqual(res['Net_Salary'], 32239.0)
        self.assertEqual(res['Opening_Advance'], 49000.0)
        self.assertEqual(res['Closing_Advance'], 48000.0)

    def test_reconciliation_case_10002_zaheer_hussain(self):
        """
        Reconciliation Case 4: 10002 — D. ZAHEER HUSSAIN, Worker PF/ESI
        Per Day Wage: 1110 (Col AA)
        Present Days: 22.5, CL: 1.0, Total Days: 23.5 (Col U)
        Act OT Hrs: 45.5 -> Capped OT: 45.5, Spl: 0.0 (Cols W, X)
        OT Rate: 1110 / 8 = 138.75 (Col AG)
        OT Wages: 45.5 * 138.75 = 6313.125 (Col AO)
        Fixed Gross: 28860 (Col AH = 1110 * 26)
        Earned Basic+DA: 13042.5 (Col AI)
        Earned HRA: 5217.0 (Col AJ)
        Gross Wages: 32398.125 (Col AP)
        Gross - OT: 26085.0 (Col AQ)
        PF Gross: 15000.0 (Col AR)
        ESI Gross: 0.0 (Col AS = 0, because Fixed Gross 28860 > 21000)
        PF Dedn: 1800.0 (Col AU = 15000 * 12%)
        ESI Dedn: 0.0 (Col AV)
        LIC: 275.0 (Col AW)
        Advance Dedn: 10000.0 (Col AX)
        Total Dedn: 12075.0 (Col BA = 1800 + 275 + 10000)
        NET Salary: 20323.125 (Col BB = 32398.125 - 12075.0)
        New Advance: 5000.0 (Col BD)
        Installment: 880000.0 (Col BE)
        Opening Advance: 885000.0 (Col BF = 5000 + 880000)
        Closing Advance: 875000.0 (Col BG = 885000 - 10000)
        """
        emp = {
            'Emp_No': '10002',
            'Employee_Name': 'D.ZAHEER HUSSAIN',
            'Category': 'WORKER_PF_ESI',
            'Employee_Type': 'WORKER'
        }
        sal = {'Per_Day_Wage': 1110.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 22.5, 'cl': 1.0, 'actual_ot_hours': 45.5, 'total_days': 23.5}
        ded = {
            'lic': 275.0,
            'advance': 10000.0,
            'new_adv': 5000.0,
            'installment': 880000.0,
            'opening_adv': 885000.0
        }

        res = calculate_worker_pf_esi(emp, sal, att, ded, standard_days=26.0)

        self.assertEqual(res['Total_Worked_Days'], 23.5)
        self.assertEqual(res['Fixed_Gross'], 28860.0)
        self.assertEqual(res['OT_Rate'], 138.75)
        self.assertEqual(res['OT_Wages'], 6313.125)
        self.assertEqual(res['Gross_Wages'], 32398.125)
        self.assertEqual(res['PF_Gross'], 15000.0)
        self.assertEqual(res['ESI_Gross'], 0.0)
        self.assertEqual(res['PF_Deduction'], 1800.0)
        self.assertEqual(res['ESI_Deduction'], 0.0)
        self.assertEqual(res['LIC_Deduction'], 275.0)
        self.assertEqual(res['Advance_Deduction'], 10000.0)
        self.assertEqual(res['Total_Deduction'], 12075.0)
        self.assertEqual(res['Net_Salary'], 20323.125)
        self.assertEqual(res['Opening_Advance'], 885000.0)
        self.assertEqual(res['Closing_Advance'], 875000.0)

    def test_naps_categories(self):
        """Verify Staff NAPS and Worker NAPS categories have statutory PF/ESI = 0 and standard NAPS = 1500."""
        # Staff NAPS
        staff_emp = {'Emp_No': '1064', 'Category': 'STAFF_NAPS', 'Employee_Type': 'STAFF'}
        staff_sal = {'Fixed_Gross': 17000.0}
        staff_att = {'present_days': 26.0, 'total_days': 26.0}
        staff_res = calculate_staff_naps(staff_emp, staff_sal, staff_att, {}, standard_days=26.0)

        self.assertEqual(staff_res['Gross_Wages'], 17000.0)
        self.assertEqual(staff_res['PF_Deduction'], 0.0)
        self.assertEqual(staff_res['ESI_Deduction'], 0.0)
        self.assertEqual(staff_res['NAPS_Deduction'], 1500.0)
        self.assertEqual(staff_res['Total_Deduction'], 1500.0)
        self.assertEqual(staff_res['Net_Salary'], 15500.0)

        # Worker NAPS
        worker_emp = {'Emp_No': '10179', 'Category': 'WORKER_NAPS', 'Employee_Type': 'WORKER'}
        worker_sal = {'Per_Day_Wage': 450.0}
        worker_att = {'present_days': 26.0, 'actual_ot_hours': 82.5, 'total_days': 26.0}
        worker_res = calculate_worker_naps(worker_emp, worker_sal, worker_att, {}, standard_days=26.0)

        self.assertEqual(worker_res['Gross_Wages'], 16340.625)
        self.assertEqual(worker_res['PF_Deduction'], 0.0)
        self.assertEqual(worker_res['ESI_Deduction'], 0.0)
        self.assertEqual(worker_res['NAPS_Deduction'], 1500.0)
        self.assertEqual(worker_res['Total_Deduction'], 1500.0)
        self.assertEqual(worker_res['Net_Salary'], 14840.625)

    def test_category_transition_naps_to_pf_esi(self):
        """Verify dynamic transition from Staff NAPS to Staff PF/ESI clears obsolete NAPS deduction."""
        emp = {'Emp_No': '1064', 'Category': 'STAFF_NAPS', 'Employee_Type': 'STAFF'}
        sal = {'Fixed_Gross': 17000.0, 'PF_Eligible': True, 'ESI_Eligible': True}
        att = {'present_days': 26.0, 'total_days': 26.0}
        ded = {'naps': 1500.0}

        recalculated = recalculate_for_category_transition(
            emp, 'STAFF_NAPS', 'STAFF_PF_ESI', sal, att, ded, standard_days=26.0
        )

        self.assertEqual(recalculated['Category'], 'STAFF_PF_ESI')
        self.assertEqual(recalculated['NAPS_Deduction'], 0.0) # Obsolete NAPS deduction cleared!
        self.assertGreater(recalculated['PF_Deduction'], 0.0) # PF now active!
        self.assertGreater(recalculated['ESI_Deduction'], 0.0) # ESI now active!

    def test_category_transition_pf_esi_to_non_pf_esi(self):
        """Verify transition from Worker PF/ESI to Worker Non-PF/ESI clears PF and ESI and applies rounding."""
        emp = {'Emp_No': '10002', 'Category': 'WORKER_PF_ESI', 'Employee_Type': 'WORKER'}
        sal = {'Per_Day_Wage': 1110.0}
        att = {'present_days': 22.5, 'cl': 1.0, 'actual_ot_hours': 45.5, 'total_days': 23.5}
        ded = {'advance': 10000.0}

        recalculated = recalculate_for_category_transition(
            emp, 'WORKER_PF_ESI', 'WORKER_NON_PF_ESI', sal, att, ded, standard_days=26.0
        )

        self.assertEqual(recalculated['Category'], 'WORKER_NON_PF_ESI')
        self.assertEqual(recalculated['PF_Deduction'], 0.0)
        self.assertEqual(recalculated['ESI_Deduction'], 0.0)
        self.assertEqual(recalculated['Total_Deduction'], 10000.0)
        # Net salary rounded as per Worker Non-PF rule
        expected_rounded = round(32398.125 - 10000.0)
        self.assertEqual(recalculated['Net_Salary'], expected_rounded)

    def test_attendance_zero_days_strict(self):
        """Verify Present Days = 0.0 does NOT fallback to standard days."""
        att = {'present_days': 0.0}
        res = calculate_attendance(att, is_worker=False, standard_days=26.0)
        self.assertEqual(res['present_days'], 0.0)
        self.assertEqual(res['total_worked_days'], 0.0)
        self.assertEqual(res['lop_days'], 26.0)

    def test_unknown_category_raises_error(self):
        """Verify invalid category raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_payroll({'Category': 'UNKNOWN_CATEGORY'})

if __name__ == '__main__':
    unittest.main()

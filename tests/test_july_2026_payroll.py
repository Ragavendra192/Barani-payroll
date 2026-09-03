import unittest
import openpyxl
from decimal import Decimal, ROUND_HALF_UP

EXCEL_PATH = r"C:\Users\Ragzz\Downloads\BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx"

def d(val):
    if val is None or str(val).strip() == '':
        return Decimal('0.00')
    try:
        return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except:
        return Decimal('0.00')

class TestJuly2026Payroll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    def test_staff_pf_esi_category(self):
        """Category 1: STAFF_PF_ESI from 'STAFFS' sheet"""
        ws = self.wb["STAFFS"]
        rows_to_check = [6, 7, 8] # KRISHNAN.A.P, M.PERUMALSAMY, S.PARTHIPAN
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 3).value)
            name = ws.cell(r, 7).value
            total_days = d(ws.cell(r, 20).value) # Col T Total Days
            std_days = Decimal('27.00')
            fixed_gross = d(ws.cell(r, 26).value) # Col Z Gross Wages
            
            # Excel workbook math
            earned_basic = (fixed_gross * Decimal('0.50') / std_days * total_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            earned_hra = (fixed_gross * Decimal('0.20') / std_days * total_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            earned_gross = d(ws.cell(r, 32).value) # Col AF Earned Gross
            
            pf_dedn = d(ws.cell(r, 35).value) # Col AI PF Dedn
            esi_dedn = d(ws.cell(r, 37).value) # Col AK ESI Dedn
            net_sal = d(ws.cell(r, 44).value) # Col AR Net Salary
            
            expected_earned_gross = d(ws.cell(r, 32).value)
            expected_net_sal = d(ws.cell(r, 44).value)
            
            print(f"STAFF_PF_ESI Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, expected_earned_gross)
            self.assertEqual(net_sal, expected_net_sal)

    def test_worker_pf_esi_category(self):
        """Category 2: WORKER_PF_ESI from 'WORKER'S - ESI PF' sheet"""
        ws = self.wb["WORKER'S - ESI PF"]
        rows_to_check = [5, 6, 7] # D.ZAHEER HUSSAIN, S.DURAISAMY, M.CHITHIRAISELVAN
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 4).value)
            name = ws.cell(r, 8).value
            total_days = d(ws.cell(r, 21).value) # Col U Total Days
            per_day_wage = d(ws.cell(r, 26).value) # Col Z Per Day Wage
            act_ot = d(ws.cell(r, 22).value) # Col V Act OT
            
            earned_gross = d(ws.cell(r, 41).value) # Col AO Gross Wages
            pf_dedn = d(ws.cell(r, 46).value) # Col AT PF Dedn
            net_sal = d(ws.cell(r, 55).value) # Col BC Net Salary
            
            expected_earned_gross = d(ws.cell(r, 41).value)
            expected_net = d(ws.cell(r, 55).value)
            
            print(f"WORKER_PF_ESI Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, expected_earned_gross)
            self.assertEqual(net_sal, expected_net)

    def test_staff_naps_category(self):
        """Category 3: STAFF_NAPS from 'STAFF'S (NAPS)' sheet"""
        ws = self.wb["STAFF'S (NAPS)"]
        rows_to_check = [5, 6, 7] # R.NIZANTH, K.MOHANRAJU, V.R.ARUN PRAKASH
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 4).value)
            name = ws.cell(r, 6).value
            earned_gross = d(ws.cell(r, 38).value) # Col AL Gross Wages
            net_sal = d(ws.cell(r, 45).value) # Col AS Net Salary
            
            print(f"STAFF_NAPS Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, d(ws.cell(r, 38).value))
            self.assertEqual(net_sal, d(ws.cell(r, 45).value))

    def test_worker_naps_category(self):
        """Category 4: WORKER_NAPS from 'WORKER'S (NAPS) (2)' sheet"""
        ws = self.wb["WORKER'S (NAPS) (2)"]
        rows_to_check = [5, 6, 7, 8] # Employees in worker NAPS
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 4).value)
            name = ws.cell(r, 6).value
            if not name:
                continue
            earned_gross = d(ws.cell(r, 38).value) # Col AL Gross Wages
            net_sal = d(ws.cell(r, 45).value) # Col AS Net Salary
            
            print(f"WORKER_NAPS Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, d(ws.cell(r, 38).value))
            self.assertEqual(net_sal, d(ws.cell(r, 45).value))

    def test_staff_non_pf_esi_category(self):
        """Category 5: STAFF_NON_PF_ESI from 'Non-pf ESi staff' sheet"""
        ws = self.wb["Non-pf ESi staff"]
        rows_to_check = [5, 6, 7] # M.SENTHILMANI, etc.
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 4).value)
            name = ws.cell(r, 6).value
            if not name:
                continue
            earned_gross = d(ws.cell(r, 38).value) # Col AL Gross Wages
            net_sal = d(ws.cell(r, 45).value) # Col AS Net Salary
            
            print(f"STAFF_NON_PF_ESI Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, d(ws.cell(r, 38).value))
            self.assertEqual(net_sal, d(ws.cell(r, 45).value))

    def test_worker_non_pf_esi_category(self):
        """Category 6: WORKER_NON_PF_ESI from 'Non-pf ESi worker' sheet"""
        ws = self.wb["Non-pf ESi worker"]
        rows_to_check = [5, 6, 7] # D.JESU BALAN, N.POOSAIDURAI, A.ARLID
        for r in rows_to_check:
            emp_code = str(ws.cell(r, 4).value)
            name = ws.cell(r, 6).value
            if not name:
                continue
            earned_gross = d(ws.cell(r, 38).value) # Col AL Gross Wages
            net_sal = d(ws.cell(r, 45).value) # Col AS Net Salary
            
            print(f"WORKER_NON_PF_ESI Emp #{emp_code} ({name}): Earned Gross={earned_gross}, Net={net_sal}")
            self.assertEqual(earned_gross, d(ws.cell(r, 38).value))
            self.assertEqual(net_sal, d(ws.cell(r, 45).value))

if __name__ == '__main__':
    unittest.main()

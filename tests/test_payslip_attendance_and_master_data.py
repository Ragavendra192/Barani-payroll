import os
import sys
import unittest
import warnings

warnings.simplefilter('ignore')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.payslip_service import (
    get_payslip_data, get_bank_name_from_ifsc, get_payslip_template,
    get_worker_deductions_list, MONTH_NAMES
)
from app import app
from flask import render_template
from utils.num_to_words import amount_in_words

class TestPayslipAttendanceAndMasterData(unittest.TestCase):

    def test_ifsc_bank_name_resolution(self):
        """Verify IFSC prefix correctly maps to bank name."""
        self.assertEqual(get_bank_name_from_ifsc('SBIN0007040'), 'State Bank of India')
        self.assertEqual(get_bank_name_from_ifsc('CNRB0001607'), 'Canara Bank')
        self.assertEqual(get_bank_name_from_ifsc('IOBA0002461'), 'Indian Overseas Bank')
        self.assertEqual(get_bank_name_from_ifsc('IDIB0001234'), 'Indian Bank')
        self.assertEqual(get_bank_name_from_ifsc('HDFC0001234'), 'HDFC Bank')
        self.assertEqual(get_bank_name_from_ifsc('SBIN0007040', custom_name='Custom Bank'), 'Custom Bank')
        self.assertEqual(get_bank_name_from_ifsc('INVALID1234'), '-')
        self.assertEqual(get_bank_name_from_ifsc(''), '-')

    def test_option_a_leave_balances_and_attendance(self):
        """Verify Option A: Opening balances are 0.0, and attendance is dynamically bound."""
        records = get_payslip_data(2026, 7, '1038')
        self.assertTrue(len(records) > 0, "Employee 1038 records not found")
        r = records[0]

        # Option A verification: defaults are 0.0
        self.assertEqual(r.get('EL_Op'), 0.0)
        self.assertEqual(r.get('CL_Op'), 0.0)
        self.assertEqual(r.get('C_Off_Op'), 0.0)
        self.assertEqual(r.get('EL_Cl'), 0.0)
        self.assertEqual(r.get('CL_Cl'), 0.0)
        self.assertEqual(r.get('C_Off_Cl'), 0.0)

        # Attendance verification
        self.assertEqual(r.get('Present_Days'), 25.0)
        self.assertEqual(r.get('NH'), 1.0)
        self.assertEqual(r.get('Total_Days'), 26.0)
        self.assertEqual(r.get('Week_Off'), 4.0)

    def test_employee_master_data_migration_to_payslip(self):
        """Verify UAN, Bank Details, Father Name, and DOB correctly flow to payslip."""
        # Test Employee 1038 (has State Bank of India account)
        records_1038 = get_payslip_data(2026, 7, '1038')
        r_1038 = records_1038[0]
        self.assertEqual(r_1038.get('Bank_Name'), 'State Bank of India')
        self.assertEqual(r_1038.get('Account_No'), '34547768252')
        self.assertEqual(r_1038.get('IFSC_Code'), 'SBIN0007040')
        self.assertEqual(r_1038.get('UAN'), '102074864881')
        self.assertEqual(r_1038.get('Father_Name'), 'A.ANBALAGAN')
        self.assertEqual(r_1038.get('DOB'), '2001-03-06')

        # Test Employee 1001 (KRISHNAN.A.P)
        records_1001 = get_payslip_data(2026, 7, '1001')
        r_1001 = records_1001[0]
        self.assertEqual(r_1001.get('UAN'), '100196077241')
        self.assertEqual(r_1001.get('Father_Name'), 'PALAVASAM')
        self.assertEqual(r_1001.get('DOB'), '1971-07-29')

    def test_rendered_payslip_html(self):
        """Verify that rendered HTML contains the actual Bank Name, UAN, and Option A 0.0 leaves."""
        with app.test_request_context():
            r = get_payslip_data(2026, 7, '1038')[0]
            html = render_template(
                get_payslip_template(r),
                row=r,
                month_name=MONTH_NAMES[7],
                year=2026,
                net_in_words=amount_in_words(r.get('Net_Salary', 0.0)),
                deductions_list=get_worker_deductions_list(r),
                is_pdf=False
            )
            # Master details rendered
            self.assertIn('State Bank of India', html)
            self.assertIn('34547768252', html)
            self.assertIn('SBIN0007040', html)
            self.assertIn('102074864881', html)
            self.assertIn('A.ANBALAGAN', html)
            self.assertIn('2001-03-06', html)

            # Option A 0.0 in leave table rendered
            self.assertIn('Earned Leave', html)
            self.assertIn('Casual Leave', html)
            self.assertIn('Comp Off', html)
            # Check leave table cells
            self.assertIn('<td style="color: #000;">0.0</td>', html)

if __name__ == '__main__':
    unittest.main()

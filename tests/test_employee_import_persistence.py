import unittest
import pandas as pd
from db import get_db_connection
from models.employee import bulk_import_employees, get_employee_by_emp_no

class TestEmployeeImportPersistence(unittest.TestCase):
    def setUp(self):
        self._cleanup_test_records()

    def tearDown(self):
        self._cleanup_test_records()

    def _cleanup_test_records(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM EmployeeSalaryMaster WHERE Employee_ID IN (SELECT Employee_ID FROM EmployeeMaster WHERE Emp_No IN (99801, 99802))")
        cur.execute("DELETE FROM EmployeeMaster WHERE Emp_No IN (99801, 99802)")
        conn.commit()
        conn.close()

    def test_worker_and_staff_excel_import_and_update(self):
        # 1. Test Initial Excel Import
        df_insert = pd.DataFrame([
            {
                "Emp_No": "99801",
                "Employee_Name": "Unit Test Worker",
                "Category": "WORKER_PF_ESI",
                "Department": "Production",
                "Designation": "Operator",
                "Per_Day_Wage": 680.00,
                "PF_Eligible": "YES",
                "ESI_Eligible": "YES",
                "Status": "Active"
            },
            {
                "Emp_No": "99802",
                "Employee_Name": "Unit Test Staff",
                "Category": "STAFF_PF_ESI",
                "Department": "Management",
                "Designation": "Officer",
                "Fixed_Gross": 26000.00,
                "Basic": 7800.00,
                "DA": 5200.00,
                "HRA": 5200.00,
                "Conveyance_Allowance": 2600.00,
                "Washing_Allowance": 2600.00,
                "Other_Allowance": 2600.00,
                "PF_Eligible": "YES",
                "ESI_Eligible": "YES",
                "Status": "Active"
            }
        ])

        res_ins = bulk_import_employees(df_insert)
        self.assertEqual(res_ins['inserted'], 2)
        self.assertEqual(len(res_ins['errors']), 0)

        worker = get_employee_by_emp_no("99801")
        self.assertIsNotNone(worker)
        self.assertEqual(worker['Employee_Type'], 'WORKER')
        self.assertEqual(float(worker['Per_Day_Wage']), 680.00)
        self.assertEqual(float(worker['Fixed_Gross']), round(680.00 * 26.0, 2))
        self.assertEqual(float(worker['Basic_DA']), round(680.00 * 26.0 * 0.50, 2))

        staff = get_employee_by_emp_no("99802")
        self.assertIsNotNone(staff)
        self.assertEqual(staff['Employee_Type'], 'STAFF')
        self.assertEqual(float(staff['Fixed_Gross']), 26000.00)
        self.assertEqual(float(staff['Basic_DA']), 13000.00)
        self.assertEqual(float(staff['HRA']), 5200.00)

        # 2. Test Excel Update / Re-upload with changes
        df_update = pd.DataFrame([
            {
                "Emp_No": "99801",
                "Employee_Name": "Unit Test Worker",
                "Category": "WORKER_PF_ESI",
                "Department": "Production",
                "Designation": "Senior Operator",
                "Per_Day_Wage": 720.00,
                "PF_Eligible": "YES",
                "ESI_Eligible": "YES",
                "Status": "Active"
            },
            {
                "Emp_No": "99802",
                "Employee_Name": "Unit Test Staff",
                "Category": "STAFF_PF_ESI",
                "Department": "Management",
                "Designation": "Senior Officer",
                "Fixed_Gross": 32000.00,
                "Basic_DA": 16000.00,
                "HRA": 6400.00,
                "Conveyance_Allowance": 3200.00,
                "Washing_Allowance": 3200.00,
                "Other_Allowance": 3200.00,
                "PF_Eligible": "YES",
                "ESI_Eligible": "YES",
                "Status": "Active"
            }
        ])

        res_upd = bulk_import_employees(df_update)
        self.assertEqual(res_upd['updated'], 2)
        self.assertEqual(len(res_upd['errors']), 0)

        worker_upd = get_employee_by_emp_no("99801")
        self.assertEqual(float(worker_upd['Per_Day_Wage']), 720.00)
        self.assertEqual(float(worker_upd['Fixed_Gross']), round(720.00 * 26.0, 2))
        self.assertEqual(worker_upd['Designation'], 'Senior Operator')

        staff_upd = get_employee_by_emp_no("99802")
        self.assertEqual(float(staff_upd['Fixed_Gross']), 32000.00)
        self.assertEqual(float(staff_upd['Basic_DA']), 16000.00)
        self.assertEqual(float(staff_upd['HRA']), 6400.00)
        self.assertEqual(staff_upd['Designation'], 'Senior Officer')

if __name__ == '__main__':
    unittest.main()

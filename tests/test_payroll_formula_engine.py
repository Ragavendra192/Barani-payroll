import unittest
from services.payroll_formula_validator import validate_formula_syntax, detect_dependency_cycles, evaluate_formula
from services.payroll_formula_engine import test_category_formulas as run_category_formulas
from config import PAYROLL_FORMULA_ADMIN_PASSWORD

class TestPayrollFormulaEngine(unittest.TestCase):

    def test_01_admin_password_config(self):
        """Verify admin password setting."""
        self.assertEqual(PAYROLL_FORMULA_ADMIN_PASSWORD, "2882")

    def test_02_valid_formula_syntax(self):
        """Verify valid formula AST parsing."""
        is_val, msg, vars_found = validate_formula_syntax("Basic / Working_Days * Worked_Days")
        self.assertTrue(is_val)
        self.assertIn("BASIC", vars_found)
        self.assertIn("WORKING_DAYS", vars_found)
        self.assertIn("WORKED_DAYS", vars_found)

    def test_03_invalid_formula_syntax(self):
        """Verify invalid syntax detection."""
        is_val, msg, _ = validate_formula_syntax("Basic / * Working_Days")
        self.assertFalse(is_val)
        self.assertIn("Invalid formula syntax", msg)

    def test_04_unsafe_code_rejection(self):
        """Verify malicious or unsafe code is blocked."""
        is_val, msg, _ = validate_formula_syntax("__import__('os').system('dir')")
        self.assertFalse(is_val)
        self.assertTrue("Forbidden" in msg or "Unauthorized" in msg)

    def test_05_dependency_cycle_detection(self):
        """Verify circular dependency detection."""
        rules_cycle = {
            'A': 'B + 10',
            'B': 'A + 5'
        }
        has_cycle, msg = detect_dependency_cycles(rules_cycle)
        self.assertTrue(has_cycle)
        self.assertIn("Formula dependency cycle detected", msg)

        rules_valid = {
            'A': '10.0',
            'B': 'A + 5.0',
            'C': 'B * 2.0'
        }
        has_cycle_2, _ = detect_dependency_cycles(rules_valid)
        self.assertFalse(has_cycle_2)

    def test_06_evaluate_formula_math(self):
        """Verify formula evaluation math."""
        ctx = {'BASIC': 10000.0, 'WORKING_DAYS': 26.0, 'WORKED_DAYS': 26.0}
        res = evaluate_formula("Basic / Working_Days * Worked_Days", ctx)
        self.assertEqual(res, 10000.0)

        res_min = evaluate_formula("min(Basic * 0.80, 15000.0)", ctx)
        self.assertEqual(res_min, 8000.0)

        res_if = evaluate_formula("if_else(Basic > 5000, 100, 0)", ctx)
        self.assertEqual(res_if, 100.0)

    def test_07_category_formula_test_runner(self):
        """Verify test runner for WORKER_PF_ESI category."""
        sample = {
            'Per_Day_Wage': 900.0,
            'Working_Days': 26.0,
            'Present_Days': 25.0,
            'PH': 1.0,
            'OT_Hours': 10.0,
            'LIC': 250.0
        }
        res = run_category_formulas('WORKER_PF_ESI', sample)
        self.assertEqual(res['worked_days'], 26.0)
        self.assertEqual(res['earned_gross'], 24525.0) # (900*26 = 23400) + OT (10 * 112.5 = 1125)
        self.assertEqual(res['pf_gross'], 15000.0)
        self.assertEqual(res['pf_deduction'], 1800.0)

if __name__ == '__main__':
    unittest.main()

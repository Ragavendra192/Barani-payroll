"""
services/payroll_engine.py
Delegate module pointing directly to the single authoritative calculation engine:
utils/payroll_calculation_engine.py
"""

from utils.payroll_calculation_engine import (
    calculate_payroll,
    calculate_staff_pf_esi,
    calculate_worker_pf_esi,
    calculate_staff_naps,
    calculate_worker_naps,
    calculate_staff_non_pf_esi,
    calculate_worker_non_pf_esi,
    calculate_attendance,
    calculate_earned_salary,
    calculate_ot,
    calculate_pf,
    calculate_esi,
    calculate_deductions,
    money
)

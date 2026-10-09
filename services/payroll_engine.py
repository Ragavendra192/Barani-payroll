"""
services/payroll_engine.py
Direct delegate to the single authoritative central calculation engine:
payroll_formulas.py
"""

from payroll_formulas import (
    calculate_payroll,
    calculate_staff_pf_esi,
    calculate_worker_pf_esi,
    calculate_staff_naps,
    calculate_worker_naps,
    calculate_staff_non_pf_esi,
    calculate_worker_non_pf_esi,
    calculate_attendance,
    calculate_earned_salary,
    calculate_worker_ot as calculate_ot,
    calculate_deductions_package as calculate_deductions,
    money,
    round_half,
    to_dec,
    recalculate_for_category_transition,
    validate_payroll_result,
    resolve_category,
    excel_round,
    excel_roundup,
    excel_rounddown,
    STANDARD_WORKING_DAYS,
    STANDARD_WORKING_HOURS,
    PF_RATE,
    PF_CAP,
    ESI_EMPLOYEE_RATE,
    ESI_LIMIT,
    OT_MAX_HOURS,
    ALL_CANONICAL_CATEGORIES,
    CATEGORY_ALIASES,
)


"""
payroll_formulas.py
================================================================================
BHIPL PAYROLL SYSTEM — CENTRALIZED FORMULA ENGINE & CALCULATION AUTHORITY
================================================================================
Single authoritative source of truth for all verified BHIPL payroll formulas,
reconciled exactly against the manual September 2026 salary statement workbook:
'BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF Sep-2026 Final.xlsx'

Organized into 18 standardized sections:
1. Imports and decimal configuration
2. Payroll constants and category identifiers
3. Excel-compatible rounding helpers
4. Attendance calculations
5. Fixed salary component calculations
6. Earned salary component calculations
7. OT and SPL calculations
8. Staff PF/ESI formulas
9. Worker PF/ESI formulas
10. Staff NAPS formulas
11. Worker NAPS formulas
12. Staff Non-PF/ESI formulas
13. Worker Non-PF/ESI formulas
14. Deduction calculations
15. Advance and closing balance calculations
16. Total earnings, total deductions, and net salary
17. Category dispatcher
18. Payroll result validation & category transition
"""

# ==============================================================================
# 1. IMPORTS AND DECIMAL CONFIGURATION
# ==============================================================================
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN, getcontext
import math

# Ensure adequate precision for high-precision decimal operations
getcontext().prec = 32


# ==============================================================================
# 2. PAYROLL CONSTANTS AND CATEGORY IDENTIFIERS
# ==============================================================================
STANDARD_WORKING_DAYS = Decimal("26.0")
STANDARD_WORKING_HOURS = Decimal("8.0")

# Statutory PF constants
PF_RATE = Decimal("0.12")
PF_CAP = Decimal("15000.00")
PF_MAX_DEDUCTION = Decimal("1800.00")
PF_STAFF_GROSS_RATIO = Decimal("0.80")

# Statutory ESI constants
ESI_EMPLOYEE_RATE = Decimal("0.0075")
ESI_LIMIT = Decimal("21000.00")
ESI_FIXED_LIMIT = Decimal("21001.00")
ESI_STAFF_GROSS_RATIO = Decimal("0.90")
ESI_WORKER_GROSS_RATIO = Decimal("0.90")

# Overtime constants
OT_MAX_HOURS = Decimal("50.0")
OT_DIVISOR = Decimal("8.0")
DEFAULT_WORKER_OT_RATE = Decimal("56.25")

# Fixed salary structure split ratios
RATIO_BASIC_DA = Decimal("0.50")
RATIO_HRA = Decimal("0.20")
RATIO_CONV = Decimal("0.10")
RATIO_WASH = Decimal("0.10")
RATIO_OTHER = Decimal("0.10")

# Fixed Basic vs DA sub-split
RATIO_BASIC_SPLIT = Decimal("0.40")
RATIO_DA_SPLIT = Decimal("0.60")

# NAPS stipend deduction standard
NAPS_STANDARD_DEDUCTION = Decimal("1500.00")

# Canonical Category Identifiers
CAT_STAFF_PF_ESI = "STAFF_PF_ESI"
CAT_WORKER_PF_ESI = "WORKER_PF_ESI"
CAT_STAFF_NAPS = "STAFF_NAPS"
CAT_WORKER_NAPS = "WORKER_NAPS"
CAT_STAFF_NON_PF_ESI = "STAFF_NON_PF_ESI"
CAT_WORKER_NON_PF_ESI = "WORKER_NON_PF_ESI"

ALL_CANONICAL_CATEGORIES = (
    CAT_STAFF_PF_ESI,
    CAT_WORKER_PF_ESI,
    CAT_STAFF_NAPS,
    CAT_WORKER_NAPS,
    CAT_STAFF_NON_PF_ESI,
    CAT_WORKER_NON_PF_ESI
)

CATEGORY_ALIASES = {
    "STAFF_PF_ESI": CAT_STAFF_PF_ESI,
    "STAFF_EPF_ESI": CAT_STAFF_PF_ESI,
    "STAFF_PF": CAT_STAFF_PF_ESI,
    "STAFF": CAT_STAFF_PF_ESI,
    "STAFFS": CAT_STAFF_PF_ESI,

    "WORKER_PF_ESI": CAT_WORKER_PF_ESI,
    "WORKER_EPF_ESI": CAT_WORKER_PF_ESI,
    "WORKER_PF": CAT_WORKER_PF_ESI,
    "WORKER": CAT_WORKER_PF_ESI,
    "WORKERS": CAT_WORKER_PF_ESI,
    "WORKER'S - ESI PF": CAT_WORKER_PF_ESI,
    "WORKERS - ESI PF": CAT_WORKER_PF_ESI,

    "STAFF_NAPS": CAT_STAFF_NAPS,
    "STAFF'S (NAPS)": CAT_STAFF_NAPS,
    "STAFFS (NAPS)": CAT_STAFF_NAPS,

    "WORKER_NAPS": CAT_WORKER_NAPS,
    "WORKER'S (NAPS)": CAT_WORKER_NAPS,
    "WORKER'S (NAPS) (2)": CAT_WORKER_NAPS,
    "WORKERS (NAPS)": CAT_WORKER_NAPS,

    "STAFF_NON_PF_ESI": CAT_STAFF_NON_PF_ESI,
    "NON-PF ESI STAFF": CAT_STAFF_NON_PF_ESI,
    "NON_PF_ESI_STAFF": CAT_STAFF_NON_PF_ESI,
    "STAFF_NON_PF": CAT_STAFF_NON_PF_ESI,

    "WORKER_NON_PF_ESI": CAT_WORKER_NON_PF_ESI,
    "NON-PF ESI WORKER": CAT_WORKER_NON_PF_ESI,
    "NON_PF_ESI_WORKER": CAT_WORKER_NON_PF_ESI,
    "WORKER_NON_PF": CAT_WORKER_NON_PF_ESI,
}


# ==============================================================================
# 3. EXCEL-COMPATIBLE ROUNDING HELPERS
# ==============================================================================
def to_dec(val, default="0.0") -> Decimal:
    """Convert value to Decimal preserving full precision, safely handling None/NaN/empty."""
    if val is None:
        return Decimal(str(default))
    if isinstance(val, Decimal):
        return val
    try:
        s = str(val).strip()
        if not s or s.lower() in ("nan", "none", "null", ""):
            return Decimal(str(default))
        return Decimal(s)
    except Exception:
        return Decimal(str(default))

def money(val) -> Decimal:
    """Convert monetary value to Decimal rounded to 2 decimal places with ROUND_HALF_UP."""
    d = to_dec(val, "0.00")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def round_half(val) -> Decimal:
    """Round value to nearest integer with >= 0.50 rounding up, returning Decimal with .00 precision."""
    d = to_dec(val, "0.00")
    return d.quantize(Decimal("1"), rounding=ROUND_HALF_UP).quantize(Decimal("0.01"))

def excel_round(val, decimals: int = 0) -> Decimal:
    """
    Excel =ROUND(val, n) implementation.
    Uses ROUND_HALF_UP away from zero matching Excel floating-point evaluation.
    """
    d = to_dec(val, "0.0")
    target = Decimal("1") if decimals == 0 else Decimal("10") ** -decimals
    return d.quantize(target, rounding=ROUND_HALF_UP)

def excel_roundup(val, decimals: int = 0) -> Decimal:
    """Excel =ROUNDUP(val, n) implementation using ROUND_UP away from zero."""
    d = to_dec(val, "0.0")
    target = Decimal("1") if decimals == 0 else Decimal("10") ** -decimals
    return d.quantize(target, rounding=ROUND_UP)

def excel_rounddown(val, decimals: int = 0) -> Decimal:
    """Excel =ROUNDDOWN(val, n) implementation using ROUND_DOWN towards zero."""
    d = to_dec(val, "0.0")
    target = Decimal("1") if decimals == 0 else Decimal("10") ** -decimals
    return d.quantize(target, rounding=ROUND_DOWN)


# ==============================================================================
# 4. ATTENDANCE CALCULATIONS
# ==============================================================================
def calculate_attendance(att_dict, is_worker: bool = False, standard_days=26.0, deduct_lop: bool = False):
    """
    Authoritative Attendance & Leave Calculator.
    Total_Worked_Days = Present_Days + N/H + EL + C-Off (Staff) + CL + SL
    LOP_Days = max(0.0, Standard_Working_Days - Total_Worked_Days)
    
    Guarantees:
    - Checks explicitly for None rather than using truthy 'or', so 0.0 present days
      never fall back to standard working days.
    """
    if att_dict is None:
        att_dict = {}

    # Extract present days with strict None-check
    pres_val = att_dict.get('present_days')
    if pres_val is None:
        pres_val = att_dict.get('Present_Days')
    if pres_val is None:
        pres_val = att_dict.get('Present')
    if pres_val is None:
        pres_val = att_dict.get('PRES')
    present_days = to_dec(pres_val if pres_val is not None else '0.0', '0.0')

    # National Holiday (N/H or PH)
    nh_val = att_dict.get('nh')
    if nh_val is None:
        nh_val = att_dict.get('NH')
    if nh_val is None:
        nh_val = att_dict.get('ph')
    if nh_val is None:
        nh_val = att_dict.get('PH')
    if nh_val is None:
        nh_val = att_dict.get('Normal_Holiday')
    nh = to_dec(nh_val if nh_val is not None else '0.0', '0.0')

    # Casual Leave (CL)
    cl_val = att_dict.get('cl')
    if cl_val is None:
        cl_val = att_dict.get('CL')
    cl = to_dec(cl_val if cl_val is not None else '0.0', '0.0')

    # Sick Leave (SL)
    sl_val = att_dict.get('sl')
    if sl_val is None:
        sl_val = att_dict.get('SL')
    sl = to_dec(sl_val if sl_val is not None else '0.0', '0.0')

    # Earned Leave / Privilege Leave (EL / PL)
    el_val = att_dict.get('el')
    if el_val is None:
        el_val = att_dict.get('EL')
    if el_val is None:
        el_val = att_dict.get('pl')
    if el_val is None:
        el_val = att_dict.get('PL')
    el = to_dec(el_val if el_val is not None else '0.0', '0.0')

    # Comp-Off (Staff Only)
    coff_val = att_dict.get('c_off')
    if coff_val is None:
        coff_val = att_dict.get('C_Off')
    if coff_val is None:
        coff_val = att_dict.get('coff')
    if coff_val is None:
        coff_val = att_dict.get('COff')
    if coff_val is None:
        coff_val = att_dict.get('comp_off')
    if coff_val is None:
        coff_val = att_dict.get('ch')
    if coff_val is None:
        coff_val = att_dict.get('C_H')
    coff = to_dec(coff_val if coff_val is not None else '0.0', '0.0') if not is_worker else Decimal('0.0')

    std_days_dec = to_dec(standard_days, '26.0')

    # Total days calculation or explicit override
    tot_val = att_dict.get('total_days')
    if tot_val is None:
        tot_val = att_dict.get('Total_Days')
    if tot_val is None:
        tot_val = att_dict.get('Total_Worked_Days')
    if tot_val is not None and str(tot_val).strip() != '':
        total_worked_days = to_dec(tot_val, '0.0')
    else:
        total_worked_days = present_days + nh + cl + sl + el + coff

    raw_lop = std_days_dec - total_worked_days
    lop_days = max(Decimal('0.0'), raw_lop)

    return {
        'present_days': float(present_days),
        'present_days_dec': present_days,
        'nh': float(nh),
        'nh_dec': nh,
        'ph': float(nh),
        'cl': float(cl),
        'cl_dec': cl,
        'sl': float(sl),
        'sl_dec': sl,
        'el': float(el),
        'el_dec': el,
        'pl': float(el),
        'c_off': float(coff),
        'c_off_dec': coff,
        'total_worked_days': float(total_worked_days),
        'total_days_dec': total_worked_days,
        'lop_days': float(lop_days),
        'lop_days_dec': lop_days,
        'standard_days': float(std_days_dec),
        'standard_days_dec': std_days_dec
    }


# ==============================================================================
# 5. FIXED SALARY COMPONENT CALCULATIONS
# ==============================================================================
def calculate_staff_fixed_salary(salary_dict):
    """
    Staff Fixed Salary Component Breakdown (50% Basic+DA, 20% HRA, 10% Conv, 10% Wash, 10% Other).
    Reconciles exactly with Staff columns U, V, W, X, Y, Z.
    """
    if salary_dict is None:
        salary_dict = {}

    fixed_gross = to_dec(
        salary_dict.get('Fixed_Gross') or salary_dict.get('Gross_Wages') or
        salary_dict.get('Base_Gross') or salary_dict.get('fixed_gross') or '0.00'
    )

    fixed_bda = to_dec(salary_dict.get('Basic_DA') or salary_dict.get('Fixed_Basic_DA'))
    fixed_hra = to_dec(salary_dict.get('HRA') or salary_dict.get('Fixed_HRA'))
    fixed_conv = to_dec(salary_dict.get('Conveyance_Allowance') or salary_dict.get('Fixed_Conveyance'))
    fixed_wash = to_dec(salary_dict.get('Washing_Allowance') or salary_dict.get('Fixed_Washing'))
    fixed_other = to_dec(salary_dict.get('Other_Allowance') or salary_dict.get('Fixed_Other'))
    fixed_spl = to_dec(salary_dict.get('Special_Allowance') or salary_dict.get('Fixed_Special') or '0.00')

    # If components are zero but Fixed Gross is present, apply exact standard formula split
    if (fixed_bda + fixed_hra + fixed_conv + fixed_wash + fixed_other) == Decimal('0.00') and fixed_gross > Decimal('0.00'):
        fixed_bda = fixed_gross * RATIO_BASIC_DA
        fixed_hra = fixed_gross * RATIO_HRA
        fixed_conv = fixed_gross * RATIO_CONV
        fixed_wash = fixed_gross * RATIO_WASH
        fixed_other = fixed_gross * RATIO_OTHER

    if fixed_gross == Decimal('0.00'):
        fixed_gross = fixed_bda + fixed_hra + fixed_conv + fixed_wash + fixed_other + fixed_spl

    return {
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_bda,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl
    }

def calculate_worker_fixed_salary(salary_dict, standard_days_dec=STANDARD_WORKING_DAYS):
    """
    Worker Fixed Salary Component Breakdown:
    Fixed Gross = Per Day Wage * Standard Days (Col AH = AA * 26)
    50% Basic+DA, 20% HRA, 10% Conv, 10% Wash, 10% Other.
    """
    if salary_dict is None:
        salary_dict = {}

    pdw = to_dec(salary_dict.get('Per_Day_Wage') or salary_dict.get('per_day_wage') or '0.00')
    if pdw > Decimal('0.00'):
        fixed_gross = pdw * standard_days_dec
    else:
        fixed_gross = to_dec(
            salary_dict.get('Fixed_Gross') or salary_dict.get('Gross_Wages') or
            salary_dict.get('Base_Gross') or '0.00'
        )
        if standard_days_dec > Decimal('0.00'):
            pdw = fixed_gross / standard_days_dec

    fixed_bda = fixed_gross * RATIO_BASIC_DA
    fixed_hra = fixed_gross * RATIO_HRA
    fixed_conv = fixed_gross * RATIO_CONV
    fixed_wash = fixed_gross * RATIO_WASH
    fixed_other = fixed_gross * RATIO_OTHER

    return {
        'per_day_wage': pdw,
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_bda,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': Decimal('0.00')
    }


# ==============================================================================
# 6. EARNED SALARY COMPONENT CALCULATIONS
# ==============================================================================
def calculate_earned_salary(fixed_comp_dec: Decimal, worked_days_dec: Decimal, standard_days_dec: Decimal) -> Decimal:
    """
    Prorated earned component calculation preserving full Decimal precision:
    =+Fixed_Comp / Standard_Days * Worked_Days
    """
    if standard_days_dec <= Decimal('0.00'):
        return Decimal('0.00')
    return (fixed_comp_dec * worked_days_dec) / standard_days_dec


# ==============================================================================
# 7. OT AND SPL CALCULATIONS
# ==============================================================================
def calculate_worker_ot(act_ot_hours, per_day_wage_dec: Decimal, ot_rate_override=None):
    """
    Worker Overtime and Special Overtime Wages Calculator:
    - OT Rate = Per Day Wage / 8 (Col AG = AA / 8)
    - Capped OT (W) = min(Act_OT_Hrs, 50.0)
    - Spl OT (X) = max(0.0, Act_OT_Hrs - 50.0)
    - OT Wages (AO) = Capped OT * OT Rate (SUM(W * AG))
    - Spl Allow (AN) = Spl OT * OT Rate (SUM(X * AG))
    """
    act_ot_dec = to_dec(act_ot_hours, '0.0')

    if per_day_wage_dec > Decimal('0.00'):
        ot_rate = per_day_wage_dec / OT_DIVISOR
    elif ot_rate_override is not None and float(ot_rate_override) > 0:
        ot_rate = to_dec(ot_rate_override, '56.25')
    else:
        ot_rate = DEFAULT_WORKER_OT_RATE

    if act_ot_dec <= OT_MAX_HOURS:
        capped_ot = act_ot_dec
        spl_ot = Decimal('0.00')
    else:
        capped_ot = OT_MAX_HOURS
        spl_ot = act_ot_dec - OT_MAX_HOURS

    ot_wages = capped_ot * ot_rate
    spl_allow = spl_ot * ot_rate

    return {
        'act_ot_hours': act_ot_dec,
        'capped_ot_hours': capped_ot,
        'spl_ot_hours': spl_ot,
        'ot_hours_half': capped_ot / Decimal('2.0'),
        'ot_rate': ot_rate,
        'ot_wages': ot_wages,
        'spl_allow': spl_allow
    }


# ==============================================================================
# 8. STAFF PF/ESI FORMULAS (CATEGORY 1)
# ==============================================================================
def calculate_staff_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 1: STAFF_PF_ESI (Sheet 'STAFFS')
    
    Verified Formulas:
    - Fixed: 50% Basic+DA, 20% HRA, 10% Conv, 10% Wash, 10% Other
    - Earned Components: =+Fixed / Standard_Days * Worked_Days (Cols AA:AE)
    - Earned Gross: AF = SUM(AA:AE)
    - PF Gross: AG = IF(AF * 80% >= 15000, 15000, AF * 80%)
    - ESI Gross: AH = IF(AF > 21000, 0, AF * 90%)
      * Reconciled with Emp #1014: ESI Gross is calculated whenever AF <= 21000,
        regardless of Fixed Gross.
    - PF Dedn: AI = IF(AG > 15000, 1800, AG * 12%)
    - ESI Dedn: AJ = ROUNDUP(IF(Fixed_Gross > 21001, 0, AH * 0.75%), 0)
    - Total Dedn: AO = SUM(AI:AN)
    - Net Salary: AP = AF - AO + Arrears
    """
    att = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    f_sal = calculate_staff_fixed_salary(salary)
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = calculate_earned_salary(f_sal['fixed_spl'], worked_days, std_days)

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other + e_spl

    # Statutory calculations
    pf_eligible = bool(salary.get('PF_Eligible', True)) if salary else True
    esi_eligible = bool(salary.get('ESI_Eligible', True)) if salary else True

    # PF Gross & Deduction
    if pf_eligible:
        raw_pf_gross = earned_gross * PF_STAFF_GROSS_RATIO
        pf_gross = min(raw_pf_gross, PF_CAP) if raw_pf_gross >= Decimal('0.00') else Decimal('0.00')
        pf_ded = min(pf_gross * PF_RATE, PF_MAX_DEDUCTION)
        acc_pf_ded = PF_MAX_DEDUCTION if pf_gross >= PF_CAP else pf_ded
    else:
        pf_gross = Decimal('0.00')
        pf_ded = Decimal('0.00')
        acc_pf_ded = Decimal('0.00')

    # ESI Gross & Deduction
    # Reconciled: ESI Gross checks if earned_gross <= 21000
    if esi_eligible and earned_gross <= ESI_LIMIT:
        esi_gross = earned_gross * ESI_STAFF_GROSS_RATIO
    else:
        esi_gross = Decimal('0.00')

    # ESI Deduction checks if Fixed Gross <= 21001
    if esi_eligible and f_sal['fixed_gross'] <= ESI_FIXED_LIMIT and esi_gross > Decimal('0.00'):
        raw_esi_ded = esi_gross * ESI_EMPLOYEE_RATE
        esi_ded = excel_roundup(raw_esi_ded, 0)
    else:
        esi_ded = Decimal('0.00')
    acc_esi_ded = esi_ded

    # Deductions
    ded_info = calculate_deductions_package(
        deductions, pf_ded, esi_ded, acc_pf_ded, acc_esi_ded,
        is_worker=False, default_naps=Decimal('0.00')
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    net_salary = earned_gross_total - ded_info['total_ded']

    ot_info = {
        'act_ot_hours': Decimal('0.00'), 'capped_ot_hours': Decimal('0.00'),
        'spl_ot_hours': Decimal('0.00'), 'ot_rate': Decimal('0.00'),
        'ot_wages': Decimal('0.00'), 'spl_allow': Decimal('0.00')
    }

    return assemble_payroll_result(
        emp, CAT_STAFF_PF_ESI, "STAFF", "PF_ESI", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, pf_gross, pf_ded, acc_pf_ded, esi_gross, esi_ded, acc_esi_ded,
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 9. WORKER PF/ESI FORMULAS (CATEGORY 2)
# ==============================================================================
def calculate_worker_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 2: WORKER_PF_ESI (Sheet 'WORKER\\'S - ESI PF')
    
    Verified Formulas:
    - Fixed Gross: AH = Per Day Wage * 26
    - OT Rate: AG = Per Day Wage / 8
    - Spl Allow: AN = Spl OT * OT Rate
    - OT Wages: AO = Capped OT * OT Rate
    - Earned Gross: AP = SUM(AI:AO)
    - Gross - OT: AQ = AP - AO
    - PF Gross: AR = IF((AP - AJ - AO) >= 15000, 15000, (AP - AJ - AO))
      (Earned Gross - Earned HRA - OT Wages)
    - ESI Gross: AS = IF(AH > 21000, 0, IF((AP * 90%) > 21000, 21000, AP * 90%))
    - PF Dedn: AU = AR * 12%
    - ESI Dedn: AV = AS * 0.75% (unrounded precision in manual sheet)
    - Total Dedn: BA = SUM(AU:AZ)
    - Net Salary: BB = AP - BA + Arrears
    """
    att = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    f_sal = calculate_worker_fixed_salary(salary, att['standard_days_dec'])
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    # Prorated earnings
    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = Decimal('0.00')

    # OT calculations
    act_ot = attendance.get('actual_ot_hours') or attendance.get('act_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_Hrs') if attendance else 0.0
    ot_info = calculate_worker_ot(act_ot, f_sal['per_day_wage'], salary.get('OT_Rate') if salary else None)

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other + ot_info['ot_wages'] + ot_info['spl_allow']

    # Statutory calculations
    pf_eligible = bool(salary.get('PF_Eligible', True)) if salary else True
    esi_eligible = bool(salary.get('ESI_Eligible', True)) if salary else True

    # PF Gross: Earned Gross - Earned HRA - OT Wages
    if pf_eligible:
        raw_pf_basis = earned_gross - e_hra - ot_info['ot_wages']
        pf_gross = min(raw_pf_basis, PF_CAP) if raw_pf_basis >= Decimal('0.00') else Decimal('0.00')
        pf_ded = min(pf_gross * PF_RATE, PF_MAX_DEDUCTION)
        acc_pf_ded = PF_MAX_DEDUCTION if pf_gross >= PF_CAP else pf_ded
    else:
        pf_gross = Decimal('0.00')
        pf_ded = Decimal('0.00')
        acc_pf_ded = Decimal('0.00')

    # ESI Gross: IF Fixed Gross > 21000 -> 0; else min(Earned Gross * 90%, 21000)
    if esi_eligible and f_sal['fixed_gross'] <= ESI_LIMIT:
        raw_esi_gross = earned_gross * ESI_WORKER_GROSS_RATIO
        esi_gross = min(raw_esi_gross, ESI_LIMIT) if raw_esi_gross >= Decimal('0.00') else Decimal('0.00')
        esi_ded = esi_gross * ESI_EMPLOYEE_RATE
    else:
        esi_gross = Decimal('0.00')
        esi_ded = Decimal('0.00')
    acc_esi_ded = esi_ded

    # Deductions
    ded_info = calculate_deductions_package(
        deductions, pf_ded, esi_ded, acc_pf_ded, acc_esi_ded,
        is_worker=True, default_naps=Decimal('0.00')
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    net_salary = earned_gross_total - ded_info['total_ded']

    return assemble_payroll_result(
        emp, CAT_WORKER_PF_ESI, "WORKER", "PF_ESI", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, pf_gross, pf_ded, acc_pf_ded, esi_gross, esi_ded, acc_esi_ded,
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 10. STAFF NAPS FORMULAS (CATEGORY 3)
# ==============================================================================
def calculate_staff_naps(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 3: STAFF_NAPS (Sheet 'STAFF\\'S (NAPS)')
    
    Verified Formulas:
    - Fixed Gross: AE
    - Earned Components: Prorated by worked_days / standard_days
    - Earned Gross: AM = SUM(AF:AL)
    - Statutory: PF = 0, ESI = 0
    - NAPS Deduction: AO = 1500 standard
    - Total Dedn: AS = SUM(AO:AR)
    - Net Salary: AT = AM - AS + Arrears
    """
    att = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    f_sal = calculate_staff_fixed_salary(salary)
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = Decimal('0.00')

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other

    # Deductions: PF=0, ESI=0, NAPS=1500 default
    ded_info = calculate_deductions_package(
        deductions, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        is_worker=False, default_naps=NAPS_STANDARD_DEDUCTION
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    net_salary = earned_gross_total - ded_info['total_ded']

    ot_info = {
        'act_ot_hours': Decimal('0.00'), 'capped_ot_hours': Decimal('0.00'),
        'spl_ot_hours': Decimal('0.00'), 'ot_rate': Decimal('0.00'),
        'ot_wages': Decimal('0.00'), 'spl_allow': Decimal('0.00')
    }

    return assemble_payroll_result(
        emp, CAT_STAFF_NAPS, "STAFF", "NAPS", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 11. WORKER NAPS FORMULAS (CATEGORY 4)
# ==============================================================================
def calculate_worker_naps(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 4: WORKER_NAPS (Sheet 'WORKER\\'S (NAPS) (2)')
    
    Verified Formulas:
    - Fixed Gross: AE = Per Day Wage * 26
    - OT & Spl: OT Wages (AL), Spl Allow (AK)
    - Earned Gross: AM = SUM(AF:AL)
    - Statutory: PF = 0, ESI = 0
    - NAPS Deduction: AO = 1500 standard
    - Total Dedn: AS = SUM(AO:AR)
    - Net Salary: AT = AM - AS + Arrears
    """
    att = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    f_sal = calculate_worker_fixed_salary(salary, att['standard_days_dec'])
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = Decimal('0.00')

    act_ot = attendance.get('actual_ot_hours') or attendance.get('act_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_Hrs') if attendance else 0.0
    ot_info = calculate_worker_ot(act_ot, f_sal['per_day_wage'], salary.get('OT_Rate') if salary else None)

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other + ot_info['ot_wages'] + ot_info['spl_allow']

    # Deductions: PF=0, ESI=0, NAPS=1500 default
    ded_info = calculate_deductions_package(
        deductions, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        is_worker=True, default_naps=NAPS_STANDARD_DEDUCTION
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    net_salary = earned_gross_total - ded_info['total_ded']

    return assemble_payroll_result(
        emp, CAT_WORKER_NAPS, "WORKER", "NAPS", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 12. STAFF NON-PF/ESI FORMULAS (CATEGORY 5)
# ==============================================================================
def calculate_staff_non_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 5: STAFF_NON_PF_ESI (Sheet 'Non-pf ESi staff')
    
    Verified Formulas:
    - Reconciled with Emp #1094 (S.MADHESWARAN): Total Days = 13, Gross = 7500, Net = 7500
    - Fixed Gross: AE
    - Earned Components: Prorated by worked_days / standard_days
    - Earned Gross: AM = SUM(AF:AL)
    - Statutory: PF = 0, ESI = 0, NAPS = 0
    - Total Dedn: AS = SUM(AO:AR)
    - Net Salary: AT = AM - AS + Arrears
    """
    att = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    f_sal = calculate_staff_fixed_salary(salary)
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = Decimal('0.00')

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other

    # Deductions: PF=0, ESI=0, NAPS=0
    ded_info = calculate_deductions_package(
        deductions, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        is_worker=False, default_naps=Decimal('0.00')
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    net_salary = earned_gross_total - ded_info['total_ded']

    ot_info = {
        'act_ot_hours': Decimal('0.00'), 'capped_ot_hours': Decimal('0.00'),
        'spl_ot_hours': Decimal('0.00'), 'ot_rate': Decimal('0.00'),
        'ot_wages': Decimal('0.00'), 'spl_allow': Decimal('0.00')
    }

    return assemble_payroll_result(
        emp, CAT_STAFF_NON_PF_ESI, "STAFF", "NON_PF_ESI", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 13. WORKER NON-PF/ESI FORMULAS (CATEGORY 6)
# ==============================================================================
def calculate_worker_non_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Category 6: WORKER_NON_PF_ESI (Sheet 'Non-pf ESi worker')
    
    Verified Formulas:
    - Reconciled with Emp #10041 (D.JESU BALAN):
      * Earned Gross: 33238.875
      * Total Dedn: 1000
      * NET Salary Formula: =ROUND(AM5-AS5, 0) -> exactly 32239
    - Fixed Gross: AE = Per Day Wage * 26
    - OT Wages + Spl Allow based on Act OT Hrs
    - Statutory: PF = 0, ESI = 0, NAPS = 0
    - Total Dedn: AS = Advance + LIC + Accomdn + Other
    - Net Salary: AT = excel_round(Earned_Gross - Total_Dedn + Arrears, 0)
    """
    att = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    f_sal = calculate_worker_fixed_salary(salary, att['standard_days_dec'])
    std_days = att['standard_days_dec']
    worked_days = att['total_days_dec']

    e_bda = calculate_earned_salary(f_sal['fixed_basic_da'], worked_days, std_days)
    e_hra = calculate_earned_salary(f_sal['fixed_hra'], worked_days, std_days)
    e_conv = calculate_earned_salary(f_sal['fixed_conv'], worked_days, std_days)
    e_wash = calculate_earned_salary(f_sal['fixed_wash'], worked_days, std_days)
    e_other = calculate_earned_salary(f_sal['fixed_other'], worked_days, std_days)
    e_spl = Decimal('0.00')

    act_ot = attendance.get('actual_ot_hours') or attendance.get('act_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_Hrs') if attendance else 0.0
    ot_info = calculate_worker_ot(act_ot, f_sal['per_day_wage'], salary.get('OT_Rate') if salary else None)

    earned_gross = e_bda + e_hra + e_conv + e_wash + e_other + ot_info['ot_wages'] + ot_info['spl_allow']

    # Deductions: PF=0, ESI=0, NAPS=0
    ded_info = calculate_deductions_package(
        deductions, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        is_worker=True, default_naps=Decimal('0.00')
    )

    arrears = to_dec(deductions.get('arrears') or deductions.get('Arrears') if deductions else 0.0)
    earned_gross_total = earned_gross + arrears
    raw_net = earned_gross_total - ded_info['total_ded']

    # Verified: Sheet explicitly applies =ROUND(AM5-AS5, 0)
    net_salary = excel_round(raw_net, 0)

    return assemble_payroll_result(
        emp, CAT_WORKER_NON_PF_ESI, "WORKER", "NON_PF_ESI", att, f_sal,
        e_bda, e_hra, e_conv, e_wash, e_other, e_spl, earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_salary
    )


# ==============================================================================
# 14. DEDUCTION CALCULATIONS
# ==============================================================================
def calculate_deductions_package(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi, is_worker: bool = False, default_naps: Decimal = Decimal('0.00')):
    """
    Unified Deduction Package Calculator for All Categories.
    Extracts all standard & manual deduction items and advance tracking fields.
    """
    if ded_dict is None:
        ded_dict = {}

    pt = money(ded_dict.get('pt') or ded_dict.get('PT') or 0.0)
    mess = money(ded_dict.get('mess') or ded_dict.get('Mess') or 0.0)
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC') or 0.0)
    tds = money(ded_dict.get('tds') or ded_dict.get('TDS') or 0.0)
    advance = money(ded_dict.get('advance') or ded_dict.get('Advance') or ded_dict.get('Advance_Deduction') or 0.0)
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation') or ded_dict.get('Accomdation') or ded_dict.get('Accomdn') or 0.0)
    other = money(ded_dict.get('other') or ded_dict.get('Other') or ded_dict.get('Other_Deduction') or 0.0)

    # NAPS deduction handling
    naps_raw = ded_dict.get('naps') or ded_dict.get('NAPS') or ded_dict.get('NATS')
    if naps_raw is not None and str(naps_raw).strip() != '':
        naps = money(naps_raw)
    else:
        naps = default_naps

    total_ded = pf_ded + esi_ded + pt + mess + lic + tds + naps + advance + accom + other

    # Advance Tracking
    op_adv, nw_adv, inst, cl_adv = calculate_advance_tracking(ded_dict, advance)

    return {
        'pf_ded': pf_ded,
        'accounts_pf_ded': acc_pf,
        'esi_ded': esi_ded,
        'accounts_esi_ded': acc_esi,
        'pt': pt,
        'mess': mess,
        'lic': lic,
        'tds': tds,
        'naps': naps,
        'advance': advance,
        'accom': accom,
        'other': other,
        'total_ded': total_ded,
        'opening_adv': op_adv,
        'new_adv': nw_adv,
        'installment': inst,
        'closing_adv': cl_adv
    }


# ==============================================================================
# 15. ADVANCE AND CLOSING BALANCE CALCULATIONS
# ==============================================================================
def calculate_advance_tracking(ded_dict, advance_ded: Decimal):
    """
    Advance Tracking Calculator Reconciled with Excel Columns:
    - New Advance (BD / AV)
    - Installment / Prior Balance (BE / AW)
    - Opening Advance (BF / AX = BD + BE)
    - Closing Advance (BG / AY = max(0, Opening_Advance - Advance_Deduction))
    """
    if ded_dict is None:
        ded_dict = {}

    nw_adv = money(ded_dict.get('new_adv') or ded_dict.get('New_Advance') or ded_dict.get('New Adv') or 0.0)
    inst_input = ded_dict.get('installment') or ded_dict.get('Installment') or ded_dict.get('Installment_Amount')
    op_adv_input = ded_dict.get('opening_adv') or ded_dict.get('Opening_Advance') or ded_dict.get('Opening Adv')

    if inst_input is not None and str(inst_input).strip() != '':
        installment = money(inst_input)
        if op_adv_input is not None and str(op_adv_input).strip() != '':
            op_adv = money(op_adv_input)
        else:
            op_adv = nw_adv + installment
    else:
        op_adv = money(op_adv_input or 0.0)
        installment = max(Decimal('0.00'), op_adv - nw_adv)

    raw_closing = ded_dict.get('closing_adv') or ded_dict.get('Closing_Advance') or ded_dict.get('Closing Adv')
    if raw_closing is not None and str(raw_closing).strip() != '':
        cl_adv = money(raw_closing)
    else:
        cl_adv = max(Decimal('0.00'), op_adv - advance_ded)

    return op_adv, nw_adv, installment, cl_adv


# ==============================================================================
# 16. TOTAL EARNINGS, TOTAL DEDUCTIONS, AND NET SALARY
# ==============================================================================
def assemble_payroll_result(emp, category: str, emp_type: str, pay_cat: str,
                            att_info, f_sal,
                            e_basic: Decimal, e_hra: Decimal, e_conv: Decimal,
                            e_wash: Decimal, e_other: Decimal, e_spl: Decimal,
                            e_gross_total: Decimal,
                            ot_info,
                            pf_gross: Decimal, pf_ded: Decimal, acc_pf_ded: Decimal,
                            esi_gross: Decimal, esi_ded: Decimal, acc_esi_ded: Decimal,
                            arrears: Decimal, ded_info, net_salary: Decimal):
    """
    Assembles comprehensive authoritative payroll dictionary.
    Includes both high-precision Decimals and standard float outputs for schema compatibility.
    """
    if emp is None:
        emp = {}

    emp_id = emp.get('Employee_ID') or emp.get('Emp_ID') or emp.get('id')
    emp_no = emp.get('Emp_No') or emp.get('ERP_Emp_No') or emp.get('emp_no') or emp.get('Emp_Code')
    name = emp.get('Employee_Name') or emp.get('Emp_Name') or emp.get('Name') or ''

    std_days_dec = att_info['standard_days_dec']
    lop_days_dec = att_info['lop_days_dec']

    if emp_type == 'STAFF':
        per_day_salary = (f_sal['fixed_gross'] / std_days_dec) if std_days_dec > Decimal('0.0') else Decimal('0.00')
    else:
        per_day_salary = f_sal.get('per_day_wage', Decimal('0.00'))

    lop_deduction = per_day_salary * lop_days_dec

    earned_basic_split = e_basic * RATIO_BASIC_SPLIT
    earned_da_split = e_basic * RATIO_DA_SPLIT

    return {
        'Employee_ID': emp_id,
        'Emp_No': emp_no,
        'Emp_Code': emp_no,
        'Name': name,
        'Employee_Name': name,
        'Category': category,
        'Employee_Type': emp_type,
        'Payroll_Category': pay_cat,

        # Attendance & LOP
        'Present_Days': att_info['present_days'],
        'PH': att_info['nh'],
        'NH': att_info['nh'],
        'CL': att_info['cl'],
        'SL': att_info['sl'],
        'PL': att_info['el'],
        'EL': att_info['el'],
        'C_Off': att_info['c_off'],
        'c_off': att_info['c_off'],
        'Total_Worked_Days': att_info['total_worked_days'],
        'Worked_Days': att_info['total_worked_days'],
        'Total_Days': att_info['total_worked_days'],
        'Working_Days': float(std_days_dec),
        'LOP_Days': att_info['lop_days'],
        'Per_Day_Salary': float(per_day_salary),
        'LOP_Deduction': float(lop_deduction),

        # Fixed Salary Structure
        'Per_Day_Wage': float(f_sal.get('per_day_wage', Decimal('0.00'))),
        'Fixed_Gross': float(f_sal['fixed_gross']),
        'Fixed_Basic_DA': float(f_sal['fixed_basic_da']),
        'Fixed_HRA': float(f_sal['fixed_hra']),
        'Fixed_Conveyance': float(f_sal['fixed_conv']),
        'Fixed_Washing': float(f_sal['fixed_wash']),
        'Fixed_Other': float(f_sal['fixed_other']),
        'Fixed_Special': float(f_sal['fixed_spl']),

        # Earned Salary Components
        'Earned_Basic_DA': float(e_basic),
        'Basic_DA_Earned': float(e_basic),
        'Earned_Basic': float(earned_basic_split),
        'Earned_DA': float(earned_da_split),
        'Earned_HRA': float(e_hra),
        'HRA_Earned': float(e_hra),
        'Earned_Conveyance': float(e_conv),
        'Conveyance_Earned': float(e_conv),
        'Earned_Washing': float(e_wash),
        'Washing_Allowance_Earned': float(e_wash),
        'Earned_Other': float(e_other),
        'Other_Allowance_Earned': float(e_other),
        'Earned_Special': float(e_spl),
        'Special_Allowance_Earned': float(e_spl),
        'Gross_Wages': float(e_gross_total),
        'Earned_Gross': float(e_gross_total),

        # Overtime & Special OT
        'Act_OT_Hrs': float(ot_info['act_ot_hours']),
        'OT_Hours': float(ot_info['capped_ot_hours']),
        'Special_OT_Hours': float(ot_info['spl_ot_hours']),
        'OT_Rate': float(ot_info['ot_rate']),
        'OT_Wages': float(ot_info['ot_wages']),
        'Special_OT_Amount': float(ot_info['spl_allow']),

        # Statutory Bases & Deductions
        'PF_Gross': float(pf_gross),
        'PF_Deduction': float(pf_ded),
        'Accounts_PF_Deduction': float(acc_pf_ded),
        'ESI_Gross': float(esi_gross),
        'ESI_Deduction': float(esi_ded),
        'Accounts_ESI_Deduction': float(acc_esi_ded),

        # Deductions & Net Pay
        'PT_Deduction': float(ded_info['pt']),
        'Mess_Deduction': float(ded_info['mess']),
        'LIC_Deduction': float(ded_info['lic']),
        'TDS_Deduction': float(ded_info['tds']),
        'NAPS_Deduction': float(ded_info['naps']),
        'Advance_Deduction': float(ded_info['advance']),
        'Accommodation_Deduction': float(ded_info['accom']),
        'Other_Deduction': float(ded_info['other']),
        'Arrears': float(arrears),
        'Total_Deduction': float(ded_info['total_ded']),
        'Net_Salary': float(net_salary),
        'Net_Pay': float(net_salary),

        # Advance Tracking
        'Opening_Advance': float(ded_info['opening_adv']),
        'New_Advance': float(ded_info['new_adv']),
        'Installment': float(ded_info['installment']),
        'Closing_Advance': float(ded_info['closing_adv']),

        # Exact Decimal representations for high-precision audit/downstream
        'Gross_Wages_dec': e_gross_total,
        'Earned_Gross_dec': e_gross_total,
        'Net_Salary_dec': net_salary,
        'Net_Pay_dec': net_salary,
        'Total_Deduction_dec': ded_info['total_ded'],
        'PF_Gross_dec': pf_gross,
        'PF_Deduction_dec': pf_ded,
        'ESI_Gross_dec': esi_gross,
        'ESI_Deduction_dec': esi_ded,
        'Earned_Basic_DA_dec': e_basic,
        'Earned_HRA_dec': e_hra,
        'Earned_Conveyance_dec': e_conv,
        'Earned_Washing_dec': e_wash,
        'Earned_Other_dec': e_other,
        'OT_Wages_dec': ot_info['ot_wages'],
        'Special_OT_dec': ot_info['spl_allow']
    }


# ==============================================================================
# 17. CATEGORY DISPATCHER
# ==============================================================================
def resolve_category(emp) -> str:
    """Resolve normalized canonical category identifier for an employee. Unknown categories raise ValueError."""
    if not emp:
        raise ValueError("Cannot resolve category from empty employee object.")

    cat_raw = emp.get('Category')
    if cat_raw is not None and str(cat_raw).strip() != '':
        cat_key = str(cat_raw).strip().upper()
        if cat_key in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[cat_key]
        for canonical in ALL_CANONICAL_CATEGORIES:
            if canonical == cat_key:
                return canonical
        raise ValueError(f"Unknown or unsupported employee category: '{cat_raw}'. Must be one of {ALL_CANONICAL_CATEGORIES}")

    # If Category was not given, check Employee_Type and Payroll_Category
    emp_type = emp.get('Employee_Type')
    pay_cat = emp.get('Payroll_Category')
    if emp_type or pay_cat:
        emp_t_str = str(emp_type or 'STAFF').strip().upper()
        pay_c_str = str(pay_cat or 'PF_ESI').strip().upper()
        composed = f"{emp_t_str}_{pay_c_str}"
        if composed in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[composed]
        for canonical in ALL_CANONICAL_CATEGORIES:
            if canonical == composed:
                return canonical
        raise ValueError(f"Unknown or unsupported employee type/payroll category combination: '{composed}'.")

    raise ValueError(f"Employee has no category specified. Must be one of {ALL_CANONICAL_CATEGORIES}")

def calculate_payroll(employee, salary=None, attendance=None, deductions=None, payroll_period=None, standard_days=None):
    """
    Central Authoritative Payroll Engine Dispatcher:
    Routes employee calculation to its exact dedicated category formula implementation.
    
    Supports both signatures:
    1. calculate_payroll(employee, salary, attendance, deductions, standard_days=26.0)
    2. calculate_payroll(employee, attendance, deductions, payroll_period=None)
    """
    # Handle signature variations gracefully
    if salary is not None and attendance is None and deductions is None:
        # Caller passed (employee, attendance, deductions, payroll_period) in positional slots
        # where salary was actually attendance
        attendance = salary
        salary = employee

    if salary is None:
        salary = employee

    if attendance is None:
        attendance = {}

    if deductions is None:
        deductions = {}

    if standard_days is None:
        if payroll_period is not None:
            if isinstance(payroll_period, dict):
                standard_days = payroll_period.get('standard_days') or payroll_period.get('Standard_Working_Days')
            elif hasattr(payroll_period, 'standard_days'):
                standard_days = getattr(payroll_period, 'standard_days')
        if standard_days is None:
            # Check employee type default
            emp_type = str(employee.get('Employee_Type', 'STAFF')).strip().upper() if employee else 'STAFF'
            standard_days = 26.0

    canonical_cat = resolve_category(employee)

    if canonical_cat == CAT_STAFF_PF_ESI:
        return calculate_staff_pf_esi(employee, salary, attendance, deductions, standard_days=standard_days)
    elif canonical_cat == CAT_WORKER_PF_ESI:
        return calculate_worker_pf_esi(employee, salary, attendance, deductions, standard_days=standard_days)
    elif canonical_cat == CAT_STAFF_NAPS:
        return calculate_staff_naps(employee, salary, attendance, deductions, standard_days=standard_days)
    elif canonical_cat == CAT_WORKER_NAPS:
        return calculate_worker_naps(employee, salary, attendance, deductions, standard_days=standard_days)
    elif canonical_cat == CAT_STAFF_NON_PF_ESI:
        return calculate_staff_non_pf_esi(employee, salary, attendance, deductions, standard_days=standard_days)
    elif canonical_cat == CAT_WORKER_NON_PF_ESI:
        return calculate_worker_non_pf_esi(employee, salary, attendance, deductions, standard_days=standard_days)
    else:
        raise ValueError(f"Unsupported category '{canonical_cat}'.")


# ==============================================================================
# 18. PAYROLL RESULT VALIDATION & CATEGORY TRANSITION
# ==============================================================================
def validate_payroll_result(result: dict) -> list:
    """
    Validates calculation integrity and returns a list of error strings if any.
    Ensures mathematical consistency between Gross, Deductions, and Net Pay.
    """
    errors = []
    if not isinstance(result, dict):
        return ["Payroll calculation result is not a dictionary."]

    gross = to_dec(result.get('Gross_Wages', 0.0))
    total_ded = to_dec(result.get('Total_Deduction', 0.0))
    net = to_dec(result.get('Net_Salary', 0.0))
    arrears = to_dec(result.get('Arrears', 0.0))

    cat = result.get('Category', '')

    # For Worker Non-PF/ESI, net is integer-rounded
    if cat == CAT_WORKER_NON_PF_ESI:
        expected_net = excel_round(gross - total_ded, 0)
        if abs(net - expected_net) > Decimal('0.01'):
            errors.append(f"Net salary mismatch for {cat}: expected {expected_net}, got {net}")
    else:
        expected_net = gross - total_ded
        if abs(net - expected_net) > Decimal('0.05'):
            errors.append(f"Net salary mismatch for {cat}: expected {expected_net}, got {net}")

    if total_ded < Decimal('0.00'):
        errors.append(f"Total deductions cannot be negative: {total_ded}")

    return errors

def recalculate_for_category_transition(employee: dict, old_category: str, new_category: str,
                                         salary_dict: dict, att_dict: dict, ded_dict: dict,
                                         standard_days=26.0) -> dict:
    """
    Safely recalculates payroll when an employee changes category
    (e.g., Staff NAPS -> Staff PF/ESI, Worker PF/ESI -> Worker Non-PF/ESI).
    
    Guarantees:
    1. Preserves underlying input data (attendance days, advance balances, LIC).
    2. Clears obsolete category-specific calculated outputs (e.g. NAPS deduction
       when transitioning to PF/ESI; PF/ESI gross/deduction when moving to Non-PF/ESI).
    3. Re-routes to the exact authoritative formula set for new_category.
    4. Validates the result.
    """
    # 1. Normalize and validate new category
    test_emp = dict(employee)
    test_emp['Category'] = new_category
    norm_cat = resolve_category(test_emp)

    clean_emp = dict(employee)
    clean_emp['Category'] = norm_cat
    if 'STAFF' in norm_cat:
        clean_emp['Employee_Type'] = 'STAFF'
    else:
        clean_emp['Employee_Type'] = 'WORKER'

    clean_ded = dict(ded_dict) if ded_dict else {}

    # 2. Reset obsolete category-specific deduction overrides
    if 'PF_ESI' in norm_cat:
        # Leaving NAPS -> clear NAPS deduction
        clean_ded['naps'] = 0.0
        clean_ded['NAPS'] = 0.0
    elif 'NAPS' in norm_cat:
        # Moving to NAPS -> statutory PF and ESI will automatically be 0.0
        clean_ded['naps'] = float(NAPS_STANDARD_DEDUCTION)
    elif 'NON_PF_ESI' in norm_cat:
        # Moving to Non-PF/ESI -> clear NAPS
        clean_ded['naps'] = 0.0
        clean_ded['NAPS'] = 0.0

    # 3. Recalculate with authoritative central dispatcher
    result = calculate_payroll(clean_emp, salary_dict, att_dict, clean_ded, standard_days=standard_days)

    # 4. Validate output
    val_errors = validate_payroll_result(result)
    if val_errors:
        raise ValueError(f"Category transition validation failed: {'; '.join(val_errors)}")

    return result

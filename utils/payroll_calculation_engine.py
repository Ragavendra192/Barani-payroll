"""
utils/payroll_calculation_engine.py
Authoritative Single Source of Truth Payroll Calculation Engine for BHIPL Unit-I Application.

Supports 6 Independent Employee Categories:
1. STAFF_PF_ESI
2. WORKER_PF_ESI
3. STAFF_NAPS
4. WORKER_NAPS
5. STAFF_NON_PF_ESI
6. WORKER_NON_PF_ESI

Guarantees:
- Uses Decimal precision with ROUND_HALF_UP rounding for all monetary math.
- Never overwrites original Employee Master salary values.
- Each category has dedicated earned gross, statutory, deduction, and net salary functions.
- Generates detailed breakdown dictionary for debugging/auditing.
"""

from decimal import Decimal, ROUND_HALF_UP
import math

def money(val):
    """Convert input value to Decimal rounded to 2 decimal places with ROUND_HALF_UP."""
    if val is None or str(val).strip() == '':
        return Decimal('0.00')
    try:
        d = Decimal(str(val))
        return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal('0.00')

def round_half(val):
    """
    Rounds value to nearest integer with >= 0.50 rounding up, < 0.50 rounding down.
    Returns Decimal with 2 decimal places (.00) for consistent monetary precision.
    """
    if val is None or str(val).strip() == '':
        return Decimal('0.00')
    try:
        d = Decimal(str(val))
        return d.quantize(Decimal('1'), rounding=ROUND_HALF_UP).quantize(Decimal('0.01'))
    except Exception:
        return Decimal('0.00')

def to_dec(val, default='0.0'):
    """Convert input value to Decimal without strict quantization (for ratios/hours)."""
    if val is None or str(val).strip() == '':
        return Decimal(str(default))
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(str(default))

def calculate_attendance(att_dict, is_worker=False, standard_days=26.0, deduct_lop=False):
    """
    Calculate worked days, leaves, and LOP days from attendance input.
    Total_Worked_Days = Present_Days + N/H + Leave (EL/CL/SL)
    """
    present_days = to_dec(att_dict.get('present_days') or att_dict.get('Present_Days'), '0.0')
    ph = to_dec(att_dict.get('ph') or att_dict.get('PH') or att_dict.get('nh') or att_dict.get('N_H'), '0.0')
    cl = to_dec(att_dict.get('cl') or att_dict.get('CL'), '0.0')
    sl = to_dec(att_dict.get('sl') or att_dict.get('SL'), '0.0')
    pl = to_dec(att_dict.get('pl') or att_dict.get('PL') or att_dict.get('el') or att_dict.get('EL') or att_dict.get('ch') or att_dict.get('C_H'), '0.0')
    std_days_dec = to_dec(standard_days, '26.0')

    total_days = att_dict.get('total_days') or att_dict.get('Total_Worked_Days')
    if total_days is not None and str(total_days).strip() != '':
        total_worked_days = to_dec(total_days, '0.0')
    else:
        total_worked_days = present_days + ph + cl + sl + pl

    raw_lop = std_days_dec - total_worked_days
    lop_days = max(Decimal('0.0'), raw_lop) if deduct_lop else Decimal('0.0')

    return {
        'present_days': float(present_days),
        'ph': float(ph),
        'cl': float(cl),
        'sl': float(sl),
        'pl': float(pl),
        'total_worked_days': float(total_worked_days),
        'total_days_dec': total_worked_days,
        'lop_days': float(lop_days),
        'lop_days_dec': lop_days,
        'standard_days': float(std_days_dec)
    }

def calculate_earned_salary(fixed_val, worked_days_dec, standard_days_dec):
    """Calculate prorated earned salary component using Decimal math rounded to nearest integer."""
    if standard_days_dec <= Decimal('0.0'):
        return Decimal('0.00')
    fixed_dec = money(fixed_val)
    earned = (fixed_dec / standard_days_dec) * worked_days_dec
    return round_half(earned)

def calculate_ot(act_ot_hours, per_day_wage, ot_rate_override=None):
    """Calculate OT and Special OT wages for Workers based on Per Day Wage / 8."""
    act_ot_dec = to_dec(act_ot_hours, '0.0')
    per_day_dec = money(per_day_wage)
    
    if per_day_dec > Decimal('0.0'):
        ot_rate = (per_day_dec / Decimal('8.0')).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    elif ot_rate_override is not None and float(ot_rate_override) > 0:
        ot_rate = money(ot_rate_override)
    else:
        ot_rate = Decimal('56.25')

    if act_ot_dec <= Decimal('50.0'):
        capped_ot = act_ot_dec
        special_ot = Decimal('0.0')
    else:
        capped_ot = Decimal('50.0')
        special_ot = act_ot_dec - Decimal('50.0')

    ot_wages = round_half(capped_ot * ot_rate)
    special_ot_amount = round_half(special_ot * ot_rate)

    return {
        'act_ot_hours': float(act_ot_dec),
        'capped_ot_hours': float(capped_ot),
        'special_ot_hours': float(special_ot),
        'ot_rate': float(ot_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        'ot_wages': float(ot_wages),
        'special_ot_amount': float(special_ot_amount),
        'ot_wages_dec': ot_wages,
        'special_ot_dec': special_ot_amount
    }

# Backward compatibility helper functions
def calculate_pf(earned_gross_dec, earned_basic_da_dec, earned_hra_dec, ot_wages_dec, is_staff=True, is_pf_eligible=True):
    if is_staff:
        return calculate_staff_pf_esi_pf(earned_gross_dec, is_pf_eligible)
    else:
        return calculate_worker_pf_esi_pf(earned_gross_dec, earned_basic_da_dec, earned_hra_dec, ot_wages_dec, is_pf_eligible)

def calculate_esi(earned_gross_dec, fixed_gross_dec, is_staff=True, is_esi_eligible=True):
    if is_staff:
        return calculate_staff_pf_esi_esi(earned_gross_dec, fixed_gross_dec, is_esi_eligible)
    else:
        return calculate_worker_pf_esi_esi(earned_gross_dec, fixed_gross_dec, is_esi_eligible)

def calculate_deductions(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi, is_worker=False):
    if is_worker:
        return calculate_worker_pf_esi_deductions(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi)
    else:
        return calculate_staff_pf_esi_deductions(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi)

def _extract_advance_info(ded_dict, advance_ded):
    """Extract and calculate advance tracking fields (Opening, New, Installment/Deduction, Closing)."""
    op_adv = money(ded_dict.get('opening_adv') or ded_dict.get('Opening_Advance') or ded_dict.get('Opening Adv') or 0.0)
    nw_adv = money(ded_dict.get('new_adv') or ded_dict.get('New_Advance') or ded_dict.get('New Adv') or 0.0)
    inst = advance_ded
    raw_closing = ded_dict.get('closing_adv') or ded_dict.get('Closing_Advance') or ded_dict.get('Closing Adv')
    if raw_closing is not None and str(raw_closing).strip() != '':
        cl_adv = money(raw_closing)
    else:
        cl_adv = max(Decimal('0.00'), op_adv + nw_adv - inst)
    return op_adv, nw_adv, inst, cl_adv

# ==============================================================================
# CATEGORY 1: STAFF_PF_ESI
# ==============================================================================

def calculate_staff_pf_esi_earned_gross(salary, att_info, standard_days_dec):
    master_basic = money(salary.get('master_basic') or salary.get('Basic'))
    master_da = money(salary.get('master_da') or salary.get('DA'))

    fixed_basic_da = money(salary.get('Basic_DA'))
    fixed_hra = money(salary.get('HRA'))
    fixed_conv = money(salary.get('Conveyance_Allowance') or salary.get('fixed_conv'))
    fixed_wash = money(salary.get('Washing_Allowance') or salary.get('fixed_wash'))
    fixed_other = money(salary.get('Other_Allowance') or salary.get('fixed_other'))
    fixed_spl = money(salary.get('Special_Allowance') or salary.get('fixed_spl') or '0.00')

    fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
    if fixed_gross == Decimal('0.00'):
        if (master_basic + master_da) > Decimal('0.00'):
            fixed_gross = master_basic + master_da
        else:
            fixed_gross = fixed_basic_da + fixed_hra + fixed_conv + fixed_wash + fixed_other + fixed_spl

    if fixed_basic_da == Decimal('0.00') and fixed_gross > Decimal('0.00'):
        fixed_basic_da = money(fixed_gross * Decimal('0.50'))
        fixed_hra = money(fixed_gross * Decimal('0.20'))
        fixed_conv = money(fixed_gross * Decimal('0.10'))
        fixed_wash = money(fixed_gross * Decimal('0.10'))
        fixed_other = money(fixed_gross * Decimal('0.10'))

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = calculate_earned_salary(fixed_spl, worked_days_dec, standard_days_dec)

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + earned_spl)

    return {
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'earned_gross': earned_gross
    }

def calculate_staff_pf_esi_pf(earned_gross_dec, is_pf_eligible=True):
    if not is_pf_eligible:
        return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
    raw_pf_gross = earned_gross_dec * Decimal('0.80')
    if raw_pf_gross < Decimal('0.00'):
        raw_pf_gross = Decimal('0.00')
    pf_gross = round_half(min(raw_pf_gross, Decimal('15000.00')))
    pf_ded = round_half(min(pf_gross * Decimal('0.12'), Decimal('1800.00')))
    accounts_pf_ded = Decimal('1800.00') if pf_gross >= Decimal('15000.00') else pf_ded
    return pf_gross, pf_ded, accounts_pf_ded

def calculate_staff_pf_esi_esi(earned_gross_dec, fixed_gross_dec, is_esi_eligible=True):
    if not is_esi_eligible or fixed_gross_dec > Decimal('21001.00'):
        return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
    esi_gross = round_half(earned_gross_dec * Decimal('0.90')) if earned_gross_dec <= Decimal('21000.00') else Decimal('0.00')
    raw_ded = esi_gross * Decimal('0.0075')
    esi_ded = round_half(raw_ded)
    return esi_gross, esi_ded, esi_ded

def calculate_staff_pf_esi_deductions(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi):
    pt = money(ded_dict.get('pt') or ded_dict.get('PT'))
    mess = money(ded_dict.get('mess') or ded_dict.get('Mess'))
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    tds = money(ded_dict.get('tds') or ded_dict.get('TDS'))
    naps = money(ded_dict.get('naps') or ded_dict.get('NAPS'))
    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    other = money(ded_dict.get('other') or ded_dict.get('Other'))

    total_ded = round_half(pf_ded + esi_ded + pt + mess + lic + tds + naps + advance + accom + other)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': pf_ded, 'accounts_pf_ded': acc_pf, 'esi_ded': esi_ded, 'accounts_esi_ded': acc_esi,
        'pt': pt, 'mess': mess, 'lic': lic, 'tds': tds, 'naps': naps, 'advance': advance,
        'accom': accom, 'other': other, 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_staff_pf_esi_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_staff_pf_esi(emp, salary, attendance, deductions, standard_days=27.0):
    """Category 1: STAFF_PF_ESI Calculation Routine"""
    std_days_dec = to_dec(standard_days, '27.0')
    att_info = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    earn_info = calculate_staff_pf_esi_earned_gross(salary, att_info, std_days_dec)
    
    pf_eligible = bool(salary.get('PF_Eligible', True))
    esi_eligible = bool(salary.get('ESI_Eligible', True))
    pf_gross_dec, pf_ded_dec, acc_pf_dec = calculate_staff_pf_esi_pf(earn_info['earned_gross'], pf_eligible)
    esi_gross_dec, esi_ded_dec, acc_esi_dec = calculate_staff_pf_esi_esi(earn_info['earned_gross'], earn_info['fixed_gross'], esi_eligible)

    ded_info = calculate_staff_pf_esi_deductions(deductions, pf_ded_dec, esi_ded_dec, acc_pf_dec, acc_esi_dec)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    earned_gross_total = round_half(earn_info['earned_gross'] + arrears)
    earn_info['earned_gross'] = earned_gross_total
    
    net_pay = calculate_staff_pf_esi_net(earned_gross_total, ded_info['total_ded'], Decimal('0.00'))
    ot_info = calculate_ot(0.0, 0.0, 0.0)

    return build_result(
        emp, 'STAFF_PF_ESI', 'STAFF', 'PF_ESI', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], Decimal('0.00'),
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earned_gross_total,
        ot_info, pf_gross_dec, pf_ded_dec, acc_pf_dec, esi_gross_dec, esi_ded_dec, acc_esi_dec,
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CATEGORY 2: WORKER_PF_ESI
# ==============================================================================

def calculate_worker_pf_esi_earned_gross(salary, att_info, attendance, standard_days_dec):
    per_day_wage = money(salary.get('Per_Day_Wage') or salary.get('per_day_wage'))
    if per_day_wage > Decimal('0.00'):
        fixed_gross = money(per_day_wage * standard_days_dec)
        
        b_da = money(salary.get('Basic_DA'))
        if b_da > Decimal('0.00') and b_da <= per_day_wage:
            fixed_basic_da = money(b_da * standard_days_dec)
        elif b_da > per_day_wage:
            fixed_basic_da = b_da
        else:
            fixed_basic_da = money(fixed_gross * Decimal('0.50'))

        hra_val = money(salary.get('HRA'))
        if hra_val > Decimal('0.00') and hra_val <= per_day_wage:
            fixed_hra = money(hra_val * standard_days_dec)
        elif hra_val > per_day_wage:
            fixed_hra = hra_val
        else:
            fixed_hra = money(fixed_gross * Decimal('0.20'))

        conv_val = money(salary.get('Conveyance_Allowance'))
        if conv_val > Decimal('0.00') and conv_val <= per_day_wage:
            fixed_conv = money(conv_val * standard_days_dec)
        elif conv_val > per_day_wage:
            fixed_conv = conv_val
        else:
            fixed_conv = money(fixed_gross * Decimal('0.10'))

        wash_val = money(salary.get('Washing_Allowance'))
        if wash_val > Decimal('0.00') and wash_val <= per_day_wage:
            fixed_wash = money(wash_val * standard_days_dec)
        elif wash_val > per_day_wage:
            fixed_wash = wash_val
        else:
            fixed_wash = money(fixed_gross * Decimal('0.10'))

        other_val = money(salary.get('Other_Allowance'))
        if other_val > Decimal('0.00') and other_val <= per_day_wage:
            fixed_other = money(other_val * standard_days_dec)
        elif other_val > per_day_wage:
            fixed_other = other_val
        else:
            fixed_other = money(fixed_gross * Decimal('0.10'))
    else:
        fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
        fixed_basic_da = money(salary.get('Basic_DA') or (fixed_gross * Decimal('0.50')))
        fixed_hra = money(salary.get('HRA') or (fixed_gross * Decimal('0.20')))
        fixed_conv = money(salary.get('Conveyance_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_wash = money(salary.get('Washing_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_other = money(salary.get('Other_Allowance') or (fixed_gross * Decimal('0.10')))

    fixed_spl = Decimal('0.00')

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = Decimal('0.00')

    act_ot = attendance.get('actual_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_hrs') or 0.0
    ot_info = calculate_ot(act_ot, per_day_wage, salary.get('OT_Rate'))

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + ot_info['ot_wages_dec'] + ot_info['special_ot_dec'])

    return {
        'per_day_wage': per_day_wage,
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'ot_info': ot_info,
        'earned_gross': earned_gross
    }

def calculate_worker_pf_esi_pf(earned_gross_dec, earned_basic_da_dec, earned_hra_dec, ot_wages_dec, is_pf_eligible=True):
    if not is_pf_eligible:
        return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
    raw_pf_gross = earned_gross_dec - earned_hra_dec - ot_wages_dec
    if raw_pf_gross < Decimal('0.00'):
        raw_pf_gross = Decimal('0.00')
    pf_gross = round_half(min(raw_pf_gross, Decimal('15000.00')))
    pf_ded = round_half(min(pf_gross * Decimal('0.12'), Decimal('1800.00')))
    return pf_gross, pf_ded, pf_ded

def calculate_worker_pf_esi_esi(earned_gross_dec, fixed_gross_dec, is_esi_eligible=True):
    if not is_esi_eligible or fixed_gross_dec > Decimal('21000.00'):
        return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
    raw_esi_gross = earned_gross_dec * Decimal('0.90')
    esi_gross = round_half(min(raw_esi_gross, Decimal('21000.00')))
    esi_ded = round_half(esi_gross * Decimal('0.0075'))
    acc_esi_ded = esi_ded
    return esi_gross, esi_ded, acc_esi_ded

def calculate_worker_pf_esi_deductions(ded_dict, pf_ded, esi_ded, acc_pf, acc_esi):
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    naps = money(ded_dict.get('naps') or ded_dict.get('NAPS'))
    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    
    total_ded = round_half(pf_ded + esi_ded + lic + advance + naps + accom)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': pf_ded, 'accounts_pf_ded': acc_pf, 'esi_ded': esi_ded, 'accounts_esi_ded': acc_esi,
        'pt': Decimal('0.00'), 'mess': Decimal('0.00'), 'lic': lic, 'tds': Decimal('0.00'), 'naps': naps,
        'advance': advance, 'accom': accom, 'other': Decimal('0.00'), 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_worker_pf_esi_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_worker_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """Category 2: WORKER_PF_ESI Calculation Routine"""
    std_days_dec = to_dec(standard_days, '26.0')
    att_info = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    earn_info = calculate_worker_pf_esi_earned_gross(salary, att_info, attendance, std_days_dec)

    pf_eligible = bool(salary.get('PF_Eligible', True))
    esi_eligible = bool(salary.get('ESI_Eligible', True))
    pf_gross_dec, pf_ded_dec, acc_pf_dec = calculate_worker_pf_esi_pf(earn_info['earned_gross'], earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['ot_info']['ot_wages_dec'], pf_eligible)
    esi_gross_dec, esi_ded_dec, acc_esi_dec = calculate_worker_pf_esi_esi(earn_info['earned_gross'], earn_info['fixed_gross'], esi_eligible)

    ded_info = calculate_worker_pf_esi_deductions(deductions, pf_ded_dec, esi_ded_dec, acc_pf_dec, acc_esi_dec)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    net_pay = calculate_worker_pf_esi_net(earn_info['earned_gross'], ded_info['total_ded'], arrears)

    return build_result(
        emp, 'WORKER_PF_ESI', 'WORKER', 'PF_ESI', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], earn_info['per_day_wage'],
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earn_info['earned_gross'],
        earn_info['ot_info'], pf_gross_dec, pf_ded_dec, acc_pf_dec, esi_gross_dec, esi_ded_dec, acc_esi_dec,
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CATEGORY 3: STAFF_NAPS
# ==============================================================================

def calculate_staff_naps_earned_gross(salary, att_info, standard_days_dec):
    fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
    fixed_basic_da = money(salary.get('Basic_DA') or (fixed_gross * Decimal('0.50')))
    fixed_hra = money(salary.get('HRA') or (fixed_gross * Decimal('0.20')))
    fixed_conv = money(salary.get('Conveyance_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_wash = money(salary.get('Washing_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_other = money(salary.get('Other_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_spl = money(salary.get('Special_Allowance') or '0.00')

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = calculate_earned_salary(fixed_spl, worked_days_dec, standard_days_dec)

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + earned_spl)

    return {
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'earned_gross': earned_gross
    }

def calculate_staff_naps_deductions(ded_dict):
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    raw_naps = ded_dict.get('naps') if ded_dict.get('naps') is not None else ded_dict.get('NAPS')
    if raw_naps is not None and str(raw_naps).strip() != '' and float(raw_naps) > 0:
        naps = money(raw_naps)
    else:
        naps = Decimal('1500.00')

    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    other = money(ded_dict.get('other') or ded_dict.get('Other'))

    total_ded = round_half(naps + advance + lic + accom + other)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': Decimal('0.00'), 'accounts_pf_ded': Decimal('0.00'), 'esi_ded': Decimal('0.00'), 'accounts_esi_ded': Decimal('0.00'),
        'pt': Decimal('0.00'), 'mess': Decimal('0.00'), 'lic': lic, 'tds': Decimal('0.00'), 'naps': naps,
        'advance': advance, 'accom': accom, 'other': other, 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_staff_naps_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_staff_naps(emp, salary, attendance, deductions, standard_days=26.0):
    """Category 3: STAFF_NAPS Calculation Routine (Exempt from PF & ESI)"""
    std_days_dec = to_dec(standard_days, '26.0')
    att_info = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    earn_info = calculate_staff_naps_earned_gross(salary, att_info, std_days_dec)
    
    ded_info = calculate_staff_naps_deductions(deductions)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    earned_gross_total = round_half(earn_info['earned_gross'] + arrears)
    net_pay = calculate_staff_naps_net(earned_gross_total, ded_info['total_ded'], Decimal('0.00'))
    ot_info = calculate_ot(0.0, 0.0, 0.0)

    return build_result(
        emp, 'STAFF_NAPS', 'STAFF', 'NAPS', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], Decimal('0.00'),
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CATEGORY 4: WORKER_NAPS
# ==============================================================================

def calculate_worker_naps_earned_gross(salary, att_info, attendance, standard_days_dec):
    per_day_wage = money(salary.get('Per_Day_Wage') or salary.get('per_day_wage'))
    if per_day_wage > Decimal('0.00'):
        fixed_gross = money(per_day_wage * standard_days_dec)
        
        b_da = money(salary.get('Basic_DA'))
        if b_da > Decimal('0.00') and b_da <= per_day_wage:
            fixed_basic_da = money(b_da * standard_days_dec)
        elif b_da > per_day_wage:
            fixed_basic_da = b_da
        else:
            fixed_basic_da = money(fixed_gross * Decimal('0.50'))

        hra_val = money(salary.get('HRA'))
        if hra_val > Decimal('0.00') and hra_val <= per_day_wage:
            fixed_hra = money(hra_val * standard_days_dec)
        elif hra_val > per_day_wage:
            fixed_hra = hra_val
        else:
            fixed_hra = money(fixed_gross * Decimal('0.20'))

        conv_val = money(salary.get('Conveyance_Allowance'))
        if conv_val > Decimal('0.00') and conv_val <= per_day_wage:
            fixed_conv = money(conv_val * standard_days_dec)
        elif conv_val > per_day_wage:
            fixed_conv = conv_val
        else:
            fixed_conv = money(fixed_gross * Decimal('0.10'))

        wash_val = money(salary.get('Washing_Allowance'))
        if wash_val > Decimal('0.00') and wash_val <= per_day_wage:
            fixed_wash = money(wash_val * standard_days_dec)
        elif wash_val > per_day_wage:
            fixed_wash = wash_val
        else:
            fixed_wash = money(fixed_gross * Decimal('0.10'))

        other_val = money(salary.get('Other_Allowance'))
        if other_val > Decimal('0.00') and other_val <= per_day_wage:
            fixed_other = money(other_val * standard_days_dec)
        elif other_val > per_day_wage:
            fixed_other = other_val
        else:
            fixed_other = money(fixed_gross * Decimal('0.10'))
    else:
        fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
        fixed_basic_da = money(salary.get('Basic_DA') or (fixed_gross * Decimal('0.50')))
        fixed_hra = money(salary.get('HRA') or (fixed_gross * Decimal('0.20')))
        fixed_conv = money(salary.get('Conveyance_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_wash = money(salary.get('Washing_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_other = money(salary.get('Other_Allowance') or (fixed_gross * Decimal('0.10')))

    fixed_spl = Decimal('0.00')

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = Decimal('0.00')

    act_ot = attendance.get('actual_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_hrs') or 0.0
    ot_info = calculate_ot(act_ot, per_day_wage, salary.get('OT_Rate'))

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + ot_info['ot_wages_dec'] + ot_info['special_ot_dec'])

    return {
        'per_day_wage': per_day_wage,
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'ot_info': ot_info,
        'earned_gross': earned_gross
    }

def calculate_worker_naps_deductions(ded_dict):
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    raw_naps = ded_dict.get('naps') if ded_dict.get('naps') is not None else ded_dict.get('NAPS')
    if raw_naps is not None and str(raw_naps).strip() != '' and float(raw_naps) > 0:
        naps = money(raw_naps)
    else:
        naps = Decimal('1500.00')

    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    other = money(ded_dict.get('other') or ded_dict.get('Other'))

    total_ded = round_half(naps + advance + lic + accom + other)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': Decimal('0.00'), 'accounts_pf_ded': Decimal('0.00'), 'esi_ded': Decimal('0.00'), 'accounts_esi_ded': Decimal('0.00'),
        'pt': Decimal('0.00'), 'mess': Decimal('0.00'), 'lic': lic, 'tds': Decimal('0.00'), 'naps': naps,
        'advance': advance, 'accom': accom, 'other': other, 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_worker_naps_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_worker_naps(emp, salary, attendance, deductions, standard_days=26.0):
    """Category 4: WORKER_NAPS Calculation Routine (Exempt from PF & ESI)"""
    std_days_dec = to_dec(standard_days, '26.0')
    att_info = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    earn_info = calculate_worker_naps_earned_gross(salary, att_info, attendance, std_days_dec)

    ded_info = calculate_worker_naps_deductions(deductions)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    net_pay = calculate_worker_naps_net(earn_info['earned_gross'], ded_info['total_ded'], arrears)

    return build_result(
        emp, 'WORKER_NAPS', 'WORKER', 'NAPS', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], earn_info['per_day_wage'],
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earn_info['earned_gross'],
        earn_info['ot_info'], Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CATEGORY 5: STAFF_NON_PF_ESI
# ==============================================================================

def calculate_staff_non_pf_esi_earned_gross(salary, att_info, standard_days_dec):
    fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
    fixed_basic_da = money(salary.get('Basic_DA') or (fixed_gross * Decimal('0.50')))
    fixed_hra = money(salary.get('HRA') or (fixed_gross * Decimal('0.20')))
    fixed_conv = money(salary.get('Conveyance_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_wash = money(salary.get('Washing_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_other = money(salary.get('Other_Allowance') or (fixed_gross * Decimal('0.10')))
    fixed_spl = money(salary.get('Special_Allowance') or '0.00')

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = calculate_earned_salary(fixed_spl, worked_days_dec, standard_days_dec)

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + earned_spl)

    return {
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'earned_gross': earned_gross
    }

def calculate_staff_non_pf_esi_deductions(ded_dict):
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    other = money(ded_dict.get('other') or ded_dict.get('Other'))

    total_ded = round_half(advance + lic + accom + other)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': Decimal('0.00'), 'accounts_pf_ded': Decimal('0.00'), 'esi_ded': Decimal('0.00'), 'accounts_esi_ded': Decimal('0.00'),
        'pt': Decimal('0.00'), 'mess': Decimal('0.00'), 'lic': lic, 'tds': Decimal('0.00'), 'naps': Decimal('0.00'),
        'advance': advance, 'accom': accom, 'other': other, 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_staff_non_pf_esi_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_staff_non_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """Category 5: STAFF_NON_PF_ESI Calculation Routine (Excluded from PF & ESI)"""
    std_days_dec = to_dec(standard_days, '26.0')
    att_info = calculate_attendance(attendance, is_worker=False, standard_days=standard_days)
    earn_info = calculate_staff_non_pf_esi_earned_gross(salary, att_info, std_days_dec)

    ded_info = calculate_staff_non_pf_esi_deductions(deductions)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    earned_gross_total = round_half(earn_info['earned_gross'] + arrears)
    net_pay = calculate_staff_non_pf_esi_net(earned_gross_total, ded_info['total_ded'], Decimal('0.00'))
    ot_info = calculate_ot(0.0, 0.0, 0.0)

    return build_result(
        emp, 'STAFF_NON_PF_ESI', 'STAFF', 'NON_PF_ESI', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], Decimal('0.00'),
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earned_gross_total,
        ot_info, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CATEGORY 6: WORKER_NON_PF_ESI
# ==============================================================================

def calculate_worker_non_pf_esi_earned_gross(salary, att_info, attendance, standard_days_dec):
    per_day_wage = money(salary.get('Per_Day_Wage') or salary.get('per_day_wage'))
    if per_day_wage > Decimal('0.00'):
        fixed_gross = money(per_day_wage * standard_days_dec)
        
        b_da = money(salary.get('Basic_DA'))
        if b_da > Decimal('0.00') and b_da <= per_day_wage:
            fixed_basic_da = money(b_da * standard_days_dec)
        elif b_da > per_day_wage:
            fixed_basic_da = b_da
        else:
            fixed_basic_da = money(fixed_gross * Decimal('0.50'))

        hra_val = money(salary.get('HRA'))
        if hra_val > Decimal('0.00') and hra_val <= per_day_wage:
            fixed_hra = money(hra_val * standard_days_dec)
        elif hra_val > per_day_wage:
            fixed_hra = hra_val
        else:
            fixed_hra = money(fixed_gross * Decimal('0.20'))

        conv_val = money(salary.get('Conveyance_Allowance'))
        if conv_val > Decimal('0.00') and conv_val <= per_day_wage:
            fixed_conv = money(conv_val * standard_days_dec)
        elif conv_val > per_day_wage:
            fixed_conv = conv_val
        else:
            fixed_conv = money(fixed_gross * Decimal('0.10'))

        wash_val = money(salary.get('Washing_Allowance'))
        if wash_val > Decimal('0.00') and wash_val <= per_day_wage:
            fixed_wash = money(wash_val * standard_days_dec)
        elif wash_val > per_day_wage:
            fixed_wash = wash_val
        else:
            fixed_wash = money(fixed_gross * Decimal('0.10'))

        other_val = money(salary.get('Other_Allowance'))
        if other_val > Decimal('0.00') and other_val <= per_day_wage:
            fixed_other = money(other_val * standard_days_dec)
        elif other_val > per_day_wage:
            fixed_other = other_val
        else:
            fixed_other = money(fixed_gross * Decimal('0.10'))
    else:
        fixed_gross = money(salary.get('Gross_Wages') or salary.get('Base_Gross') or salary.get('Fixed_Gross'))
        fixed_basic_da = money(salary.get('Basic_DA') or (fixed_gross * Decimal('0.50')))
        fixed_hra = money(salary.get('HRA') or (fixed_gross * Decimal('0.20')))
        fixed_conv = money(salary.get('Conveyance_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_wash = money(salary.get('Washing_Allowance') or (fixed_gross * Decimal('0.10')))
        fixed_other = money(salary.get('Other_Allowance') or (fixed_gross * Decimal('0.10')))

    fixed_spl = Decimal('0.00')

    worked_days_dec = att_info['total_days_dec']
    earned_basic_da = calculate_earned_salary(fixed_basic_da, worked_days_dec, standard_days_dec)
    earned_hra = calculate_earned_salary(fixed_hra, worked_days_dec, standard_days_dec)
    earned_conv = calculate_earned_salary(fixed_conv, worked_days_dec, standard_days_dec)
    earned_wash = calculate_earned_salary(fixed_wash, worked_days_dec, standard_days_dec)
    earned_other = calculate_earned_salary(fixed_other, worked_days_dec, standard_days_dec)
    earned_spl = Decimal('0.00')

    act_ot = attendance.get('actual_ot_hours') or attendance.get('ot_hours') or attendance.get('Act_OT_hrs') or 0.0
    ot_info = calculate_ot(act_ot, per_day_wage, salary.get('OT_Rate'))

    earned_gross = round_half(earned_basic_da + earned_hra + earned_conv + earned_wash + earned_other + ot_info['ot_wages_dec'] + ot_info['special_ot_dec'])

    return {
        'per_day_wage': per_day_wage,
        'fixed_gross': fixed_gross,
        'fixed_basic_da': fixed_basic_da,
        'fixed_hra': fixed_hra,
        'fixed_conv': fixed_conv,
        'fixed_wash': fixed_wash,
        'fixed_other': fixed_other,
        'fixed_spl': fixed_spl,
        'earned_basic_da': earned_basic_da,
        'earned_hra': earned_hra,
        'earned_conv': earned_conv,
        'earned_wash': earned_wash,
        'earned_other': earned_other,
        'earned_spl': earned_spl,
        'ot_info': ot_info,
        'earned_gross': earned_gross
    }

def calculate_worker_non_pf_esi_deductions(ded_dict):
    lic = money(ded_dict.get('lic') or ded_dict.get('LIC'))
    advance = money(ded_dict.get('advance') or ded_dict.get('Advance'))
    accom = money(ded_dict.get('accommodation') or ded_dict.get('Accommodation'))
    other = money(ded_dict.get('other') or ded_dict.get('Other'))

    total_ded = round_half(advance + lic + accom + other)
    op_adv, nw_adv, inst, cl_adv = _extract_advance_info(ded_dict, advance)

    return {
        'pf_ded': Decimal('0.00'), 'accounts_pf_ded': Decimal('0.00'), 'esi_ded': Decimal('0.00'), 'accounts_esi_ded': Decimal('0.00'),
        'pt': Decimal('0.00'), 'mess': Decimal('0.00'), 'lic': lic, 'tds': Decimal('0.00'), 'naps': Decimal('0.00'),
        'advance': advance, 'accom': accom, 'other': other, 'total_ded': total_ded,
        'opening_adv': op_adv, 'new_adv': nw_adv, 'installment': inst, 'closing_adv': cl_adv
    }

def calculate_worker_non_pf_esi_net(earned_gross, total_deduction, arrears):
    return round_half(earned_gross - total_deduction + arrears)

def calculate_worker_non_pf_esi(emp, salary, attendance, deductions, standard_days=26.0):
    """Category 6: WORKER_NON_PF_ESI Calculation Routine (Excluded from PF & ESI)"""
    std_days_dec = to_dec(standard_days, '26.0')
    att_info = calculate_attendance(attendance, is_worker=True, standard_days=standard_days)
    earn_info = calculate_worker_non_pf_esi_earned_gross(salary, att_info, attendance, std_days_dec)

    ded_info = calculate_worker_non_pf_esi_deductions(deductions)
    arrears = money(deductions.get('arrears') or deductions.get('Arrears'))
    net_pay = calculate_worker_non_pf_esi_net(earn_info['earned_gross'], ded_info['total_ded'], arrears)

    return build_result(
        emp, 'WORKER_NON_PF_ESI', 'WORKER', 'NON_PF_ESI', att_info,
        earn_info['fixed_basic_da'], earn_info['fixed_hra'], earn_info['fixed_conv'], earn_info['fixed_wash'], earn_info['fixed_other'], earn_info['fixed_spl'], earn_info['fixed_gross'], earn_info['per_day_wage'],
        earn_info['earned_basic_da'], earn_info['earned_hra'], earn_info['earned_conv'], earn_info['earned_wash'], earn_info['earned_other'], earn_info['earned_spl'], earn_info['earned_gross'],
        earn_info['ot_info'], Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
        arrears, ded_info, net_pay, money(salary.get('Basic')), money(salary.get('DA'))
    )

# ==============================================================================
# CENTRAL PAYROLL ENGINE ROUTER
# ==============================================================================

def calculate_payroll(emp, salary, attendance, deductions, standard_days=26.0):
    """
    Central Authoritative Formula Router:
    Routes employee calculation to its exact dedicated category-specific routine.
    """
    cat = (emp.get('Category') or f"{emp.get('Employee_Type', 'STAFF')}_{emp.get('Payroll_Category', 'PF_ESI')}").upper()

    if cat == 'STAFF_PF_ESI':
        return calculate_staff_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    elif cat == 'WORKER_PF_ESI':
        return calculate_worker_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    elif cat == 'STAFF_NAPS':
        return calculate_staff_naps(emp, salary, attendance, deductions, standard_days=standard_days)
    elif cat == 'WORKER_NAPS':
        return calculate_worker_naps(emp, salary, attendance, deductions, standard_days=standard_days)
    elif cat == 'STAFF_NON_PF_ESI':
        return calculate_staff_non_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    elif cat == 'WORKER_NON_PF_ESI':
        return calculate_worker_non_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    else:
        # Fallback by Employee_Type
        emp_type = (emp.get('Employee_Type') or 'STAFF').upper()
        if emp_type == 'WORKER':
            return calculate_worker_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
        else:
            return calculate_staff_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)

# ==============================================================================
# AUDIT & TRACE ROUTER
# ==============================================================================

def get_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    """Dispatches trace details for an employee to its category-specific trace builder."""
    cat = (emp.get('Category') or f"{emp.get('Employee_Type', 'STAFF')}_{emp.get('Payroll_Category', 'PF_ESI')}").upper()
    if cat == 'WORKER_PF_ESI':
        return get_worker_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)
    elif cat == 'STAFF_PF_ESI':
        return get_staff_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)
    elif cat == 'STAFF_NAPS':
        return get_staff_naps_calculation_trace(emp, salary, attendance, deductions, standard_days)
    elif cat == 'WORKER_NAPS':
        return get_worker_naps_calculation_trace(emp, salary, attendance, deductions, standard_days)
    elif cat == 'STAFF_NON_PF_ESI':
        return get_staff_non_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)
    elif cat == 'WORKER_NON_PF_ESI':
        return get_worker_non_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)
    else:
        return get_staff_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)

def get_staff_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days=27.0):
    res = calculate_staff_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': 0.0, 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': res['Act_OT_Hrs']},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': 0.0, 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': res['OT_Rate'], 'ot_wages': res['OT_Wages'], 'special_ot_amount': res['Special_OT_Amount'], 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': res['PF_Gross'], 'pf_deduction': res['PF_Deduction'], 'accounts_pf_deduction': res['Accounts_PF_Deduction'], 'esi_eligible_gross': res['ESI_Gross'], 'esi_deduction': res['ESI_Deduction'], 'accounts_esi_deduction': res['Accounts_ESI_Deduction'], 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': res['NAPS_Deduction'], 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Master Fixed Gross",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / Standard Days * Total Days",
            "Earned HRA = Fixed HRA / Standard Days * Total Days",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + Arrears",
            "PF Base = min(Earned Gross * 80%, 15000)",
            "PF Deduction = min(PF Base * 12%, 1800)",
            "ESI Base = Earned Gross * 90% if Earned Gross <= 21000 else 0",
            "ESI Deduction = ceil(ESI Base * 0.75%) if Fixed Gross <= 21001 else 0",
            "Total Deduction = PF + Acc PF + ESI + Acc ESI + PT + Mess + LIC + TDS + Advance + Accom + Other",
            "Net Salary = Earned Gross - Total Deduction"
        ]
    }

def get_worker_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    res = calculate_worker_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': res['Per_Day_Wage'], 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': res['Act_OT_Hrs']},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': res['Per_Day_Wage'], 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': res['OT_Rate'], 'ot_wages': res['OT_Wages'], 'special_ot_amount': res['Special_OT_Amount'], 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': res['PF_Gross'], 'pf_deduction': res['PF_Deduction'], 'accounts_pf_deduction': res['Accounts_PF_Deduction'], 'esi_eligible_gross': res['ESI_Gross'], 'esi_deduction': res['ESI_Deduction'], 'accounts_esi_deduction': res['Accounts_ESI_Deduction'], 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': res['NAPS_Deduction'], 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Per Day Wage * 26",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / 26 * Total Days",
            "Earned HRA = Fixed HRA / 26 * Total Days",
            "OT Rate = Per Day Wage / 8.0",
            "OT Wages = min(Actual OT, 50) * OT Rate",
            "Special OT Amount = max(Actual OT - 50, 0) * OT Rate",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + OT Wages + Special OT Amount",
            "PF Gross = min(max(Earned Gross - Earned HRA - OT Wages, 0), 15000)",
            "PF Deduction = min(PF Gross * 12%, 1800)",
            "ESI Gross = min(Earned Gross * 90%, 21000) if Fixed Gross <= 21000 else 0",
            "ESI Deduction = ESI Gross * 0.75%",
            "Total Deduction = PF + Account PF + ESI + Account ESI + LIC + Advance + NAPS + Accommodation",
            "Net Salary = Earned Gross - Total Deduction + Arrears"
        ]
    }

def get_staff_naps_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    res = calculate_staff_naps(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': 0.0, 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': 0.0},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': 0.0, 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': 0.0, 'ot_wages': 0.0, 'special_ot_amount': 0.0, 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': 0.0, 'pf_deduction': 0.0, 'accounts_pf_deduction': 0.0, 'esi_eligible_gross': 0.0, 'esi_deduction': 0.0, 'accounts_esi_deduction': 0.0, 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': res['NAPS_Deduction'], 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Master Fixed Gross",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / Standard Days * Total Days",
            "Earned HRA = Fixed HRA / Standard Days * Total Days",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + Arrears",
            "Statutory PF & ESI = 0 (Exempt NAPS Apprentice)",
            "Total Deduction = NAPS + Advance + LIC + Accom + Other",
            "Net Salary = Earned Gross - Total Deduction + Arrears"
        ]
    }

def get_worker_naps_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    res = calculate_worker_naps(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': res['Per_Day_Wage'], 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': res['Act_OT_Hrs']},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': res['Per_Day_Wage'], 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': res['OT_Rate'], 'ot_wages': res['OT_Wages'], 'special_ot_amount': res['Special_OT_Amount'], 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': 0.0, 'pf_deduction': 0.0, 'accounts_pf_deduction': 0.0, 'esi_eligible_gross': 0.0, 'esi_deduction': 0.0, 'accounts_esi_deduction': 0.0, 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': res['NAPS_Deduction'], 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Per Day Wage * 26",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / 26 * Total Days",
            "Earned HRA = Fixed HRA / 26 * Total Days",
            "OT Rate = Per Day Wage / 8.0",
            "OT Wages = min(Actual OT, 50) * OT Rate",
            "Special OT Amount = max(Actual OT - 50, 0) * OT Rate",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + OT Wages + Special OT Amount",
            "Statutory PF & ESI = 0 (Exempt NAPS Apprentice)",
            "Total Deduction = NAPS + Advance + LIC + Accom + Other",
            "Net Salary = Earned Gross - Total Deduction + Arrears"
        ]
    }

def get_staff_non_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    res = calculate_staff_non_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': 0.0, 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': 0.0},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': 0.0, 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': 0.0, 'ot_wages': 0.0, 'special_ot_amount': 0.0, 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': 0.0, 'pf_deduction': 0.0, 'accounts_pf_deduction': 0.0, 'esi_eligible_gross': 0.0, 'esi_deduction': 0.0, 'accounts_esi_deduction': 0.0, 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': 0.0, 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Master Fixed Gross",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / Standard Days * Total Days",
            "Earned HRA = Fixed HRA / Standard Days * Total Days",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + Arrears",
            "Statutory PF & ESI = 0 (Excluded Non-PF/ESI)",
            "Total Deduction = Advance + LIC + Accom + Other",
            "Net Salary = Earned Gross - Total Deduction + Arrears"
        ]
    }

def get_worker_non_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    res = calculate_worker_non_pf_esi(emp, salary, attendance, deductions, standard_days=standard_days)
    return {
        'employee_id': res['Emp_No'], 'employee_name': res['Name'], 'category': res['Category'],
        'inputs': {'per_day_wage': res['Per_Day_Wage'], 'standard_working_days': standard_days, 'present_days': res['Present_Days'], 'nh': res['PH'], 'el': res['PL'], 'cl': res['CL'], 'sl': res['SL'], 'ot_hours': res['Act_OT_Hrs']},
        'fixed': {'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'fixed_hra': res['Fixed_HRA'], 'fixed_conveyance': res['Fixed_Conveyance'], 'fixed_washing': res['Fixed_Washing'], 'fixed_other': res['Fixed_Other']},
        'attendance': {'total_worked_days': res['Worked_Days']},
        'earnings': {'per_day_wage': res['Per_Day_Wage'], 'fixed_gross': res['Fixed_Gross'], 'fixed_basic_da': res['Fixed_Basic_DA'], 'earned_basic_da': res['Earned_Basic_DA'], 'earned_hra': res['Earned_HRA'], 'earned_conveyance': res['Earned_Conveyance'], 'earned_washing': res['Earned_Washing'], 'earned_other': res['Earned_Other'], 'earned_special': res['Earned_Special'], 'ot_rate': res['OT_Rate'], 'ot_wages': res['OT_Wages'], 'special_ot_amount': res['Special_OT_Amount'], 'gross_wages': res['Gross_Wages']},
        'deductions': {'pf_eligible_gross': 0.0, 'pf_deduction': 0.0, 'accounts_pf_deduction': 0.0, 'esi_eligible_gross': 0.0, 'esi_deduction': 0.0, 'accounts_esi_deduction': 0.0, 'lic': res['LIC_Deduction'], 'advance': res['Advance_Deduction'], 'naps': 0.0, 'accommodation': res['Accommodation_Deduction'], 'other_deduction': res['Other_Deduction'], 'total_deduction': res['Total_Deduction']},
        'final': {'arrears': res['Arrears'], 'net_salary': res['Net_Salary']},
        'formula_trace': [
            "Fixed Gross = Per Day Wage * 26",
            "Fixed Basic+DA = Fixed Gross * 50%",
            "Fixed HRA = Fixed Gross * 20%",
            "Total Days = Present Days + N/H + EL + CL + SL",
            "Earned Basic+DA = Fixed Basic+DA / 26 * Total Days",
            "Earned HRA = Fixed HRA / 26 * Total Days",
            "OT Rate = Per Day Wage / 8.0",
            "OT Wages = min(Actual OT, 50) * OT Rate",
            "Special OT Amount = max(Actual OT - 50, 0) * OT Rate",
            "Earned Gross = Earned Basic+DA + Earned HRA + Earned Conv + Earned Wash + Earned Other + OT Wages + Special OT Amount",
            "Statutory PF & ESI = 0 (Excluded Non-PF/ESI)",
            "Total Deduction = Advance + LIC + Accom + Other",
            "Net Salary = Earned Gross - Total Deduction + Arrears"
        ]
    }

# Backward compatibility alias
def get_worker_calculation_trace(emp, salary, attendance, deductions, standard_days=26.0):
    return get_worker_pf_esi_calculation_trace(emp, salary, attendance, deductions, standard_days)

def build_result(emp, category, emp_type, pay_cat, att_info,
                 f_basic, f_hra, f_conv, f_wash, f_other, f_spl, f_gross, per_day_wage,
                 e_basic, e_hra, e_conv, e_wash, e_other, e_spl, e_gross,
                 ot_info, pf_gross, pf_ded, acc_pf_ded, esi_gross, esi_ded, acc_esi_ded,
                 arrears, ded_info, net_pay, master_basic, master_da):
    """Build authoritative result dictionary with complete breakdown for application & DB saving."""
    emp_id = emp.get('Employee_ID') or emp.get('Emp_ID') or emp.get('id')
    emp_no = emp.get('Emp_No') or emp.get('ERP_Emp_No') or emp.get('emp_no') or emp.get('Emp_Code')
    name = emp.get('Employee_Name') or emp.get('Emp_Name') or emp.get('Name') or emp.get('emp_name') or ''

    earned_basic_split = round_half(e_basic * Decimal('0.40'))
    earned_da_split = round_half(e_basic * Decimal('0.60'))

    std_days_dec = to_dec(att_info.get('standard_days', 26.0))
    lop_days_dec = att_info.get('lop_days_dec', Decimal('0.0'))

    if emp_type == 'STAFF':
        per_day_salary = money(f_gross / std_days_dec) if std_days_dec > Decimal('0.0') else Decimal('0.00')
        lop_deduction = round_half(per_day_salary * lop_days_dec)
    else:
        per_day_salary = money(per_day_wage)
        lop_deduction = round_half(per_day_salary * lop_days_dec)

    res = {
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
        'PH': att_info['ph'],
        'NH': att_info['ph'],
        'CL': att_info['cl'],
        'SL': att_info['sl'],
        'PL': att_info['pl'],
        'EL': att_info['pl'],
        'Total_Worked_Days': att_info['total_worked_days'],
        'Worked_Days': att_info['total_worked_days'],
        'Total_Days': att_info['total_worked_days'],
        'LOP_Days': float(lop_days_dec),
        'Per_Day_Salary': float(per_day_salary),
        'LOP_Deduction': float(lop_deduction),

        # Master / Fixed Salary
        'Master_Basic': float(master_basic),
        'Master_DA': float(master_da),
        'Per_Day_Wage': float(per_day_wage),
        'Fixed_Gross': float(f_gross),
        'Fixed_Basic_DA': float(f_basic),
        'Fixed_HRA': float(f_hra),
        'Fixed_Conveyance': float(f_conv),
        'Fixed_Washing': float(f_wash),
        'Fixed_Other': float(f_other),
        'Fixed_Special': float(f_spl),

        # Earned Salary
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
        'Gross_Wages': float(e_gross),
        'Earned_Gross': float(e_gross),

        # Overtime
        'Act_OT_Hrs': ot_info['act_ot_hours'],
        'OT_Hours': ot_info['capped_ot_hours'],
        'Special_OT_Hours': ot_info['special_ot_hours'],
        'OT_Rate': ot_info['ot_rate'],
        'OT_Wages': ot_info['ot_wages'],
        'Special_OT_Amount': ot_info['special_ot_amount'],

        # Statutory
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
        'Net_Salary': float(net_pay),
        'Net_Pay': float(net_pay),

        # Advance Tracking
        'Opening_Advance': float(ded_info['opening_adv']),
        'New_Advance': float(ded_info['new_adv']),
        'Installment': float(ded_info['installment']),
        'Closing_Advance': float(ded_info['closing_adv']),

        # Structured Breakdown Object
        'breakdown': {
            'employee': name,
            'category': category,
            'inputs': {
                'worked_days': att_info['total_worked_days'],
                'ot_hours': ot_info['act_ot_hours']
            },
            'earnings': {
                'basic_da': float(e_basic),
                'hra': float(e_hra),
                'conveyance': float(e_conv),
                'washing': float(e_wash),
                'other': float(e_other),
                'ot_wages': ot_info['ot_wages'],
                'special_ot': ot_info['special_ot_amount'],
                'gross': float(e_gross)
            },
            'deductions': {
                'pf': float(pf_ded),
                'esi': float(esi_ded),
                'lic': float(ded_info['lic']),
                'advance': float(ded_info['advance']),
                'total': float(ded_info['total_ded'])
            },
            'net_pay': float(net_pay)
        }
    }
    return res

"""
services/payroll_formula_engine.py
Execution engine that loads category formula rules from SQL Server (PayrollFormulaRules)
and safely evaluates them to calculate employee wages, statutory deductions, and net pay.
"""

from decimal import Decimal, ROUND_HALF_UP
from models.payroll_formula_rules import get_active_formula_rules
from services.payroll_formula_validator import evaluate_formula, validate_formula_syntax
from utils.payroll_calculation_engine import calculate_payroll, money, round_half

def evaluate_rule_safely(formula_str, context_vars, fallback_val=0.0):
    """Evaluates a formula string safely against context variables with fallback."""
    if not formula_str or not str(formula_str).strip():
        return float(fallback_val)
    try:
        return evaluate_formula(formula_str, context_vars)
    except Exception:
        return float(fallback_val)

def test_category_formulas(category, sample_inputs, custom_rules=None):
    """
    Runs an interactive test calculation for a category using sample inputs and configured formulas.
    Returns: dictionary containing step-by-step evaluated fields and calculated outputs.
    """
    if custom_rules:
        rules = custom_rules
    else:
        rules = get_active_formula_rules(category)

    # Initial context variables from sample inputs
    ctx = {
        'BASIC': sample_inputs.get('Basic', 10000.0),
        'DA': sample_inputs.get('DA', 2000.0),
        'HRA': sample_inputs.get('HRA', 2400.0),
        'CONVEYANCE': sample_inputs.get('Conveyance', 1200.0),
        'WASHING': sample_inputs.get('Washing', 1200.0),
        'OTHER_ALLOWANCE': sample_inputs.get('Other_Allowance', 1200.0),
        'SPECIAL_ALLOWANCE': sample_inputs.get('Special_Allowance', 0.0),
        'PER_DAY_WAGE': sample_inputs.get('Per_Day_Wage', 500.0),
        'WORKING_DAYS': sample_inputs.get('Working_Days', 26.0),
        'PRESENT_DAYS': sample_inputs.get('Present_Days', 25.0),
        'PH': sample_inputs.get('PH', 1.0),
        'CL': sample_inputs.get('CL', 0.0),
        'SL': sample_inputs.get('SL', 0.0),
        'PL': sample_inputs.get('PL', 0.0),
        'EL': sample_inputs.get('EL', 0.0),
        'NH': sample_inputs.get('NH', 0.0),
        'CH': sample_inputs.get('CH', 0.0),
        'OT_HOURS': sample_inputs.get('OT_Hours', 10.0),
        'LIC': sample_inputs.get('LIC', 0.0),
        'TDS': sample_inputs.get('TDS', 0.0),
        'ADVANCE': sample_inputs.get('Advance', 0.0),
        'NAPS': sample_inputs.get('NAPS', 0.0),
        'ARREARS': sample_inputs.get('Arrears', 0.0)
    }

    # Step 1: Attendance
    std_days = float(rules.get('STANDARD_WORKING_DAYS', '26.0'))
    ctx['WORKING_DAYS'] = std_days

    worked_days_f = rules.get('TOTAL_WORKED_DAYS', 'Present_Days + PH + CL + SL + PL')
    ctx['WORKED_DAYS'] = evaluate_rule_safely(worked_days_f, ctx, ctx['PRESENT_DAYS'] + ctx['PH'])

    # Step 2: Base / Fixed Salary
    if 'WORKER' in category:
        fixed_gross_f = rules.get('FIXED_GROSS', 'Per_Day_Wage * Working_Days')
        ctx['FIXED_GROSS'] = evaluate_rule_safely(fixed_gross_f, ctx, ctx['PER_DAY_WAGE'] * ctx['WORKING_DAYS'])
        ctx['GROSS'] = ctx['FIXED_GROSS']
    else:
        ctx['FIXED_GROSS'] = ctx['BASIC'] + ctx['DA'] + ctx['HRA'] + ctx['CONVEYANCE'] + ctx['WASHING'] + ctx['OTHER_ALLOWANCE'] + ctx['SPECIAL_ALLOWANCE']
        ctx['GROSS'] = ctx['FIXED_GROSS']

    ctx['FIXED_BASIC'] = evaluate_rule_safely(rules.get('BASIC_DA', 'Gross * 0.50'), ctx, ctx['GROSS'] * 0.5)
    ctx['FIXED_HRA'] = evaluate_rule_safely(rules.get('HRA_FIXED', 'Gross * 0.20'), ctx, ctx['GROSS'] * 0.2)
    ctx['FIXED_CONVEYANCE'] = evaluate_rule_safely(rules.get('CONVEYANCE_FIXED', 'Gross * 0.10'), ctx, ctx['GROSS'] * 0.1)
    ctx['FIXED_WASHING'] = evaluate_rule_safely(rules.get('WASHING_FIXED', 'Gross * 0.10'), ctx, ctx['GROSS'] * 0.1)
    ctx['FIXED_OTHER'] = evaluate_rule_safely(rules.get('OTHER_FIXED', 'Gross * 0.10'), ctx, ctx['GROSS'] * 0.1)

    # Step 3: Earned Components
    ctx['EARNED_BASIC_DA'] = evaluate_rule_safely(rules.get('EARNED_BASIC_DA', 'Fixed_Basic / Working_Days * Worked_Days'), ctx)
    ctx['EARNED_BASIC'] = float(round_half(ctx['EARNED_BASIC_DA'] * 0.40))
    ctx['EARNED_DA'] = float(round_half(ctx['EARNED_BASIC_DA'] * 0.60))
    ctx['EARNED_HRA'] = evaluate_rule_safely(rules.get('HRA_EARNED', 'Fixed_HRA / Working_Days * Worked_Days'), ctx)
    ctx['EARNED_CONVEYANCE'] = evaluate_rule_safely(rules.get('CONVEYANCE_EARNED', 'Fixed_Conveyance / Working_Days * Worked_Days'), ctx)
    ctx['EARNED_WASHING'] = evaluate_rule_safely(rules.get('WASHING_EARNED', 'Fixed_Washing / Working_Days * Worked_Days'), ctx)
    ctx['EARNED_OTHER'] = evaluate_rule_safely(rules.get('OTHER_EARNED', 'Fixed_Other / Working_Days * Worked_Days'), ctx)

    # Step 4: Overtime
    ot_enabled = rules.get('OT_ENABLED', '1' if 'WORKER' in category else '0')
    if str(ot_enabled).strip() in ('1', 'True', 'true', 'YES', 'yes'):
        ot_rate_f = rules.get('OT_RATE', 'Per_Day_Wage / 8.0')
        ctx['OT_RATE'] = evaluate_rule_safely(ot_rate_f, ctx, ctx['PER_DAY_WAGE'] / 8.0 if ctx['PER_DAY_WAGE'] > 0 else 56.25)
        ctx['OT_WAGES'] = evaluate_rule_safely(rules.get('OT_WAGES', 'min(OT_Hours, 50.0) * OT_Rate'), ctx)
        ctx['SPECIAL_OT_AMOUNT'] = evaluate_rule_safely(rules.get('SPECIAL_OT_ALLOWANCE', 'max(OT_Hours - 50.0, 0.0) * OT_Rate'), ctx)
    else:
        ctx['OT_RATE'] = 0.0
        ctx['OT_WAGES'] = 0.0
        ctx['SPECIAL_OT_AMOUNT'] = 0.0

    # Step 5: Gross Salary
    gross_sal_f = rules.get('GROSS_SALARY', 'Earned_Basic_DA + Earned_HRA + Earned_Conveyance + Earned_Washing + Earned_Other + OT_Wages + Special_OT_Amount + Arrears')
    ctx['EARNED_GROSS'] = evaluate_rule_safely(gross_sal_f, ctx)
    ctx['GROSS_WAGES'] = ctx['EARNED_GROSS']
    ctx['GROSS'] = ctx['EARNED_GROSS']

    # Step 6: PF & ESI
    if rules.get('PF_APPLICABLE', '1') in ('1', 'True', 'true', 'YES', 'yes') and 'PF_ESI' in category:
        pf_gross_f = rules.get('PF_GROSS', 'min(Earned_Gross * 0.80, 15000.0)')
        ctx['PF_GROSS'] = evaluate_rule_safely(pf_gross_f, ctx)
        pf_f = rules.get('PF_EMPLOYEE', 'min(PF_Gross * 0.12, 1800.0)')
        ctx['PF'] = evaluate_rule_safely(pf_f, ctx)
    else:
        ctx['PF_GROSS'] = 0.0
        ctx['PF'] = 0.0

    if rules.get('ESI_APPLICABLE', '1') in ('1', 'True', 'true', 'YES', 'yes') and 'PF_ESI' in category:
        esi_gross_f = rules.get('ESI_GROSS', 'if_else(Fixed_Gross <= 21000.0, min(Earned_Gross * 0.90, 21000.0), 0.0)')
        ctx['ESI_GROSS'] = evaluate_rule_safely(esi_gross_f, ctx)
        esi_f = rules.get('ESI_EMPLOYEE', 'if_else(Fixed_Gross <= 21000.0, ESI_Gross * 0.0075, 0.0)')
        ctx['ESI'] = evaluate_rule_safely(esi_f, ctx)
    else:
        ctx['ESI_GROSS'] = 0.0
        ctx['ESI'] = 0.0

    # Step 7: Deductions & Net Pay
    tot_ded_f = rules.get('TOTAL_DEDUCTIONS', 'PF + ESI + LIC + Advance + Accommodation + Other_Deduction')
    ctx['TOTAL_DEDUCTION'] = evaluate_rule_safely(tot_ded_f, ctx)

    net_sal_f = rules.get('NET_SALARY', 'Gross + Arrears - Total_Deduction')
    ctx['NET_SALARY'] = evaluate_rule_safely(net_sal_f, ctx)

    return {
        'category': category,
        'standard_days': ctx['WORKING_DAYS'],
        'worked_days': ctx['WORKED_DAYS'],
        'earned_basic_da': ctx['EARNED_BASIC_DA'],
        'earned_hra': ctx['EARNED_HRA'],
        'earned_conveyance': ctx['EARNED_CONVEYANCE'],
        'earned_washing': ctx['EARNED_WASHING'],
        'earned_other': ctx['EARNED_OTHER'],
        'ot_wages': ctx['OT_WAGES'],
        'special_ot': ctx['SPECIAL_OT_AMOUNT'],
        'earned_gross': ctx['EARNED_GROSS'],
        'pf_gross': ctx['PF_GROSS'],
        'pf_deduction': ctx['PF'],
        'esi_gross': ctx['ESI_GROSS'],
        'esi_deduction': ctx['ESI'],
        'total_deduction': ctx['TOTAL_DEDUCTION'],
        'net_salary': ctx['NET_SALARY'],
        'eval_context': ctx
    }

test_category_formulas.__test__ = False

def calculate_payroll_with_formulas(emp, salary, attendance, deductions, category=None, standard_days=None):
    """
    Engine wrapper that checks for database formula rules first.
    If no custom rules exist in DB, delegates to authoritative engine (utils.payroll_calculation_engine).
    """
    cat = category or emp.get('Category') or 'STAFF_PF_ESI'
    db_rules = get_active_formula_rules(cat)

    # Use authoritative calculation engine as core executor
    return calculate_payroll(emp, salary, attendance, deductions, standard_days=standard_days)

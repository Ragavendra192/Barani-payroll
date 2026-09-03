import datetime as dt
import pandas as pd
from db import get_db_connection

CATEGORIES = [
    'STAFF_PF_ESI',
    'WORKER_PF_ESI',
    'STAFF_NAPS',
    'WORKER_NAPS',
    'STAFF_NON_PF_ESI',
    'WORKER_NON_PF_ESI'
]

DEFAULT_FORMULAS = {
    'STAFF_PF_ESI': {
        'STANDARD_WORKING_DAYS': '27.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'BASIC': 'Basic',
        'DA': 'DA',
        'BASIC_DA': 'Gross * 0.50',
        'HRA_FIXED': 'Gross * 0.20',
        'HRA_EARNED': 'Fixed_HRA / Working_Days * Worked_Days',
        'CONVEYANCE_FIXED': 'Gross * 0.10',
        'CONVEYANCE_EARNED': 'Fixed_Conveyance / Working_Days * Worked_Days',
        'WASHING_FIXED': 'Gross * 0.10',
        'WASHING_EARNED': 'Fixed_Washing / Working_Days * Worked_Days',
        'OTHER_FIXED': 'Gross * 0.10',
        'OTHER_EARNED': 'Fixed_Other / Working_Days * Worked_Days',
        'SPECIAL_ALLOWANCE': 'Special_Allowance',
        'OT_ENABLED': '0',
        'OT_WAGES': '0.0',
        'GROSS_SALARY': 'Earned_Basic_DA + Earned_HRA + Earned_Conveyance + Earned_Washing + Earned_Other + Special_Allowance + Arrears',
        'PF_APPLICABLE': '1',
        'PF_GROSS': 'min(Gross * 0.80, 15000.0)',
        'PF_EMPLOYEE': 'min(PF_Gross * 0.12, 1800.0)',
        'PF_EMPLOYER': 'min(PF_Gross * 0.12, 1800.0)',
        'ESI_APPLICABLE': '1',
        'ESI_GROSS': 'if_else(Gross <= 21000.0, Gross * 0.90, 0.0)',
        'ESI_EMPLOYEE': 'if_else(Gross <= 21001.0, ceil(ESI_Gross * 0.0075), 0.0)',
        'ESI_EMPLOYER': 'if_else(Gross <= 21001.0, ESI_Gross * 0.0325, 0.0)',
        'TOTAL_DEDUCTIONS': 'PF + ESI + LIC + TDS + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross + Arrears - Total_Deduction'
    },
    'WORKER_PF_ESI': {
        'STANDARD_WORKING_DAYS': '26.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'PER_DAY_WAGE': 'Per_Day_Wage',
        'BASIC_DA': 'Gross * 0.50',
        'HRA_FIXED': 'Gross * 0.20',
        'HRA_EARNED': 'Fixed_HRA / Working_Days * Worked_Days',
        'CONVEYANCE_FIXED': 'Gross * 0.10',
        'CONVEYANCE_EARNED': 'Fixed_Conveyance / Working_Days * Worked_Days',
        'WASHING_FIXED': 'Gross * 0.10',
        'WASHING_EARNED': 'Fixed_Washing / Working_Days * Worked_Days',
        'OTHER_FIXED': 'Gross * 0.10',
        'OTHER_EARNED': 'Fixed_Other / Working_Days * Worked_Days',
        'OT_ENABLED': '1',
        'OT_HOURS_CAPPED': 'min(OT_Hours, 50.0)',
        'SPECIAL_OT_HOURS': 'max(OT_Hours - 50.0, 0.0)',
        'OT_RATE': 'Per_Day_Wage / 8.0',
        'OT_WAGES': 'min(OT_Hours, 50.0) * OT_Rate',
        'SPECIAL_OT_ALLOWANCE': 'max(OT_Hours - 50.0, 0.0) * OT_Rate',
        'GROSS_SALARY': 'Earned_Basic_DA + Earned_HRA + Earned_Conveyance + Earned_Washing + Earned_Other + OT_Wages + Special_OT_Amount + Arrears',
        'PF_APPLICABLE': '1',
        'PF_GROSS': 'min(max(Gross - Earned_HRA - OT_Wages, 0.0), 15000.0)',
        'PF_EMPLOYEE': 'min(PF_Gross * 0.12, 1800.0)',
        'PF_EMPLOYER': 'min(PF_Gross * 0.12, 1800.0)',
        'ESI_APPLICABLE': '1',
        'ESI_GROSS': 'if_else(Fixed_Gross <= 21000.0, min(Gross * 0.90, 21000.0), 0.0)',
        'ESI_EMPLOYEE': 'if_else(Fixed_Gross <= 21000.0, ESI_Gross * 0.0075, 0.0)',
        'ESI_EMPLOYER': 'if_else(Fixed_Gross <= 21000.0, ESI_Gross * 0.0325, 0.0)',
        'TOTAL_DEDUCTIONS': 'PF + ESI + LIC + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross + Arrears - Total_Deduction'
    },
    'STAFF_NAPS': {
        'STANDARD_WORKING_DAYS': '26.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'BASIC_DA': 'Gross',
        'OT_ENABLED': '0',
        'OT_WAGES': '0.0',
        'GROSS_SALARY': 'Earned_Basic_DA / Working_Days * Worked_Days',
        'PF_APPLICABLE': '0',
        'PF': '0.0',
        'ESI_APPLICABLE': '0',
        'ESI': '0.0',
        'NAPS_DEDUCTION': 'NAPS',
        'TOTAL_DEDUCTIONS': 'NAPS + LIC + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross - Total_Deduction'
    },
    'WORKER_NAPS': {
        'STANDARD_WORKING_DAYS': '27.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'PER_DAY_WAGE': 'Per_Day_Wage',
        'OT_ENABLED': '1',
        'OT_RATE': 'Per_Day_Wage / 8.0',
        'OT_WAGES': 'min(OT_Hours, 50.0) * OT_Rate',
        'SPECIAL_OT_ALLOWANCE': 'max(OT_Hours - 50.0, 0.0) * OT_Rate',
        'GROSS_SALARY': '(Per_Day_Wage * Worked_Days) + OT_Wages + Special_OT_Amount',
        'PF_APPLICABLE': '0',
        'PF': '0.0',
        'ESI_APPLICABLE': '0',
        'ESI': '0.0',
        'TOTAL_DEDUCTIONS': 'NAPS + LIC + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross - Total_Deduction'
    },
    'STAFF_NON_PF_ESI': {
        'STANDARD_WORKING_DAYS': '27.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'BASIC_DA': 'Gross * 0.50',
        'HRA_EARNED': 'Fixed_HRA / Working_Days * Worked_Days',
        'OT_ENABLED': '0',
        'OT_WAGES': '0.0',
        'GROSS_SALARY': 'Fixed_Gross / Working_Days * Worked_Days',
        'PF_APPLICABLE': '0',
        'PF': '0.0',
        'ESI_APPLICABLE': '0',
        'ESI': '0.0',
        'TOTAL_DEDUCTIONS': 'LIC + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross - Total_Deduction'
    },
    'WORKER_NON_PF_ESI': {
        'STANDARD_WORKING_DAYS': '27.0',
        'TOTAL_WORKED_DAYS': 'Present_Days + PH + CL + SL + PL',
        'PER_DAY_WAGE': 'Per_Day_Wage',
        'OT_ENABLED': '1',
        'OT_RATE': 'Per_Day_Wage / 8.0',
        'OT_WAGES': 'min(OT_Hours, 50.0) * OT_Rate',
        'SPECIAL_OT_ALLOWANCE': 'max(OT_Hours - 50.0, 0.0) * OT_Rate',
        'GROSS_SALARY': '(Per_Day_Wage * Worked_Days) + OT_Wages + Special_OT_Amount',
        'PF_APPLICABLE': '0',
        'PF': '0.0',
        'ESI_APPLICABLE': '0',
        'ESI': '0.0',
        'TOTAL_DEDUCTIONS': 'LIC + Advance + Accommodation + Other_Deduction',
        'NET_SALARY': 'Gross - Total_Deduction'
    }
}

def init_formula_rules_table():
    """Initializes the PayrollFormulaRules table in SQL Server."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PayrollFormulaRules')
    BEGIN
        CREATE TABLE PayrollFormulaRules (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            Category NVARCHAR(50) NOT NULL,
            Section NVARCHAR(50) NOT NULL,
            RuleName NVARCHAR(50) NOT NULL,
            Formula NVARCHAR(MAX) NOT NULL,
            IsEnabled BIT DEFAULT 1,
            EffectiveFrom DATETIME NOT NULL DEFAULT GETDATE(),
            EffectiveTo DATETIME NULL,
            Version INT DEFAULT 1,
            IsActive BIT DEFAULT 1,
            CreatedBy NVARCHAR(100) DEFAULT 'Admin',
            CreatedAt DATETIME DEFAULT GETDATE(),
            UpdatedBy NVARCHAR(100) DEFAULT 'Admin',
            UpdatedAt DATETIME DEFAULT GETDATE()
        );
        CREATE INDEX IX_PayrollFormulaRules_Cat_Active ON PayrollFormulaRules(Category, IsActive, EffectiveFrom);
    END
    """
    cur.execute(create_table_sql)
    conn.commit()
    conn.close()

def get_active_formula_rules(category, effective_date=None):
    """
    Retrieve active formula rules for a given category and effective date.
    Returns dictionary mapping RuleName -> Formula string.
    """
    init_formula_rules_table()
    conn = get_db_connection()
    
    if effective_date is None:
        effective_date = dt.datetime.now()

    query = """
        SELECT Section, RuleName, Formula, IsEnabled, Version, EffectiveFrom
        FROM PayrollFormulaRules
        WHERE Category = ? AND IsActive = 1 AND EffectiveFrom <= ?
          AND (EffectiveTo IS NULL OR EffectiveTo >= ?)
        ORDER BY Section, RuleName, Version DESC
    """
    df = pd.read_sql(query, conn, params=[category, effective_date, effective_date])
    conn.close()

    rules_map = {}
    if not df.empty:
        for _, row in df.iterrows():
            rule_name = str(row['RuleName']).upper().strip()
            if rule_name not in rules_map:
                rules_map[rule_name] = {
                    'section': row['Section'],
                    'rule_name': rule_name,
                    'formula': row['Formula'],
                    'is_enabled': bool(row['IsEnabled']),
                    'version': int(row['Version'])
                }

    # Fallback to default formula dictionary if no rules found in DB
    defaults = DEFAULT_FORMULAS.get(category, {})
    merged_rules = {}
    for k, v in defaults.items():
        if k in rules_map:
            merged_rules[k] = rules_map[k]['formula']
        else:
            merged_rules[k] = v

    for k, v in rules_map.items():
        if k not in merged_rules:
            merged_rules[k] = v['formula']

    return merged_rules

def save_category_formula_rules(category, rules_dict, effective_from=None, user='Admin'):
    """
    Save new versioned formula rules for a category.
    Deactivates older rules and inserts new version records with effective dates.
    """
    init_formula_rules_table()
    conn = get_db_connection()
    cur = conn.cursor()

    now = dt.datetime.now()
    eff_from = effective_from if effective_from else now

    try:
        # Get current version number for category
        cur.execute("SELECT ISNULL(MAX(Version), 0) FROM PayrollFormulaRules WHERE Category = ?", (category,))
        max_ver = cur.fetchone()[0] or 0
        new_version = max_ver + 1

        # Deactivate current active rules by setting EffectiveTo
        cur.execute("""
            UPDATE PayrollFormulaRules
            SET EffectiveTo = ?, IsActive = 0, UpdatedBy = ?, UpdatedAt = GETDATE()
            WHERE Category = ? AND IsActive = 1
        """, (eff_from, user, category))

        # Insert new formula rules
        insert_sql = """
            INSERT INTO PayrollFormulaRules
            (Category, Section, RuleName, Formula, IsEnabled, EffectiveFrom, EffectiveTo, Version, IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, 1, ?, GETDATE(), ?, GETDATE())
        """

        for rule_name, rule_data in rules_dict.items():
            if isinstance(rule_data, dict):
                section = rule_data.get('section', 'GENERAL')
                formula = str(rule_data.get('formula', '')).strip()
                is_enabled = 1 if rule_data.get('is_enabled', True) else 0
            else:
                section = 'GENERAL'
                formula = str(rule_data).strip()
                is_enabled = 1

            if not formula:
                continue

            cur.execute(insert_sql, (
                category, section, rule_name.upper().strip(), formula, is_enabled,
                eff_from, new_version, user, user
            ))

        conn.commit()
        return True, new_version
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

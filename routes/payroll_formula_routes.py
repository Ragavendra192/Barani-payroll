from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from config import PAYROLL_FORMULA_ADMIN_PASSWORD
from models.payroll_formula_rules import get_active_formula_rules, save_category_formula_rules, CATEGORIES, DEFAULT_FORMULAS
from services.payroll_formula_validator import validate_formula_syntax, detect_dependency_cycles
from services.payroll_formula_engine import test_category_formulas

payroll_formulas_bp = Blueprint('payroll_formulas', __name__, url_prefix='/payroll-formulas')

def require_formula_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('payroll_formula_admin'):
            if request.is_json or request.path.endswith('/save') or request.path.endswith('/test') or request.path.endswith('/validate'):
                return jsonify({'success': False, 'error': 'Unauthorized admin access required', 'authenticated': False}), 401
            return render_template('payroll_formulas.html', is_authenticated=False)
        return f(*args, **kwargs)
    return decorated_function

@payroll_formulas_bp.route('/', methods=['GET'])
def index():
    is_authenticated = session.get('payroll_formula_admin', False)
    category = request.args.get('category', 'STAFF_PF_ESI')
    if category not in CATEGORIES:
        category = 'STAFF_PF_ESI'

    rules = {}
    if is_authenticated:
        rules = get_active_formula_rules(category)

    return render_template(
        'payroll_formulas.html',
        is_authenticated=is_authenticated,
        category=category,
        categories=CATEGORIES,
        rules=rules,
        default_formulas=DEFAULT_FORMULAS
    )

@payroll_formulas_bp.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '').strip()
    if password == PAYROLL_FORMULA_ADMIN_PASSWORD:
        session['payroll_formula_admin'] = True
        flash('Successfully authenticated as Payroll Formula Admin.', 'success')
        return redirect(url_for('payroll_formulas.index'))
    else:
        flash('Invalid password', 'danger')
        return render_template('payroll_formulas.html', is_authenticated=False, error_msg='Invalid password')

@payroll_formulas_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('payroll_formula_admin', None)
    flash('Logged out of Payroll Formula Configuration.', 'info')
    return redirect(url_for('payroll_formulas.index'))

@payroll_formulas_bp.route('/get-rules/<category>', methods=['GET'])
@require_formula_admin
def get_rules(category):
    if category not in CATEGORIES:
        return jsonify({'success': False, 'error': 'Invalid category'}), 400
    rules = get_active_formula_rules(category)
    return jsonify({'success': True, 'category': category, 'rules': rules})

@payroll_formulas_bp.route('/validate', methods=['POST'])
@require_formula_admin
def validate_single_formula():
    data = request.get_json() or {}
    formula = data.get('formula', '')
    is_val, msg, vars_found = validate_formula_syntax(formula)
    return jsonify({
        'success': is_val,
        'message': msg,
        'variables': list(vars_found)
    })

@payroll_formulas_bp.route('/test', methods=['POST'])
@require_formula_admin
def test_formulas():
    data = request.get_json() or {}
    category = data.get('category', 'STAFF_PF_ESI')
    sample_inputs = data.get('sample_inputs', {})
    custom_rules = data.get('rules', None)

    if category not in CATEGORIES:
        return jsonify({'success': False, 'error': 'Invalid category'}), 400

    try:
        test_result = test_category_formulas(category, sample_inputs, custom_rules=custom_rules)
        return jsonify({'success': True, 'result': test_result})
    except Exception as e:
        return jsonify({'success': False, 'error': f"Test evaluation error: {str(e)}"}), 400

@payroll_formulas_bp.route('/save', methods=['POST'])
@require_formula_admin
def save_rules():
    data = request.get_json() or request.form.to_dict()
    category = data.get('category')
    rules = data.get('rules', {})

    if not category or category not in CATEGORIES:
        return jsonify({'success': False, 'error': 'Invalid payroll category'}), 400

    # Step 1: Validate individual formula syntax
    syntax_errors = []
    rule_dict_for_cycle = {}
    for r_name, r_val in rules.items():
        if isinstance(r_val, dict):
            f_str = r_val.get('formula', '')
        else:
            f_str = str(r_val)

        f_str = str(f_str).strip()
        if f_str:
            rule_dict_for_cycle[r_name] = f_str
            is_val, msg, _ = validate_formula_syntax(f_str)
            if not is_val:
                syntax_errors.append(f"Rule '{r_name}': {msg}")

    if syntax_errors:
        return jsonify({'success': False, 'error': 'Formula syntax error', 'details': syntax_errors}), 400

    # Step 2: Cycle detection
    has_cycle, cycle_msg = detect_dependency_cycles(rule_dict_for_cycle)
    if has_cycle:
        return jsonify({'success': False, 'error': cycle_msg}), 400

    # Step 3: Save to SQL Server table
    try:
        ok, version = save_category_formula_rules(category, rules, user='Admin')
        return jsonify({
            'success': True,
            'message': f"Payroll formulas for '{category}' saved successfully (Version {version}).",
            'version': version
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Database save error: {str(e)}"}), 500

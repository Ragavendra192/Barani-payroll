import ast
import math
from decimal import Decimal, ROUND_HALF_UP

ALLOWED_VARIABLES = {
    # Employee Master / Fixed Salary Variables
    'BASIC', 'DA', 'HRA', 'CONVEYANCE', 'WASHING', 'OTHER_ALLOWANCE', 'SPECIAL_ALLOWANCE', 'PER_DAY_WAGE',
    'FIXED_BASIC', 'FIXED_DA', 'FIXED_HRA', 'FIXED_CONVEYANCE', 'FIXED_WASHING', 'FIXED_OTHER', 'FIXED_GROSS',

    # Attendance Variables
    'WORKING_DAYS', 'PRESENT_DAYS', 'PH', 'CL', 'SL', 'PL', 'EL', 'NH', 'CH', 'WORKED_DAYS', 'TOTAL_WORKED_DAYS',

    # Overtime Variables
    'OT_HOURS', 'ACT_OT_HOURS', 'CAPPED_OT_HOURS', 'SPECIAL_OT_HOURS', 'OT_RATE', 'OT_WAGES', 'SPECIAL_OT_AMOUNT', 'SPECIAL_OT_ALLOWANCE',

    # Earned Salary Variables
    'EARNED_BASIC', 'EARNED_DA', 'EARNED_BASIC_DA', 'EARNED_HRA', 'EARNED_CONVEYANCE', 'EARNED_WASHING', 'EARNED_OTHER', 'EARNED_SPECIAL',

    # Payroll Summary & Deductions Variables
    'GROSS', 'GROSS_WAGES', 'EARNED_GROSS', 'PF_GROSS', 'ESI_GROSS', 'PF', 'PF_DEDUCTION', 'ESI', 'ESI_DEDUCTION',
    'NAPS', 'NAPS_DEDUCTION', 'PT', 'MESS', 'LIC', 'TDS', 'ADVANCE', 'ADVANCE_DEDUCTION', 'ACCOMMODATION', 'OTHER_DEDUCTION',
    'ARREARS', 'TOTAL_DEDUCTION', 'TOTAL_DEDUCTIONS', 'NET_SALARY', 'NET_PAY'
}

ALLOWED_FUNCTIONS = {
    'min': min,
    'max': max,
    'ceil': math.ceil,
    'floor': math.floor,
    'round': round,
    'abs': abs,
    'int': int,
    'float': float,
    'if_else': lambda cond, true_val, false_val: true_val if cond else false_val
}

_allowed_node_list = [
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Name, ast.Load, ast.Call, ast.Tuple, ast.IfExp, ast.Compare,
    ast.BoolOp, ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE,
    ast.Gt, ast.GtE, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
    ast.Pow, ast.USub, ast.UAdd
]
if hasattr(ast, 'Num'):
    _allowed_node_list.append(ast.Num)

ALLOWED_NODES = tuple(_allowed_node_list)

def validate_formula_syntax(formula_str, extra_vars=None):
    """
    Validates mathematical formula string for safety, parentheses, operators, and allowed variables.
    Returns: (is_valid, message, variables_found_set)
    """
    if not formula_str or not str(formula_str).strip():
        return False, "Formula string cannot be empty", set()

    clean_str = str(formula_str).strip()

    try:
        parsed_ast = ast.parse(clean_str, mode='eval')
    except SyntaxError as se:
        return False, f"Invalid formula syntax: {se.msg} at position {se.offset}", set()
    except Exception as e:
        return False, f"Syntax error: {str(e)}", set()

    allowed_vars_pool = set(ALLOWED_VARIABLES)
    if extra_vars:
        allowed_vars_pool.update(str(v).upper() for v in extra_vars)

    vars_found = set()

    for node in ast.walk(parsed_ast):
        if not isinstance(node, ALLOWED_NODES):
            return False, f"Forbidden expression syntax or operator: '{type(node).__name__}'", set()

        if isinstance(node, ast.Name):
            var_name = node.id
            upper_var = var_name.upper()
            if upper_var not in allowed_vars_pool and var_name not in ALLOWED_FUNCTIONS:
                return False, f"Unauthorized variable or function reference: '{var_name}'", set()
            if upper_var in allowed_vars_pool:
                vars_found.add(upper_var)

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                return False, "Forbidden dynamic function call", set()
            func_name = node.func.id
            if func_name not in ALLOWED_FUNCTIONS:
                return False, f"Unauthorized function call: '{func_name}'", set()

    return True, "Valid formula", vars_found

def detect_dependency_cycles(rules_dict):
    """
    Detects circular dependencies in a category's formula dictionary.
    Returns: (has_cycle, cycle_path_message)
    """
    rules_upper = {str(k).upper().strip(): str(v) for k, v in rules_dict.items()}

    graph = {}
    for rule_name, formula in rules_upper.items():
        is_val, msg, vars_found = validate_formula_syntax(formula, extra_vars=set(rules_upper.keys()))
        if is_val:
            graph[rule_name] = [v for v in vars_found if v in rules_upper]
        else:
            graph[rule_name] = []

    visited = {}
    path = []

    def dfs(node):
        visited[node] = 1 # Visiting
        path.append(node)

        for neighbor in graph.get(node, []):
            if visited.get(neighbor) == 1:
                cycle_start = path.index(neighbor)
                cycle_path = path[cycle_start:] + [neighbor]
                return True, " -> ".join(cycle_path)
            elif visited.get(neighbor) == 0 or neighbor not in visited:
                has_cycle, msg = dfs(neighbor)
                if has_cycle:
                    return True, msg

        path.pop()
        visited[node] = 2 # Visited
        return False, ""

    for node in graph:
        if node not in visited:
            has_c, cycle_msg = dfs(node)
            if has_c:
                return True, f"Formula dependency cycle detected: {cycle_msg}"

    return False, ""

def evaluate_formula(formula_str, context_vars):
    """
    Safely evaluates formula string against a dictionary of numeric context variables using AST.
    Returns: float or Decimal result.
    """
    is_val, msg, _ = validate_formula_syntax(formula_str, extra_vars=set(context_vars.keys()))
    if not is_val:
        raise ValueError(f"Cannot evaluate invalid formula: {msg}")

    eval_context = {}
    for k, v in ALLOWED_FUNCTIONS.items():
        eval_context[k] = v

    for k, v in context_vars.items():
        up_k = str(k).upper()
        try:
            val = float(v) if v is not None else 0.0
        except (ValueError, TypeError):
            val = 0.0
        eval_context[up_k] = val
        eval_context[str(k)] = val

    parsed_ast = ast.parse(str(formula_str).strip(), mode='eval')

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return eval_context.get(node.id.upper(), eval_context.get(node.id, 0.0))
        elif isinstance(node, ast.UnaryOp):
            val = eval_node(node.operand)
            if isinstance(node.op, ast.USub):
                return -val
            elif isinstance(node.op, ast.UAdd):
                return +val
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right if right != 0 else 0.0
            elif isinstance(node.op, ast.Mod):
                return left % right if right != 0 else 0.0
            elif isinstance(node.op, ast.Pow):
                return left ** right
        elif isinstance(node, ast.IfExp):
            cond = eval_node(node.test)
            return eval_node(node.body) if cond else eval_node(node.orelse)
        elif isinstance(node, ast.Compare):
            left = eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = eval_node(comparator)
                if isinstance(op, ast.Eq) and not (left == right): return False
                elif isinstance(op, ast.NotEq) and not (left != right): return False
                elif isinstance(op, ast.Lt) and not (left < right): return False
                elif isinstance(op, ast.LtE) and not (left <= right): return False
                elif isinstance(op, ast.Gt) and not (left > right): return False
                elif isinstance(op, ast.GtE) and not (left >= right): return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(eval_node(v) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(eval_node(v) for v in node.values)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            args = [eval_node(arg) for arg in node.args]
            func = ALLOWED_FUNCTIONS.get(func_name)
            if func:
                return func(*args)
            return 0.0
        return 0.0

    res = eval_node(parsed_ast)
    try:
        return float(Decimal(str(res)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except Exception:
        return float(res)

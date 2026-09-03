import datetime as dt
from flask import Blueprint, render_template
from db import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Active employee counts by category
    cur.execute("""
        SELECT Category, COUNT(*)
        FROM EmployeeMaster
        WHERE Status = 'Active'
        GROUP BY Category
    """)
    cat_counts = dict(cur.fetchall())

    # Active count aggregates
    total_staff = sum(v for k, v in cat_counts.items() if k.startswith('STAFF'))
    total_workers = sum(v for k, v in cat_counts.items() if k.startswith('WORKER'))
    total_naps = sum(v for k, v in cat_counts.items() if 'NAPS' in k)
    total_pf_esi = sum(v for k, v in cat_counts.items() if 'PF_ESI' in k)
    total_non_pf_esi = sum(v for k, v in cat_counts.items() if 'NON_PF_ESI' in k)

    # Current month payroll metrics (e.g. July 2026 or latest period)
    cur.execute("SELECT TOP 1 Payroll_Year, Payroll_Month FROM PayrollPeriod ORDER BY Payroll_Year DESC, Payroll_Month DESC")
    latest_period = cur.fetchone()
    
    if latest_period:
        curr_year, curr_month = latest_period[0], latest_period[1]
        cur.execute("""
            SELECT 
                COUNT(*), ISNULL(SUM(Gross_Wages), 0.0), ISNULL(SUM(OT_Wages + Special_Allowance_Earned), 0.0),
                ISNULL(SUM(PF_Deduction), 0.0), ISNULL(SUM(ESI_Deduction), 0.0),
                ISNULL(SUM(Total_Deduction), 0.0), ISNULL(SUM(Net_Salary), 0.0)
            FROM PayrollTransaction t
            JOIN PayrollPeriod p ON t.PayrollPeriod_ID = p.PayrollPeriod_ID
            WHERE p.Payroll_Year = ? AND p.Payroll_Month = ?
        """, (curr_year, curr_month))
        p_stats = cur.fetchone()
    else:
        now = dt.datetime.now()
        curr_year, curr_month = now.year, now.month
        p_stats = (0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    conn.close()

    summary = {
        'total_staff': total_staff,
        'total_workers': total_workers,
        'total_naps': total_naps,
        'total_pf_esi': total_pf_esi,
        'total_non_pf_esi': total_non_pf_esi,
        'cat_counts': cat_counts,
        'curr_year': curr_year,
        'curr_month': curr_month,
        'month_emp_count': p_stats[0],
        'month_gross': float(p_stats[1]),
        'month_ot': float(p_stats[2]),
        'month_pf': float(p_stats[3]),
        'month_esi': float(p_stats[4]),
        'month_deductions': float(p_stats[5]),
        'month_net': float(p_stats[6])
    }

    return render_template('dashboard.html', summary=summary)

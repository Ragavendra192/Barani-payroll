import datetime as dt
from flask import Blueprint, render_template, request
from models.payroll_transaction import get_payroll_transactions
from services.excel_service import generate_monthly_salary_statement_excel

history_bp = Blueprint('history', __name__, url_prefix='/history')

CATEGORIES = [
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS'),
    ('WORKER_NAPS', 'Worker — NAPS'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@history_bp.route('/')
def index():
    now = dt.datetime.now()
    year = request.args.get('year', 2026, type=int)
    month = request.args.get('month', 7, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '').strip()

    records = get_payroll_transactions(year, month, category=category if category else None, search=search if search else None)

    tot_gross = sum(r['Gross_Wages'] for r in records)
    tot_ded = sum(r['Total_Deduction'] for r in records)
    tot_net = sum(r['Net_Salary'] for r in records)

    return render_template(
        'history/history.html',
        year=year,
        month=month,
        category=category,
        categories=CATEGORIES,
        search=search,
        records=records,
        total_gross=tot_gross,
        total_ded=tot_ded,
        total_net=tot_net
    )

@history_bp.route('/download/excel/<int:year>/<int:month>')
def download_excel(year, month):
    excel_buf = generate_monthly_salary_statement_excel(year, month)
    filename = f"BHIPL_UNIT_1_SALARY_STATEMENT_{year}_{month:02d}.xlsx"
    return send_file(
        excel_buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

import datetime as dt
from flask import Blueprint, render_template, request, send_file
from models.payroll_transaction import get_payroll_transactions
from services.excel_service import generate_monthly_salary_statement_excel

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

CATEGORIES = [
    ('STAFF_PF_ESI', 'Staff — PF / ESI'),
    ('WORKER_PF_ESI', 'Worker — PF / ESI'),
    ('STAFF_NAPS', 'Staff — NAPS'),
    ('WORKER_NAPS', 'Worker — NAPS'),
    ('STAFF_NON_PF_ESI', 'Staff — Non PF / ESI'),
    ('WORKER_NON_PF_ESI', 'Worker — Non PF / ESI')
]

@reports_bp.route('/')
def index():
    now = dt.datetime.now()
    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 7))
    category = request.args.get('category', 'STAFF_PF_ESI')

    records = get_payroll_transactions(year, month, category=category)

    tot_gross = sum(r['Gross_Wages'] for r in records)
    tot_pf = sum(r['PF_Deduction'] for r in records)
    tot_esi = sum(r['ESI_Deduction'] for r in records)
    tot_ded = sum(r['Total_Deduction'] for r in records)
    tot_net = sum(r['Net_Salary'] for r in records)

    return render_template(
        'reports/report_view.html',
        year=year,
        month=month,
        category=category,
        categories=CATEGORIES,
        records=records,
        tot_gross=tot_gross,
        tot_pf=tot_pf,
        tot_esi=tot_esi,
        tot_ded=tot_ded,
        tot_net=tot_net
    )

@reports_bp.route('/export/excel/<int:year>/<int:month>')
def export_excel(year, month):
    excel_buf = generate_monthly_salary_statement_excel(year, month)
    filename = f"BHIPL_UNIT_1_SALARY_STATEMENT_{year}_{month:02d}.xlsx"
    return send_file(
        excel_buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

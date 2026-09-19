import io
import zipfile
import datetime as dt
from flask import render_template
from xhtml2pdf import pisa
from models.payroll_transaction import get_payroll_transactions
from models.employee import get_all_employees
from utils.num_to_words import amount_in_words

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def clean_emp_no(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def get_payslip_data(year, month, emp_no=None, category=None):
    """Retrieve payroll transaction and merge with EmployeeMaster for payslip rendering."""
    records = get_payroll_transactions(year, month, category=category)
    all_emps = {clean_emp_no(e['Emp_No']): e for e in get_all_employees(status=None)}
    
    enriched = []
    for r in records:
        emp_key = clean_emp_no(r['Emp_No'])
        emp_master = all_emps.get(emp_key) or {}
        r['Emp_No'] = emp_key
        
        # Convert decimal values to floats to prevent Jinja type mismatch
        for k, v in list(r.items()):
            if v is not None and not isinstance(v, (bool, str, list, dict)):
                try:
                    r[k] = float(v)
                except Exception:
                    pass

        # Merge master info
        r['Father_Name'] = emp_master.get('Father_Name') or '-'
        r['DOB'] = emp_master.get('DOB') or '-'
        r['DOJ'] = emp_master.get('DOJ') or '-'
        r['Bank_Name'] = emp_master.get('Bank_Name') or emp_master.get('Bank') or '-'
        r['Account_No'] = emp_master.get('Bank_Acc_No') or emp_master.get('Account_No') or '-'
        r['IFSC_Code'] = emp_master.get('Bank_IFSC') or emp_master.get('IFSC_Code') or '-'
        r['UAN'] = emp_master.get('UAN') or '-'
        r['ESI_No'] = emp_master.get('ESI_No') or '-'
        
        # Salary component master fallbacks
        r['Master_Basic'] = float(emp_master.get('Basic_Pay', 0.0) or 0.0)
        r['Master_DA'] = float(emp_master.get('DA', 0.0) or 0.0)
        r['Master_HRA'] = float(emp_master.get('HRA', 0.0) or 0.0)
        r['Master_Conveyance'] = float(emp_master.get('Conveyance_Allowance', 0.0) or 0.0)
        r['Master_Washing'] = float(emp_master.get('Washing_Allowance', 0.0) or 0.0)
        r['Master_Other'] = float(emp_master.get('Other_Allowance', 0.0) or 0.0)
        
        enriched.append(r)

    if emp_no:
        emp_no_str = clean_emp_no(emp_no)
        enriched = [r for r in enriched if clean_emp_no(r['Emp_No']) == emp_no_str]
        
    return enriched

def fetch_resources(uri, rel):
    import os
    if uri.startswith('/static/'):
        path = os.path.join(os.path.dirname(__file__), '..', uri.lstrip('/'))
        return os.path.abspath(path)
    return uri

def is_worker(row):
    cat = str(row.get('Category') or '').upper()
    emp_type = str(row.get('Employee_Type') or '').upper()
    return 'WORKER' in cat or emp_type == 'WORKER'

def get_payslip_template(row):
    return 'payslips/worker_payslip.html' if is_worker(row) else 'payslips/payslip_template.html'

def get_worker_deductions_list(row):
    deductions = []
    if float(row.get('PF_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('PF', float(row.get('PF_Deduction', 0.0))))
    if float(row.get('Advance_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('ADVANCE', float(row.get('Advance_Deduction', 0.0))))
    if float(row.get('ESI_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('ESI', float(row.get('ESI_Deduction', 0.0))))
    if float(row.get('LIC_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('LIC', float(row.get('LIC_Deduction', 0.0))))
    if float(row.get('TDS_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('TDS', float(row.get('TDS_Deduction', 0.0))))
    if float(row.get('NAPS_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('NAPS', float(row.get('NAPS_Deduction', 0.0))))
    if float(row.get('Accommodation_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('ACCOMMODATION', float(row.get('Accommodation_Deduction', 0.0))))
    if float(row.get('Other_Deduction', 0.0) or 0.0) > 0:
        deductions.append(('OTHERS', float(row.get('Other_Deduction', 0.0))))
    return deductions

def generate_payslip_pdf(year, month, emp_no, category=None):
    """Renders single A4 PDF payslip for a given employee."""
    records = get_payslip_data(year, month, emp_no=emp_no, category=category)
    if not records:
        return None, None

    row = records[0]
    month_name = MONTH_NAMES[month]
    net_in_words = amount_in_words(row.get('Net_Salary', 0.0))
    template_name = get_payslip_template(row)
    deductions_list = get_worker_deductions_list(row)

    html = render_template(
        template_name,
        row=row,
        month_name=month_name,
        year=year,
        net_in_words=net_in_words,
        deductions_list=deductions_list,
        is_pdf=True
    )

    pdf_io = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_io, link_callback=fetch_resources)
    pdf_io.seek(0)

    if pisa_status.err:
        return None, None

    filename = f"Payslip_{row['Emp_No']}_{str(row['Employee_Name']).replace(' ', '_')}_{year}_{month:02d}.pdf"
    return pdf_io, filename

def generate_all_payslips_zip(year, month, category=None):
    """Bundles all payslips for a given month/year into a ZIP archive."""
    records = get_payslip_data(year, month, category=category)
    if not records:
        return None

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for row in records:
            pdf_io, pdf_name = generate_payslip_pdf(year, month, row['Emp_No'], category=row['Category'])
            if pdf_io:
                zip_file.writestr(pdf_name, pdf_io.getvalue())

    zip_io.seek(0)
    return zip_io

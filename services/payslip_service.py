import io
import zipfile
import datetime as dt
from flask import render_template
from xhtml2pdf import pisa
from models.payroll_transaction import get_payroll_transactions
from models.employee import get_all_employees
from models.payroll_period_settings import calculate_month_working_days
from utils.num_to_words import amount_in_words

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

IFSC_BANK_MAP = {
    "SBIN": "State Bank of India",
    "CNRB": "Canara Bank",
    "IOBA": "Indian Overseas Bank",
    "IDIB": "Indian Bank",
    "UBIN": "Union Bank of India",
    "BARB": "Bank of Baroda",
    "PUNB": "Punjab National Bank",
    "HDFC": "HDFC Bank",
    "ICIC": "ICICI Bank",
    "UTIB": "Axis Bank",
    "KVBL": "Karur Vysya Bank",
    "CIUB": "City Union Bank",
    "TMBL": "Tamilnad Mercantile Bank",
    "FDRL": "Federal Bank",
    "KKBK": "Kotak Mahindra Bank",
    "INDB": "IndusInd Bank",
    "YESB": "Yes Bank",
    "CORP": "Corporation Bank",
    "SYNB": "Syndicate Bank",
    "ANDB": "Andhra Bank",
    "ALLA": "Allahabad Bank",
    "BKID": "Bank of India",
    "CBIN": "Central Bank of India",
    "MAHB": "Bank of Maharashtra",
    "PSIB": "Punjab & Sind Bank",
    "UCOB": "UCO Bank",
    "DBSS": "DBS Bank",
    "ESFB": "Equitas Small Finance Bank",
    "AUBL": "AU Small Finance Bank",
    "JSFB": "Jana Small Finance Bank",
    "IPOS": "India Post Payments Bank",
    "AIRP": "Airtel Payments Bank",
    "PYTM": "Paytm Payments Bank"
}

def get_bank_name_from_ifsc(ifsc, custom_name=None):
    if custom_name and str(custom_name).strip() and str(custom_name).strip() not in ('-', 'None', 'nan'):
        return str(custom_name).strip()
    if ifsc and isinstance(ifsc, str):
        clean_ifsc = ifsc.strip().upper()
        prefix = clean_ifsc[:4]
        if prefix in IFSC_BANK_MAP:
            return IFSC_BANK_MAP[prefix]
    return '-'

def clean_emp_no(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def clean_val_str(val):
    if val is None:
        return '-'
    s = str(val).strip()
    if s.endswith('.0') and s[:-2].isdigit():
        s = s[:-2]
    if s in ('', '-', 'None', 'nan', 'null'):
        return '-'
    return s

def get_payslip_data(year, month, emp_no=None, category=None):
    """Retrieve payroll transaction and merge with EmployeeMaster for payslip rendering."""
    records = get_payroll_transactions(year, month, category=category)
    all_emps = {clean_emp_no(e['Emp_No']): e for e in get_all_employees(status=None)}
    
    period_info = calculate_month_working_days(year, month)
    sunday_count = float(period_info.get('sunday_count', 4.0))

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

        # Merge master info with comprehensive fallbacks
        father = clean_val_str(emp_master.get('Father_Name') or r.get('Father_Name'))
        r['Father_Name'] = father

        dob = clean_val_str(emp_master.get('DOB') or r.get('DOB'))
        r['DOB'] = dob

        doj = clean_val_str(emp_master.get('DOJ') or r.get('DOJ'))
        r['DOJ'] = doj

        # Bank details
        acc_no = clean_val_str(
            emp_master.get('Bank_Acc_No') or emp_master.get('Account_No') or
            emp_master.get('Bank_Account') or r.get('Bank_Acc_No') or
            r.get('Account_No')
        )
        r['Account_No'] = acc_no
        r['Bank_Acc_No'] = acc_no

        ifsc_code = clean_val_str(
            emp_master.get('Bank_IFSC') or emp_master.get('IFSC_Code') or
            r.get('Bank_IFSC') or r.get('IFSC_Code')
        )
        if ifsc_code != '-':
            ifsc_code = ifsc_code.upper()
        r['IFSC_Code'] = ifsc_code
        r['Bank_IFSC'] = ifsc_code

        custom_bname = emp_master.get('Bank_Name') or emp_master.get('Bank') or r.get('Bank_Name')
        r['Bank_Name'] = get_bank_name_from_ifsc(ifsc_code, custom_bname)

        # UAN & ESI
        uan = clean_val_str(
            emp_master.get('UAN_No') or emp_master.get('UAN') or
            r.get('UAN_No') or r.get('UAN')
        )
        r['UAN'] = uan
        r['UAN_No'] = uan

        esi = clean_val_str(
            emp_master.get('ESI_No') or emp_master.get('ESI') or
            r.get('ESI_No') or r.get('ESI')
        )
        r['ESI_No'] = esi

        # Attendance data as recorded
        r['Present_Days'] = float(r.get('Present_Days') if r.get('Present_Days') is not None else 0.0)
        r['NH'] = float(r.get('NH') or 0.0)
        r['CL'] = float(r.get('CL') or 0.0)
        r['EL'] = float(r.get('EL') or 0.0)
        r['C_Off'] = float(r.get('C_Off') or 0.0)
        r['SL'] = float(r.get('SL') or 0.0)
        r['LOP_Days'] = float(r.get('LOP_Days') or 0.0)
        r['Total_Days'] = float(r.get('Total_Days') if r.get('Total_Days') is not None else 0.0)
        r['Working_Days'] = float(r.get('Working_Days') or period_info.get('default_working_days') or 26.0)
        r['Week_Off'] = float(r.get('Week_Off') or sunday_count)
        r['Paid_Leave'] = float(r['EL'] + r['C_Off'] + r['CL'] + r['SL'])

        # Option A: Leave balances default to 0.0
        r['EL_Op'] = float(r.get('EL_Op') or 0.0)
        r['EL_Cl'] = float(r.get('EL_Cl') or 0.0)
        r['CL_Op'] = float(r.get('CL_Op') or 0.0)
        r['CL_Cl'] = float(r.get('CL_Cl') or 0.0)
        r['C_Off_Op'] = float(r.get('C_Off_Op') or 0.0)
        r['C_Off_Cl'] = float(r.get('C_Off_Cl') or 0.0)
        
        # Salary component master fallbacks
        r['Master_Basic'] = float(emp_master.get('Basic_Pay', 0.0) or 0.0)
        r['Master_DA'] = float(emp_master.get('DA', 0.0) or 0.0)
        r['Master_HRA'] = float(emp_master.get('HRA', 0.0) or 0.0)
        r['Master_Conveyance'] = float(emp_master.get('Conveyance_Allowance', 0.0) or 0.0)
        r['Master_Washing'] = float(emp_master.get('Washing_Allowance', 0.0) or 0.0)
        r['Master_Other'] = float(emp_master.get('Other_Allowance', 0.0) or 0.0)

        # Net Salary rounding: match the rounded integer value on the wage statement
        raw_net = float(r.get('Net_Salary') if r.get('Net_Salary') is not None else (r.get('Net_Pay') or 0.0))
        rounded_net = float(round(raw_net))
        r['Net_Salary_Raw'] = raw_net
        r['Net_Salary'] = rounded_net
        r['Net_Pay'] = rounded_net
        r['Round_Off'] = round(rounded_net - raw_net, 2)
        
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

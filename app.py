import os
import datetime as dt
from flask import Flask, redirect, url_for
from config import SECRET_KEY
from db import init_db, close_db_connection

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

from routes.main_routes import main_bp
from routes.employees import employees_bp
from routes.payroll import payroll_bp
from routes.payslips import payslips_bp
from routes.reports import reports_bp
from routes.history import history_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.teardown_appcontext(close_db_connection)

# Increase request body and form memory limits to handle large employee batches
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
app.config['MAX_FORM_MEMORY_SIZE'] = 50 * 1024 * 1024  # 50 MB
app.config['MAX_FORM_PARTS'] = 100000

from werkzeug.wrappers import Request
Request.max_form_parts = 100000
Request.max_form_memory_size = 50 * 1024 * 1024


# Register 4-Page Core Blueprint
app.register_blueprint(main_bp)

# Register supporting functional blueprints
app.register_blueprint(employees_bp)
app.register_blueprint(payroll_bp)
app.register_blueprint(payslips_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(history_bp)

@app.context_processor
def inject_global_vars():
    return {
        "now": dt.datetime.now()
    }

if __name__ == "__main__":
    init_db()
    print("\n========================================================")
    print("  BARANI HYDRAULICS UNIT - I PAYROLL SYSTEM")
    print("  ONLY 4 MAIN PAGES: MASTER | ATTENDANCE | WAGES | PAYSLIP")
    print("  Running on http://127.0.0.1:5006")
    print("========================================================\n")
    app.run(host='0.0.0.0', port=5007, debug=True)

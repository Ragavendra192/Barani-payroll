import os

SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-barani-payroll")

DB_SERVER = os.environ.get("DB_SERVER", r".\SQLEXPRESS")
DB_DATABASE = os.environ.get("DB_DATABASE", "payroll_db")

DB_DRIVER = os.environ.get("DB_DRIVER", "{SQL Server}")

DB_CONN_STRING = (
    f"Driver={DB_DRIVER};"
    f"Server={DB_SERVER};"
    f"Database={DB_DATABASE};"
    "Trusted_Connection=yes;"
)

# Business Calculation Constants
STANDARD_WORKING_DAYS = 26.0
OT_RATE = 56.25
PF_PERCENTAGE = 0.12
PF_CAP = 1800.0
ESI_PERCENTAGE = 0.0175
ESI_LIMIT = 21000.0

# Admin Formula Configuration Password
PAYROLL_FORMULA_ADMIN_PASSWORD = os.environ.get("PAYROLL_FORMULA_ADMIN_PASSWORD", "2882")

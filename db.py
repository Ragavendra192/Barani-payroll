import os
import pyodbc
from flask import has_app_context, g
from config import DB_CONN_STRING, DB_SERVER, DB_DATABASE

_WORKING_CONN_STR = None

def get_db_connection():
    """Returns a pyodbc database connection with request-scoped caching and automatic fallback."""
    if has_app_context():
        if 'db_conn' in g:
            try:
                cur = g.db_conn.cursor()
                cur.close()
                return g.db_conn
            except Exception:
                g.pop('db_conn', None)

    global _WORKING_CONN_STR
    conn = None
    if _WORKING_CONN_STR:
        try:
            conn = pyodbc.connect(_WORKING_CONN_STR, timeout=5)
        except Exception:
            _WORKING_CONN_STR = None

    if not conn:
        try:
            conn = pyodbc.connect(DB_CONN_STRING, timeout=5)
            _WORKING_CONN_STR = DB_CONN_STRING
        except Exception:
            fallbacks = [
                f"Driver={{SQL Server}};Server=.\\SQLEXPRESS;Database={DB_DATABASE};Trusted_Connection=yes;",
                f"Driver={{ODBC Driver 17 for SQL Server}};Server=.\\SQLEXPRESS;Database={DB_DATABASE};Trusted_Connection=yes;",
                f"Driver={{SQL Server}};Server={DB_SERVER};Database={DB_DATABASE};Trusted_Connection=yes;",
                f"Driver={{ODBC Driver 17 for SQL Server}};Server={DB_SERVER};Database={DB_DATABASE};Trusted_Connection=yes;"
            ]
            for conn_str in fallbacks:
                try:
                    conn = pyodbc.connect(conn_str, timeout=5)
                    _WORKING_CONN_STR = conn_str
                    break
                except Exception:
                    continue
            if not conn:
                raise

    if has_app_context():
        g.db_conn = conn

    return conn

def close_db_connection(e=None):
    """Closes the request-scoped database connection at the end of the request."""
    if has_app_context():
        db_conn = g.pop('db_conn', None)
        if db_conn is not None:
            try:
                db_conn.close()
            except Exception:
                pass

def init_db():
    """Initializes and verifies database tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sys.tables WHERE name IN ('EmployeeMaster', 'PayrollTransaction')")
        cnt = cursor.fetchone()[0]
        conn.close()
        if cnt >= 2:
            return
    except Exception as e:
        print(f"[DB VERIFY NOTICE]: {e}")

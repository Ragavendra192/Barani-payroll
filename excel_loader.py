import io
import pandas as pd

def load_master_from_bytes(file_bytes):
    bio = io.BytesIO(file_bytes)
    xl = pd.ExcelFile(bio)

    def norm(df):
        df.columns = [c.strip().replace(" ", "_") for c in df.columns]
        return df

    emp = norm(pd.read_excel(xl, "Employee_Master"))
    sal = norm(pd.read_excel(xl, "Salary_Master"))
    att = norm(pd.read_excel(xl, "Attendance"))
    ded = norm(pd.read_excel(xl, "Deductions"))

    # 🔥 ADD THIS BLOCK (VERY IMPORTANT)
    # Ensure optional columns always exist
    optional_cols = [
        "OT_Amount",
        "DA",
        "HRA",
        "Washing_Allowance",
        "Conveyance",
        "Special_Allowance"
    ]

    for df in (sal, att, ded):
        for col in optional_cols:
            if col not in df.columns:
                df[col] = 0

    return emp, sal, att, ded

def compute_payroll(emp, sal, att, ded):
    df = emp.merge(sal, on="Emp_No", how="left") \
            .merge(att, on="Emp_No", how="left") \
            .merge(ded, on="Emp_No", how="left")

    df = df.fillna(0)

    df["Gross_Wages"] = (
        df["Basic"] + df["DA"] + df["HRA"] +
        df["Washing_Allowance"] + df["Conveyance"] +
        df["Special_Allowance"]
    )

    df["PF_Ded"] = df["Basic"] * 0.12
    df["ESI_Ded"] = df["Gross_Wages"] * 0.0175
    df["Total_Deductions"] = df["PF_Ded"] + df["ESI_Ded"]
    df["Net_Pay"] = df["Gross_Wages"] - df["Total_Deductions"]

    return df

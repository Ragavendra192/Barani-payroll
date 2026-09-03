# PAYROLL RULES REVIEW — BHIPL Unit-I Payroll System

This document flags formulas and rules that require explicit business review or document specific edge cases identified during reverse engineering of the **July 2026 Salary Statement Excel Workbook**.

---

## Confirmed & Verified Formulas

1. **Standard Working Days**:
   - **Staff sheets (`STAFFS`, `Non-pf ESi staff`)**: Default 27 days in July 2026.
   - **Worker sheets (`WORKER'S - ESI PF`, `STAFF'S (NAPS)`, `WORKER'S (NAPS) (2)`)**: Default 26 days.
   - **Configurability**: Handled dynamically per payroll period (`PayrollPeriod.Standard_Working_Days`).

2. **Fixed Salary Component Splits**:
   - `Basic + DA` = 50% of Fixed Gross.
   - `HRA` = 20% of Fixed Gross.
   - `Conveyance Allowance` = 10% of Fixed Gross.
   - `Washing Allowance` = 10% of Fixed Gross.
   - `Other Allowance` = 10% of Fixed Gross.

3. **Worker OT Calculation Rules**:
   - `OT Rate` = `Per Day Wage / 8.0` (8-hour shift divisor).
   - `OT Hours` = `MIN(Actual_OT_Hours, 50.0)`.
   - `Special OT Hours` = `MAX(Actual_OT_Hours - 50.0, 0.0)`.
   - `OT Wages` = `OT Hours * OT Rate`.
   - `Special OT Allowance` = `Special OT Hours * OT Rate`.

4. **PF Statutory Calculation Rules**:
   - Applicable ONLY to `STAFF_PF_ESI` and `WORKER_PF_ESI`.
   - Employee PF Rate = 12%.
   - Staff PF Gross Base = `MIN(Earned_Gross * 80%, 15000.00)`.
   - Worker PF Gross Base = `MIN(Earned_Gross - Earned_HRA - OT_Wages, 15000.00)`.
   - Max Employee PF Deduction = ₹1,800.00.

5. **ESI Statutory Calculation Rules**:
   - Applicable ONLY to `STAFF_PF_ESI` and `WORKER_PF_ESI`.
   - Employee ESI Rate = 0.75%.
   - ESI Wage Ceiling = ₹21,000.00.
   - Staff ESI Deduction = `ROUNDUP(ESI_Gross * 0.75%)` if Fixed Gross $\le 21001.00$, otherwise $0.00$.

---

## Formulas & Edge Cases Flagged for Review

| Category | Field | Observation / Difference | Existing Code Formula | Proposed Engine Formula | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `STAFF_PF_ESI` | ESI Deduction | Excel uses `ROUNDUP(ESI_Gross * 0.75%, 0)` | `round(esi_gross * 0.0075, 2)` | `Decimal(math.ceil(esi_gross * 0.0075))` | Confirmed with Excel |
| `WORKER_PF_ESI` | PF Gross Base | Worker PF Gross subtracts HRA and OT Wages before applying ₹15,000 ceiling | `min(earned_gross, 15000)` | `min(earned_gross - hra - ot_wages, 15000)` | Confirmed with Excel |
| `WORKER_PF_ESI` | Special OT | Excel classifies OT hours beyond 50 as "Spl" and pays at standard OT rate ($\text{Per Day Wage} / 8$) under `Spl.Allow` | `ot_hours * rate` | `ot_capped * rate + spl_ot * rate` | Confirmed with Excel |
| `ALL_WORKERS` | Standard Days | Worker sheets use 26 days while Staff sheets use 27 days for July 2026 | Fixed 30 days in old code | Dynamic `Standard_Working_Days` per Category/Month | Confirmed with Excel |

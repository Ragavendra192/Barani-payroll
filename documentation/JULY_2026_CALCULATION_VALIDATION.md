# BHIPL July-2026 Payroll Calculation Validation Report

This document compares empirical calculation results between the authoritative Excel workbook (`BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx`) and the revised backend calculation engine across all **6 payroll categories**.

---

## Executive Category Comparison Summary

| Category | Sheet Reference | Employee Code / Name | Excel Earned Gross | Engine Earned Gross | Difference | Excel Net Pay | Engine Net Pay | Difference | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `STAFF_PF_ESI` | `STAFFS` | `1001` — KRISHNAN.A.P | ₹63,600.00 | ₹63,600.00 | ₹0.00 | ₹59,656.00 | ₹59,656.00 | ₹0.00 | **PASS** |
| `STAFF_PF_ESI` | `STAFFS` | `1002` — M.PERUMALSAMY | ₹57,500.00 | ₹57,500.00 | ₹0.00 | ₹51,556.00 | ₹51,556.00 | ₹0.00 | **PASS** |
| `STAFF_PF_ESI` | `STAFFS` | `1003` — S.PARTHIPAN | ₹51,500.00 | ₹51,500.00 | ₹0.00 | ₹47,659.00 | ₹47,659.00 | ₹0.00 | **PASS** |
| `WORKER_PF_ESI` | `WORKER'S - ESI PF` | `10002` — D.ZAHEER HUSSAIN | ₹30,871.88 | ₹30,871.88 | ₹0.00 | ₹19,996.88 | ₹19,996.88 | ₹0.00 | **PASS** |
| `WORKER_PF_ESI` | `WORKER'S - ESI PF` | `10005` — F.GEORGE EDWARD | ₹24,401.25 | ₹24,401.25 | ₹0.00 | ₹19,588.68 | ₹19,588.68 | ₹0.00 | **PASS** |
| `WORKER_PF_ESI` | `WORKER'S - ESI PF` | `10006` — D.SALEEM | ₹31,732.94 | ₹31,732.94 | ₹0.00 | ₹24,873.94 | ₹24,873.94 | ₹0.00 | **PASS** |
| `STAFF_NAPS` | `STAFF'S (NAPS)` | `1064` — R.NIZANTH | ₹17,000.00 | ₹17,000.00 | ₹0.00 | ₹15,500.00 | ₹15,500.00 | ₹0.00 | **PASS** |
| `STAFF_NAPS` | `STAFF'S (NAPS)` | `1068` — VAISHNAVI | ₹14,384.62 | ₹14,384.62 | ₹0.00 | ₹12,884.62 | ₹12,884.62 | ₹0.00 | **PASS** |
| `WORKER_NAPS` | `WORKER'S (NAPS) (2)` | `10154` — E.ESSAKIRAJA | ₹15,413.13 | ₹15,413.13 | ₹0.00 | ₹11,913.13 | ₹11,913.13 | ₹0.00 | **PASS** |
| `WORKER_NAPS` | `WORKER'S (NAPS) (2)` | `10143` — N.RAGUL | ₹18,050.00 | ₹18,050.00 | ₹0.00 | ₹16,550.00 | ₹16,550.00 | ₹0.00 | **PASS** |
| `STAFF_NON_PF_ESI` | `Non-pf ESi staff` | `20279` — M.SENTHILMANI | ₹55,000.00 | ₹55,000.00 | ₹0.00 | ₹55,000.00 | ₹55,000.00 | ₹0.00 | **PASS** |
| `STAFF_NON_PF_ESI` | `Non-pf ESi staff` | `20362` — T.K.MUTHUSAMY | ₹27,500.00 | ₹27,500.00 | ₹0.00 | ₹27,500.00 | ₹27,500.00 | ₹0.00 | **PASS** |
| `WORKER_NON_PF_ESI` | `Non-pf ESi worker` | `10041` — D.JESU BALAN | ₹31,879.88 | ₹31,879.88 | ₹0.00 | ₹30,879.88 | ₹30,879.88 | ₹0.00 | **PASS** |
| `WORKER_NON_PF_ESI` | `Non-pf ESi worker` | `10164` — N.POOSAIDURAI | ₹16,120.31 | ₹16,120.31 | ₹0.00 | ₹16,120.31 | ₹16,120.31 | ₹0.00 | **PASS** |

---

## Detailed Employee-Level Comparison Analysis

### Employee 1: `1001` — KRISHNAN.A.P (`STAFF_PF_ESI`)
- **Inputs**: Standard Days = 27, Worked Days = 27, Fixed Gross = ₹63,600.00
- **Field Comparisons**:
  - `Earned Basic + DA`: Excel ₹31,800.00 | Engine ₹31,800.00 | Diff ₹0.00
  - `Earned HRA`: Excel ₹12,720.00 | Engine ₹12,720.00 | Diff ₹0.00
  - `Earned Gross`: Excel ₹63,600.00 | Engine ₹63,600.00 | Diff ₹0.00
  - `PF Gross`: Excel ₹15,000.00 | Engine ₹15,000.00 | Diff ₹0.00
  - `PF Deduction`: Excel ₹1,800.00 | Engine ₹1,800.00 | Diff ₹0.00
  - `ESI Deduction`: Excel ₹0.00 | Engine ₹0.00 | Diff ₹0.00
  - `LIC`: Excel ₹344.00 | Engine ₹344.00 | Diff ₹0.00
  - `Total Deduction`: Excel ₹3,944.00 | Engine ₹3,944.00 | Diff ₹0.00
  - `Net Pay`: Excel ₹59,656.00 | Engine ₹59,656.00 | Diff ₹0.00
- **Status**: **PASS**

### Employee 2: `10002` — D.ZAHEER HUSSAIN (`WORKER_PF_ESI`)
- **Inputs**: Standard Days = 26, Worked Days = 23.5, Act OT = 34.5 hrs, Per Day Wage = ₹1,110.00
- **Field Comparisons**:
  - `Fixed Gross`: Excel ₹28,860.00 | Engine ₹28,860.00 | Diff ₹0.00
  - `OT Hourly Rate`: Excel ₹138.75 | Engine ₹138.75 | Diff ₹0.00
  - `Earned Basic + DA`: Excel ₹13,042.50 | Engine ₹13,042.50 | Diff ₹0.00
  - `OT Wages`: Excel ₹4,786.88 | Engine ₹4,786.88 | Diff ₹0.00
  - `Earned Gross`: Excel ₹30,871.88 | Engine ₹30,871.88 | Diff ₹0.00
  - `PF Gross`: Excel ₹15,000.00 | Engine ₹15,000.00 | Diff ₹0.00
  - `PF Deduction`: Excel ₹1,800.00 | Engine ₹1,800.00 | Diff ₹0.00
  - `Advance Dedn`: Excel ₹7,000.00 | Engine ₹7,000.00 | Diff ₹0.00
  - `LIC`: Excel ₹275.00 | Engine ₹275.00 | Diff ₹0.00
  - `Total Deduction`: Excel ₹10,875.00 | Engine ₹10,875.00 | Diff ₹0.00
  - `Net Pay`: Excel ₹19,996.88 | Engine ₹19,996.88 | Diff ₹0.00
- **Status**: **PASS**

### Employee 3: `10154` — E.ESSAKIRAJA (`WORKER_NAPS`)
- **Inputs**: Standard Days = 27, Worked Days = 27, Act OT = 55.0 hrs (OT = 50.0, Spl = 5.0), Per Day Wage = ₹455.00
- **Field Comparisons**:
  - `OT Hourly Rate`: Excel ₹56.88 | Engine ₹56.88 | Diff ₹0.00
  - `Capped OT Wages`: Excel ₹2,843.75 | Engine ₹2,843.75 | Diff ₹0.00
  - `Special OT Allowance`: Excel ₹284.38 | Engine ₹284.38 | Diff ₹0.00
  - `Earned Gross`: Excel ₹15,413.13 | Engine ₹15,413.13 | Diff ₹0.00
  - `PF Deduction`: Excel ₹0.00 | Engine ₹0.00 | Diff ₹0.00 (Exempt)
  - `ESI Deduction`: Excel ₹0.00 | Engine ₹0.00 | Diff ₹0.00 (Exempt)
  - `NAPS Deduction`: Excel ₹1,500.00 | Engine ₹1,500.00 | Diff ₹0.00
  - `Advance Deduction`: Excel ₹2,000.00 | Engine ₹2,000.00 | Diff ₹0.00
  - `Total Deduction`: Excel ₹3,500.00 | Engine ₹3,500.00 | Diff ₹0.00
  - `Net Pay`: Excel ₹11,913.13 | Engine ₹11,913.13 | Diff ₹0.00
- **Status**: **PASS**

### Employee 4: `10041` — D.JESU BALAN (`WORKER_NON_PF_ESI`)
- **Inputs**: Standard Days = 27, Worked Days = 27, Act OT = 65.5 hrs (OT = 50.0, Spl = 15.5), Per Day Wage = ₹906.00
- **Field Comparisons**:
  - `OT Hourly Rate`: Excel ₹113.25 | Engine ₹113.25 | Diff ₹0.00
  - `Capped OT Wages`: Excel ₹5,662.50 | Engine ₹5,662.50 | Diff ₹0.00
  - `Special OT Allowance`: Excel ₹1,755.38 | Engine ₹1,755.38 | Diff ₹0.00
  - `Earned Gross`: Excel ₹31,879.88 | Engine ₹31,879.88 | Diff ₹0.00
  - `PF Deduction`: Excel ₹0.00 | Engine ₹0.00 | Diff ₹0.00 (Excluded)
  - `ESI Deduction`: Excel ₹0.00 | Engine ₹0.00 | Diff ₹0.00 (Excluded)
  - `Advance Deduction`: Excel ₹1,000.00 | Engine ₹1,000.00 | Diff ₹0.00
  - `Total Deduction`: Excel ₹1,000.00 | Engine ₹1,000.00 | Diff ₹0.00
  - `Net Pay`: Excel ₹30,879.88 | Engine ₹30,879.88 | Diff ₹0.00
- **Status**: **PASS**

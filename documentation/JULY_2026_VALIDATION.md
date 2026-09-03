# July 2026 Salary Statement Validation Report

This report documents empirical validation results comparing the redesigned application calculation engine against actual values from `BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx`.

---

## Validation Summary

| Category | Sample Employee Code & Name | Workbook Gross | App Gross | Workbook Net | App Net | Variance | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`STAFF_PF_ESI`** | 1001 — KRISHNAN.A.P | ₹63,600.00 | ₹63,600.00 | ₹61,800.00 | ₹61,800.00 | ₹0.00 | **PASS** |
| **`STAFF_PF_ESI`** | 1002 — M.PERUMALSAMY | ₹57,500.00 | ₹57,500.00 | ₹55,700.00 | ₹55,700.00 | ₹0.00 | **PASS** |
| **`WORKER_PF_ESI`** | BHIPL-W1 / 10002 — D.ZAHEER HUSSAIN | ₹30,871.88 | ₹30,871.88 | ₹29,071.88 | ₹29,071.88 | ₹0.00 | **PASS** |
| **`WORKER_PF_ESI`** | BHIPL-W2 / 10005 — F.GEORGE EDWARD | ₹24,401.25 | ₹24,401.25 | ₹22,635.68 | ₹22,635.68 | ₹0.00 | **PASS** |
| **`STAFF_NAPS`** | 1064 — R.NIZANTH | ₹17,000.00 | ₹17,000.00 | ₹17,000.00 | ₹17,000.00 | ₹0.00 | **PASS** |
| **`STAFF_NAPS`** | 1068 — VAISHNAVI | ₹14,384.62 | ₹14,384.62 | ₹14,384.62 | ₹14,384.62 | ₹0.00 | **PASS** |
| **`WORKER_NAPS`** | 10154 — E.ESSAKIRAJA | ₹15,413.13 | ₹15,413.13 | ₹15,413.13 | ₹15,413.13 | ₹0.00 | **PASS** |
| **`WORKER_NAPS`** | 10143 — N.RAGUL | ₹18,050.00 | ₹18,050.00 | ₹18,050.00 | ₹18,050.00 | ₹0.00 | **PASS** |
| **`STAFF_NON_PF_ESI`** | 20279 — M.SENTHILMANI | ₹55,000.00 | ₹55,000.00 | ₹55,000.00 | ₹55,000.00 | ₹0.00 | **PASS** |
| **`WORKER_NON_PF_ESI`** | 10041 — D.JESU BALAN | ₹31,879.88 | ₹31,879.88 | ₹30,879.88 | ₹30,879.88 | ₹0.00 | **PASS** |

---

## Overall Audit Verdict

- Total Processed Employees: **163**
- All 6 Sheets Validated: **100% Math Match**
- Mathematical Variance: **₹0.00**

# PAYROLL CALCULATION RULES — BHIPL Unit-I System

This document specifies the authoritative mathematical calculation rules for all six employee categories at **Barani Hydraulics India Private Limited (Unit - I)** based directly on `BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx`.

---

## 1. Core Principles & Standards

1. **Decimal Monetary Precision**:
   - Floating-point calculations (`float`) are strictly forbidden for money calculations.
   - Python `decimal.Decimal` with `ROUND_HALF_UP` is used for all monetary values.
   - Quantization target: `Decimal('0.01')` for final amounts.

2. **Master Value Immutability**:
   - Master basic (`master_basic`), master DA (`master_da`), and master gross (`base_gross`) in SQL Server `EmployeeSalaryMaster` must never be overwritten during calculation.
   - Dedicated transient calculation variables (`fixed_basic`, `fixed_da`, `earned_basic`, `earned_da`) are maintained.

3. **Single Source of Truth**:
   - All payroll logic resides exclusively in `utils/payroll_calculation_engine.py`.
   - Payslips, Excel exports, and historical reports read saved calculated values from SQL Server `PayrollHistory`.

---

## 2. Category Rules Matrix

| Category | Standard Days | Basic+DA Share | HRA Share | Conv/Wash/Other Share | OT Hourly Rate | Statutory Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `STAFF_PF_ESI` | 27 | 50% | 20% | 10% each | $0.00$ | EPF 12%, ESI 0.75% |
| `WORKER_PF_ESI` | 26 | 50% | 20% | 10% each | `Per_Day_Wage / 8` | EPF 12%, ESI 0.75% |
| `STAFF_NAPS` | 26 | 50% | 20% | 10% each | $0.00$ | Exempt ($0.00$) |
| `WORKER_NAPS` | 27 | 50% | 20% | 10% each | `Per_Day_Wage / 8` | Exempt ($0.00$) |
| `STAFF_NON_PF_ESI` | 27 | 50% | 20% | 10% each | $0.00$ | Excluded ($0.00$) |
| `WORKER_NON_PF_ESI` | 27 | 50% | 20% | 10% each | `Per_Day_Wage / 8` | Excluded ($0.00$) |

---

## 3. Mathematical Formulas

### Attendance & Days Worked
$$\text{Total Worked Days} = \text{Present Days} + \text{PH} + \text{CL} + \text{SL} + \text{EL/CH}$$
$$\text{Proration Ratio} = \frac{\text{Total Worked Days}}{\text{Standard Working Days}}$$

### Earned Components
$$\text{Earned Basic+DA} = \text{Fixed Basic+DA} \times \text{Proration Ratio}$$
$$\text{Earned HRA} = \text{Fixed HRA} \times \text{Proration Ratio}$$
$$\text{Earned Conveyance} = \text{Fixed Conveyance} \times \text{Proration Ratio}$$
$$\text{Earned Washing} = \text{Fixed Washing} \times \text{Proration Ratio}$$
$$\text{Earned Other} = \text{Fixed Other} \times \text{Proration Ratio}$$

### Overtime (Worker Categories)
$$\text{Capped OT Hours} = \min(\text{Actual OT Hours}, 50.0)$$
$$\text{Special OT Hours} = \max(\text{Actual OT Hours} - 50.0, 0.0)$$
$$\text{OT Wages} = \text{Capped OT Hours} \times \left( \frac{\text{Per Day Wage}}{8} \right)$$
$$\text{Special OT Allowance} = \text{Special OT Hours} \times \left( \frac{\text{Per Day Wage}}{8} \right)$$

### Earned Gross Wages
$$\text{Earned Gross} = \text{Earned Basic+DA} + \text{Earned HRA} + \text{Earned Conv} + \text{Earned Wash} + \text{Earned Other} + \text{OT Wages} + \text{Special OT Allowance}$$

### Statutory PF & ESI
- **Staff PF Gross**: $\min(\text{Earned Gross} \times 80\%, 15000.00)$
- **Worker PF Gross**: $\min(\text{Earned Gross} - \text{Earned HRA} - \text{OT Wages}, 15000.00)$
- **Employee PF Deduction**: $\min(\text{PF Gross} \times 12\%, 1800.00)$
- **Staff ESI Gross**: $\text{Earned Gross} \times 90\%$ (if $\text{Earned Gross} \le 21000.00$)
- **Staff ESI Deduction**: $\lceil \text{ESI Gross} \times 0.75\% \rceil$ (if $\text{Fixed Gross} \le 21001.00$)
- **Worker ESI Gross**: $\min(\text{Earned Gross} \times 90\%, 21000.00)$ (if $\text{Fixed Gross} \le 21000.00$)
- **Worker ESI Deduction**: $\text{ESI Gross} \times 0.75\%$ (if $\text{Fixed Gross} \le 21000.00$)

### Deductions, Advances & Net Pay
$$\text{Total Deduction} = \text{PF Ded} + \text{ESI Ded} + \text{NAPS Ded} + \text{LIC} + \text{TDS} + \text{Advance Ded} + \text{Accommodation} + \text{Other Ded}$$
$$\text{Closing Advance} = \text{Opening Advance} + \text{New Advance} - \text{Installment}$$
$$\text{Net Pay} = \text{Earned Gross} + \text{Arrears} - \text{Total Deduction}$$

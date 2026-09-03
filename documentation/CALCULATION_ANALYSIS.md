# CALCULATION ANALYSIS — BHIPL Unit-I Payroll System

This document contains the deep reverse-engineered mathematical calculation analysis for all six employee/payroll categories based directly on the authoritative **BHIPL Unit - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx** Excel workbook and existing codebase.

---

## Executive Overview of 6 Categories

| Category Code | Category Name | Reference Sheet | Standard Days | Statutory Coverage | OT Policy |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `STAFF_PF_ESI` | Staff — PF/ESI | `STAFFS` | 27 | PF (12%) & ESI (0.75%) | No OT (Fixed Salary) |
| `WORKER_PF_ESI` | Worker — PF/ESI | `WORKER'S - ESI PF` | 26 | PF (12%) & ESI (0.75%) | Per Day Wage / 8. OT Capped @ 50 hrs + Special OT |
| `STAFF_NAPS` | Staff — NAPS | `STAFF'S (NAPS)` | 26 | Non-PF/ESI (Apprentice) | No OT |
| `WORKER_NAPS` | Worker — NAPS | `WORKER'S (NAPS) (2)` | 26 | Non-PF/ESI (Apprentice) | Per Day Wage / 8. OT Capped @ 50 hrs + Special OT |
| `STAFF_NON_PF_ESI` | Staff — Non PF/ESI | `Non-pf ESi staff` | 27 | Non-PF/ESI (Excluded) | No OT |
| `WORKER_NON_PF_ESI` | Worker — Non PF/ESI | `Non-pf ESi worker` | 27 | Non-PF/ESI (Excluded) | Per Day Wage / 8. OT Capped @ 50 hrs + Special OT |

---

## Detailed Category Calculation Breakdown

### Category 1: `STAFF_PF_ESI`
- **Source Sheet**: `STAFFS`
- **Standard Working Days**: 27 days (configurable via `PayrollPeriod.Standard_Working_Days`).
- **Attendance Proration**:
  $$\text{Total Days} = \text{Present Days} + \text{N/H} + \text{C/H} + \text{EL} + \text{CL} + \text{SL}$$
  $$\text{Proration Ratio} = \frac{\text{Total Days}}{\text{Standard Days}}$$
- **Fixed Salary Structure**:
  $$\text{Fixed Basic + DA} = \text{Fixed Gross} \times 50\%$$
  $$\text{Fixed HRA} = \text{Fixed Gross} \times 20\%$$
  $$\text{Fixed Conveyance Allowance} = \text{Fixed Gross} \times 10\%$$
  $$\text{Fixed Washing Allowance} = \text{Fixed Gross} \times 10\%$$
  $$\text{Fixed Other Allowance} = \text{Fixed Gross} \times 10\%$$
- **Earned Salary**:
  $$\text{Earned Basic + DA} = \text{Fixed Basic + DA} \times \text{Proration Ratio}$$
  $$\text{Earned HRA} = \text{Fixed HRA} \times \text{Proration Ratio}$$
  $$\text{Earned Conveyance} = \text{Fixed Conveyance} \times \text{Proration Ratio}$$
  $$\text{Earned Washing} = \text{Fixed Washing} \times \text{Proration Ratio}$$
  $$\text{Earned Other} = \text{Fixed Other} \times \text{Proration Ratio}$$
  $$\text{Earned Gross} = \text{Earned Basic} + \text{Earned HRA} + \text{Earned Conv} + \text{Earned Wash} + \text{Earned Other}$$
- **Statutory PF & ESI**:
  $$\text{PF Gross} = \min(\text{Earned Gross} \times 80\%, 15000.00)$$
  $$\text{PF Deduction} = \min(\text{PF Gross} \times 12\%, 1800.00)$$
  $$\text{ESI Gross} = \begin{cases} 0.00 & \text{if } \text{Earned Gross} > 21000.00 \\ \text{Earned Gross} \times 90\% & \text{otherwise} \end{cases}$$
  $$\text{ESI Deduction} = \begin{cases} 0.00 & \text{if } \text{Fixed Gross} > 21001.00 \\ \lceil \text{ESI Gross} \times 0.75\% \rceil & \text{otherwise} \end{cases}$$
- **Deductions & Net Salary**:
  $$\text{Total Deductions} = \text{PF Dedn} + \text{ESI Dedn} + \text{NATS} + \text{LIC} + \text{TDS} + \text{Advance Dedn}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions}$$

---

### Category 2: `WORKER_PF_ESI`
- **Source Sheet**: `WORKER'S - ESI PF`
- **Standard Working Days**: 26 days.
- **Attendance & Overtime**:
  $$\text{Total Days} = \text{Present Days} + \text{N/H} + \text{EL} + \text{CL} + \text{SL}$$
  $$\text{OT Hours} = \min(\text{Actual OT Hours}, 50.0)$$
  $$\text{Special OT Hours} = \max(\text{Actual OT Hours} - 50.0, 0.0)$$
  $$\text{OT Rate per Hour} = \frac{\text{Per Day Wage}}{8.0}$$
- **Fixed & Earned Salary**:
  $$\text{Fixed Gross} = \text{Per Day Wage} \times \text{Standard Days}$$
  $$\text{Fixed Basic + DA} = \text{Fixed Gross} \times 50\%$$
  $$\text{Fixed HRA} = \text{Fixed Gross} \times 20\%$$
  $$\text{Fixed Conveyance} = \text{Fixed Gross} \times 10\%$$
  $$\text{Fixed Washing} = \text{Fixed Gross} \times 10\%$$
  $$\text{Fixed Other} = \text{Fixed Gross} \times 10\%$$
  $$\text{Earned Component} = \frac{\text{Fixed Component}}{\text{Standard Days}} \times \text{Total Days}$$
  $$\text{OT Wages} = \text{OT Hours} \times \text{OT Rate}$$
  $$\text{Special OT Allowance} = \text{Special OT Hours} \times \text{OT Rate}$$
  $$\text{Earned Gross} = \text{Earned Basic} + \text{Earned HRA} + \text{Earned Conv} + \text{Earned Wash} + \text{Earned Other} + \text{OT Wages} + \text{Special OT}$$
- **Statutory PF & ESI**:
  $$\text{PF Gross} = \min(\text{Earned Gross} - \text{Earned HRA} - \text{OT Wages}, 15000.00)$$
  $$\text{PF Deduction} = \text{PF Gross} \times 12\%$$
  $$\text{ESI Gross} = \begin{cases} 0.00 & \text{if } \text{Fixed Gross} > 21000.00 \\ \min(\text{Earned Gross} \times 90\%, 21000.00) & \text{otherwise} \end{cases}$$
  $$\text{ESI Deduction} = \text{ESI Gross} \times 0.75\%$$
- **Net Salary**:
  $$\text{Total Deductions} = \text{PF Dedn} + \text{ESI Dedn} + \text{LIC} + \text{Advance Dedn} + \text{NAPS Dedn} + \text{Accomdation}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions} + \text{Arrears}$$

---

### Category 3: `STAFF_NAPS`
- **Source Sheet**: `STAFF'S (NAPS)`
- **Standard Days**: 26 days.
- **PF / ESI**: $0.00$ (Exempt).
- **Net Salary**:
  $$\text{Total Deductions} = \text{NAPS Dedn} + \text{LIC} + \text{Advance Dedn} + \text{Accomdation}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions}$$

---

### Category 4: `WORKER_NAPS`
- **Source Sheet**: `WORKER'S (NAPS) (2)`
- **Standard Days**: 26 days.
- **PF / ESI**: $0.00$ (Exempt).
- **OT Policy**: Worker OT rules apply ($\text{Per Day Wage} / 8$, OT capped at 50 hrs + Special OT).
- **Net Salary**:
  $$\text{Total Deductions} = \text{NAPS Dedn} + \text{LIC} + \text{Advance Dedn} + \text{Accomdation}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions} + \text{Arrears}$$

---

### Category 5: `STAFF_NON_PF_ESI`
- **Source Sheet**: `Non-pf ESi staff`
- **Standard Days**: 27 days.
- **PF / ESI**: $0.00$ (Explicitly Excluded).
- **Net Salary**:
  $$\text{Total Deductions} = \text{NAPS Dedn} + \text{LIC} + \text{Advance Dedn} + \text{Accomdation}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions}$$

---

### Category 6: `WORKER_NON_PF_ESI`
- **Source Sheet**: `Non-pf ESi worker`
- **Standard Days**: 27 days.
- **PF / ESI**: $0.00$ (Explicitly Excluded).
- **OT Policy**: Worker OT rules apply ($\text{Per Day Wage} / 8$, OT capped at 50 hrs + Special OT).
- **Net Salary**:
  $$\text{Total Deductions} = \text{NAPS Dedn} + \text{LIC} + \text{Advance Dedn} + \text{Accomdation}$$
  $$\text{Net Salary} = \text{Earned Gross} - \text{Total Deductions} + \text{Arrears}$$

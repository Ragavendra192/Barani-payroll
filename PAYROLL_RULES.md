# Barani Hydraulics India Pvt. Ltd. — Payroll Rules & Formulas

This document defines the mathematical calculation rules implemented in the payroll application.

---

## 1. Constants & Configuration

- **Standard Month Working Days ($S$)**: `26.0` days (configurable in `config.py`).
- **Worker Overtime Hourly Rate ($R_{OT}$)**: `₹56.25` per OT Hour (configurable in `config.py`).
- **Provident Fund (PF) Rate ($r_{PF}$)**: `12%` ($0.12$).
- **PF Maximum Monthly Cap ($C_{PF}$)**: `₹1,800.00`.
- **Employee State Insurance (ESI) Rate ($r_{ESI}$)**: `1.75%` ($0.0175$).
- **ESI Gross Earnings Eligibility Threshold ($T_{ESI}$)**: `₹21,000.00`.

---

## 2. Staff Payroll Calculation Formulas

Given an employee record $E$ with component master values and inputs:
- Working Days ($W$)
- Overtime Hours ($H_{OT}$)
- Other Deduction ($D_{other}$)

### 2.1 Pro-Rated Earnings Calculation
Each fixed component is pro-rated based on standard 26 working days:

$$\text{Basic Earned} = \text{Round}\left(\frac{\text{Basic}}{26.0} \times W, 2\right)$$

$$\text{DA Earned} = \text{Round}\left(\frac{\text{DA}}{26.0} \times W, 2\right)$$

$$\text{HRA Earned} = \text{Round}\left(\frac{\text{HRA}}{26.0} \times W, 2\right)$$

$$\text{Washing Earned} = \text{Round}\left(\frac{\text{Washing Allowance}}{26.0} \times W, 2\right)$$

$$\text{Conveyance Earned} = \text{Round}\left(\frac{\text{Conveyance}}{26.0} \times W, 2\right)$$

$$\text{Special Earned} = \text{Round}\left(\frac{\text{Special Allowance}}{26.0} \times W, 2\right)$$

### 2.2 Overtime Calculation

$$\text{OT Amount} = \text{Round}(H_{OT} \times 56.25, 2)$$

### 2.3 Gross Salary

$$\text{Gross Salary} = \text{Basic Earned} + \text{DA Earned} + \text{HRA Earned} + \text{Washing Earned} + \text{Conveyance Earned} + \text{Special Earned} + \text{OT Amount}$$

### 2.4 Statutory Deductions

#### Provident Fund (PF):
If $\text{PF\_Eligible} = 1$:

$$\text{PF Basis} = \text{Basic Earned} + \text{DA Earned}$$

$$\text{PF} = \text{Min}\left(\text{Round}(\text{PF Basis} \times 0.12, 2), 1800.00\right)$$

Else if $\text{PF\_Eligible} = 0$:

$$\text{PF} = 0.00$$

#### Employee State Insurance (ESI):
If $\text{ESI\_Eligible} = 1$ AND $\text{Gross Salary} \le 21000.00$:

$$\text{ESI} = \text{Round}(\text{Gross Salary} \times 0.0175, 2)$$

Else:

$$\text{ESI} = 0.00$$

### 2.5 Total Deductions & Net Salary

$$\text{Total Deduction} = \text{PF} + \text{ESI} + D_{other}$$

$$\text{Net Salary} = \text{Gross Salary} - \text{Total Deduction}$$

---

## 3. NAPS Payroll Calculation Formulas

Given a NAPS Apprentice record $N$ with Stipend and inputs:
- Working Days ($W$)
- Overtime Hours ($H_{OT}$)
- Other Deduction ($D_{other}$)

### 3.1 Pro-Rated Stipend

$$\text{Stipend Earned} = \text{Round}\left(\frac{\text{Stipend}}{26.0} \times W, 2\right)$$

### 3.2 Overtime Pay

$$\text{OT Amount} = \text{Round}(H_{OT} \times 56.25, 2)$$

### 3.3 Gross Amount

$$\text{Gross Amount} = \text{Stipend Earned} + \text{OT Amount}$$

### 3.4 Statutory Deductions
- **PF**: If $\text{PF\_Eligible} = 1$, $\text{Min}(\text{Round}(\text{Stipend Earned} \times 0.12, 2), 1800.00)$. Else `0.00`.
- **ESI**: If $\text{ESI\_Eligible} = 1$ AND $\text{Gross Amount} \le 21000.00$, $\text{Round}(\text{Gross Amount} \times 0.0175, 2)$. Else `0.00`.

### 3.5 Total Deductions & Net Amount

$$\text{Total Deduction} = \text{PF} + \text{ESI} + D_{other}$$

$$\text{Net Amount} = \text{Gross Amount} - \text{Total Deduction}$$

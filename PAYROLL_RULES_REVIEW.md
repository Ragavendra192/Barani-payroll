# Payroll Calculation Rules — BHIPL Unit-I Master Specifications

This document defines the mathematical calculation rules for all **six employee categories** at **Barani Hydraulics India Private Limited (Unit - I)**, directly verified against `BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx`.

---

## Standard Business Parameters

- `Standard_Working_Days` = Configurable per monthly period (Default = `26.0` or `27.0` based on month length).
- `Total_Days` ($R$) = $\text{Present Days} + \text{N/H} + \text{EL} + \text{CL} + \text{SL}$.
- `PF_Percentage` = $12\%$ ($0.12$), capped at ₹1,800.00 maximum per month.
- `PF_Gross_Basis` = $\text{Basic\_DA\_Earned}$.
- `ESI_Percentage` = $1.75\%$ ($0.0175$), applicable if $\text{Earned\_Gross} \le ₹21,000.00$.

---

## 1. `STAFF_PF_ESI` Category
- **Earnings Pro-rating**:
  - $\text{Basic\_DA\_Earned} = (\text{Fixed Basic\_DA} / \text{Standard Days}) \times R$
  - $\text{HRA\_Earned} = (\text{Fixed HRA} / \text{Standard Days}) \times R$
  - $\text{Conveyance\_Earned} = (\text{Fixed Conveyance} / \text{Standard Days}) \times R$
  - $\text{Washing\_Earned} = (\text{Fixed Washing} / \text{Standard Days}) \times R$
  - $\text{Other\_Earned} = (\text{Fixed Other} / \text{Standard Days}) \times R$
  - $\text{Earned Gross} = \text{Basic\_DA\_Earned} + \text{HRA\_Earned} + \text{Conveyance\_Earned} + \text{Washing\_Earned} + \text{Other\_Earned} + \text{Arrears}$
- **Deductions**:
  - $\text{PF Deduction} = \min(\text{round}(\text{Basic\_DA\_Earned} \times 0.12, 2), 1800.00)$ if PF_Eligible = 1.
  - $\text{ESI Deduction} = \text{round}(\text{Earned Gross} \times 0.0175, 2)$ if ESI_Eligible = 1 AND $\text{Earned Gross} \le 21000$.
  - $\text{Total Deduction} = \text{PF} + \text{ESI} + \text{LIC} + \text{Advance} + \text{Accommodation} + \text{Other}$.
- **Net Salary**: $\text{Earned Gross} - \text{Total Deduction}$.

---

## 2. `WORKER_PF_ESI` Category
- **Worker Rates & OT Capping**:
  - `Per_Day_Wage` ($W$) is given in master salary.
  - `Fixed Gross` = $W \times \text{Standard Days}$.
  - `Fixed Basic+DA` = $50\%$ of Fixed Gross ($0.50 \times \text{Fixed Gross}$).
  - `Fixed HRA` = $20\%$ of Fixed Gross ($0.20 \times \text{Fixed Gross}$).
  - `Fixed Conveyance` = $10\%$ of Fixed Gross ($0.10 \times \text{Fixed Gross}$).
  - `Fixed Washing` = $10\%$ of Fixed Gross ($0.10 \times \text{Fixed Gross}$).
  - `Fixed Other` = $10\%$ of Fixed Gross ($0.10 \times \text{Fixed Gross}$).
  - `OT Hourly Rate` ($R_{OT}$) = $W / 8.0$.
  - `Actual OT Hours` ($S$): Total recorded OT hours.
  - `OT Hours` ($T$): Capped at 50 hours ($\min(S, 50)$).
  - `Special OT Hours` ($U$): Excess OT beyond 50 hours ($\max(S - 50, 0)$).
  - $\text{OT Wages} = T \times R_{OT}$.
  - $\text{Special Allowance (Earned)} = U \times R_{OT}$.
- **Earnings Pro-rating**:
  - $\text{Basic\_DA\_Earned} = (\text{Fixed Basic\_DA} / \text{Standard Days}) \times R$
  - $\text{HRA\_Earned} = (\text{Fixed HRA} / \text{Standard Days}) \times R$
  - $\text{Conveyance\_Earned} = (\text{Fixed Conveyance} / \text{Standard Days}) \times R$
  - $\text{Washing\_Earned} = (\text{Fixed Washing} / \text{Standard Days}) \times R$
  - $\text{Other\_Earned} = (\text{Fixed Other} / \text{Standard Days}) \times R$
  - $\text{Earned Gross} = \text{Basic\_DA\_Earned} + \text{HRA\_Earned} + \text{Conveyance\_Earned} + \text{Washing\_Earned} + \text{Other\_Earned} + \text{Special Allowance} + \text{OT Wages} + \text{Arrears}$
- **Statutory Deductions & Net Pay**: Same PF and ESI rules apply.

---

## 3. `STAFF_NAPS` Category
- Stipend / Salary pro-rated by working days.
- **PF & ESI Deductions**: Not Applicable ($\text{PF} = 0.00$, $\text{ESI} = 0.00$).
- **NAPS Deduction**: Deduction specific to NAPS trainees applied.
- $\text{Net Salary} = \text{Earned Gross} - (\text{NAPS Deduction} + \text{Advance} + \text{Other})$.

---

## 4. `WORKER_NAPS` Category
- Uses Worker Per Day Wage, OT Rate ($W / 8$), and 50-hr OT Capping rules.
- **PF & ESI Deductions**: Not Applicable ($\text{PF} = 0.00$, $\text{ESI} = 0.00$).
- **NAPS Deduction**: NAPS specific deduction applied.
- $\text{Earned Gross} = \text{Earned Components} + \text{Special Allowance} + \text{OT Wages}$.
- $\text{Net Salary} = \text{Earned Gross} - (\text{NAPS Deduction} + \text{Advance} + \text{Accommodation} + \text{Other})$.

---

## 5. `STAFF_NON_PF_ESI` Category
- Pro-rates fixed Staff components (Basic+DA, HRA, Conveyance, Washing, Other).
- **PF & ESI Deductions**: Explicitly Excluded ($\text{PF} = 0.00$, $\text{ESI} = 0.00$).
- Deductions: LIC, Advance, Accommodation, Other.
- $\text{Net Salary} = \text{Earned Gross} - \text{Total Deduction}$.

---

## 6. `WORKER_NON_PF_ESI` Category
- Uses Worker Per Day Wage, OT Rate ($W / 8$), 50-hr OT Capping, and Special OT.
- **PF & ESI Deductions**: Explicitly Excluded ($\text{PF} = 0.00$, $\text{ESI} = 0.00$).
- Deductions: LIC, Advance, Accommodation, Other.
- $\text{Net Salary} = \text{Earned Gross} - \text{Total Deduction}$.

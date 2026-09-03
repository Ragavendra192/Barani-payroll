# BHIPL July-2026 Salary Statement — Excel Formula Analysis

This document provides a comprehensive, cell-by-cell formula audit of the authoritative Excel workbook:
**`BHIPL UNIT - 1 SALARY STATEMENT FOR THE MONTH OF July-2026.xlsx`**

---

## 1. Sheet: `STAFFS` (`STAFF_PF_ESI`)

### General Structure & Standards
- **Standard Working Days**: `27` (stored in Header Cell `$H$4`).
- **Target Category**: `STAFF_PF_ESI`
- **Employee Type**: `STAFF`
- **Statutory Coverage**: EPF (12%) & ESI (0.75% / 1.75%)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 6) | Meaning & Calculation Logic | Example Result (Row 6) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col C / D** | Emp Code / ERP Emp.No | Fixed Value | `1001` | Unique Employee Identifier | `1001` |
| **Col G** | Name | Fixed Value | `KRISHNAN.A.P` | Employee Name | `KRISHNAN.A.P` |
| **Col H** | Standard Days | Header Fixed | `27` | Standard working days for July 2026 Staff | `27` |
| **Col N** | Present Days | Input | `=VLOOKUP(C6,'[1]stff-sal'!$B$2:$R$41,17,0)` | Days present in the month | `27.0` |
| **Col O** | N/H | Input | `0` | National / Public Holidays | `0.0` |
| **Col P** | C/H | Input | `0` | Casual Holidays | `0.0` |
| **Col Q** | EL | Input | `=VLOOKUP(C6,'[1]stff-sal'!$B$2:$S$41,18,0)` | Earned Leave | `0.0` |
| **Col R** | CL | Input | `0` | Casual Leave | `0.0` |
| **Col S** | SL | Input | `0` | Sick Leave | `0.0` |
| **Col T** | Total Days | Formula | `=SUM(N6:S6)` | Sum of all worked and paid leave days | `27.0` |
| **Col Z** | Fixed Gross Wages | Fixed Master | `63600` | Base gross salary before proration | ₹63,600.00 |
| **Col U** | Fixed Basic + DA | Formula | `=Z6*50%` | Fixed Basic + DA component (50% of Fixed Gross) | ₹31,800.00 |
| **Col V** | Fixed HRA | Formula | `=Z6*20%` | Fixed House Rent Allowance (20% of Fixed Gross) | ₹12,720.00 |
| **Col W** | Fixed Conveyance | Formula | `=Z6*10%` | Fixed Conveyance Allowance (10% of Fixed Gross) | ₹6,360.00 |
| **Col X** | Fixed Washing | Formula | `=Z6*10%` | Fixed Washing Allowance (10% of Fixed Gross) | ₹6,360.00 |
| **Col Y** | Fixed Other | Formula | `=Z6*10%` | Fixed Other Allowance (10% of Fixed Gross) | ₹6,360.00 |
| **Col AA** | Earned Basic + DA | Formula | `=+U6/$H$4*T6` | Prorated Basic + DA = `Fixed Basic+DA / 27 * Total Days` | ₹31,800.00 |
| **Col AB** | Earned HRA | Formula | `=+V6/$H$4*T6` | Prorated HRA = `Fixed HRA / 27 * Total Days` | ₹12,720.00 |
| **Col AC** | Earned Conveyance | Formula | `=+X6/$H$4*T6` | Prorated Conveyance = `Fixed Conveyance / 27 * Total Days` | ₹6,360.00 |
| **Col AD** | Earned Washing | Formula | `=+X6/$H$4*T6` | Prorated Washing = `Fixed Washing / 27 * Total Days` | ₹6,360.00 |
| **Col AE** | Earned Other | Formula | `=+Y6/$H$4*T6` | Prorated Other = `Fixed Other / 27 * Total Days` | ₹6,360.00 |
| **Col AF** | Earned Gross Wages | Formula | `=SUM(AA6:AE6)` | Total Earned Gross Salary | ₹63,600.00 |
| **Col AG** | PF Gross | Formula | `=+IF($AF6*80%>=15000,15000,MIN($AF6*80%))` | Wages eligible for PF (80% of Earned Gross, capped at 15000) | ₹15,000.00 |
| **Col AH** | ESI Gross | Formula | `=+IF($AF6>21000,0,MIN($AF6*90%))` | Wages eligible for ESI (90% of Earned Gross if <= 21000) | ₹0.00 |
| **Col AI** | PF Deduction | Formula | `=+IF(AG6>15000,1800,MIN(AG6*12%))` | Employee PF deduction (12% of PF Gross, capped at 1800) | ₹1,800.00 |
| **Col AJ** | Accounts PF Dedn | Formula | `1800` | Accounts audit PF amount | ₹1,800.00 |
| **Col AK** | ESI Deduction | Formula | `=+ROUNDUP((IF(Z6>21001,0,MIN(AH6,AH6*0.75%))),0)` | ESI deduction rounded up (0.75% of ESI Gross if Fixed <= 21000) | ₹0.00 |
| **Col AL** | Accounts ESI Dedn | Fixed | `0` | Accounts ESI amount | ₹0.00 |
| **Col AN** | LIC | Input | `344` | Monthly LIC policy deduction | ₹344.00 |
| **Col AP** | Advance Dedn | Input | `0` | Advance deduction installment | ₹0.00 |
| **Col AQ** | Total Deduction | Formula | `=SUM(AI6:AP6)` | Sum of PF + ESI + NATS + LIC + TDS + Advance | ₹3,944.00 |
| **Col AR** | Net Salary | Formula | `=SUM(AF6-AQ6)` | Final Net Salary Payable (`Earned Gross - Total Dedn`) | ₹59,656.00 |
| **Col AT** | New Advance Recd | Input | `0` | New advance issued in current month | ₹0.00 |
| **Col AU** | Installment Amt | Input | `15640` | Remaining advance installment balance | ₹15,640.00 |
| **Col AV** | Opening Advance | Formula | `=AT6+AU6` | `New Advance + Installment` | ₹15,640.00 |
| **Col AW** | Closing Advance | Formula | `=AV6-AP6` | `Opening Advance - Advance Dedn` | ₹15,640.00 |

---

## 2. Sheet: `WORKER'S - ESI PF` (`WORKER_PF_ESI`)

### General Structure & Standards
- **Standard Working Days**: `26`
- **Target Category**: `WORKER_PF_ESI`
- **Employee Type**: `WORKER`
- **Statutory Coverage**: EPF (12%) & ESI (0.75%)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 5) | Meaning & Calculation Logic | Example Result (Row 5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col D** | ERP Emp.No. | Fixed Value | `10002` | Worker Employee ID | `10002` |
| **Col H** | Name | Fixed Value | `D.ZAHEER HUSSAIN` | Worker Name | `D.ZAHEER HUSSAIN` |
| **Col P** | Present Days | Input | `21.5` | Days present | `21.5` |
| **Col R** | EL | Input | `=VLOOKUP(D5,'[1]work-sAl'!$B$2:$P$39,15,0)` | Earned Leave | `2.0` |
| **Col U** | Total Days | Formula | `=SUM(P5:T5)` | Total Worked + Paid Leave Days | `23.5` |
| **Col V** | Act. OT hrs | Input | `34.5` | Total Actual Overtime Hours worked | `34.5` |
| **Col W** | OT | Formula | `=IF(V5<=50,V5,IF(V5>=50,50,))` | Standard Capped OT hours (max 50 hrs) | `34.5` |
| **Col X** | Spl | Formula | `=SUM(V5-W5)` | Special OT hours above 50 | `0.0` |
| **Col Y** | OT hrs | Formula | `=W5/2` | Standard OT hours equivalent | `17.25` |
| **Col Z** | Per Day Wages | Fixed Master | `1110` | Daily wage rate | ₹1,110.00 |
| **Col AF** | OT hrs Wages | Formula | `=Z5/8` | Hourly wage rate (`Per Day Wage / 8`) | ₹138.75 |
| **Col AG** | Gross Wages | Formula | `=Z5*26` | Base Fixed Gross (`Per Day Wage * 26`) | ₹28,860.00 |
| **Col AA** | Fixed Basic + DA | Formula | `=AG5*50%` | Fixed Basic + DA (50% of Fixed Gross) | ₹14,430.00 |
| **Col AB** | Fixed HRA | Formula | `=AG5*20%` | Fixed HRA (20% of Fixed Gross) | ₹5,772.00 |
| **Col AC** | Fixed Conveyance | Formula | `=AG5*10%` | Fixed Conveyance Allowance (10% of Fixed Gross) | ₹2,886.00 |
| **Col AD** | Fixed Washing | Formula | `=AG5*10%` | Fixed Washing Allowance (10% of Fixed Gross) | ₹2,886.00 |
| **Col AE** | Fixed Other | Formula | `=AG5*10%` | Fixed Other Allowance (10% of Fixed Gross) | ₹2,886.00 |
| **Col AH** | Earned Basic + DA | Formula | `=+AA5/26*U5` | `Fixed Basic+DA / 26 * Total Days` | ₹13,042.50 |
| **Col AI** | Earned HRA | Formula | `=+AB5/26*U5` | `Fixed HRA / 26 * Total Days` | ₹5,217.00 |
| **Col AJ** | Earned Conveyance | Formula | `=+AC5/26*U5` | `Fixed Conveyance / 26 * Total Days` | ₹2,608.50 |
| **Col AK** | Earned Washing | Formula | `=+AD5/26*U5` | `Fixed Washing / 26 * Total Days` | ₹2,608.50 |
| **Col AL** | Earned Other | Formula | `=+AE5/26*U5` | `Fixed Other / 26 * Total Days` | ₹2,608.50 |
| **Col AM** | Spl. Allow | Formula | `=SUM(X5*AF5)` | `Special OT Hours * Hourly OT Rate` | ₹0.00 |
| **Col AN** | OT Wages | Formula | `=SUM(W5*AF5)` | `Capped OT Hours * Hourly OT Rate` | ₹4,786.88 |
| **Col AO** | Earned Gross | Formula | `=SUM(AH5:AN5)` | `Earned Components + Spl Allow + OT Wages` | ₹30,871.88 |
| **Col AQ** | PF Gross | Formula | `=IF((AO5-AI5-AN5)>=15000,15000,(AO5-AI5-AN5))` | `Earned Gross - Earned HRA - OT Wages`, capped at 15000 | ₹15,000.00 |
| **Col AR** | ESI Gross | Formula | `=IF(AG5>21000,0,IF(((AO5)*90/100)>21000,21000,((AO5)*90/100)))` | `90% of Earned Gross` if Fixed Gross <= 21000 | ₹0.00 |
| **Col AT** | PF Deduction | Formula | `=AQ5*12%` | `12% of PF Gross` | ₹1,800.00 |
| **Col AV** | ESI Deduction | Formula | `=AR5*0.75%` | `0.75% of ESI Gross` | ₹0.00 |
| **Col AX** | LIC | Input | `275` | LIC deduction | ₹275.00 |
| **Col AY** | Advance Dedn | Input | `7000` | Advance deduction | ₹7,000.00 |
| **Col BB** | Total Dedn | Formula | `=SUM(AT5:BA5)` | Sum of PF + ESI + LIC + Advance + NAPS + Accomdn | ₹10,875.00 |
| **Col BC** | Net Salary | Formula | `=+AO5-BB5+AS5` | `Earned Gross - Total Dedn + Arrears` | ₹19,996.88 |

---

## 3. Sheet: `STAFF'S (NAPS)` (`STAFF_NAPS`)

### General Structure & Standards
- **Standard Working Days**: `26`
- **Target Category**: `STAFF_NAPS`
- **Statutory Coverage**: Exempt ($PF=0$, $ESI=0$)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 5) | Meaning & Calculation Logic | Example Result (Row 5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col D** | ERP Emp.No | Fixed Value | `1064` | Apprentice ID | `1064` |
| **Col F** | Name | Fixed Value | `R.NIZANTH` | Apprentice Name | `R.NIZANTH` |
| **Col R** | Total Days | Formula | `=SUM(M5:Q5)` | Worked Days + Leave | `26.0` |
| **Col AD** | Fixed Gross | Fixed Master | `17000` | Base Stipend | ₹17,000.00 |
| **Col X** | Fixed Basic + DA | Formula | `=AD5*50%` | 50% of Stipend | ₹8,500.00 |
| **Col AE** | Earned Basic + DA | Formula | `=+X5/26*R5` | `Fixed Basic / 26 * Total Days` | ₹8,500.00 |
| **Col AL** | Earned Gross | Formula | `=SUM(AE5:AK5)` | Earned Stipend | ₹17,000.00 |
| **Col AN** | NAPS Dedn | Input | `1500` | Monthly NAPS contribution deduction | ₹1,500.00 |
| **Col AR** | Total Dedn | Formula | `=SUM(AN5:AQ5)` | `NAPS + LIC + Advance + Accomdation` | ₹1,500.00 |
| **Col AS** | Net Salary | Formula | `=+AL5-AR5` | `Earned Gross - Total Dedn` | ₹15,500.00 |

---

## 4. Sheet: `WORKER'S (NAPS) (2)` (`WORKER_NAPS`)

### General Structure & Standards
- **Standard Working Days**: `27`
- **Target Category**: `WORKER_NAPS`
- **Statutory Coverage**: Exempt ($PF=0$, $ESI=0$)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 5) | Meaning & Calculation Logic | Example Result (Row 5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col D** | ERP Emp.No | Fixed Value | `10154` | Worker NAPS ID | `10154` |
| **Col F** | Name | Fixed Value | `E.ESSAKIRAJA` | Worker NAPS Name | `E.ESSAKIRAJA` |
| **Col R** | Total Days | Formula | `=SUM(M5:Q5)` | Total Worked Days | `27.0` |
| **Col S** | Act. OT hrs | Input | `55` | Actual OT Hours | `55.0` |
| **Col T** | OT | Formula | `=IF(S5<=50,S5,IF(S5>=50,50,))` | Capped OT (50 hrs) | `50.0` |
| **Col U** | Spl | Formula | `=SUM(S5-T5)` | Special OT (above 50 hrs) | `5.0` |
| **Col W** | Per Day Wages | Fixed Master | `455` | Daily wage | ₹455.00 |
| **Col AC** | OT hrs Wages | Formula | `=W5/8` | `Per Day Wage / 8` | ₹56.88 |
| **Col AD** | Gross Wages | Formula | `=W5*27` | Base Fixed Gross (`Per Day Wage * 27`) | ₹12,285.00 |
| **Col AE** | Earned Basic + DA | Formula | `=+X5/27*R5` | Prorated Basic + DA | ₹6,142.50 |
| **Col AJ** | Spl. Allow | Formula | `=SUM(U5*AC5)` | `Special OT * Hourly Rate` | ₹284.38 |
| **Col AK** | OT Wages | Formula | `=SUM(T5*AC5)` | `Capped OT * Hourly Rate` | ₹2,843.75 |
| **Col AL** | Earned Gross | Formula | `=SUM(AE5:AK5)` | Total Earned Wages + OT | ₹15,413.13 |
| **Col AN** | NAPS Dedn | Input | `1500` | NAPS Deduction | ₹1,500.00 |
| **Col AP** | Advance Dedn | Input | `2000` | Advance Deduction | ₹2,000.00 |
| **Col AR** | Total Dedn | Formula | `=SUM(AN5:AQ5)` | `NAPS + LIC + Advance + Accomdation` | ₹3,500.00 |
| **Col AS** | Net Salary | Formula | `=+AL5-AR5` | `Earned Gross - Total Dedn` | ₹11,913.13 |

---

## 5. Sheet: `Non-pf ESi staff` (`STAFF_NON_PF_ESI`)

### General Structure & Standards
- **Standard Working Days**: `27`
- **Target Category**: `STAFF_NON_PF_ESI`
- **Statutory Coverage**: Excluded ($PF=0$, $ESI=0$)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 5) | Meaning & Calculation Logic | Example Result (Row 5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col D** | ERP Emp.No | Fixed Value | `20279` | Non-PF Staff ID | `20279` |
| **Col F** | Name | Fixed Value | `M.SENTHILMANI` | Staff Name | `M.SENTHILMANI` |
| **Col R** | Total Days | Formula | `=SUM(M5:Q5)` | Worked Days | `27.0` |
| **Col AD** | Fixed Gross | Fixed Master | `55000` | Base Fixed Gross | ₹55,000.00 |
| **Col AE** | Earned Basic + DA | Formula | `=+X5/27*R5` | `Fixed Basic / 27 * Total Days` | ₹27,500.00 |
| **Col AL** | Earned Gross | Formula | `=SUM(AE5:AK5)` | Total Earned Gross | ₹55,000.00 |
| **Col AR** | Total Dedn | Formula | `=SUM(AN5:AQ5)` | Deductions ($0.00$) | ₹0.00 |
| **Col AS** | Net Salary | Formula | `=+AL5-AR5` | `Earned Gross - Total Dedn` | ₹55,000.00 |

---

## 6. Sheet: `Non-pf ESi worker` (`WORKER_NON_PF_ESI`)

### General Structure & Standards
- **Standard Working Days**: `27`
- **Target Category**: `WORKER_NON_PF_ESI`
- **Statutory Coverage**: Excluded ($PF=0$, $ESI=0$)

### Column Formula Mapping

| Column | Header | Data Type | Cell Formula (Row 5) | Meaning & Calculation Logic | Example Result (Row 5) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Col D** | ERP Emp.No | Fixed Value | `10041` | Non-PF Worker ID | `10041` |
| **Col F** | Name | Fixed Value | `D.JESU BALAN` | Worker Name | `D.JESU BALAN` |
| **Col R** | Total Days | Formula | `=SUM(M5:Q5)` | Worked Days | `27.0` |
| **Col S** | Act. OT hrs | Input | `65.5` | Actual OT Hours | `65.5` |
| **Col T** | OT | Formula | `=IF(S5<=50,S5,IF(S5>=50,50,))` | Capped OT (50 hrs) | `50.0` |
| **Col U** | Spl | Formula | `=SUM(S5-T5)` | Special OT (15.5 hrs) | `15.5` |
| **Col W** | Per Day Wages | Fixed Master | `906` | Daily Wage Rate | ₹906.00 |
| **Col AC** | OT hrs Wages | Formula | `=W5/8` | `Per Day Wage / 8` | ₹113.25 |
| **Col AD** | Gross Wages | Formula | `=+W5*27` | Base Fixed Gross (`Per Day Wage * 27`) | ₹24,462.00 |
| **Col AJ** | Spl. Allow | Formula | `=SUM(U5*AC5)` | `Special OT * Hourly Rate` | ₹1,755.38 |
| **Col AK** | OT Wages | Formula | `=SUM(T5*AC5)` | `Capped OT * Hourly Rate` | ₹5,662.50 |
| **Col AL** | Earned Gross | Formula | `=SUM(AE5:AK5)` | Earned Wages + OT | ₹31,879.88 |
| **Col AP** | Advance Dedn | Input | `1000` | Advance Deduction | ₹1,000.00 |
| **Col AR** | Total Dedn | Formula | `=SUM(AN5:AQ5)` | Total Deductions | ₹1,000.00 |
| **Col AS** | Net Salary | Formula | `=+AL5-AR5` | `Earned Gross - Total Dedn` | ₹30,879.88 |

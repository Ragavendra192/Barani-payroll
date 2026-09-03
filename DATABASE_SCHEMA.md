# Database Schema Documentation — BHIPL Payroll Application

The **Barani Hydraulics India Private Limited (Unit - I)** Payroll System uses a normalized SQL Server database model supporting six employee/payroll categories:

1. `STAFF_PF_ESI`: Staff with PF and ESI
2. `WORKER_PF_ESI`: Worker with Per Day Wages, 50-hr OT Capping, Special OT, PF, and ESI
3. `STAFF_NAPS`: Staff Apprentice (Non-PF/ESI, NAPS Deduction)
4. `WORKER_NAPS`: Worker Apprentice (Per Day Wages, Worker OT, Non-PF/ESI, NAPS Deduction)
5. `STAFF_NON_PF_ESI`: Staff Excluded from PF/ESI Coverage
6. `WORKER_NON_PF_ESI`: Worker Excluded from PF/ESI Coverage (Per Day Wages & Worker OT)

---

## 1. `EmployeeMaster` Table
Central employee master table storing permanent information.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `Employee_ID` | INT IDENTITY(1,1) | PRIMARY KEY, UNIQUE | Surrogate key |
| `Emp_No` | NVARCHAR(50) | NOT NULL, UNIQUE | Business Employee Code / ERP Emp No |
| `ERP_Emp_No` | NVARCHAR(50) | NULL | ERP Employee Identifier |
| `Emp_Code` | NVARCHAR(50) | NULL | Employee Code |
| `Emp_Name` / `Employee_Name` | NVARCHAR(150) | NOT NULL | Full Name of Employee |
| `Employee_Type` | NVARCHAR(20) | NOT NULL | `STAFF` or `WORKER` |
| `Payroll_Category` | NVARCHAR(30) | NOT NULL | `PF_ESI`, `NAPS`, `NON_PF_ESI` |
| `Category` | NVARCHAR(40) | NOT NULL | `STAFF_PF_ESI`, `WORKER_PF_ESI`, `STAFF_NAPS`, `WORKER_NAPS`, `STAFF_NON_PF_ESI`, `WORKER_NON_PF_ESI` |
| `UAN_No` | NVARCHAR(50) | NULL | Universal Account Number (PF) |
| `ESI_No` | NVARCHAR(50) | NULL | ESI Card Number |
| `Designation` | NVARCHAR(100) | NULL | Role Designation |
| `Grade` | NVARCHAR(100) | NULL | Grade Classification |
| `Department` | NVARCHAR(100) | NULL | Department Name |
| `DOJ` | DATE | NULL | Date of Joining |
| `Rejoin_DOJ` | DATE | NULL | Rejoin Date of Joining |
| `Status` | NVARCHAR(20) | DEFAULT 'Active' | `Active` / `Inactive` |

---

## 2. `EmployeeSalaryMaster` Table
Stores fixed component structures and wage rates per employee.

| Column | Type | Description |
| :--- | :--- | :--- |
| `EmployeeSalary_ID` | INT IDENTITY(1,1) PRIMARY KEY | Master Salary ID |
| `Employee_ID` | INT FK -> `EmployeeMaster(Employee_ID)` | Foreign Key |
| `Basic_DA` | DECIMAL(12,2) | Fixed Basic + DA Amount |
| `HRA` | DECIMAL(12,2) | Fixed House Rent Allowance |
| `Conveyance_Allowance` | DECIMAL(12,2) | Fixed Conveyance Allowance |
| `Washing_Allowance` | DECIMAL(12,2) | Fixed Washing Allowance |
| `Other_Allowance` | DECIMAL(12,2) | Fixed Other Allowance |
| `Per_Day_Wage` | DECIMAL(12,2) | Fixed Per Day Wage (Workers) |
| `OT_Rate` | DECIMAL(12,2) | Hourly Overtime Rate ($\text{Per Day Wage} / 8$) |
| `Special_OT_Rate` | DECIMAL(12,2) | Special Overtime Hourly Rate |
| `PF_Eligible` | BIT | 1 if PF applies, else 0 |
| `ESI_Eligible` | BIT | 1 if ESI applies, else 0 |
| `Effective_From` | DATE | Effective Date |
| `Active` | BIT | 1 if active rate |

---

## 3. `PayrollPeriod` Table
Monthly payroll period state tracking.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `PayrollPeriod_ID` | INT IDENTITY(1,1) | PRIMARY KEY | Period ID |
| `Payroll_Year` | INT | NOT NULL | Calendar Year |
| `Payroll_Month` | INT | NOT NULL | Calendar Month (1-12) |
| `Standard_Working_Days` | DECIMAL(6,2) | DEFAULT 26.00 | Standard working days |
| `Status` | NVARCHAR(20) | DEFAULT 'DRAFT' | `DRAFT`, `CALCULATED`, `APPROVED`, `LOCKED` |

---

## 4. `PayrollAttendance` Table
Monthly attendance and overtime records.

| Column | Type | Description |
| :--- | :--- | :--- |
| `PayrollAttendance_ID` | INT IDENTITY(1,1) PRIMARY KEY | Attendance ID |
| `PayrollPeriod_ID` | INT FK -> `PayrollPeriod` | Foreign Key |
| `Employee_ID` | INT FK -> `EmployeeMaster` | Foreign Key |
| `Present_Days` | DECIMAL(5,2) | Days Present |
| `Normal_Holiday` | DECIMAL(5,2) | National / Normal Holidays |
| `EL` / `CL` / `SL` | DECIMAL(5,2) | Earned / Casual / Sick Leave |
| `Total_Days` | DECIMAL(5,2) | Present + Holidays + Leave |
| `Actual_OT_Hours` | DECIMAL(8,2) | Total Recorded OT Hours |
| `OT_Hours` | DECIMAL(8,2) | OT Hours (capped at 50 for Workers) |
| `Special_OT_Hours` | DECIMAL(8,2) | Excess OT Hours beyond 50 |

---

## 5. `PayrollTransaction` Table
Monthly calculated earnings, statutory deductions, loan repayments, and Net Payable Salary.

| Column | Type | Description |
| :--- | :--- | :--- |
| `PayrollTransaction_ID` | INT IDENTITY(1,1) PRIMARY KEY | Transaction ID |
| `PayrollPeriod_ID` | INT FK -> `PayrollPeriod` | Period Foreign Key |
| `Employee_ID` | INT FK -> `EmployeeMaster` | Employee Foreign Key |
| `Category` | NVARCHAR(40) | 1 of 6 standard categories |
| `Basic_DA_Earned` | DECIMAL(12,2) | Pro-rated Earned Basic + DA |
| `HRA_Earned` | DECIMAL(12,2) | Pro-rated Earned HRA |
| `Conveyance_Earned` | DECIMAL(12,2) | Pro-rated Earned Conveyance |
| `Washing_Allowance_Earned` | DECIMAL(12,2) | Pro-rated Earned Washing Allowance |
| `Other_Allowance_Earned` | DECIMAL(12,2) | Pro-rated Earned Other Allowance |
| `Special_Allowance_Earned` | DECIMAL(12,2) | Earned Special Allowance (Special OT) |
| `OT_Wages` | DECIMAL(12,2) | Overtime Wages |
| `Gross_Wages` | DECIMAL(12,2) | Earned Gross Salary |
| `PF_Deduction` | DECIMAL(12,2) | Employee PF Deduction |
| `ESI_Deduction` | DECIMAL(12,2) | Employee ESI Deduction |
| `Arrears` | DECIMAL(12,2) | Arrears Addition / Adjustment |
| `NAPS_Deduction` | DECIMAL(12,2) | NAPS Apprentice Deduction |
| `LIC_Deduction` | DECIMAL(12,2) | Life Insurance Deduction |
| `Advance_Deduction` | DECIMAL(12,2) | Monthly Loan / Advance Installment |
| `Accommodation_Deduction` | DECIMAL(12,2) | Accommodation Deduction |
| `Other_Deduction` | DECIMAL(12,2) | Miscellaneous Deduction |
| `Total_Deduction` | DECIMAL(12,2) | Total Deductions |
| `Net_Salary` | DECIMAL(12,2) | Net Payable Salary |

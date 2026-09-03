# PAYROLL FORMULA CONFIGURATION — TECHNICAL SPECIFICATION

Authoritative Specification for the Protected Admin-Only Payroll Formula Configuration System in BHIPL Unit-I Payroll Application.

---

## 1. Overview & Security Architecture

The **Payroll Formula Configuration Page** (`/payroll-formulas`) provides an admin-only, password-protected interface for defining, testing, versioning, and maintaining category-specific payroll calculation formulas.

### Access Control
- **URL Route**: `/payroll-formulas`
- **Admin Password**: `2882` (Configurable via environment variable `PAYROLL_FORMULA_ADMIN_PASSWORD`).
- **Server-Side Session Security**:
  - Sets `session['payroll_formula_admin'] = True` upon successful password validation.
  - Password is never stored in HTML, JavaScript, URL, localStorage, or cookies as plain text.
  - All formula viewing, validation, testing, and saving routes are enforced with the `@require_formula_admin` decorator.
  - Unauthenticated direct URL requests to `/payroll-formulas/save`, `/payroll-formulas/test`, or `/payroll-formulas/validate` are blocked with HTTP `401 Unauthorized`.

---

## 2. Six Separate Category Isolation

The system maintains six completely isolated category configurations in SQL Server:

1. **`STAFF_PF_ESI`**: Staff employees under statutory PF & ESI.
2. **`WORKER_PF_ESI`**: Factory workers under statutory PF & ESI (with OT rules).
3. **`STAFF_NAPS`**: Staff NAPS apprentices (Exempt from PF & ESI).
4. **`WORKER_NAPS`**: Worker NAPS apprentices (Exempt from PF & ESI, worker OT rules).
5. **`STAFF_NON_PF_ESI`**: Staff employees excluded from statutory PF & ESI.
6. **`WORKER_NON_PF_ESI`**: Worker employees excluded from statutory PF & ESI.

> [!IMPORTANT]
> Modifying formulas for one category (e.g. `WORKER_PF_ESI`) will **never** modify or affect formulas for any other category.

---

## 3. SQL Server Database Table (`PayrollFormulaRules`)

Formula rules are stored in a dedicated SQL Server table supporting incremental versioning and effective date tracking.

### DDL Schema

```sql
CREATE TABLE PayrollFormulaRules (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Category NVARCHAR(50) NOT NULL,
    Section NVARCHAR(50) NOT NULL,
    RuleName NVARCHAR(50) NOT NULL,
    Formula NVARCHAR(MAX) NOT NULL,
    IsEnabled BIT DEFAULT 1,
    EffectiveFrom DATETIME NOT NULL DEFAULT GETDATE(),
    EffectiveTo DATETIME NULL,
    Version INT DEFAULT 1,
    IsActive BIT DEFAULT 1,
    CreatedBy NVARCHAR(100) DEFAULT 'Admin',
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy NVARCHAR(100) DEFAULT 'Admin',
    UpdatedAt DATETIME DEFAULT GETDATE()
);

CREATE INDEX IX_PayrollFormulaRules_Cat_Active ON PayrollFormulaRules(Category, IsActive, EffectiveFrom);
```

---

## 4. Safe AST Formula Validator & Cycle Detector

Formula evaluation is executed using a custom Python `ast` (Abstract Syntax Tree) expression parser (`services/payroll_formula_validator.py`).

### Security Features
- **No `eval()`**: Direct call to Python `eval()` is strictly prohibited.
- **Allowed Operators**: `+`, `-`, `*`, `/`, `%`, `**`, `()`.
- **Allowed Math Functions**: `min`, `max`, `ceil`, `floor`, `round`, `abs`, `if_else`.
- **Dependency Cycle Detection**: Automatically inspects formula dependencies across all rules in a category and rejects circular formulas (e.g. `A = B + 10; B = A + 5`) returning:
  ```text
  Formula dependency cycle detected: A -> B -> A
  ```

---

## 5. Standardized Variable Reference List

| Category | Variable Name | Description |
| :--- | :--- | :--- |
| **Employee Master** | `Basic` | Fixed Basic Salary |
| | `DA` | Fixed Dearness Allowance |
| | `HRA` | Fixed House Rent Allowance |
| | `Conveyance` | Fixed Conveyance Allowance |
| | `Washing` | Fixed Washing Allowance |
| | `Other_Allowance` | Fixed Other Allowance |
| | `Special_Allowance` | Special Allowance |
| | `Per_Day_Wage` | Worker Daily Wage Rate |
| | `Fixed_Gross` | Base Fixed Gross Wages |
| **Attendance** | `Working_Days` | Standard Monthly Working Days (e.g. 26 or 27) |
| | `Present_Days` | Actual Present Days |
| | `PH` / `CL` / `SL` / `PL` | Leave Types |
| | `Worked_Days` | Total Payable Worked Days |
| **Overtime** | `OT_Hours` | Actual Overtime Hours |
| | `OT_Rate` | Computed Overtime Rate (`Per_Day_Wage / 8.0`) |
| | `OT_Wages` | Capped OT Wages (First 50 Hours) |
| | `Special_OT_Amount` | Special OT Wages (Above 50 Hours) |
| **Earned Wages** | `Earned_Basic_DA` | Earned Basic & DA Salary |
| | `Earned_HRA` | Earned HRA Allowance |
| | `Earned_Conveyance` | Earned Conveyance Allowance |
| | `Earned_Washing` | Earned Washing Allowance |
| | `Earned_Other` | Earned Other Allowance |
| **Payroll Summary** | `Gross` | Total Earned Gross Wages |
| | `PF_Gross` | Statutory PF Eligible Gross |
| | `PF` | Employee PF Deduction |
| | `ESI_Gross` | Statutory ESI Eligible Gross |
| | `ESI` | Employee ESI Deduction |
| | `LIC` / `TDS` / `Advance` | Manual Deductions |
| | `Total_Deduction` | Sum of All Deductions |
| | `Net_Salary` | Net Salary Payable (`Gross + Arrears - Total_Deduction`) |

---

## 6. How to Use the Configuration Interface

1. **Access Page**: Navigate to `http://127.0.0.1:5000/payroll-formulas`.
2. **Authenticate**: Enter password `2882` and click **LOGIN**.
3. **Select Category**: Choose target category from top dropdown (e.g. `2. Worker — PF / ESI`).
4. **Define Formulas**: Edit formulas in input fields (or click variable chips on sidebar to insert).
5. **Test Formulas**: Click `[ TEST FORMULAS ]`, enter sample values, and click **RUN TEST EVALUATION** to preview step-by-step calculation results.
6. **Save**: Click `[ SAVE FORMULAS ]`. The system validates AST syntax and cycle dependencies before writing new versioned records to SQL Server `PayrollFormulaRules`.

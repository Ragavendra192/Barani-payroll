-- ============================================================================
-- Migration: 001_payroll_redesign.sql
-- Description: Creates normalized schema for all 6 BHIPL Employee/Payroll categories:
--              STAFF_PF_ESI, WORKER_PF_ESI, STAFF_NAPS, WORKER_NAPS, STAFF_NON_PF_ESI, WORKER_NON_PF_ESI
-- ============================================================================

-- 1. Ensure EmployeeMaster Has All Redesigned Columns
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeMaster') AND type in (N'U'))
BEGIN
    CREATE TABLE EmployeeMaster (
        Employee_ID INT IDENTITY(1,1) PRIMARY KEY,
        Emp_No NVARCHAR(50) NOT NULL UNIQUE,
        ERP_Emp_No NVARCHAR(50) NULL,
        Emp_Code NVARCHAR(50) NULL,
        Employee_Name NVARCHAR(150) NOT NULL,
        Employee_Type NVARCHAR(20) NOT NULL DEFAULT 'STAFF',      -- STAFF / WORKER
        Payroll_Category NVARCHAR(30) NOT NULL DEFAULT 'PF_ESI',   -- PF_ESI / NAPS / NON_PF_ESI
        Category NVARCHAR(40) NOT NULL DEFAULT 'STAFF_PF_ESI',    -- STAFF_PF_ESI, WORKER_PF_ESI, STAFF_NAPS, WORKER_NAPS, STAFF_NON_PF_ESI, WORKER_NON_PF_ESI
        UAN_No NVARCHAR(50) NULL,
        ESI_No NVARCHAR(50) NULL,
        Designation NVARCHAR(100) NULL,
        Grade NVARCHAR(100) NULL,
        Department NVARCHAR(100) NULL,
        DOJ DATE NULL,
        Rejoin_DOJ DATE NULL,
        Status NVARCHAR(20) DEFAULT 'Active',
        Created_At DATETIME2 DEFAULT GETDATE(),
        Updated_At DATETIME2 DEFAULT GETDATE()
    );
END;

-- Alter existing EmployeeMaster safely if it was created previously
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeMaster') AND type in (N'U'))
BEGIN
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Employee_ID')
        ALTER TABLE EmployeeMaster ADD Employee_ID INT IDENTITY(1,1);
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='ERP_Emp_No')
        ALTER TABLE EmployeeMaster ADD ERP_Emp_No NVARCHAR(50) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Emp_Code')
        ALTER TABLE EmployeeMaster ADD Emp_Code NVARCHAR(50) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Employee_Name')
        ALTER TABLE EmployeeMaster ADD Employee_Name NVARCHAR(150) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Employee_Type')
        ALTER TABLE EmployeeMaster ADD Employee_Type NVARCHAR(20) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Payroll_Category')
        ALTER TABLE EmployeeMaster ADD Payroll_Category NVARCHAR(30) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='UAN_No')
        ALTER TABLE EmployeeMaster ADD UAN_No NVARCHAR(50) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Designation')
        ALTER TABLE EmployeeMaster ADD Designation NVARCHAR(100) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Grade')
        ALTER TABLE EmployeeMaster ADD Grade NVARCHAR(100) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Rejoin_DOJ')
        ALTER TABLE EmployeeMaster ADD Rejoin_DOJ DATE NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Status')
        ALTER TABLE EmployeeMaster ADD Status NVARCHAR(20) NULL;
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='EmployeeMaster' AND COLUMN_NAME='Updated_At')
        ALTER TABLE EmployeeMaster ADD Updated_At DATETIME2 NULL;
END;

-- Sync existing column values into redesigned fields if needed
UPDATE EmployeeMaster SET Employee_Name = Emp_Name WHERE Employee_Name IS NULL AND Emp_Name IS NOT NULL;
UPDATE EmployeeMaster SET UAN_No = UAN WHERE UAN_No IS NULL AND UAN IS NOT NULL;
UPDATE EmployeeMaster SET Status = 'Active' WHERE Status IS NULL;
UPDATE EmployeeMaster SET Employee_Type = 'STAFF' WHERE Employee_Type IS NULL;
UPDATE EmployeeMaster SET Payroll_Category = 'PF_ESI' WHERE Payroll_Category IS NULL;
UPDATE EmployeeMaster SET Category = 'STAFF_PF_ESI' WHERE Category IS NULL;

-- 2. Create EmployeeSalaryMaster Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeSalaryMaster') AND type in (N'U'))
BEGIN
    CREATE TABLE EmployeeSalaryMaster (
        EmployeeSalary_ID INT IDENTITY(1,1) PRIMARY KEY,
        Employee_ID INT NOT NULL,
        Basic_DA DECIMAL(12,2) DEFAULT 0.00,
        HRA DECIMAL(12,2) DEFAULT 0.00,
        Conveyance_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Washing_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Other_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Per_Day_Wage DECIMAL(12,2) DEFAULT 0.00,
        OT_Rate DECIMAL(12,2) DEFAULT 0.00,
        Special_OT_Rate DECIMAL(12,2) DEFAULT 0.00,
        PF_Eligible BIT DEFAULT 1,
        ESI_Eligible BIT DEFAULT 1,
        Effective_From DATE DEFAULT GETDATE(),
        Effective_To DATE NULL,
        Active BIT DEFAULT 1,
        CONSTRAINT FK_EmployeeSalaryMaster_Employee FOREIGN KEY (Employee_ID) REFERENCES EmployeeMaster(Employee_ID) ON DELETE CASCADE
    );
END;

-- 3. Create PayrollPeriod Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollPeriod') AND type in (N'U'))
BEGIN
    CREATE TABLE PayrollPeriod (
        PayrollPeriod_ID INT IDENTITY(1,1) PRIMARY KEY,
        Payroll_Year INT NOT NULL,
        Payroll_Month INT NOT NULL,
        Standard_Working_Days DECIMAL(6,2) DEFAULT 26.00,
        Status NVARCHAR(20) DEFAULT 'DRAFT',  -- DRAFT, CALCULATED, APPROVED, LOCKED
        Created_At DATETIME2 DEFAULT GETDATE(),
        Updated_At DATETIME2 DEFAULT GETDATE(),
        CONSTRAINT UQ_PayrollPeriod_Year_Month UNIQUE (Payroll_Year, Payroll_Month)
    );
END;

-- 4. Create PayrollAttendance Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollAttendance') AND type in (N'U'))
BEGIN
    CREATE TABLE PayrollAttendance (
        PayrollAttendance_ID INT IDENTITY(1,1) PRIMARY KEY,
        PayrollPeriod_ID INT NOT NULL,
        Employee_ID INT NOT NULL,
        Present_Days DECIMAL(5,2) DEFAULT 0.00,
        Normal_Holiday DECIMAL(5,2) DEFAULT 0.00,
        Company_Holiday DECIMAL(5,2) DEFAULT 0.00,
        EL DECIMAL(5,2) DEFAULT 0.00,
        CL DECIMAL(5,2) DEFAULT 0.00,
        SL DECIMAL(5,2) DEFAULT 0.00,
        Total_Days DECIMAL(5,2) DEFAULT 0.00,
        Working_Days DECIMAL(5,2) DEFAULT 0.00,
        Actual_OT_Hours DECIMAL(8,2) DEFAULT 0.00,
        OT_Hours DECIMAL(8,2) DEFAULT 0.00,
        Special_OT_Hours DECIMAL(8,2) DEFAULT 0.00,
        OT_Days DECIMAL(5,2) DEFAULT 0.00,
        CONSTRAINT UQ_PayrollAttendance_Period_Emp UNIQUE (PayrollPeriod_ID, Employee_ID),
        CONSTRAINT FK_PayrollAttendance_Period FOREIGN KEY (PayrollPeriod_ID) REFERENCES PayrollPeriod(PayrollPeriod_ID) ON DELETE CASCADE,
        CONSTRAINT FK_PayrollAttendance_Employee FOREIGN KEY (Employee_ID) REFERENCES EmployeeMaster(Employee_ID) ON DELETE CASCADE
    );
END;

-- 5. Create PayrollTransaction Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollTransaction') AND type in (N'U'))
BEGIN
    CREATE TABLE PayrollTransaction (
        PayrollTransaction_ID INT IDENTITY(1,1) PRIMARY KEY,
        PayrollPeriod_ID INT NOT NULL,
        Employee_ID INT NOT NULL,
        Employee_Type NVARCHAR(20) NOT NULL,
        Payroll_Category NVARCHAR(30) NOT NULL,
        Category NVARCHAR(40) NOT NULL,
        Basic_DA DECIMAL(12,2) DEFAULT 0.00,
        HRA DECIMAL(12,2) DEFAULT 0.00,
        Conveyance_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Washing_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Other_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Special_Allowance DECIMAL(12,2) DEFAULT 0.00,
        Per_Day_Wage DECIMAL(12,2) DEFAULT 0.00,
        OT_Hours DECIMAL(8,2) DEFAULT 0.00,
        OT_Rate DECIMAL(12,2) DEFAULT 0.00,
        OT_Wages DECIMAL(12,2) DEFAULT 0.00,
        Basic_DA_Earned DECIMAL(12,2) DEFAULT 0.00,
        HRA_Earned DECIMAL(12,2) DEFAULT 0.00,
        Conveyance_Earned DECIMAL(12,2) DEFAULT 0.00,
        Washing_Allowance_Earned DECIMAL(12,2) DEFAULT 0.00,
        Other_Allowance_Earned DECIMAL(12,2) DEFAULT 0.00,
        Special_Allowance_Earned DECIMAL(12,2) DEFAULT 0.00,
        Gross_Wages DECIMAL(12,2) DEFAULT 0.00,
        PF_Gross DECIMAL(12,2) DEFAULT 0.00,
        ESI_Gross DECIMAL(12,2) DEFAULT 0.00,
        PF_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Accounts_PF_Deduction DECIMAL(12,2) DEFAULT 0.00,
        ESI_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Accounts_ESI_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Arrears DECIMAL(12,2) DEFAULT 0.00,
        NAPS_Deduction DECIMAL(12,2) DEFAULT 0.00,
        LIC_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Advance_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Accommodation_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Other_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Total_Deduction DECIMAL(12,2) DEFAULT 0.00,
        Net_Salary DECIMAL(12,2) DEFAULT 0.00,
        Created_At DATETIME2 DEFAULT GETDATE(),
        Updated_At DATETIME2 DEFAULT GETDATE(),
        CONSTRAINT UQ_PayrollTransaction_Period_Emp UNIQUE (PayrollPeriod_ID, Employee_ID),
        CONSTRAINT FK_PayrollTransaction_Period FOREIGN KEY (PayrollPeriod_ID) REFERENCES PayrollPeriod(PayrollPeriod_ID) ON DELETE CASCADE,
        CONSTRAINT FK_PayrollTransaction_Employee FOREIGN KEY (Employee_ID) REFERENCES EmployeeMaster(Employee_ID) ON DELETE CASCADE
    );
END;

-- 6. Create EmployeeAdvance Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeAdvance') AND type in (N'U'))
BEGIN
    CREATE TABLE EmployeeAdvance (
        Advance_ID INT IDENTITY(1,1) PRIMARY KEY,
        Employee_ID INT NOT NULL,
        Advance_Date DATE DEFAULT GETDATE(),
        New_Advance_Received DECIMAL(12,2) DEFAULT 0.00,
        Total_Advance DECIMAL(12,2) DEFAULT 0.00,
        Installment_Amount DECIMAL(12,2) DEFAULT 0.00,
        Opening_Advance DECIMAL(12,2) DEFAULT 0.00,
        Closing_Advance DECIMAL(12,2) DEFAULT 0.00,
        Status NVARCHAR(20) DEFAULT 'Active',
        CONSTRAINT FK_EmployeeAdvance_Employee FOREIGN KEY (Employee_ID) REFERENCES EmployeeMaster(Employee_ID) ON DELETE CASCADE
    );
END;

-- 7. Create PayrollDeduction Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollDeduction') AND type in (N'U'))
BEGIN
    CREATE TABLE PayrollDeduction (
        Deduction_ID INT IDENTITY(1,1) PRIMARY KEY,
        PayrollPeriod_ID INT NOT NULL,
        Employee_ID INT NOT NULL,
        Deduction_Type NVARCHAR(50) NOT NULL,  -- LIC, Advance, Accommodation, NAPS, Arrears, Other
        Amount DECIMAL(12,2) DEFAULT 0.00,
        Reason NVARCHAR(255) NULL,
        Created_At DATETIME2 DEFAULT GETDATE(),
        CONSTRAINT FK_PayrollDeduction_Period FOREIGN KEY (PayrollPeriod_ID) REFERENCES PayrollPeriod(PayrollPeriod_ID) ON DELETE CASCADE,
        CONSTRAINT FK_PayrollDeduction_Employee FOREIGN KEY (Employee_ID) REFERENCES EmployeeMaster(Employee_ID) ON DELETE CASCADE
    );
END;

-- 8. Populate EmployeeSalaryMaster for existing employees if not present
INSERT INTO EmployeeSalaryMaster (
    Employee_ID, Basic_DA, HRA, Conveyance_Allowance, Washing_Allowance,
    Other_Allowance, Per_Day_Wage, OT_Rate, PF_Eligible, ESI_Eligible, Active
)
SELECT
    m.Employee_ID,
    ISNULL(m.Basic, 0.00) + ISNULL(m.DA, 0.00) AS Basic_DA,
    ISNULL(m.HRA, 0.00) AS HRA,
    ISNULL(m.Conveyance, 0.00) AS Conveyance_Allowance,
    ISNULL(m.Washing_Allowance, 0.00) AS Washing_Allowance,
    ISNULL(m.Special_Allowance, 0.00) AS Other_Allowance,
    ISNULL(m.Daily_Wage, 0.00) AS Per_Day_Wage,
    CASE WHEN ISNULL(m.Daily_Wage,0) > 0 THEN m.Daily_Wage / 8.0 ELSE 56.25 END AS OT_Rate,
    ISNULL(m.PF_Eligible, 1) AS PF_Eligible,
    ISNULL(m.ESI_Eligible, 1) AS ESI_Eligible,
    1 AS Active
FROM EmployeeMaster m
WHERE NOT EXISTS (SELECT 1 FROM EmployeeSalaryMaster sm WHERE sm.Employee_ID = m.Employee_ID);

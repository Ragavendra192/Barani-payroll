-- ============================================================================
-- Migration Rollback Reference: 002_rollback_payroll_redesign.sql
-- Description: Reference script for rolling back redesigned 6-category tables
-- WARNING: DO NOT RUN UNLESS YOU INTEND TO REMOVE THE REDESIGNED TABLES!
-- ============================================================================

-- Drop new tables in reverse dependency order
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollDeduction') AND type in (N'U'))
    DROP TABLE PayrollDeduction;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeAdvance') AND type in (N'U'))
    DROP TABLE EmployeeAdvance;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollTransaction') AND type in (N'U'))
    DROP TABLE PayrollTransaction;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollAttendance') AND type in (N'U'))
    DROP TABLE PayrollAttendance;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'PayrollPeriod') AND type in (N'U'))
    DROP TABLE PayrollPeriod;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'EmployeeSalaryMaster') AND type in (N'U'))
    DROP TABLE EmployeeSalaryMaster;

-- Note: EmployeeMaster contains permanent employee records.
-- To preserve employee history, EmployeeMaster is NOT dropped.

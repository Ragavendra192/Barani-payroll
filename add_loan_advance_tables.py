from db import get_db_connection

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Loans table
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Loans') AND type in (N'U'))
    CREATE TABLE Loans (
        Id INT IDENTITY PRIMARY KEY,
        Emp_No INT NOT NULL,
        Start_Year INT NOT NULL,
        Start_Month INT NOT NULL,
        Total_Amount DECIMAL(12,2) NOT NULL,
        Installments INT NOT NULL,
        Monthly_Amount DECIMAL(12,2) NOT NULL,
        Remaining_Amount DECIMAL(12,2) NOT NULL,
        Status NVARCHAR(50) DEFAULT 'Active',
        Note NVARCHAR(400),
        Created_At DATETIME DEFAULT GETDATE()
    )
    """)

    # Advances table
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Advances') AND type in (N'U'))
    CREATE TABLE Advances (
        Id INT IDENTITY PRIMARY KEY,
        Emp_No INT NOT NULL,
        Start_Year INT NOT NULL,
        Start_Month INT NOT NULL,
        Total_Amount DECIMAL(12,2) NOT NULL,
        Installments INT NOT NULL,
        Monthly_Amount DECIMAL(12,2) NOT NULL,
        Remaining_Amount DECIMAL(12,2) NOT NULL,
        Status NVARCHAR(50) DEFAULT 'Active',
        Note NVARCHAR(400),
        Created_At DATETIME DEFAULT GETDATE()
    )
    """)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print('Loans and Advances tables created (if not existing).')

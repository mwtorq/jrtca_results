"""Add ClassNumber column to TrialClass table."""

import pyodbc
import sys

# Connection string
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=TrialResults;"
    "Trusted_Connection=yes;"
)

ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]

def get_connection():
    """Get database connection."""
    for driver in ODBC_DRIVERS:
        try:
            conn_str = CONN_STR.replace("ODBC Driver 17 for SQL Server", driver)
            conn = pyodbc.connect(conn_str, timeout=10)
            print(f"Connected using driver: {driver}\n")
            return conn
        except pyodbc.Error as e:
            if driver == ODBC_DRIVERS[-1]:
                raise
            continue
    return None

def add_classnumber_column(conn):
    """Add ClassNumber column to TrialClass table if it doesn't exist."""
    cursor = conn.cursor()
    
    print("Checking if ClassNumber column exists in TrialClass table...")
    
    # Check if column already exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('sResults.TrialClass') 
        AND name = 'ClassNumber'
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print("ClassNumber column already exists in TrialClass table.")
        return
    
    # Add the column
    print("Adding ClassNumber column to TrialClass table...")
    try:
        cursor.execute("""
            ALTER TABLE [sResults].[TrialClass]
            ADD [ClassNumber] VARCHAR(50) NULL
        """)
        conn.commit()
        print("ClassNumber column added successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error adding ClassNumber column: {e}")
        raise

if __name__ == "__main__":
    try:
        conn = get_connection()
        if conn:
            add_classnumber_column(conn)
            conn.close()
            print("\nDone!")
        else:
            print("Failed to connect to database")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

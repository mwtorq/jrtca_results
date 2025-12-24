"""Investigate TrialList table schema, triggers, and constraints."""

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

def investigate_triallist(conn):
    """Investigate TrialList table structure, triggers, and constraints."""
    cursor = conn.cursor()
    
    print("=" * 80)
    print("TRIALLIST TABLE INVESTIGATION")
    print("=" * 80)
    
    # 1. Check if table exists
    print("\n1. Checking if table exists...")
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'TrialList'
        """)
        exists = cursor.fetchone()[0]
        if exists:
            print("   [OK] Table [sResults].[TrialList] exists")
        else:
            print("   [ERROR] Table [sResults].[TrialList] does NOT exist")
            return
    except Exception as e:
        print(f"   [ERROR] Error checking table existence: {e}")
        return
    
    # 2. Get column information
    print("\n2. Column Information:")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT 
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT,
                CASE WHEN ic.is_identity = 1 THEN 'YES' ELSE 'NO' END AS IS_IDENTITY,
                ic.seed_value,
                ic.increment_value
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN sys.columns sc ON sc.object_id = OBJECT_ID('sResults.TrialList') AND sc.name = c.COLUMN_NAME
            LEFT JOIN sys.identity_columns ic ON ic.object_id = sc.object_id AND ic.column_id = sc.column_id
            WHERE c.TABLE_SCHEMA = 'sResults' AND c.TABLE_NAME = 'TrialList'
            ORDER BY c.ORDINAL_POSITION
        """)
        columns = cursor.fetchall()
        for col in columns:
            col_name, data_type, max_len, nullable, default, is_identity, seed, increment = col
            max_len_str = f"({max_len})" if max_len else ""
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            identity_str = f" IDENTITY({seed},{increment})" if is_identity == "YES" else ""
            default_str = f" DEFAULT {default}" if default else ""
            identity_note = " [NOT IDENTITY - MANUAL VALUE REQUIRED!]" if col_name == 'TrialListID' and is_identity != "YES" else ""
            print(f"   {col_name:20} {data_type}{max_len_str:15} {nullable_str:10}{identity_str}{default_str}{identity_note}")
    except Exception as e:
        print(f"   [ERROR] Error getting column information: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Check for triggers
    print("\n3. Triggers on TrialList table:")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT 
                t.name AS trigger_name,
                t.is_disabled,
                OBJECT_DEFINITION(t.object_id) AS trigger_definition
            FROM sys.triggers t
            INNER JOIN sys.tables tab ON t.parent_id = tab.object_id
            WHERE tab.name = 'TrialList' AND SCHEMA_NAME(tab.schema_id) = 'sResults'
        """)
        triggers = cursor.fetchall()
        if triggers:
            for trigger_name, is_disabled, definition in triggers:
                status = "DISABLED" if is_disabled else "ENABLED"
                print(f"   {trigger_name} ({status})")
                if definition:
                    # Show first 500 chars of definition
                    def_preview = definition[:500] if len(definition) > 500 else definition
                    print(f"      Definition preview: {def_preview}...")
        else:
            print("   No triggers found")
    except Exception as e:
        print(f"   ✗ Error checking triggers: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Check for constraints
    print("\n4. Constraints on TrialList table:")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                CONSTRAINT_TYPE,
                CHECK_CLAUSE
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            LEFT JOIN INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc 
                ON tc.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = 'sResults' AND tc.TABLE_NAME = 'TrialList'
            ORDER BY CONSTRAINT_TYPE, CONSTRAINT_NAME
        """)
        constraints = cursor.fetchall()
        if constraints:
            for const_name, const_type, check_clause in constraints:
                print(f"   {const_name} ({const_type})")
                if check_clause:
                    print(f"      Check: {check_clause}")
        else:
            print("   No constraints found")
    except Exception as e:
        print(f"   [ERROR] Error checking constraints: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Check for foreign keys (referencing TrialList)
    print("\n5. Foreign Keys referencing TrialList:")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT 
                fk.name AS foreign_key_name,
                OBJECT_SCHEMA_NAME(fk.parent_object_id) + '.' + OBJECT_NAME(fk.parent_object_id) AS referencing_table,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS referencing_column
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            WHERE OBJECT_SCHEMA_NAME(fk.referenced_object_id) = 'sResults' 
                AND OBJECT_NAME(fk.referenced_object_id) = 'TrialList'
        """)
        fks = cursor.fetchall()
        if fks:
            for fk_name, ref_table, ref_column in fks:
                print(f"   {fk_name}: {ref_table}.{ref_column} -> TrialList")
        else:
            print("   No foreign keys found")
    except Exception as e:
        print(f"   ✗ Error checking foreign keys: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Check for indexes
    print("\n6. Indexes on TrialList table:")
    print("-" * 80)
    try:
        cursor.execute("""
            SELECT 
                i.name AS index_name,
                i.type_desc,
                i.is_unique,
                i.is_primary_key,
                STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('sResults.TrialList')
            GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
            ORDER BY i.is_primary_key DESC, i.name
        """)
        indexes = cursor.fetchall()
        if indexes:
            for idx_name, idx_type, is_unique, is_pk, columns in indexes:
                unique_str = "UNIQUE " if is_unique else ""
                pk_str = "PRIMARY KEY " if is_pk else ""
                print(f"   {pk_str}{unique_str}{idx_name} ({idx_type}) on ({columns})")
        else:
            print("   No indexes found")
    except Exception as e:
        print(f"   [ERROR] Error checking indexes: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Try a test INSERT to see the exact error
    print("\n7. Testing INSERT statement:")
    print("-" * 80)
    try:
        # Get column names that are NOT IDENTITY
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'TrialList'
                AND COLUMN_NAME NOT IN (
                    SELECT name FROM sys.columns 
                    WHERE object_id = OBJECT_ID('sResults.TrialList') 
                    AND is_identity = 1
                )
            ORDER BY ORDINAL_POSITION
        """)
        non_identity_cols = [row[0] for row in cursor.fetchall()]
        print(f"   Non-IDENTITY columns: {', '.join(non_identity_cols)}")
        
        # Try to construct a minimal INSERT
        if 'TrialName' in non_identity_cols and 'Year' in non_identity_cols:
            print("\n   Attempting test INSERT with TrialName='TEST_TRIAL' and Year=9999...")
            try:
                cursor.execute("""
                    INSERT INTO [sResults].[TrialList] ([TrialName], [Year]) 
                    VALUES (?, ?)
                """, 'TEST_TRIAL', 9999)
                conn.commit()
                print("   ✓ Test INSERT succeeded")
                
                # Clean up test record
                cursor.execute("DELETE FROM [sResults].[TrialList] WHERE TrialName = 'TEST_TRIAL'")
                conn.commit()
                print("   ✓ Test record cleaned up")
            except Exception as insert_error:
                print(f"   ✗ Test INSERT failed: {insert_error}")
                print(f"   Error type: {type(insert_error).__name__}")
                import traceback
                traceback.print_exc()
        else:
            print("   Cannot perform test INSERT - required columns not found")
    except Exception as e:
        print(f"   [ERROR] Error testing INSERT: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        conn = get_connection()
        if conn:
            investigate_triallist(conn)
            conn.close()
        else:
            print("Failed to connect to database")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

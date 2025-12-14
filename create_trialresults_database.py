#!/usr/bin/env python3
"""
Create third normal form SQL Server tables in sResults schema in TrialResults database.
Bases table structure on sJRTCA schema in TrialData database.
Uses Windows authentication to connect to localhost\SQLEXPRESS.
"""

import pyodbc
import sys
from typing import List, Dict, Optional

# Connection strings
SOURCE_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=TrialData;"
    "Trusted_Connection=yes;"
)

TARGET_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=TrialResults;"
    "Trusted_Connection=yes;"
)

# Fallback connection strings (try different ODBC drivers if needed)
ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]


def get_connection_string(base_str: str, driver: str) -> str:
    """Replace driver in connection string."""
    return base_str.replace("ODBC Driver 17 for SQL Server", driver)


def get_connection(conn_str_template: str, database: str) -> Optional[pyodbc.Connection]:
    """Get database connection, trying different ODBC drivers if needed."""
    for driver in ODBC_DRIVERS:
        try:
            conn_str = get_connection_string(conn_str_template, driver)
            # Replace database name
            if "DATABASE=" in conn_str:
                conn_str = conn_str.rsplit("DATABASE=", 1)[0] + f"DATABASE={database};"
            else:
                conn_str += f"DATABASE={database};"
            
            conn = pyodbc.connect(conn_str, timeout=10)
            print(f"  Connected using driver: {driver}")
            return conn
        except pyodbc.Error as e:
            print(f"  Failed with driver {driver}: {e}")
            continue
    return None


def get_table_definitions(source_conn: pyodbc.Connection, schema: str) -> Dict[str, Dict]:
    """Get table definitions from source schema."""
    cursor = source_conn.cursor()
    
    # Get all tables in the schema
    tables_query = """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """
    
    cursor.execute(tables_query, schema)
    table_names = [row[0] for row in cursor.fetchall()]
    
    table_defs = {}
    
    for table_name in table_names:
        # Get columns with IDENTITY information
        # First get basic column info
        columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(columns_query, schema, table_name)
        base_columns = cursor.fetchall()
        
        # Get IDENTITY information from sys.columns and sys.identity_columns
        # seed_value and increment_value are sql_variant, so we cast them to numeric
        identity_query = """
        SELECT 
            c.name AS COLUMN_NAME,
            ISNULL(CAST(c.is_identity AS INT), 0) AS is_identity,
            ISNULL(CAST(ic.seed_value AS NUMERIC(18,0)), 1) AS seed_value,
            ISNULL(CAST(ic.increment_value AS NUMERIC(18,0)), 1) AS increment_value
        FROM sys.columns c
        INNER JOIN sys.tables t ON c.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.identity_columns ic ON c.object_id = ic.object_id AND c.column_id = ic.column_id
        WHERE s.name = ? AND t.name = ?
        """
        
        cursor.execute(identity_query, schema, table_name)
        identity_info = {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}
        
        # Combine column info with IDENTITY info
        columns = []
        for col in base_columns:
            col_name = col[0]
            identity_data = identity_info.get(col_name, (0, 1, 1))
            is_identity = identity_data[0]
            seed_value = identity_data[1]
            increment_value = identity_data[2]
            # Convert pyodbc.Row to tuple and append IDENTITY info
            col_tuple = tuple(col) + (is_identity, seed_value, increment_value)
            columns.append(col_tuple)
        
        # Get primary keys
        pk_query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = ? 
            AND TABLE_NAME = ?
            AND CONSTRAINT_NAME IN (
                SELECT CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = ? 
                    AND TABLE_NAME = ?
                    AND CONSTRAINT_TYPE = 'PRIMARY KEY'
            )
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(pk_query, schema, table_name, schema, table_name)
        pk_columns = [row[0] for row in cursor.fetchall()]
        
        # Get foreign keys
        fk_query = """
        SELECT
            fk.CONSTRAINT_NAME,
            fk.COLUMN_NAME,
            pk.TABLE_SCHEMA AS REFERENCED_SCHEMA,
            pk.TABLE_NAME AS REFERENCED_TABLE,
            pk.COLUMN_NAME AS REFERENCED_COLUMN
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS c
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
            ON c.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
            AND c.CONSTRAINT_SCHEMA = fk.CONSTRAINT_SCHEMA
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
            ON c.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
            AND c.UNIQUE_CONSTRAINT_SCHEMA = pk.CONSTRAINT_SCHEMA
        WHERE fk.TABLE_SCHEMA = ?
            AND fk.TABLE_NAME = ?
        ORDER BY fk.ORDINAL_POSITION
        """
        
        cursor.execute(fk_query, schema, table_name)
        fk_constraints = cursor.fetchall()
        
        foreign_keys = {}
        for fk in fk_constraints:
            constraint_name, col_name, ref_schema, ref_table, ref_col = fk
            if constraint_name not in foreign_keys:
                foreign_keys[constraint_name] = {
                    'columns': [],
                    'referenced_schema': ref_schema,
                    'referenced_table': ref_table,
                    'referenced_columns': []
                }
            foreign_keys[constraint_name]['columns'].append(col_name)
            foreign_keys[constraint_name]['referenced_columns'].append(ref_col)
        
        table_defs[table_name] = {
            'columns': columns,
            'primary_key': pk_columns,
            'foreign_keys': foreign_keys
        }
    
    return table_defs


def sql_type_from_info_schema(data_type: str, max_length: Optional[int], 
                               precision: Optional[int], scale: Optional[int]) -> str:
    """Convert INFORMATION_SCHEMA data type to SQL Server type."""
    data_type_upper = data_type.upper()
    
    if data_type_upper in ('VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR'):
        if max_length and max_length > 0:
            if max_length == -1:
                return f"{data_type}(MAX)"
            return f"{data_type}({max_length})"
        return f"{data_type}(255)"  # Default
    elif data_type_upper in ('DECIMAL', 'NUMERIC'):
        if precision and scale is not None:
            return f"{data_type}({precision},{scale})"
        return f"{data_type}(18,0)"  # Default
    elif data_type_upper in ('FLOAT', 'REAL'):
        if precision:
            return f"{data_type}({precision})"
        return data_type
    elif data_type_upper in ('BINARY', 'VARBINARY'):
        if max_length and max_length > 0:
            if max_length == -1:
                return f"{data_type}(MAX)"
            return f"{data_type}({max_length})"
        return f"{data_type}(255)"  # Default
    else:
        return data_type


def create_table_sql(table_name: str, table_def: Dict, schema: str = 'sResults') -> str:
    """Generate CREATE TABLE SQL statement."""
    sql_parts = [f"CREATE TABLE [{schema}].[{table_name}] ("]
    
    column_defs = []
    for col in table_def['columns']:
        # Unpack column info (now includes IDENTITY fields)
        if len(col) >= 11:
            col_name, data_type, max_length, precision, scale, is_nullable, default, ordinal, is_identity, identity_seed, identity_increment = col
        else:
            # Fallback for old format (no IDENTITY info)
            col_name, data_type, max_length, precision, scale, is_nullable, default, ordinal = col[:8]
            is_identity = 0
            identity_seed = 1
            identity_increment = 1
        
        sql_type = sql_type_from_info_schema(data_type, max_length, precision, scale)
        
        # Check if this is an ID column (ends with 'ID' and is likely primary key)
        is_id_column = col_name.upper().endswith('ID')
        is_pk = col_name in table_def.get('primary_key', [])
        
        # Check if this is the table's OWN ID column (pattern: {TableName}ID)
        # This is the only ID column that should be IDENTITY
        table_name_upper = table_name.upper()
        is_table_own_id = (col_name.upper() == f"{table_name_upper}ID")
        
        # Check if this column is a foreign key (FK columns should NOT be IDENTITY)
        is_fk = False
        for fk_def in table_def.get('foreign_keys', {}).values():
            if col_name in fk_def.get('columns', []):
                is_fk = True
                break
        
        # Additional check: if column name matches pattern {ReferencedTable}ID, it's likely a FK
        # This catches cases where FK detection might have failed
        if not is_fk and is_id_column:
            for fk_def in table_def.get('foreign_keys', {}).values():
                ref_table = fk_def.get('referenced_table', '')
                # Check if column name matches the referenced table's ID pattern
                if ref_table and col_name.upper() == f"{ref_table.upper()}ID":
                    is_fk = True
                    break
        
        # Stricter check: if column ends with 'ID' but is NOT the table's own ID column,
        # it's likely a foreign key and should NOT be IDENTITY
        if not is_fk and is_id_column and not is_table_own_id:
            # This is an ID column but not the table's own ID - treat as potential FK
            # Only make it IDENTITY if it was already IDENTITY in source AND we confirmed it's not a FK
            # But to be safe, if it's not the table's own ID, don't force it to be IDENTITY
            pass  # Will be handled in the logic below
        
        # Ensure ID columns that are primary keys are IDENTITY
        # BUT: Only the table's OWN ID column should be IDENTITY
        # Foreign key columns should NEVER be IDENTITY, even if they end with 'ID'
        if is_fk:
            # Foreign key columns should NEVER be IDENTITY, regardless of source setting
            should_be_identity = False
        elif is_table_own_id and is_pk:
            # This is the table's own primary key ID column - should be IDENTITY
            if bool(is_identity):
                # Already IDENTITY in source, use source values
                seed = int(identity_seed) if identity_seed else 1
                increment = int(identity_increment) if identity_increment else 1
                should_be_identity = True
            else:
                # Not IDENTITY in source, but should be - make it IDENTITY
                seed = 1
                increment = 1
                should_be_identity = True
        elif is_id_column and not is_table_own_id:
            # This is an ID column but NOT the table's own ID column
            # It's likely a foreign key - do NOT make it IDENTITY
            should_be_identity = False
        else:
            # Not an ID column or not primary key - use source setting
            # But if source has it as IDENTITY and it's not a FK, preserve that
            should_be_identity = bool(is_identity) and not is_fk
            if should_be_identity:
                seed = int(identity_seed) if identity_seed else 1
                increment = int(identity_increment) if identity_increment else 1
        
        col_def = f"    [{col_name}] {sql_type}"
        
        # Add IDENTITY if needed
        if should_be_identity:
            col_def += f" IDENTITY({seed},{increment})"
        
        if is_nullable == 'NO':
            col_def += " NOT NULL"
        elif is_nullable == 'YES':
            col_def += " NULL"
        
        # Don't add DEFAULT for IDENTITY columns
        if default and not should_be_identity:
            # Clean up default value (remove parentheses if wrapped)
            default_str = str(default).strip()
            if default_str.startswith('(') and default_str.endswith(')'):
                default_str = default_str[1:-1]
            col_def += f" DEFAULT {default_str}"
        
        column_defs.append(col_def)
    
    sql_parts.append(",\n".join(column_defs))
    
    # Add primary key constraint
    if table_def['primary_key']:
        pk_cols = ", ".join([f"[{col}]" for col in table_def['primary_key']])
        sql_parts.append(f",\n    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({pk_cols})")
    
    sql_parts.append("\n);")
    
    return "\n".join(sql_parts)


def create_foreign_key_sql(table_name: str, fk_name: str, fk_def: Dict, 
                           schema: str = 'sResults') -> str:
    """Generate ALTER TABLE ADD CONSTRAINT SQL for foreign key."""
    fk_cols = ", ".join([f"[{col}]" for col in fk_def['columns']])
    ref_cols = ", ".join([f"[{col}]" for col in fk_def['referenced_columns']])
    
    # For sResults schema, we'll reference tables in the same schema
    # (not the original sJRTCA schema)
    ref_table = fk_def['referenced_table']
    
    return (
        f"ALTER TABLE [{schema}].[{table_name}]\n"
        f"    ADD CONSTRAINT [{fk_name}] FOREIGN KEY ({fk_cols})\n"
        f"    REFERENCES [{schema}].[{ref_table}] ({ref_cols});"
    )


def ensure_database_exists(target_conn_str_template: str):
    """Ensure TrialResults database exists."""
    # Connect to master database to create TrialResults if needed
    master_conn_str = get_connection_string(
        target_conn_str_template.replace("DATABASE=TrialResults", "DATABASE=master"),
        ODBC_DRIVERS[0]
    )
    
    for driver in ODBC_DRIVERS:
        try:
            conn_str = get_connection_string(
                target_conn_str_template.replace("DATABASE=TrialResults", "DATABASE=master"),
                driver
            )
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("""
                SELECT name FROM sys.databases WHERE name = 'TrialResults'
            """)
            if not cursor.fetchone():
                print("Creating TrialResults database...")
                cursor.execute("CREATE DATABASE TrialResults")
                conn.commit()
                print("  Database created.")
            else:
                print("TrialResults database already exists.")
            
            conn.close()
            return
        except pyodbc.Error as e:
            if driver == ODBC_DRIVERS[-1]:
                raise
            continue


def create_schema_if_not_exists(target_conn: pyodbc.Connection, schema: str):
    """Create schema if it doesn't exist."""
    cursor = target_conn.cursor()
    
    cursor.execute(f"""
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema}')
        BEGIN
            EXEC('CREATE SCHEMA [{schema}]')
        END
    """)
    target_conn.commit()
    print(f"Schema [{schema}] ensured.")


def drop_existing_tables(target_conn: pyodbc.Connection, schema: str, table_defs: Dict):
    """Drop existing tables in reverse dependency order."""
    cursor = target_conn.cursor()
    
    # Build dependency graph
    dependencies = {}
    for table_name, table_def in table_defs.items():
        dependencies[table_name] = []
        for fk_def in table_def['foreign_keys'].values():
            ref_table = fk_def['referenced_table']
            if ref_table in table_defs:
                dependencies[table_name].append(ref_table)
    
    # Topological sort to get drop order (reverse of create order)
    visited = set()
    drop_order = []
    
    def visit(table):
        if table in visited:
            return
        visited.add(table)
        for dep in dependencies.get(table, []):
            visit(dep)
        drop_order.append(table)
    
    for table in table_defs.keys():
        visit(table)
    
    # Drop in reverse order
    drop_order.reverse()
    
    print("\nDropping existing tables (if any)...")
    for table_name in drop_order:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS [{schema}].[{table_name}]")
            target_conn.commit()
            print(f"  Dropped {table_name}")
        except pyodbc.Error as e:
            print(f"  Warning: Could not drop {table_name}: {e}")


def main():
    """Main function to create sResults schema based on sJRTCA schema."""
    print("=" * 80)
    print("Creating sResults schema in TrialResults database")
    print("Based on sJRTCA schema in TrialData database")
    print("=" * 80)
    print()
    
    # Ensure target database exists
    print("Checking/creating TrialResults database...")
    try:
        ensure_database_exists(TARGET_CONN_STR)
    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        sys.exit(1)
    
    # Connect to source database
    print("\nConnecting to source database (TrialData)...")
    source_conn = get_connection(SOURCE_CONN_STR, "TrialData")
    if not source_conn:
        print("ERROR: Could not connect to source database.")
        sys.exit(1)
    
    # Connect to target database
    print("\nConnecting to target database (TrialResults)...")
    target_conn = get_connection(TARGET_CONN_STR, "TrialResults")
    if not target_conn:
        print("ERROR: Could not connect to target database.")
        source_conn.close()
        sys.exit(1)
    
    try:
        # Get table definitions from source
        print("\nReading table definitions from sJRTCA schema...")
        table_defs = get_table_definitions(source_conn, 'sJRTCA')
        print(f"  Found {len(table_defs)} tables")
        
        if not table_defs:
            print("WARNING: No tables found in sJRTCA schema.")
            print("This script will create tables based on the data model from the Python scripts.")
            # Create minimal schema based on Python data models
            create_basic_schema(target_conn)
            return
        
        # Create schema
        print("\nCreating sResults schema...")
        create_schema_if_not_exists(target_conn, 'sResults')
        
        # Drop existing tables
        drop_existing_tables(target_conn, 'sResults', table_defs)
        
        # Determine table creation order (tables without foreign keys first)
        # Build dependency graph
        dependencies = {}
        for table_name, table_def in table_defs.items():
            dependencies[table_name] = []
            for fk_def in table_def['foreign_keys'].values():
                ref_table = fk_def['referenced_table']
                if ref_table in table_defs:
                    dependencies[table_name].append(ref_table)
        
        # Topological sort
        visited = set()
        create_order = []
        
        def visit(table):
            if table in visited:
                return
            visited.add(table)
            for dep in dependencies.get(table, []):
                visit(dep)
            create_order.append(table)
        
        for table in table_defs.keys():
            visit(table)
        
        # Create tables
        print("\nCreating tables...")
        cursor = target_conn.cursor()
        for table_name in create_order:
            print(f"  Creating {table_name}...")
            table_def = table_defs[table_name]
            create_sql = create_table_sql(table_name, table_def, 'sResults')
            
            try:
                cursor.execute(create_sql)
                target_conn.commit()
                print(f"    ✓ Created successfully")
            except pyodbc.Error as e:
                print(f"    ✗ Error: {e}")
                print(f"    SQL: {create_sql[:200]}...")
        
        # Create foreign keys
        print("\nCreating foreign key constraints...")
        for table_name in create_order:
            table_def = table_defs[table_name]
            for fk_name, fk_def in table_def['foreign_keys'].items():
                # Only create FK if referenced table exists in our new schema
                ref_table = fk_def['referenced_table']
                if ref_table in table_defs:
                    print(f"  Creating FK {fk_name} on {table_name}...")
                    fk_sql = create_foreign_key_sql(table_name, fk_name, fk_def, 'sResults')
                    try:
                        cursor.execute(fk_sql)
                        target_conn.commit()
                        print(f"    ✓ Created successfully")
                    except pyodbc.Error as e:
                        print(f"    ✗ Error: {e}")
        
        # Ensure Dog table exists (may be in sAll schema, not sResults)
        print("\nEnsuring Dog table exists in sResults schema...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'Dog'
        """)
        if cursor.fetchone()[0] == 0:
            print("  Creating Dog table...")
            # Check if Owner table exists
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'Owner'
            """)
            owner_exists = cursor.fetchone()[0] > 0
            
            if owner_exists:
                cursor.execute("""
                    CREATE TABLE [sResults].[Dog] (
                        [DogID] INT IDENTITY(1,1) PRIMARY KEY,
                        [DogName] NVARCHAR(255) NOT NULL,
                        [OwnerID] INT NULL,
                        [Sire] NVARCHAR(255) NULL,
                        [Dam] NVARCHAR(255) NULL,
                        [Sex] NVARCHAR(10) NULL,
                        CONSTRAINT [FK_Dog_Owner] FOREIGN KEY ([OwnerID])
                            REFERENCES [sResults].[Owner]([OwnerID])
                    );
                """)
            else:
                # Create Owner table first if it doesn't exist
                print("  Creating Owner table first...")
                cursor.execute("""
                    CREATE TABLE [sResults].[Owner] (
                        [OwnerID] INT IDENTITY(1,1) PRIMARY KEY,
                        [OwnerName] NVARCHAR(255) NOT NULL
                    );
                """)
                target_conn.commit()
                
                cursor.execute("""
                    CREATE TABLE [sResults].[Dog] (
                        [DogID] INT IDENTITY(1,1) PRIMARY KEY,
                        [DogName] NVARCHAR(255) NOT NULL,
                        [OwnerID] INT NULL,
                        [Sire] NVARCHAR(255) NULL,
                        [Dam] NVARCHAR(255) NULL,
                        [Sex] NVARCHAR(10) NULL,
                        CONSTRAINT [FK_Dog_Owner] FOREIGN KEY ([OwnerID])
                            REFERENCES [sResults].[Owner]([OwnerID])
                    );
                """)
            target_conn.commit()
            print("    ✓ Dog table created")
        else:
            print("  Dog table already exists")
        
        # Ensure Section table exists (may not be in source schema)
        print("\nEnsuring Section table exists...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'Section'
        """)
        if cursor.fetchone()[0] == 0:
            print("  Creating Section table...")
            cursor.execute("""
                CREATE TABLE [sResults].[Section] (
                    [SectionID] INT IDENTITY(1,1) PRIMARY KEY,
                    [SectionName] NVARCHAR(255) NOT NULL
                );
            """)
            target_conn.commit()
            print("    ✓ Section table created")
        else:
            print("  Section table already exists")
        
        # Check if Class table has Section column and update it to use SectionID
        print("\nChecking Class table structure...")
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'sResults' 
            AND TABLE_NAME = 'Class' 
            AND COLUMN_NAME = 'Section'
        """)
        if cursor.fetchone():
            print("  Class table has 'Section' column - updating to use SectionID...")
            # Check if SectionID column already exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'sResults' 
                AND TABLE_NAME = 'Class' 
                AND COLUMN_NAME = 'SectionID'
            """)
            if not cursor.fetchone():
                # Add SectionID column
                cursor.execute("""
                    ALTER TABLE [sResults].[Class]
                    ADD [SectionID] INT NULL;
                """)
                print("    ✓ Added SectionID column")
            
            # Add foreign key constraint if it doesn't exist
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = 'sResults' 
                AND TABLE_NAME = 'Class' 
                AND CONSTRAINT_NAME = 'FK_Class_Section'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE [sResults].[Class]
                    ADD CONSTRAINT [FK_Class_Section] FOREIGN KEY ([SectionID])
                        REFERENCES [sResults].[Section]([SectionID]);
                """)
                print("    ✓ Added FK_Class_Section foreign key")
            
            # Drop the old Section column
            cursor.execute("""
                ALTER TABLE [sResults].[Class]
                DROP COLUMN [Section];
            """)
            print("    ✓ Removed old Section column")
            target_conn.commit()
        else:
            # Check if SectionID exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'sResults' 
                AND TABLE_NAME = 'Class' 
                AND COLUMN_NAME = 'SectionID'
            """)
            if cursor.fetchone():
                # SectionID exists, just ensure FK exists
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA = 'sResults' 
                    AND TABLE_NAME = 'Class' 
                    AND CONSTRAINT_NAME = 'FK_Class_Section'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE [sResults].[Class]
                        ADD CONSTRAINT [FK_Class_Section] FOREIGN KEY ([SectionID])
                            REFERENCES [sResults].[Section]([SectionID]);
                    """)
                    target_conn.commit()
                    print("    ✓ Added FK_Class_Section foreign key")
                else:
                    print("    ✓ FK_Class_Section foreign key already exists")
            else:
                # SectionID doesn't exist - add it
                print("  Class table missing SectionID column - adding it...")
                cursor.execute("""
                    ALTER TABLE [sResults].[Class]
                    ADD [SectionID] INT NULL;
                """)
                print("    ✓ Added SectionID column")
                
                # Add foreign key constraint
                cursor.execute("""
                    ALTER TABLE [sResults].[Class]
                    ADD CONSTRAINT [FK_Class_Section] FOREIGN KEY ([SectionID])
                        REFERENCES [sResults].[Section]([SectionID]);
                """)
                target_conn.commit()
                print("    ✓ Added FK_Class_Section foreign key")
        
        # Ensure CatalogEntry table exists (may not be in source schema)
        print("\nEnsuring CatalogEntry table exists...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'CatalogEntry'
        """)
        if cursor.fetchone()[0] == 0:
            print("  Creating CatalogEntry table...")
            cursor.execute("""
                CREATE TABLE [sResults].[CatalogEntry] (
                    [CatalogEntryID] INT IDENTITY(1,1) PRIMARY KEY,
                    [Year] NVARCHAR(4) NOT NULL,
                    [EntryNumber] NVARCHAR(50) NULL,
                    [DogID] INT NULL,
                    [DogName] NVARCHAR(255) NOT NULL,
                    [OwnerID] INT NULL,
                    [Sire] NVARCHAR(255) NULL,
                    [Dam] NVARCHAR(255) NULL,
                    [Sex] NVARCHAR(10) NULL,
                    [ClassID] INT NULL,
                    [ClassName] NVARCHAR(255) NULL,
                    CONSTRAINT [FK_CatalogEntry_Dog] FOREIGN KEY ([DogID])
                        REFERENCES [sResults].[Dog]([DogID]),
                    CONSTRAINT [FK_CatalogEntry_Owner] FOREIGN KEY ([OwnerID])
                        REFERENCES [sResults].[Owner]([OwnerID]),
                    CONSTRAINT [FK_CatalogEntry_Class] FOREIGN KEY ([ClassID])
                        REFERENCES [sResults].[Class]([ClassID])
                );
            """)
            target_conn.commit()
            print("    ✓ CatalogEntry table created")
        else:
            print("  CatalogEntry table already exists")
        
        # Ensure Relationship table exists (may not be in source schema)
        print("\nEnsuring Relationship table exists...")
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'Relationship'
        """)
        if cursor.fetchone()[0] == 0:
            print("  Creating Relationship table...")
            cursor.execute("""
                CREATE TABLE [sResults].[Relationship] (
                    [RelationshipID] INT IDENTITY(1,1) PRIMARY KEY,
                    [DogID] INT NOT NULL,
                    [RelatedDogID] INT NULL,
                    [RelatedDogName] NVARCHAR(255) NOT NULL,
                    [RelationshipType] NVARCHAR(100) NOT NULL,
                    [ViaDogName] NVARCHAR(255) NULL,
                    [RelatedDogSex] NVARCHAR(10) NULL,
                    CONSTRAINT [FK_Relationship_Dog] FOREIGN KEY ([DogID])
                        REFERENCES [sResults].[Dog]([DogID]),
                    CONSTRAINT [FK_Relationship_RelatedDog] FOREIGN KEY ([RelatedDogID])
                        REFERENCES [sResults].[Dog]([DogID])
                );
            """)
            target_conn.commit()
            print("    ✓ Relationship table created")
        else:
            print("  Relationship table already exists")
        
        print("\n" + "=" * 80)
        print("Schema creation completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        source_conn.close()
        target_conn.close()


def create_basic_schema(target_conn: pyodbc.Connection):
    """Create basic schema based on Python data models if source schema not found."""
    print("\nCreating basic schema from Python data models...")
    
    cursor = target_conn.cursor()
    create_schema_if_not_exists(target_conn, 'sResults')
    
    # Define tables based on Python data models
    
    # Division table
    cursor.execute("""
        CREATE TABLE [sResults].[Division] (
            [DivisionID] INT IDENTITY(1,1) PRIMARY KEY,
            [DivisionName] NVARCHAR(100) NOT NULL
        );
    """)
    
    # Section table
    cursor.execute("""
        CREATE TABLE [sResults].[Section] (
            [SectionID] INT IDENTITY(1,1) PRIMARY KEY,
            [SectionName] NVARCHAR(255) NOT NULL
        );
    """)
    
    # Class table
    cursor.execute("""
        CREATE TABLE [sResults].[Class] (
            [ClassID] INT IDENTITY(1,1) PRIMARY KEY,
            [DivisionID] INT NULL,
            [SectionID] INT NULL,
            [ClassName] NVARCHAR(255) NOT NULL,
            CONSTRAINT [FK_Class_Division] FOREIGN KEY ([DivisionID])
                REFERENCES [sResults].[Division]([DivisionID]),
            CONSTRAINT [FK_Class_Section] FOREIGN KEY ([SectionID])
                REFERENCES [sResults].[Section]([SectionID])
        );
    """)
    
    # TrialList table
    cursor.execute("""
        CREATE TABLE [sResults].[TrialList] (
            [TrialListID] INT IDENTITY(1,1) PRIMARY KEY,
            [TrialName] NVARCHAR(255) NOT NULL,
            [TrialDate] NVARCHAR(100) NULL,
            [Year] NVARCHAR(4) NULL
        );
    """)
    
    # TrialClass table (junction between trials and classes)
    cursor.execute("""
        CREATE TABLE [sResults].[TrialClass] (
            [TrialClassID] INT IDENTITY(1,1) PRIMARY KEY,
            [TrialListID] INT NOT NULL,
            [ClassID] INT NOT NULL,
            [ClassNumber] INT NULL,
            [EntryCount] INT NULL,
            CONSTRAINT [FK_TrialClass_TrialList] FOREIGN KEY ([TrialListID])
                REFERENCES [sResults].[TrialList]([TrialListID]),
            CONSTRAINT [FK_TrialClass_Class] FOREIGN KEY ([ClassID])
                REFERENCES [sResults].[Class]([ClassID])
        );
    """)
    
    # Owner table
    cursor.execute("""
        CREATE TABLE [sResults].[Owner] (
            [OwnerID] INT IDENTITY(1,1) PRIMARY KEY,
            [OwnerName] NVARCHAR(255) NOT NULL
        );
    """)
    
    # Dog table
    cursor.execute("""
        CREATE TABLE [sResults].[Dog] (
            [DogID] INT IDENTITY(1,1) PRIMARY KEY,
            [DogName] NVARCHAR(255) NOT NULL,
            [OwnerID] INT NULL,
            [Sire] NVARCHAR(255) NULL,
            [Dam] NVARCHAR(255) NULL,
            [Sex] NVARCHAR(10) NULL,
            CONSTRAINT [FK_Dog_Owner] FOREIGN KEY ([OwnerID])
                REFERENCES [sResults].[Owner]([OwnerID])
        );
    """)
    
    # TrialPlacements table
    cursor.execute("""
        CREATE TABLE [sResults].[TrialPlacements] (
            [TrialPlacementsID] INT IDENTITY(1,1) PRIMARY KEY,
            [TrialClassID] INT NOT NULL,
            [DogID] INT NULL,
            [DogName] NVARCHAR(255) NULL,
            [Result] NVARCHAR(50) NULL,
            [OwnerID] INT NULL,
            CONSTRAINT [FK_TrialPlacements_TrialClass] FOREIGN KEY ([TrialClassID])
                REFERENCES [sResults].[TrialClass]([TrialClassID]),
            CONSTRAINT [FK_TrialPlacements_Dog] FOREIGN KEY ([DogID])
                REFERENCES [sResults].[Dog]([DogID]),
            CONSTRAINT [FK_TrialPlacements_Owner] FOREIGN KEY ([OwnerID])
                REFERENCES [sResults].[Owner]([OwnerID])
        );
    """)
    
    # CatalogEntry table (for entries catalog data)
    cursor.execute("""
        CREATE TABLE [sResults].[CatalogEntry] (
            [CatalogEntryID] INT IDENTITY(1,1) PRIMARY KEY,
            [Year] NVARCHAR(4) NOT NULL,
            [EntryNumber] NVARCHAR(50) NULL,
            [DogID] INT NULL,
            [DogName] NVARCHAR(255) NOT NULL,
            [OwnerID] INT NULL,
            [Sire] NVARCHAR(255) NULL,
            [Dam] NVARCHAR(255) NULL,
            [Sex] NVARCHAR(10) NULL,
            [ClassID] INT NULL,
            [ClassName] NVARCHAR(255) NULL,
            CONSTRAINT [FK_CatalogEntry_Dog] FOREIGN KEY ([DogID])
                REFERENCES [sResults].[Dog]([DogID]),
            CONSTRAINT [FK_CatalogEntry_Owner] FOREIGN KEY ([OwnerID])
                REFERENCES [sResults].[Owner]([OwnerID]),
            CONSTRAINT [FK_CatalogEntry_Class] FOREIGN KEY ([ClassID])
                REFERENCES [sResults].[Class]([ClassID])
        );
    """)
    
    # Relationship table (for family relationships between dogs)
    cursor.execute("""
        CREATE TABLE [sResults].[Relationship] (
            [RelationshipID] INT IDENTITY(1,1) PRIMARY KEY,
            [DogID] INT NOT NULL,
            [RelatedDogID] INT NULL,
            [RelatedDogName] NVARCHAR(255) NOT NULL,
            [RelationshipType] NVARCHAR(100) NOT NULL,
            [ViaDogName] NVARCHAR(255) NULL,
            [RelatedDogSex] NVARCHAR(10) NULL,
            CONSTRAINT [FK_Relationship_Dog] FOREIGN KEY ([DogID])
                REFERENCES [sResults].[Dog]([DogID]),
            CONSTRAINT [FK_Relationship_RelatedDog] FOREIGN KEY ([RelatedDogID])
                REFERENCES [sResults].[Dog]([DogID])
        );
    """)
    
    target_conn.commit()
    print("  Basic schema created successfully.")


if __name__ == "__main__":
    main()

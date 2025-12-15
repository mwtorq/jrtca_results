#!/usr/bin/env python3
"""
Populate sResults schema tables in TrialResults database with data from catalog and trial results.
Uses the logic from parse_catalog.py and scrape_trial_results.py to extract and insert all data.
"""

import pyodbc
import sys
import os
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

# Import from existing scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_catalog import (
    Dog, ClassInfo, normalize_name, names_are_similar,
    find_relationships, merge_dogs_across_years,
    infer_sex_from_relationships, extract_year_from_filename,
    parse_catalog, extract_text_from_file, infer_sex_from_classes
)
from scrape_trial_results import (
    TrialResult, normalize_division_name, normalize_class_name,
    parse_local_trial_file
)

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
            print(f"  Connected using driver: {driver}")
            return conn
        except pyodbc.Error as e:
            if driver == ODBC_DRIVERS[-1]:
                raise
            continue
    return None


def get_or_create_id(cursor: pyodbc.Cursor, table: str, name_column: str, 
                     name: str, id_column: str = None, create_columns: Dict = None) -> Optional[int]:
    """Get existing ID or create new record and return ID.
    
    Note: Assumes id_column is an IDENTITY column and should NOT be included in INSERT.
    """
    if not name or not name.strip():
        return None
    
    if id_column is None:
        # Generate ID column name by simply adding 'ID' to the table name
        # This matches the standard SQL Server convention: TableName -> TableNameID
        # e.g., 'Class' -> 'ClassID', 'Division' -> 'DivisionID'
        id_column = table + 'ID'
    
    # Try to find existing record
    query = f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?"
    cursor.execute(query, name.strip())
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Create new record
    # Ensure we don't include the IDENTITY column in the INSERT
    name_stripped = name.strip()
    if not name_stripped:
        return None  # Double-check: name should not be empty at this point
    
    if create_columns is None:
        create_columns = {name_column: name_stripped}
    else:
        create_columns = create_columns.copy()
        create_columns[name_column] = name_stripped
    
    # Remove id_column from create_columns if it's present (shouldn't be, but just in case)
    if id_column in create_columns:
        del create_columns[id_column]
    
    # Ensure we have at least one column to insert and that name_column has a non-empty value
    if not create_columns or not create_columns.get(name_column, '').strip():
        return None
    
    # Final safety check: ensure id_column is NOT in the column list
    column_names = list(create_columns.keys())
    if id_column in column_names:
        print(f"  ERROR: {id_column} found in INSERT columns for {table}! Column names: {column_names}")
        raise ValueError(f"Cannot include IDENTITY column {id_column} in INSERT statement")
    
    columns = ", ".join([f"[{k}]" for k in column_names])
    placeholders = ", ".join(["?" for _ in create_columns])
    values = list(create_columns.values())
    
    # Final safety check: ensure name_column is not None or empty (other columns can be NULL)
    if name_column in create_columns:
        name_val = create_columns[name_column]
        if name_val is None or (isinstance(name_val, str) and not name_val.strip()):
            print(f"  ERROR: NULL or empty value for name column {name_column} in {table}! Value: {repr(name_val)}")
            return None
    
    insert_query = f"INSERT INTO [sResults].[{table}] ({columns}) VALUES ({placeholders})"
    
    # Debug logging before INSERT
    if table == 'Division':
        print(f"  DEBUG: About to INSERT into Division")
        print(f"    Columns: {columns}")
        print(f"    Values: {values}")
        print(f"    ID column (should NOT be present): {id_column}")
        print(f"    Name value: {repr(name_stripped)}")
        
        # Check if DivisionID is actually IDENTITY
        try:
            check_identity_query = """
                SELECT is_identity 
                FROM sys.columns 
                WHERE object_id = OBJECT_ID('sResults.Division') 
                AND name = 'DivisionID'
            """
            cursor.execute(check_identity_query)
            identity_row = cursor.fetchone()
            if identity_row:
                is_identity = identity_row[0]
                print(f"    DivisionID is_identity: {is_identity}")
                if not is_identity:
                    print(f"    WARNING: DivisionID is NOT IDENTITY! This may cause issues.")
        except Exception as schema_check_error:
            print(f"    Could not check DivisionID schema: {schema_check_error}")
    
    try:
        # Always use tuple for parameter passing with pyodbc for consistency and reliability
        cursor.execute(insert_query, tuple(values))
        
        # Get the generated ID using SCOPE_IDENTITY() for better reliability
        cursor.execute("SELECT SCOPE_IDENTITY()")
        row = cursor.fetchone()
        if row and row[0] is not None:
            return int(row[0])
        
        # Fallback: query by name
        cursor.execute(f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?", name.strip())
        row = cursor.fetchone()
        if row:
            return row[0]
        return None
    except Exception as e:
        # Log the error for debugging
        error_msg = str(e)
        print(f"  ERROR inserting into {table}: {e}")
        print(f"    Query: {insert_query}")
        print(f"    Columns being inserted: {list(create_columns.keys())}")
        print(f"    Values: {values}")
        print(f"    ID column (should NOT be in INSERT): {id_column}")
        print(f"    Name column: {name_column}")
        
        # Check if the error is about NULL in IDENTITY column
        if 'NULL' in error_msg and id_column in error_msg:
            print(f"\n    POSSIBLE ISSUE: {id_column} may not be set as IDENTITY in the table.")
            print(f"    The table '{table}' needs {id_column} to be defined as IDENTITY(1,1) NOT NULL")
            print(f"    Please check the table creation script and ensure {id_column} is IDENTITY.")
            print(f"    Example: {id_column} INT IDENTITY(1,1) NOT NULL PRIMARY KEY")
            
            # Try to check the actual table definition
            try:
                check_def_query = f"""
                    SELECT 
                        c.name AS column_name,
                        c.is_identity,
                        c.is_nullable,
                        ty.name AS data_type
                    FROM sys.columns c
                    INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                    WHERE c.object_id = OBJECT_ID('sResults.{table}')
                    AND c.name = '{id_column}'
                """
                cursor.execute(check_def_query)
                def_row = cursor.fetchone()
                if def_row:
                    col_name, is_identity, is_nullable, data_type = def_row
                    print(f"\n    ACTUAL TABLE DEFINITION:")
                    print(f"      Column: {col_name}")
                    print(f"      Data Type: {data_type}")
                    print(f"      Is IDENTITY: {is_identity}")
                    print(f"      Is Nullable: {is_nullable}")
                    if not is_identity:
                        print(f"\n    *** {id_column} is NOT IDENTITY! This is the problem. ***")
                        print(f"    The table needs to be altered or recreated with {id_column} as IDENTITY.")
            except Exception as def_error:
                print(f"    Could not check table definition: {def_error}")
        
        raise


def process_year_catalog_data(conn: pyodbc.Connection, classes: Dict[str, ClassInfo], 
                               dogs: Dict[str, Dog], year: str,
                               dog_name_to_id: Dict[str, int],
                               owner_name_to_id: Dict[str, int],
                               division_name_to_id: Dict[str, int],
                               class_name_to_id: Dict[tuple, int],
                               section_name_to_id: Dict[str, int] = None,
                               commit_interval: int = 100):
    """Process and write a single year's catalog data to database incrementally.
    
    Args:
        conn: Database connection
        classes: Classes for this year
        dogs: Dogs for this year
        year: Year being processed
        dog_name_to_id: Dict mapping normalized dog names to IDs (updated in place)
        owner_name_to_id: Dict mapping owner names to IDs (updated in place)
        division_name_to_id: Dict mapping division names to IDs (updated in place)
        class_name_to_id: Dict mapping (class_name, div_id, section) to class IDs (updated in place)
        section_name_to_id: Dict mapping section names to IDs (updated in place, optional)
        commit_interval: Commit after this many operations
    """
    if section_name_to_id is None:
        section_name_to_id = {}
    
    cursor = conn.cursor()
    operations_count = 0
    
    try:
        
        # Process divisions and classes first
        print("  Processing divisions and classes...")
        for class_key, class_info in classes.items():
            # Get or create division
            div_id = None
            if class_info.division:
                div_id = division_name_to_id.get(class_info.division)
                if div_id is None:
                    normalized_div_name = normalize_division_name(class_info.division)
                    if normalized_div_name and normalized_div_name.strip():
                        div_id = get_or_create_id(cursor, 'Division', 'DivisionName', 
                                                 normalized_div_name)
                    if div_id:
                        division_name_to_id[class_info.division] = div_id
                    # If normalized_div_name is None or empty, div_id remains None
                
                # Get or create section
                section_id = None
                if class_info.section and class_info.section.strip():
                    section_name = class_info.section.strip()
                    section_id = section_name_to_id.get(section_name)
                    if section_id is None:
                        section_id = get_or_create_id(cursor, 'Section', 'SectionName', section_name)
                        if section_id:
                            section_name_to_id[section_name] = section_id
                
                # Get or create class
                normalized_class_name = normalize_class_name(class_info.name) if class_info.name else None
                if normalized_class_name:
                    class_lookup_key = (normalized_class_name, div_id, class_info.section or None)
                    class_id = class_name_to_id.get(class_lookup_key)
                    if class_id is None:
                        class_id = get_or_create_id(
                            cursor, 'Class', 'ClassName', normalized_class_name,
                            create_columns={
                                'DivisionID': div_id,
                                'SectionID': section_id
                            }
                        )
                        if class_id:
                            class_name_to_id[class_lookup_key] = class_id
                            operations_count += 1
                            if operations_count % commit_interval == 0:
                                conn.commit()
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        # Process owners
        for dog_key, dog in dogs.items():
            if dog.owner and dog.owner.strip():
                owner_name = dog.owner.strip()
                if owner_name not in owner_name_to_id:
                    owner_id = get_or_create_id(cursor, 'Owner', 'OwnerName', owner_name)
                    if owner_id:
                        owner_name_to_id[owner_name] = owner_id
                        operations_count += 1
                        if operations_count % commit_interval == 0:
                            conn.commit()
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        # Process dogs
        for dog_key, dog in dogs.items():
            # Get or create owner
            owner_id = None
            if dog.owner and dog.owner.strip():
                owner_id = owner_name_to_id.get(dog.owner.strip())
            
            # Normalize dog name for lookup
            normalized_dog_name = normalize_name(dog.name)
            
            # Check if we already have this dog (by normalized name)
            dog_id = dog_name_to_id.get(normalized_dog_name)
            
            if dog_id is None:
                # Create new dog
                dog_id = get_or_create_id(
                    cursor, 'Dog', 'DogName', dog.name,
                    create_columns={
                        'OwnerID': owner_id,
                        'Sire': dog.sire,
                        'Dam': dog.dam,
                        'Sex': dog.sex
                    }
                )
                if dog_id:
                    dog_name_to_id[normalized_dog_name] = dog_id
                    dog_name_to_id[dog.name] = dog_id  # Also store original name
            else:
                # Update dog if we have more complete information
                update_columns = []
                update_values = []
                if dog.sire and dog.sire.strip():
                    update_columns.append('Sire = ?')
                    update_values.append(dog.sire.strip())
                if dog.dam and dog.dam.strip():
                    update_columns.append('Dam = ?')
                    update_values.append(dog.dam.strip())
                if dog.sex and dog.sex != 'unknown':
                    update_columns.append('Sex = ?')
                    update_values.append(dog.sex)
                if owner_id:
                    update_columns.append('OwnerID = ?')
                    update_values.append(owner_id)
                
                if update_columns:
                    update_values.append(dog_id)
                    update_query = f"""
                        UPDATE [sResults].[Dog]
                        SET {', '.join(update_columns)}
                        WHERE [DogID] = ?
                    """
                    cursor.execute(update_query, *update_values)
                    operations_count += 1
                    if operations_count % commit_interval == 0:
                        conn.commit()
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        # Process catalog entries (dog-class relationships)
        print("  Processing catalog entries...")
        for class_key, class_info in classes.items():
            # Get class ID
            if class_info.division and class_info.name:
                div_id = division_name_to_id.get(class_info.division)
                if div_id:
                    normalized_class_name = normalize_class_name(class_info.name) if class_info.name else None
                    if normalized_class_name:
                        class_lookup_key = (normalized_class_name, div_id, class_info.section or None)
                        class_id = class_name_to_id.get(class_lookup_key)
                        
                        if class_id:
                            # Insert catalog entries for each dog in this class
                            for dog in class_info.entries:
                                normalized_dog_name = normalize_name(dog.name)
                                dog_id = dog_name_to_id.get(normalized_dog_name) or dog_name_to_id.get(dog.name)
                                
                                owner_id = None
                                if dog.owner and dog.owner.strip():
                                    owner_id = owner_name_to_id.get(dog.owner.strip())
                                
                                # Check if entry already exists
                                check_query = """
                                    SELECT CatalogEntryID FROM [sResults].[CatalogEntry]
                                    WHERE Year = ? AND DogID = ? AND ClassID = ?
                                """
                                cursor.execute(check_query, class_info.year, dog_id, class_id)
                                if cursor.fetchone():
                                    continue  # Already exists
                                
                                # Year and DogName are NOT NULL
                                if not class_info.year or not dog.name or not dog.name.strip():
                                    continue  # Skip if required fields are missing
                                
                                insert_query = """
                                    INSERT INTO [sResults].[CatalogEntry]
                                    (Year, EntryNumber, DogID, DogName, OwnerID, Sire, Dam, Sex, ClassID, ClassName)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """
                                cursor.execute(insert_query,
                                             class_info.year,
                                             dog.number,
                                             dog_id,
                                             dog.name,
                                             owner_id,
                                             dog.sire,
                                             dog.dam,
                                             dog.sex,
                                             class_id,
                                             class_info.name)
                                operations_count += 1
                                if operations_count % commit_interval == 0:
                                    conn.commit()
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        print(f"  Year {year}: {len(dogs)} dogs, {len(classes)} classes written to database")
        
    except Exception as e:
        print(f"  ERROR processing year {year} catalog data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def populate_catalog_data(conn: pyodbc.Connection, classes: Dict[str, ClassInfo], 
                         dogs: Dict[str, Dog], years: List[str]):
    """Populate catalog data into database (legacy function - kept for compatibility)."""
    print("\nPopulating catalog data...")
    cursor = conn.cursor()
    
    try:
        # Track inserted dogs and owners to avoid duplicates
        dog_name_to_id = {}
        owner_name_to_id = {}
        division_name_to_id = {}
        section_name_to_id = {}
        class_name_to_id = {}  # (normalized_class_name, div_id, section) -> class_id
        
        # Process divisions and classes first
        print("  Processing divisions and classes...")
        for class_key, class_info in classes.items():
            # Get or create division
            if class_info.division:
                div_id = division_name_to_id.get(class_info.division)
                if div_id is None:
                    normalized_div_name = normalize_division_name(class_info.division)
                    if normalized_div_name and normalized_div_name.strip():
                        div_id = get_or_create_id(cursor, 'Division', 'DivisionName', 
                                                 normalized_div_name)
                        if div_id:
                            division_name_to_id[class_info.division] = div_id
                
                # Get or create section
                section_id = None
                if class_info.section and class_info.section.strip():
                    section_name = class_info.section.strip()
                    section_id = section_name_to_id.get(section_name)
                    if section_id is None:
                        section_id = get_or_create_id(cursor, 'Section', 'SectionName', section_name)
                        if section_id:
                            section_name_to_id[section_name] = section_id
                
                # Get or create class
                normalized_class_name = normalize_class_name(class_info.name) if class_info.name else None
                if normalized_class_name:
                    class_lookup_key = (normalized_class_name, div_id, class_info.section or None)
                    class_id = class_name_to_id.get(class_lookup_key)
                    if class_id is None:
                        class_id = get_or_create_id(
                            cursor, 'Class', 'ClassName', normalized_class_name,
                            create_columns={
                                'DivisionID': div_id,
                                'SectionID': section_id
                            }
                        )
                        if class_id:
                            class_name_to_id[class_lookup_key] = class_id
        
        conn.commit()
        
        # Process owners
        print("  Processing owners...")
        for dog_key, dog in dogs.items():
            if dog.owner and dog.owner.strip():
                owner_name = dog.owner.strip()
                if owner_name not in owner_name_to_id:
                    owner_id = get_or_create_id(cursor, 'Owner', 'OwnerName', owner_name)
                    if owner_id:
                        owner_name_to_id[owner_name] = owner_id
        
        conn.commit()
        
        # Process dogs
        print("  Processing dogs...")
        for dog_key, dog in dogs.items():
            # Get or create owner
            owner_id = None
            if dog.owner and dog.owner.strip():
                owner_id = owner_name_to_id.get(dog.owner.strip())
            
            # Normalize dog name for lookup
            normalized_dog_name = normalize_name(dog.name)
            
            # Check if we already have this dog (by normalized name)
            dog_id = dog_name_to_id.get(normalized_dog_name)
            
            if dog_id is None:
                # Create new dog
                dog_id = get_or_create_id(
                    cursor, 'Dog', 'DogName', dog.name,
                    create_columns={
                        'OwnerID': owner_id,
                        'Sire': dog.sire,
                        'Dam': dog.dam,
                        'Sex': dog.sex
                    }
                )
                if dog_id:
                    dog_name_to_id[normalized_dog_name] = dog_id
                    dog_name_to_id[dog.name] = dog_id  # Also store original name
                else:
                # Update dog if we have more complete information
                    update_columns = []
                update_values = []
                if dog.sire and dog.sire.strip():
                    update_columns.append('Sire = ?')
                    update_values.append(dog.sire.strip())
                if dog.dam and dog.dam.strip():
                    update_columns.append('Dam = ?')
                    update_values.append(dog.dam.strip())
                if dog.sex and dog.sex != 'unknown':
                    update_columns.append('Sex = ?')
                    update_values.append(dog.sex)
                if owner_id:
                    update_columns.append('OwnerID = ?')
                    update_values.append(owner_id)
                
                if update_columns:
                    update_values.append(dog_id)
                    update_query = f"""
                        UPDATE [sResults].[Dog]
                        SET {', '.join(update_columns)}
                        WHERE [DogID] = ?
                    """
                    cursor.execute(update_query, *update_values)
        
        conn.commit()
        
        # Process catalog entries (dog-class relationships)
        print("  Processing catalog entries...")
        for class_key, class_info in classes.items():
            # Get class ID
            if class_info.division and class_info.name:
                div_id = division_name_to_id.get(class_info.division)
                if div_id:
                    normalized_class_name = normalize_class_name(class_info.name) if class_info.name else None
                    if normalized_class_name:
                        class_lookup_key = (normalized_class_name, div_id, class_info.section or None)
                        class_id = class_name_to_id.get(class_lookup_key)
                        
                        if class_id:
                            # Insert catalog entries for each dog in this class
                            for dog in class_info.entries:
                                normalized_dog_name = normalize_name(dog.name)
                                dog_id = dog_name_to_id.get(normalized_dog_name) or dog_name_to_id.get(dog.name)
                                
                                owner_id = None
                                if dog.owner and dog.owner.strip():
                                    owner_id = owner_name_to_id.get(dog.owner.strip())
                                
                                # Check if entry already exists
                check_query = """
                                    SELECT CatalogEntryID FROM [sResults].[CatalogEntry]
                                    WHERE Year = ? AND DogID = ? AND ClassID = ?
                                """
                cursor.execute(check_query, class_info.year, dog_id, class_id)
                if cursor.fetchone():
                    continue  # Already exists
                
                insert_query = """
                                    INSERT INTO [sResults].[CatalogEntry]
                                    (Year, EntryNumber, DogID, DogName, OwnerID, Sire, Dam, Sex, ClassID, ClassName)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query,
                                             class_info.year,
                                             dog.number,
                             dog_id,
                                             dog.name,
                                             owner_id,
                                             dog.sire,
                                             dog.dam,
                                             dog.sex,
                                             class_id,
                                             class_info.name)
        
        conn.commit()
        print(f"  Catalog data populated: {len(dogs)} dogs, {len(classes)} classes")
        
    except Exception as e:
        print(f"  ERROR populating catalog data: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def populate_relationships(conn: pyodbc.Connection, relationships: Dict[str, List[str]], dogs: Dict[str, Dog],
                          commit_interval: int = 100):
    """Populate relationship data into database incrementally.
    
    Args:
        conn: Database connection
        relationships: Dictionary mapping dog canonical keys to relationship strings
        dogs: Dictionary of dogs (for lookup)
        commit_interval: Commit after this many relationships are inserted
    """
    if not relationships:
        return
    
    cursor = conn.cursor()
    relationship_count = 0
    operations_count = 0
    
    try:
        import re
        
        # Build mapping of normalized dog names to dog IDs
        dog_name_to_id = {}
        normalized_name_to_id = {}
        
        # First, get all dogs from database
        cursor.execute("SELECT DogID, DogName FROM [sResults].[Dog]")
        for row in cursor.fetchall():
            dog_id, dog_name = row
            dog_name_to_id[dog_name] = dog_id
            normalized_name_to_id[normalize_name(dog_name)] = dog_id
        
        for canonical_key, rel_list in relationships.items():
            # Get dog ID for this dog (using normalized name)
            dog_id = normalized_name_to_id.get(canonical_key)
            if not dog_id:
                # Try to find in dogs dict to get the actual name
                if canonical_key in dogs:
                    actual_name = dogs[canonical_key].name
                    dog_id = dog_name_to_id.get(actual_name)
                    if dog_id:
                        # Also add to normalized mapping for future lookups
                        normalized_name_to_id[canonical_key] = dog_id
            
            if not dog_id:
                continue  # Dog not found in database, skip
            
            # Parse each relationship string
            for rel_str in rel_list:
                # Parse relationship string format: "RelationshipType: RelatedDogName (sex)" 
                # or "RelationshipType (via Intermediary): RelatedDogName (sex)"
                
                # Extract relationship type (everything before the first colon)
                if ':' not in rel_str:
                    continue
                
                type_and_via, rest = rel_str.split(':', 1)
                rest = rest.strip()
                
                # Check for "via" in relationship type
                via_dog_name = None
                if ' (via ' in type_and_via:
                    type_parts = type_and_via.split(' (via ', 1)
                    relationship_type = type_parts[0].strip()
                    via_dog_name = type_parts[1].rstrip(')').strip()
                else:
                    relationship_type = type_and_via.strip()
                
                # Extract related dog name and sex from rest
                # Format: "RelatedDogName (sex)" or just "RelatedDogName"
                related_dog_name = rest
                related_dog_sex = None
                
                # Check if sex is in parentheses at the end
                sex_match = re.match(r'^(.+?)\s+\(([^)]+)\)\s*$', rest)
                if sex_match:
                    related_dog_name = sex_match.group(1).strip()
                    related_dog_sex = sex_match.group(2).strip()
                
                # Try to find related dog ID
                related_dog_id = None
                
                # First try exact name match
                related_dog_id = dog_name_to_id.get(related_dog_name)
                
                # If not found, try normalized name match
                if not related_dog_id:
                    normalized_related_name = normalize_name(related_dog_name)
                    related_dog_id = normalized_name_to_id.get(normalized_related_name)
                    
                    # Also check in dogs dict
                    if not related_dog_id and normalized_related_name in dogs:
                        actual_related_name = dogs[normalized_related_name].name
                        related_dog_id = dog_name_to_id.get(actual_related_name)
                
                # Skip if required fields are missing
                if dog_id is None:
                    continue  # Skip if dog_id is None
                if not related_dog_name or not related_dog_name.strip():
                    continue  # Skip if RelatedDogName is empty
                if not relationship_type or not relationship_type.strip():
                    continue  # Skip if RelationshipType is empty
                
                # Check if ANY relationship already exists between these two dogs
                # Prevent conflicting relationships - only one relationship per pair of dogs
                # This prevents cases like "Grandsire" and "Great-granddam" for the same pair
                existing_rel_query = """
                    SELECT RelationshipID FROM [sResults].[Relationship]
                    WHERE DogID = ? AND RelatedDogName = ?
                """
                existing_params = [dog_id, related_dog_name]
                
                if related_dog_id:
                    # Also check by RelatedDogID for more precise matching
                    existing_rel_query += " AND (RelatedDogID = ? OR RelatedDogID IS NULL)"
                    existing_params.append(related_dog_id)
                
                cursor.execute(existing_rel_query, tuple(existing_params))
                existing_rel = cursor.fetchone()
                
                # If a relationship already exists between these two dogs, skip this one
                # This prevents conflicting relationships
                if existing_rel:
                    continue  # Relationship already exists between these two dogs, skip
                
                # Also check if this exact relationship already exists (same type, same via)
                # This catches exact duplicates
                exact_check_query = """
                    SELECT RelationshipID FROM [sResults].[Relationship]
                    WHERE DogID = ? AND RelationshipType = ? AND RelatedDogName = ?
                """
                exact_check_params = [dog_id, relationship_type, related_dog_name]
                
                if via_dog_name:
                    exact_check_query += " AND ViaDogName = ?"
                    exact_check_params.append(via_dog_name)
                else:
                    exact_check_query += " AND (ViaDogName IS NULL OR ViaDogName = '')"
                
                cursor.execute(exact_check_query, tuple(exact_check_params))
                if cursor.fetchone():
                    continue  # Exact duplicate already exists, skip
                
                # Insert relationship
                insert_query = """
                    INSERT INTO [sResults].[Relationship]
                    (DogID, RelatedDogID, RelatedDogName, RelationshipType, ViaDogName, RelatedDogSex)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                try:
                    cursor.execute(insert_query,
                                 (dog_id,
                                 related_dog_id,
                                 related_dog_name,
                                 relationship_type,
                                 via_dog_name,
                                 related_dog_sex))
                    
                    relationship_count += 1
                    operations_count += 1
                    
                    # Commit periodically
                    if operations_count % commit_interval == 0:
                        conn.commit()
                        print(f"    Committed {operations_count} relationships so far...")
                except pyodbc.IntegrityError as e:
                    # Handle unique constraint violations (duplicate key errors)
                    error_msg = str(e)
                    if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower() or 'PRIMARY KEY' in error_msg:
                        # Duplicate detected - skip this insert
                        continue
                    else:
                        # Some other integrity error - re-raise
                        raise
        
        # Final commit
        if operations_count % commit_interval != 0:
            conn.commit()
        
        if relationship_count > 0:
            print(f"  ✓ Relationships populated: {relationship_count} relationships written to database")
        else:
            print(f"  No new relationships to write (all already exist in database)")
        
    except Exception as e:
        print(f"  ERROR populating relationships: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def populate_trial_results_data(conn: pyodbc.Connection, trial_results: List[TrialResult],
                                trial_name_to_id: Optional[Dict[str, int]] = None,
                                division_name_to_id: Optional[Dict[str, int]] = None,
                                class_name_to_id: Optional[Dict[tuple, int]] = None,
                                owner_name_to_id: Optional[Dict[str, int]] = None,
                                dog_name_to_id: Optional[Dict[str, int]] = None,
                                class_key_to_id: Optional[Dict[tuple, int]] = None,
                                commit_interval: int = 50):
    """Populate trial results data into database.
    
    If tracking dictionaries are provided, they are reused across calls (for incremental processing).
    Otherwise, new dictionaries are created (for bulk processing).
    """
    print("\nPopulating trial results data...")
    cursor = conn.cursor()
    
    try:
        # Initialize tracking dictionaries if not provided
        if trial_name_to_id is None:
            trial_name_to_id = {}
        if division_name_to_id is None:
            division_name_to_id = {}
            section_name_to_id = {}  # Always create new for this function
        if class_name_to_id is None:
            class_name_to_id = {}  # (normalized_class_name, div_id, section) -> class_id
        if owner_name_to_id is None:
            owner_name_to_id = {}
        if dog_name_to_id is None:
            dog_name_to_id = {}
        if class_key_to_id is None:
            class_key_to_id = {}  # (trial_id, class_id, class_number) -> trialclass_id
        
        operations_count = 0
        
        # Group results by trial
        by_trial = defaultdict(list)
        for result in trial_results:
            by_trial[result.trial_name].append(result)
        
        # Process each trial
        trial_count = 0
        for trial_name, results in by_trial.items():
            trial_count += 1
            if trial_count % 10 == 0:
                print(f"  Processing trial {trial_count}/{len(by_trial)}: {trial_name}")
            
            # Get or create trial
            trial_id = trial_name_to_id.get(trial_name)
            if trial_id is None:
                # Get date and year from first result
                date_str = results[0].date if results else None
                year = results[0].year if results else None
                
                trial_id = get_or_create_id(
                    cursor, 'TrialList', 'TrialName', trial_name,
                    create_columns={
                        'TrialDate': date_str,
                        'Year': year
                    }
                )
                if trial_id:
                    trial_name_to_id[trial_name] = trial_id
            
            # Process classes and results for this trial
            by_class = defaultdict(list)
            for result in results:
                # Normalize division
                division = normalize_division_name(result.division) if result.division else None
                div_id = None
                if division and division.strip():
                    div_id = division_name_to_id.get(division)
                    if div_id is None:
                        div_id = get_or_create_id(cursor, 'Division', 'DivisionName', division)
                        if div_id:
                            division_name_to_id[division] = div_id
                
                # Get or create section
                section_id = None
                if result.section and result.section.strip():
                    section_name = result.section.strip()
                    section_id = section_name_to_id.get(section_name)
                    if section_id is None:
                        section_id = get_or_create_id(cursor, 'Section', 'SectionName', section_name)
                        if section_id:
                            section_name_to_id[section_name] = section_id
                
                # Normalize class name
                normalized_class_name = None
                if result.class_name:
                    normalized_class_name = normalize_class_name(result.class_name)
                
                # Get or create class
                class_id = None
                if normalized_class_name and div_id:
                    class_lookup_key = (normalized_class_name, div_id, result.section or None)
                    class_id = class_name_to_id.get(class_lookup_key)
                    if class_id is None:
                        class_id = get_or_create_id(
                            cursor, 'Class', 'ClassName', normalized_class_name,
                            create_columns={
                                'DivisionID': div_id,
                                'SectionID': section_id
                            }
                        )
                        if class_id:
                            class_name_to_id[class_lookup_key] = class_id
                            operations_count += 1
                            if operations_count % commit_interval == 0:
                                conn.commit()
                
                # Group by class for this trial
                if class_id:
                    class_key = (trial_id, class_id, result.class_number)
                    by_class[class_key].append(result)
            
            # Process classes and placements for this trial
            for class_key, class_results in by_class.items():
                trial_id_key, class_id, class_number = class_key
                
                # Get or create TrialClass
                trialclass_key = (trial_id, class_id, class_number)
                trialclass_id = class_key_to_id.get(trialclass_key)
                
                if trialclass_id is None:
                    # Calculate entry count
                    entry_count = len(set((r.dog_name or '', r.owner or '') for r in class_results))
                    
                    # Insert TrialClass
                    insert_query = """
                        INSERT INTO [sResults].[TrialClass]
                        (TrialListID, ClassID, ClassNumber, EntryCount)
                        VALUES (?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, trial_id, class_id, class_number, entry_count)
                    operations_count += 1
                    
                    # Get generated ID
                    cursor.execute("""
                        SELECT TrialClassID FROM [sResults].[TrialClass]
                        WHERE TrialListID = ? AND ClassID = ? AND ClassNumber = ?
                    """, trial_id, class_id, class_number)
                    row = cursor.fetchone()
                    if row:
                        trialclass_id = row[0]
                        class_key_to_id[trialclass_key] = trialclass_id
                    
                    if operations_count % commit_interval == 0:
                        conn.commit()
                
                # Process placements for this class
                for result in class_results:
                    # Get or create owner
                    owner_id = None
                    if result.owner and result.owner.strip():
                        owner_name = result.owner.strip()
                        owner_id = owner_name_to_id.get(owner_name)
                        if owner_id is None:
                            owner_id = get_or_create_id(cursor, 'Owner', 'OwnerName', owner_name)
                            if owner_id:
                                owner_name_to_id[owner_name] = owner_id
                                operations_count += 1
                                if operations_count % commit_interval == 0:
                                    conn.commit()
                    
                    # Get or create dog
                    dog_id = None
                    if result.dog_name and result.dog_name.strip():
                        dog_name = result.dog_name.strip()
                        normalized_dog_name = normalize_name(dog_name)
                        
                        # Try to find existing dog
                        dog_id = dog_name_to_id.get(normalized_dog_name) or dog_name_to_id.get(dog_name)
                        
                        if dog_id is None:
                            # Create new dog
                            dog_id = get_or_create_id(
                                cursor, 'Dog', 'DogName', dog_name,
                                create_columns={
                                    'OwnerID': owner_id,
                                    'Sire': result.sire,
                                    'Dam': result.dam
                                }
                            )
                            if dog_id:
                                dog_name_to_id[normalized_dog_name] = dog_id
                                dog_name_to_id[dog_name] = dog_id
                    
                    # Insert placement
                    # TrialClassID is NOT NULL, so ensure it's not None
                    if trialclass_id is None:
                        print(f"  WARNING: Skipping TrialPlacements insert - trialclass_id is None")
                        continue
                    
                    insert_query = """
                        INSERT INTO [sResults].[TrialPlacements]
                        (TrialClassID, DogID, DogName, Result, OwnerID)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (trialclass_id, dog_id, result.dog_name, 
                                 result.placement, owner_id))
                    operations_count += 1
                    if operations_count % commit_interval == 0:
                        conn.commit()
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        print(f"  Trial results populated: {len(trial_results)} results, {len(by_trial)} trials")
        
    except Exception as e:
        print(f"  ERROR populating trial results: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def load_catalog_data(conn: Optional[pyodbc.Connection] = None) -> tuple:
    """Load catalog data using parse_catalog.py logic and write incrementally to database.
    
    If conn is provided, data is written to database as each year is processed.
    Otherwise, data is collected and returned for bulk processing (legacy mode).
    """
    import glob
    import os
    import re
    
    print("=" * 80)
    print("FINDING CATALOG FILES")
    print("=" * 80)
    
    # Track IDs across all years if writing incrementally
    if conn:
        dog_name_to_id = {}
        owner_name_to_id = {}
        division_name_to_id = {}
        section_name_to_id = {}
        class_name_to_id = {}
        all_merged_dogs = {}  # Track merged dogs across years
        all_relationships = {}  # Accumulate relationships
    
    # Use same file finding logic as parse_catalog.py
    doc_files = sorted(glob.glob("*Entries_Catalog*.doc") + glob.glob("*entries_catalog*.doc") + 
                       glob.glob("*Entries*catalog*.doc") + glob.glob("*entries*catalog*.doc"))
    pdf_files = sorted(glob.glob("*Entries_Catalog*.pdf") + glob.glob("*entries_catalog*.pdf") + 
                       glob.glob("*Entries*catalog*.pdf") + glob.glob("*entries*catalog*.pdf") +
                       glob.glob("*Catalog*.pdf") + glob.glob("*catalog*.pdf"))
    
    # Remove duplicates while preserving order
    doc_files = sorted(list(dict.fromkeys(doc_files)))
    pdf_files = sorted(list(dict.fromkeys(pdf_files)))
    catalog_files = sorted(doc_files + pdf_files)
    
    if not catalog_files:
        print("No catalog files found. Looking for files matching *Entries_Catalog*.doc or *Entries_Catalog*.pdf")
        return {}, {}, {}, []
    
    print(f"\nFound {len(doc_files)} .doc file(s) and {len(pdf_files)} .pdf file(s)")
    print(f"Total: {len(catalog_files)} catalog file(s) to process")
    print("=" * 80)
    
    all_classes: Dict[str, ClassInfo] = {}
    all_dogs_by_year: Dict[str, Dict[str, Dog]] = {}
    years_processed = []
    
    for file_idx, filepath in enumerate(catalog_files):
        # Extract year from filename
        year = extract_year_from_filename(filepath)
        years_processed.append(year)
        
        print(f"\n{'=' * 80}")
        print(f"Processing {filepath} (Year: {year})")
        print("=" * 80)
        
        extracted_text_file = f"extracted_text_{year}.txt"
        
        # Try to use existing extracted text file first, but only if it has substantial content
        text = None
        if os.path.exists(extracted_text_file):
            try:
                file_size = os.path.getsize(extracted_text_file)
                if file_size > 1000:  # File should be at least 1KB
                    print(f"Reading from existing {extracted_text_file} ({file_size} bytes)...")
                    with open(extracted_text_file, "r", encoding="utf-8") as f:
                        text = f.read()
                    print(f"Read {len(text)} characters of text.")
                    lines = text.split('\n')
                    print(f"Text file has {len(text)} characters, {len(lines)} lines")
                    if len(text) < 1000:
                        print(f"WARNING: {extracted_text_file} appears to be empty or truncated ({len(text)} chars). Re-extracting...")
                        text = None  # Force re-extraction
                    else:
                        # Check if text actually has class patterns
                        class_lines = [l for l in lines[:100] if 'Class' in l and re.search(r'Class\s+\d+:', l)]
                        print(f"Found {len(class_lines)} class lines in first 100 lines of file")
                        if len(class_lines) == 0 and len(lines) > 10:
                            print(f"WARNING: No class lines found in file. First few lines:")
                            for i, line in enumerate(lines[:5]):
                                print(f"  Line {i}: {line[:80]}")
                else:
                    print(f"Existing {extracted_text_file} is too small ({file_size} bytes). Re-extracting...")
                    text = None
            except Exception as e:
                print(f"Error reading {extracted_text_file}: {e}. Re-extracting...")
                text = None  # Force re-extraction
        
        if not text:
            print(f"Extracting text from {filepath}...")
            try:
                text = extract_text_from_file(filepath)
                print(f"Extracted {len(text)} characters of text.")
            except Exception as e:
                print(f"Error extracting text: {e}")
                print("Skipping this file...")
                continue
            
            # Save extracted text for debugging - ALWAYS save if we got any text
            if text and len(text) > 0:
                try:
                    with open(extracted_text_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    lines = text.split('\n')
                    print(f"Saved extracted text to {extracted_text_file} ({len(text)} chars, {len(lines)} lines).")
                    if len(text) < 1000:
                        print(f"WARNING: Extracted text is very short. First 200 chars: {text[:200]}")
                except Exception as e:
                    print(f"Error saving extracted text: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"ERROR: No text extracted ({len(text) if text else 0} chars). Cannot proceed.")
                continue
        
        print(f"\nParsing catalog for year {year}...")
        print(f"Text variable: type={type(text)}, is None={text is None}, length={len(text) if text else 0}")
        if text is None:
            print(f"ERROR: Text is None! Cannot parse. Skipping...")
            continue
        if not text or len(text) < 100:
            print(f"WARNING: Text is empty or too short ({len(text) if text else 0} chars). Skipping...")
            continue
        print(f"Text is valid: {len(text)} chars, {len(text.split(chr(10)))} lines")
        try:
            # Quick check: count "Class" lines in text BEFORE calling parse_catalog
            text_lines = text.split('\n')
            class_lines = [l for l in text_lines if 'Class' in l and re.search(r'Class\s+\d+:', l)]
            print(f"BEFORE parse_catalog: Text has {len(text_lines)} total lines, {len(class_lines)} lines with 'Class' pattern.")
            if len(class_lines) > 0:
                print(f"First class line: {repr(class_lines[0][:100])}")
                # Test if the regex matches
                test_match = re.match(r'^\s*Class\s+(\d+):[\s\t]+(.+?)[\s\t]+Entries:[\s\t]+(\d+)', class_lines[0], re.IGNORECASE)
                if test_match:
                    print(f"  Regex MATCHES: Class {test_match.group(1)}, Entries: {test_match.group(3)}")
                else:
                    print(f"  Regex does NOT match - trying alternative pattern...")
                    test_match2 = re.match(r'^\s*Class\s+(\d+):[\s\t]+(.+?)(?:\s*\.?\s*)$', class_lines[0], re.IGNORECASE)
                    if test_match2:
                        print(f"  Alternative regex MATCHES: Class {test_match2.group(1)}")
                    else:
                        print(f"  Alternative regex also does NOT match")
                        # Show the actual characters
                        print(f"  Line bytes: {class_lines[0][:100].encode('utf-8')}")
            else:
                print(f"  WARNING: No class lines found in text! First 10 lines:")
                for i, line in enumerate(text_lines[:10]):
                    print(f"    Line {i}: {repr(line[:80])}")
            
            classes, dogs = parse_catalog(text, year)
            print(f"Found {len(classes)} classes and {len(dogs)} dogs for {year}.")
            if len(dogs) == 0 and len(class_lines) > 0:
                print(f"WARNING: No dogs found for {year} but {len(class_lines)} class lines detected. This may indicate a parsing issue.")
                # Show a sample of the text around the first class
                first_class_idx = next((i for i, l in enumerate(text_lines) if 'Class' in l and re.search(r'Class\s+\d+:', l)), None)
                if first_class_idx is not None:
                    print(f"Sample text around first class (lines {first_class_idx} to {first_class_idx+5}):")
                    for i in range(max(0, first_class_idx), min(len(text_lines), first_class_idx+6)):
                        print(f"  Line {i}: {text_lines[i][:120]}")
        except Exception as e:
            print(f"Error parsing catalog for {year}: {e}")
            import traceback
            traceback.print_exc()
            print("Skipping this file...")
            continue
        
        # If writing incrementally, process and write this year's data now
        if conn:
            print(f"\nWriting year {year} data to database...")
            # Process this year's data
            process_year_catalog_data(conn, classes, dogs, year,
                                     dog_name_to_id, owner_name_to_id,
                                     division_name_to_id, class_name_to_id,
                                     section_name_to_id)
            
            # Merge with existing dogs (update all_merged_dogs)
            for dog_key, dog in dogs.items():
                normalized_name_key = normalize_name(dog.name)
                if normalized_name_key not in all_merged_dogs:
                    all_merged_dogs[normalized_name_key] = dog
                else:
                    # Merge: update with more complete information
                    existing_dog = all_merged_dogs[normalized_name_key]
                    if dog.sire and not existing_dog.sire:
                        existing_dog.sire = dog.sire
                    if dog.dam and not existing_dog.dam:
                        existing_dog.dam = dog.dam
                    if dog.sex and dog.sex != 'unknown' and (not existing_dog.sex or existing_dog.sex == 'unknown'):
                        existing_dog.sex = dog.sex
                    if dog.owner and not existing_dog.owner:
                        existing_dog.owner = dog.owner
            
            # Store classes for later relationship processing
            all_classes.update(classes)
            all_dogs_by_year[year] = dogs
            
            # Find and write relationships immediately after processing each year's data
            # This ensures relationships are written at the same time they would be displayed in the report
            print(f"  Finding relationships for accumulated dogs ({len(all_merged_dogs)} dogs)...")
            batch_relationships = find_relationships(all_merged_dogs)
            # Find new relationships (not already in all_relationships)
            new_relationships = {}
            for key, rels in batch_relationships.items():
                existing_rels = set(all_relationships.get(key, []))
                new_rels = [r for r in rels if r not in existing_rels]
                if new_rels:
                    new_relationships[key] = new_rels
                    if key not in all_relationships:
                        all_relationships[key] = []
                    all_relationships[key].extend(new_rels)
            
            # Write new relationships to database immediately
            if new_relationships:
                total_new = sum(len(rels) for rels in new_relationships.values())
                print(f"  Writing {total_new} new relationships to database...")
                populate_relationships(conn, new_relationships, all_merged_dogs)
                print(f"  ✓ Relationships for {len(new_relationships)} dogs written to database")
            else:
                print(f"  No new relationships found (all {sum(len(rels) for rels in batch_relationships.values())} relationships already written)")
            
            # Infer sex from relationships
            infer_sex_from_relationships(all_merged_dogs)
        else:
            # Legacy mode: collect all data first
            all_classes.update(classes)
            all_dogs_by_year[year] = dogs
    
    # Print summary of dogs collected per year
    print(f"\n{'=' * 80}")
    print("DOGS COLLECTED BY YEAR:")
    print("=" * 80)
    total_dogs_before_merge = 0
    for year in sorted(all_dogs_by_year.keys()):
        count = len(all_dogs_by_year[year])
        total_dogs_before_merge += count
        print(f"  {year}: {count} dogs")
    print(f"  Total before merging: {total_dogs_before_merge} dogs")
    
    if not all_dogs_by_year:
        print("No catalog files processed.")
        return {}, {}, {}, []
    
    print(f"\n{'=' * 80}")
    print("Merging dogs across years and inferring sex...")
    print("=" * 80)
    
    # Merge dogs across years
    merged_dogs = merge_dogs_across_years(all_dogs_by_year)
    
    print(f"Total unique dogs after merging: {len(merged_dogs)}")
    
    # Infer sex from relationships iteratively until no more can be inferred
    print("\nInferring sex from relationships...")
    max_iterations = 10
    for iteration in range(max_iterations):
        updated_count = infer_sex_from_relationships(merged_dogs)
        if updated_count == 0:
            break
        print(f"  Iteration {iteration + 1}: Updated sex for {updated_count} dogs")
    
    # Update class entries to reference merged dogs (so they have inferred sex)
    print("\nUpdating class entries to use merged dogs...")
    for class_key, class_info in all_classes.items():
        updated_entries = []
        for dog in class_info.entries:
            # Find the merged dog by normalized name
            dog_normalized_name = normalize_name(dog.name)
            if dog_normalized_name in merged_dogs:
                updated_entries.append(merged_dogs[dog_normalized_name])
            else:
                # Dog not found in merged (shouldn't happen, but keep original)
                updated_entries.append(dog)
        class_info.entries = updated_entries
    
    print("\nFinding relationships...")
    relationships = find_relationships(merged_dogs)
    total_relationships = sum(len(rels) for rels in relationships.values())
    print(f"  Found {total_relationships} total relationships for {len(relationships)} dogs")
    
    # If writing incrementally, write any remaining relationships that weren't written yet
    if conn:
        # Find relationships that haven't been written yet
        remaining_relationships = {}
        for key, rels in relationships.items():
            existing_rels = set(all_relationships.get(key, []))
            new_rels = [r for r in rels if r not in existing_rels]
            if new_rels:
                remaining_relationships[key] = new_rels
        
        if remaining_relationships:
            total_remaining = sum(len(rels) for rels in remaining_relationships.values())
            print(f"\nWriting {total_remaining} remaining relationships to database...")
            print(f"  (Already written: {total_relationships - total_remaining} relationships)")
            populate_relationships(conn, remaining_relationships, merged_dogs)
            print(f"  ✓ Final relationships written to database")
        else:
            print(f"\nAll {total_relationships} relationships already written to database")
    
    # Infer sex again after finding relationships (in case new relationships were found)
    print("\nRe-inferring sex from relationships after relationship finding...")
    for iteration in range(max_iterations):
        updated_count = infer_sex_from_relationships(merged_dogs)
        if updated_count == 0:
            break
        print(f"  Iteration {iteration + 1}: Updated sex for {updated_count} dogs")
    
    # Update class entries again with final inferred sex
    print("\nFinal update of class entries with inferred sex...")
    for class_key, class_info in all_classes.items():
        updated_entries = []
        for dog in class_info.entries:
            dog_normalized_name = normalize_name(dog.name)
            if dog_normalized_name in merged_dogs:
                updated_entries.append(merged_dogs[dog_normalized_name])
            else:
                updated_entries.append(dog)
        class_info.entries = updated_entries
    
    return all_classes, merged_dogs, relationships, years_processed


def load_trial_results_data(conn: Optional[pyodbc.Connection] = None) -> List[TrialResult]:
    """Load trial results data using scrape_trial_results.py logic.
    
    If conn is provided, results are written to database as each file is processed.
    Otherwise, results are collected and returned for bulk processing (legacy mode).
    """
    print("Loading trial results data...")
    
    import glob
    import re
    from pathlib import Path
    
    # Find trial result files in year directories and root
    trial_files = []
    
    # Look in year directories
    for year_dir in sorted(glob.glob("[0-9][0-9][0-9][0-9]"), reverse=True):
        if os.path.isdir(year_dir):
            trial_files.extend(glob.glob(os.path.join(year_dir, "*.html")))
            trial_files.extend(glob.glob(os.path.join(year_dir, "*.htm")))
            trial_files.extend(glob.glob(os.path.join(year_dir, "*.txt")))
            trial_files.extend(glob.glob(os.path.join(year_dir, "*.pdf")))
    
    # Also check root directory
    trial_files.extend(glob.glob("*.html"))
    trial_files.extend(glob.glob("*.htm"))
    
    # Filter out catalog files and reports
    trial_files = [f for f in trial_files 
                   if 'catalog' not in f.lower() and 
                      'report' not in f.lower() and
                      'debug' not in f.lower() and
                      not f.endswith('_files') and
                      os.path.isfile(f)]
    
    all_results = []
    seen_files = set()
    
    print(f"  Found {len(trial_files)} trial files")
    
    # If writing incrementally, set up tracking dictionaries
    if conn:
        trial_name_to_id = {}
        division_name_to_id = {}
        class_name_to_id = {}
        owner_name_to_id = {}
        dog_name_to_id = {}
        class_key_to_id = {}
    
    for filepath in trial_files:
        if filepath in seen_files:
            continue
        seen_files.add(filepath)
        
        try:
            # Extract year from filepath or directory
            year = None
            year_match = re.search(r'(\d{4})', filepath)
            if year_match:
                year = year_match.group(1)
            
            # Determine source folder from path
            source_folder = None
            path_parts = Path(filepath).parts
            if len(path_parts) > 1:
                parent_dir = path_parts[-2]
                if re.match(r'^\d{4}$', parent_dir):
                    source_folder = parent_dir
            
            print(f"    Processing {filepath}...")
            results, _ = parse_local_trial_file(filepath, year=year, source_folder=source_folder)
            
            if conn and results:
                # Write this file's results immediately
                print(f"      Writing {len(results)} results to database...")
                populate_trial_results_data(conn, results, 
                                           trial_name_to_id, division_name_to_id,
                                           class_name_to_id, owner_name_to_id,
                                           dog_name_to_id, class_key_to_id)
            else:
                # Collect for later
                all_results.extend(results)
            
            if results:
                print(f"      Extracted {len(results)} results")
            
        except Exception as e:
            print(f"    Error processing {filepath}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if conn:
        print(f"  Processed {len(trial_files)} trial files (written incrementally)")
        return []  # Already written, return empty list
    else:
        print(f"  Loaded {len(all_results)} trial results total")
    return all_results


def main():
    """Main function to populate database."""
    print("=" * 80)
    print("Populating sResults schema tables")
    print("=" * 80)
    print()
    
    # Connect to database
    print("Connecting to database...")
    try:
        conn = get_connection()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)
    
    try:
        # Load catalog data and write incrementally to database
        # Relationships are already written incrementally during load_catalog_data
        classes, dogs, relationships, years = load_catalog_data(conn)
        
        # Load trial results data and write incrementally to database
        trial_results = load_trial_results_data(conn)
        
        # If any trial results weren't written incrementally, write them now
        if trial_results:
            populate_trial_results_data(conn, trial_results)
        
        print("\n" + "=" * 80)
        print("Database population completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Populate sResults schema tables in TrialResults database with data from catalog and trial results.
Uses the logic from parse_catalog.py and scrape_trial_results.py to extract and insert all data.
"""

import pyodbc
import sys
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Import from existing scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_catalog import (
    Dog, ClassInfo, normalize_name, normalize_for_matching, names_are_similar,
    find_relationships, merge_dogs_across_years,
    infer_sex_from_relationships, extract_year_from_filename,
    parse_catalog, extract_text_from_file, infer_sex_from_classes,
    extract_catalog_division_label, CATALOG_YEAR_MIN, CATALOG_YEAR_MAX,
)
from scrape_trial_results_fixed import (
    TrialResult, normalize_division_name, normalize_class_name,
    parse_local_trial_file, scan_local_subfolders, is_duplicate_trial, extract_text_from_pdf
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


@dataclass
class CatalogEntityContext:
    """Preloaded Dog/Owner rows plus lookup indexes for catalog entity reuse."""
    dog_name_to_id: Dict[str, int] = field(default_factory=dict)
    owner_name_to_id: Dict[str, int] = field(default_factory=dict)
    owner_key_to_id: Dict[str, int] = field(default_factory=dict)
    pair_to_dog_id: Dict[Tuple[str, str], int] = field(default_factory=dict)
    pair_to_owner_id: Dict[Tuple[str, str], int] = field(default_factory=dict)
    dog_id_to_owner_id: Dict[int, int] = field(default_factory=dict)
    db_dog_owner_records: List[Tuple[int, Optional[int], str, str]] = field(default_factory=list)
    db_dog_names: List[str] = field(default_factory=list)
    db_owner_names: List[str] = field(default_factory=list)
    dog_first_word_index: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )
    owner_first_word_index: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )


def normalize_owner_key(owner: str) -> str:
    if not owner:
        return ''
    return normalize_for_matching(owner)


def normalize_dog_key(dog_name: str) -> str:
    if not dog_name:
        return ''
    return normalize_name(dog_name).lower().strip()


def dog_owner_pair_key(dog_name: str, owner_name: str) -> Tuple[str, str]:
    return (normalize_dog_key(dog_name), normalize_owner_key(owner_name or ''))


def _register_owner_in_context(ctx: CatalogEntityContext, owner_id: int, owner_name: str) -> None:
    name = owner_name.strip()
    key = normalize_owner_key(name)
    ctx.owner_name_to_id[name] = owner_id
    ctx.owner_key_to_id[key] = owner_id
    if name not in ctx.db_owner_names:
        ctx.db_owner_names.append(name)
    first_word = key.split()[0] if key else ''
    if first_word and name not in ctx.owner_first_word_index[first_word]:
        ctx.owner_first_word_index[first_word].append(name)


def _register_dog_in_context(
    ctx: CatalogEntityContext,
    dog_id: int,
    dog_name: str,
    owner_id: Optional[int] = None,
    owner_name: str = '',
) -> None:
    name = dog_name.strip()
    norm = normalize_name(name)
    ctx.dog_name_to_id[name] = dog_id
    ctx.dog_name_to_id[norm] = dog_id
    if name not in ctx.db_dog_names:
        ctx.db_dog_names.append(name)
    first_word = normalize_dog_key(name).split()[0] if normalize_dog_key(name) else ''
    if first_word and name not in ctx.dog_first_word_index[first_word]:
        ctx.dog_first_word_index[first_word].append(name)
    if owner_id is not None:
        ctx.dog_id_to_owner_id[dog_id] = owner_id
    if owner_name:
        pair = dog_owner_pair_key(name, owner_name)
        ctx.pair_to_dog_id[pair] = dog_id
        if owner_id is not None:
            ctx.pair_to_owner_id[pair] = owner_id


def preload_dogs_and_owners_from_db(conn: pyodbc.Connection) -> CatalogEntityContext:
    """Load existing Dog+Owner pairs from trial/catalog tables for reuse."""
    ctx = CatalogEntityContext()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.DogID, d.DogName, d.OwnerID, o.OwnerName
        FROM [sResults].[Dog] d
        LEFT JOIN [sResults].[Owner] o ON d.OwnerID = o.OwnerID
    """)
    seen_pairs: Set[Tuple[int, str, str]] = set()
    for dog_id, dog_name, owner_id, owner_name in cursor.fetchall():
        if not dog_name or not str(dog_name).strip():
            continue
        dog = str(dog_name).strip()
        owner = str(owner_name).strip() if owner_name else ''
        pair_sig = (dog_id, dog, owner)
        if pair_sig not in seen_pairs:
            seen_pairs.add(pair_sig)
            ctx.db_dog_owner_records.append((dog_id, owner_id, dog, owner))
        _register_dog_in_context(ctx, dog_id, dog, owner_id, owner)
        if owner and owner_id is not None:
            _register_owner_in_context(ctx, owner_id, owner)

    cursor.execute("SELECT OwnerID, OwnerName FROM [sResults].[Owner]")
    for owner_id, owner_name in cursor.fetchall():
        if owner_name and str(owner_name).strip():
            _register_owner_in_context(ctx, owner_id, str(owner_name).strip())

    cursor.execute("""
        SELECT DISTINCT ce.DogID, ce.DogName, d.OwnerID, o.OwnerName
        FROM [sResults].[CatalogEntry] ce
        JOIN [sResults].[Dog] d ON d.DogID = ce.DogID
        LEFT JOIN [sResults].[Owner] o ON d.OwnerID = o.OwnerID
        WHERE ce.DogName IS NOT NULL AND LTRIM(RTRIM(ce.DogName)) <> ''
    """)
    for dog_id, catalog_name, owner_id, owner_name in cursor.fetchall():
        dog = str(catalog_name).strip()
        owner = str(owner_name).strip() if owner_name else ''
        pair_sig = (dog_id, dog, owner)
        if pair_sig not in seen_pairs:
            seen_pairs.add(pair_sig)
            ctx.db_dog_owner_records.append((dog_id, owner_id, dog, owner))
        _register_dog_in_context(ctx, dog_id, dog, owner_id, owner)

    return ctx


def resolve_owner_id(
    owner_name: str,
    ctx: CatalogEntityContext,
    cursor: Optional[pyodbc.Cursor] = None,
    create_if_missing: bool = False,
) -> Optional[int]:
    """Match catalog owner to an existing Owner row (exact, normalized, or similar)."""
    if not owner_name or not owner_name.strip():
        return None

    name = owner_name.strip()
    owner_id = ctx.owner_name_to_id.get(name)
    if owner_id:
        return owner_id

    key = normalize_owner_key(name)
    owner_id = ctx.owner_key_to_id.get(key)
    if owner_id:
        ctx.owner_name_to_id[name] = owner_id
        return owner_id

    first_word = key.split()[0] if key else ''
    candidates = list(ctx.owner_first_word_index.get(first_word, []))
    if not candidates and len(ctx.db_owner_names) <= 5000:
        candidates = ctx.db_owner_names

    for existing_name in candidates:
        if names_are_similar(name, existing_name):
            owner_id = ctx.owner_name_to_id.get(existing_name)
            if owner_id:
                _register_owner_in_context(ctx, owner_id, name)
                return owner_id

    if create_if_missing and cursor is not None:
        owner_id = get_or_create_id(cursor, 'Owner', 'OwnerName', name)
        if owner_id:
            _register_owner_in_context(ctx, owner_id, name)
        return owner_id

    return None


def _resolve_dog_id_only(dog_name: str, ctx: CatalogEntityContext) -> Optional[int]:
    """Dog-only fallback when catalog entry has no owner (rare)."""
    if not dog_name or not dog_name.strip():
        return None

    name = dog_name.strip()
    normalized = normalize_name(name)
    for key in (normalized, name):
        dog_id = ctx.dog_name_to_id.get(key)
        if dog_id:
            return dog_id

    first_word = normalize_dog_key(name).split()[0] if normalize_dog_key(name) else ''
    candidates = list(ctx.dog_first_word_index.get(first_word, []))
    if not candidates and len(ctx.db_dog_names) <= 5000:
        candidates = ctx.db_dog_names

    for existing_name in candidates:
        if names_are_similar(name, existing_name):
            dog_id = (
                ctx.dog_name_to_id.get(existing_name)
                or ctx.dog_name_to_id.get(normalize_name(existing_name))
            )
            if dog_id:
                _register_dog_in_context(ctx, dog_id, name)
                return dog_id

    return None


def resolve_dog_owner_pair(
    dog_name: str,
    owner_name: Optional[str],
    ctx: CatalogEntityContext,
) -> Tuple[Optional[int], Optional[int]]:
    """Match catalog dog+owner to existing Dog/Owner rows from trial results.

    Prefers (dog, owner) pair matches so same-named dogs with different owners
    stay distinct. Falls back to dog-only match only when owner is absent.
    """
    if not dog_name or not dog_name.strip():
        return None, resolve_owner_id(owner_name or '', ctx)

    dog = dog_name.strip()
    owner = owner_name.strip() if owner_name else ''

    if owner:
        pair = dog_owner_pair_key(dog, owner)
        dog_id = ctx.pair_to_dog_id.get(pair)
        if dog_id:
            owner_id = (
                ctx.pair_to_owner_id.get(pair)
                or ctx.dog_id_to_owner_id.get(dog_id)
                or resolve_owner_id(owner, ctx)
            )
            return dog_id, owner_id

        dog_first = normalize_dog_key(dog).split()[0] if normalize_dog_key(dog) else ''
        for db_dog_id, db_owner_id, db_dog, db_owner in ctx.db_dog_owner_records:
            if dog_first and normalize_dog_key(db_dog).split()[:1] != [dog_first]:
                continue
            if not names_are_similar(dog, db_dog):
                continue
            if db_owner and names_are_similar(owner, db_owner):
                owner_id = db_owner_id or resolve_owner_id(db_owner, ctx)
                _register_dog_in_context(ctx, db_dog_id, dog, owner_id, owner)
                return db_dog_id, owner_id or resolve_owner_id(owner, ctx)

        owner_id = resolve_owner_id(owner, ctx)
        if owner_id is not None:
            for db_dog_id, db_owner_id, db_dog, db_owner in ctx.db_dog_owner_records:
                if db_owner_id != owner_id:
                    continue
                if dog_first and normalize_dog_key(db_dog).split()[:1] != [dog_first]:
                    continue
                if names_are_similar(dog, db_dog):
                    _register_dog_in_context(ctx, db_dog_id, dog, owner_id, owner)
                    return db_dog_id, owner_id

        return None, owner_id

    return _resolve_dog_id_only(dog, ctx), None


def resolve_dog_id(
    dog_name: str,
    ctx: CatalogEntityContext,
) -> Optional[int]:
    """Backward-compatible dog resolver; prefers pair match when owner known."""
    dog_id, _ = resolve_dog_owner_pair(dog_name, None, ctx)
    return dog_id


def resolve_or_create_dog_owner_pair(
    dog_name: str,
    owner_name: Optional[str],
    ctx: CatalogEntityContext,
    cursor: pyodbc.Cursor,
    *,
    create_dog_fn,
) -> Tuple[Optional[int], Optional[int]]:
    """Resolve dog+owner against preloaded entities; create only when no match exists."""
    dog_id, owner_id = resolve_dog_owner_pair(dog_name, owner_name, ctx)
    if owner_id is None and owner_name and owner_name.strip():
        owner_id = resolve_owner_id(
            owner_name, ctx, cursor=cursor, create_if_missing=True,
        )

    if dog_id is None and dog_name and dog_name.strip():
        dog_id = create_dog_fn(cursor, dog_name.strip(), owner_id)
        if dog_id:
            _register_dog_in_context(
                ctx, dog_id, dog_name.strip(), owner_id, owner_name or '',
            )

    return dog_id, owner_id


def canonical_catalog_division_name(division: str) -> str:
    """Normalize a parsed catalog division to the same canonical names as trial results."""
    if not division:
        return division
    label = extract_catalog_division_label(division)
    return normalize_division_name(label) or label

def clear_trial_results_tables(conn: pyodbc.Connection):
    """Clear TrialPlacements, TrialClass, and TrialList tables.
    
    Tables are cleared in order to respect foreign key constraints:
    1. TrialPlacements (references TrialClass)
    2. TrialClass (references TrialList)
    3. TrialList
    """
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("CLEARING TRIAL RESULTS TABLES")
    print("=" * 80)
    
    try:
        # Clear child tables before TrialPlacements
        print("Clearing TrialPlacements_Times table...")
        try:
            cursor.execute("DELETE FROM [sResults].[TrialPlacements_Times]")
            times_count = cursor.rowcount
            print(f"  Deleted {times_count} records from TrialPlacements_Times")
        except pyodbc.Error as e:
            if "Invalid object name" in str(e):
                print("  Skipping TrialPlacements_Times (table not found)")
            else:
                raise

        # Clear TrialPlacements first (has foreign key to TrialClass)
        print("Clearing TrialPlacements table...")
        cursor.execute("DELETE FROM [sResults].[TrialPlacements]")
        placements_count = cursor.rowcount
        print(f"  Deleted {placements_count} records from TrialPlacements")
        
        # Clear TrialClass (has foreign key to TrialList)
        print("Clearing TrialClass table...")
        cursor.execute("DELETE FROM [sResults].[TrialClass]")
        class_count = cursor.rowcount
        print(f"  Deleted {class_count} records from TrialClass")
        
        # Clear TrialList last
        print("Clearing TrialList table...")
        cursor.execute("DELETE FROM [sResults].[TrialList]")
        trial_count = cursor.rowcount
        print(f"  Deleted {trial_count} records from TrialList")
        
        conn.commit()
        print(f"\nCleared {placements_count} placements, {class_count} classes, and {trial_count} trials")
        print("=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Failed to clear trial results tables: {e}")
        raise

def normalize_date_for_sql(date_str: str, year: int) -> str:
    """Normalize a date string to SQL Server format (YYYY-MM-DD).
    
    Handles various date formats and invalid dates.
    Returns a date in YYYY-MM-DD format, or a default date if parsing fails.
    """
    if not date_str or not date_str.strip():
        return f"{year}-01-01"
    
    date_str = date_str.strip()
    
    # Check if it's already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            pass
    
    # Try common date formats
    date_formats = [
        '%B %d, %Y',      # October 10, 1996
        '%b %d, %Y',      # Oct 10, 1996
        '%m/%d/%Y',       # 10/10/1996
        '%m-%d-%Y',       # 10-10-1996
        '%d/%m/%Y',       # 10/10/1996 (European)
        '%Y-%m-%d',       # 1996-10-10
        '%B %d %Y',       # October 10 1996
        '%b %d %Y',       # Oct 10 1996
        '%m/%d/%y',       # 10/10/96
        '%d %B %Y',       # 10 October 1996
        '%d %b %Y',       # 10 Oct 1996
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Try to extract date components from malformed dates
    # Handle cases like "and 10, 1996" -> "October 10, 1996" or use year
    month_match = re.search(r'(\w+)\s+(\d+),?\s+(\d{4})', date_str)
    if month_match:
        month_str, day_str, year_str = month_match.groups()
        # Try to fix common issues
        if month_str.lower() in ['and', 'the']:
            # Invalid month, use January as default
            try:
                day = int(day_str)
                year_val = int(year_str)
                if 1 <= day <= 31 and 1900 <= year_val <= 2100:
                    return f"{year_val}-01-{day:02d}"
            except ValueError:
                pass
    
    # If all parsing fails, return default date for the year
    print(f"  WARNING: Could not parse date '{date_str}', using default date for year {year}")
    return f"{year}-01-01"

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
    
    # Check if id_column is actually an IDENTITY column
    is_identity = False
    try:
        # Use string formatting for schema.table since it's not user input
        cursor.execute(f"""
            SELECT is_identity 
            FROM sys.columns 
            WHERE object_id = OBJECT_ID('sResults.[{table}]') 
            AND name = ?
        """, id_column)
        row = cursor.fetchone()
        if row:
            is_identity = bool(row[0])
    except Exception:
        # If we can't check, assume it's IDENTITY (safer default)
        is_identity = True
    
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
    
    # If id_column is NOT an IDENTITY column, we need to provide a value for it
    # Get the next available ID value
    if not is_identity:
        try:
            cursor.execute(f"SELECT ISNULL(MAX([{id_column}]), 0) + 1 FROM [sResults].[{table}]")
            row = cursor.fetchone()
            if row and row[0] is not None:
                next_id = int(row[0])
                create_columns[id_column] = next_id
                # Only print for TrialListID to avoid excessive output
                if id_column == 'TrialListID':
                    print(f"  Note: {id_column} is not IDENTITY, using next available ID: {next_id}")
        except Exception as e:
            print(f"  WARNING: Could not get next ID for {id_column}: {e}")
            # Try to continue anyway - might work if there's a default or trigger
    
    # Ensure we have at least one column to insert and that name_column has a non-empty value
    if not create_columns or not create_columns.get(name_column, '').strip():
        return None
    
    # Final safety check: ensure id_column is NOT in the column list if it's IDENTITY
    column_names = list(create_columns.keys())
    if is_identity and id_column in column_names:
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
    
    # Use fully qualified table name - ensure we're using the correct database
    # The error message format suggests there might be a database name prefix issue
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
    except pyodbc.IntegrityError as e:
        error_msg = str(e).lower()
        error_str_full = str(e)
        
        # For TrialList with TrialListID errors, try to get existing record first
        # This handles cases where there might be database triggers or constraints
        # Check both lowercase and original case for TrialListID
        if table == 'TrialList' and ('triallistid' in error_msg or 'TrialListID' in error_str_full or 'cannot insert' in error_msg):
            try:
                cursor.execute(f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?", name.strip())
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception:
                pass  # If lookup fails, continue with normal error handling
        
        # Handle duplicate key violations - record may have been inserted by another process
        if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
            # Try to get the existing ID
            cursor.execute(f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?", name.strip())
            row = cursor.fetchone()
            if row:
                return row[0]
        
        # Re-raise if we can't handle it
        raise
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
                               entity_ctx: CatalogEntityContext,
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
        entity_ctx: Preloaded dog/owner match context (updated in place)
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
                    normalized_div_name = canonical_catalog_division_name(class_info.division)
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
        
        # Process owners (resolve or create before dogs)
        for dog_key, dog in dogs.items():
            if dog.owner and dog.owner.strip():
                if resolve_owner_id(
                    dog.owner, entity_ctx, cursor=cursor, create_if_missing=True,
                ):
                    operations_count += 1
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        # Process dogs — reuse existing dog+owner pairs from trial results when possible
        for dog_key, dog in dogs.items():
            dog_id, owner_id = resolve_dog_owner_pair(dog.name, dog.owner, entity_ctx)
            if owner_id is None and dog.owner and dog.owner.strip():
                owner_id = resolve_owner_id(
                    dog.owner, entity_ctx, cursor=cursor, create_if_missing=True,
                )
            
            if dog_id is None:
                # Create new dog linked to resolved owner
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
                    _register_dog_in_context(
                        entity_ctx, dog_id, dog.name, owner_id, dog.owner or '',
                    )
                    operations_count += 1
                    if operations_count % commit_interval == 0:
                        conn.commit()
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
                                dog_id, owner_id = resolve_dog_owner_pair(
                                    dog.name, dog.owner, entity_ctx,
                                )
                                if owner_id is None and dog.owner and dog.owner.strip():
                                    owner_id = resolve_owner_id(
                                        dog.owner, entity_ctx, cursor=cursor, create_if_missing=True,
                                    )
                                
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
                                try:
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
                                except pyodbc.IntegrityError as e:
                                    # Handle duplicate - may have been inserted by another process
                                    error_msg = str(e).lower()
                                    if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
                                        # Duplicate detected - skip this insert
                                        continue
                                    else:
                                        raise
        
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
        entity_ctx = preload_dogs_and_owners_from_db(conn)
        division_name_to_id = {}
        section_name_to_id = {}
        class_name_to_id = {}
        
        # Process divisions and classes first
        print("  Processing divisions and classes...")
        for class_key, class_info in classes.items():
            # Get or create division
            if class_info.division:
                div_id = division_name_to_id.get(class_info.division)
                if div_id is None:
                    normalized_div_name = canonical_catalog_division_name(class_info.division)
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

        # Group dogs by catalog year for per-year processing
        dogs_by_year: Dict[str, Dict[str, Dog]] = defaultdict(dict)
        for class_info in classes.values():
            year = class_info.year
            for dog in class_info.entries:
                dogs_by_year[year][dog.number] = dog

        for year in years:
            year_dogs = dogs_by_year.get(year, {})
            year_classes = {
                k: v for k, v in classes.items() if v.year == year
            }
            if year_dogs and year_classes:
                process_year_catalog_data(
                    conn, year_classes, year_dogs, year,
                    entity_ctx, division_name_to_id, class_name_to_id, section_name_to_id,
                )

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
            print(f"  Relationships populated: {relationship_count} relationships written to database")
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
        # Always create section_name_to_id (matching scrape_trial_results.py behavior)
        # This must be initialized regardless of whether division_name_to_id was provided
        section_name_to_id = {}
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
            
            # Get date and year from results first (needed for checking if trial exists)
            # Collect all unique dates from results
            unique_dates = set()
            year = None
            for result in results:
                if result.date and result.date.strip():
                    unique_dates.add(result.date.strip())
                if result.year:
                    year = result.year
            
            # TrialList table has StartDate and EndDate, not TrialDate
            # Year is required, so ensure we have it and convert to int if needed
            if year is None:
                print(f"  WARNING: No year found for trial '{trial_name}', skipping...")
                continue
            
            # Ensure Year is an integer (database expects INT, not VARCHAR)
            try:
                year_int = int(year) if not isinstance(year, int) else year
            except (ValueError, TypeError):
                print(f"  WARNING: Invalid year '{year}' for trial '{trial_name}', skipping...")
                continue
            
            # Get or create trial - check using both name and year
            trial_key = (trial_name, year_int)
            trial_id = trial_name_to_id.get(trial_name)
            if trial_id is None:
                # Check if trial already exists in database (to avoid re-loading)
                # Use both TrialName and Year to uniquely identify a trial
                cursor.execute("SELECT TrialListID FROM [sResults].[TrialList] WHERE TrialName = ? AND Year = ?", trial_name, year_int)
                row = cursor.fetchone()
                if row:
                    trial_id = row[0]
                    trial_name_to_id[trial_name] = trial_id
                    print(f"  Trial '{trial_name}' (Year {year_int}) already exists in database (ID: {trial_id}), skipping...")
                    continue
            
            if trial_id is None:
                
                # StartDate is required (NOT NULL), so we must provide a value
                create_cols = {'Year': year_int}
                
                if len(unique_dates) == 1:
                    # Only one date available - use it for both StartDate and EndDate
                    date_str = unique_dates.pop()
                    normalized_date = normalize_date_for_sql(date_str, year_int)
                    create_cols['StartDate'] = normalized_date
                    create_cols['EndDate'] = normalized_date
                elif len(unique_dates) > 1:
                    # Multiple dates available - normalize and use first and last (sorted)
                    normalized_dates = [normalize_date_for_sql(d, year_int) for d in unique_dates]
                    sorted_dates = sorted(normalized_dates)
                    create_cols['StartDate'] = sorted_dates[0]
                    create_cols['EndDate'] = sorted_dates[-1]
                else:
                    # No date available - use January 1st of the year as a default date
                    default_date = f"{year_int}-01-01"
                    create_cols['StartDate'] = default_date
                    create_cols['EndDate'] = default_date
                
                try:
                    trial_id = get_or_create_id(
                        cursor, 'TrialList', 'TrialName', trial_name,
                        create_columns=create_cols
                    )
                except Exception as e:
                    print(f"  ERROR: Failed to create/get trial '{trial_name}': {e}")
                    raise  # Quit on error as requested
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
                            # Commit after creating Division to ensure it's visible
                            conn.commit()
                    
                    # Verify div_id exists in database before using it
                    if div_id:
                        try:
                            cursor.execute("SELECT DivisionID FROM [sResults].[Division] WHERE DivisionID = ?", div_id)
                            if not cursor.fetchone():
                                print(f"  WARNING: DivisionID {div_id} for '{division}' does not exist in database, skipping class creation")
                                div_id = None
                        except Exception as e:
                            print(f"  WARNING: Could not verify DivisionID {div_id}: {e}")
                            div_id = None
                
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
                        # Only include SectionID if it's not None (NULL is allowed but let's be explicit)
                        create_cols = {'DivisionID': div_id}
                        if section_id:
                            create_cols['SectionID'] = section_id
                        
                        class_id = get_or_create_id(
                            cursor, 'Class', 'ClassName', normalized_class_name,
                            create_columns=create_cols
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
                    # Check if TrialClass already exists
                    check_query = """
                        SELECT TrialClassID FROM [sResults].[TrialClass]
                        WHERE TrialListID = ? AND ClassID = ? AND ClassNumber = ?
                    """
                    cursor.execute(check_query, trial_id, class_id, class_number)
                    row = cursor.fetchone()
                    if row:
                        trialclass_id = row[0]
                        class_key_to_id[trialclass_key] = trialclass_id
                    else:
                        # Calculate entry count
                        entry_count = len(set((r.dog_name or '', r.owner or '') for r in class_results))
                        
                        # Check if TrialClassID is IDENTITY, if not get next available ID
                        trialclass_id_value = None
                        try:
                            cursor.execute("""
                                SELECT is_identity 
                                FROM sys.columns 
                                WHERE object_id = OBJECT_ID('sResults.TrialClass') 
                                AND name = 'TrialClassID'
                            """)
                            row = cursor.fetchone()
                            is_identity = bool(row[0]) if row else True  # Default to True if can't check
                            
                            if not is_identity:
                                # Get next available TrialClassID
                                cursor.execute("SELECT ISNULL(MAX([TrialClassID]), 0) + 1 FROM [sResults].[TrialClass]")
                                row = cursor.fetchone()
                                if row and row[0] is not None:
                                    trialclass_id_value = int(row[0])
                        except Exception as e:
                            # If we can't check, assume it's IDENTITY
                            pass
                        
                        # Insert TrialClass (includes ClassNumber column)
                        if trialclass_id_value is not None:
                            # TrialClassID is not IDENTITY, include it in INSERT
                            insert_query = """
                                INSERT INTO [sResults].[TrialClass]
                                (TrialClassID, TrialListID, ClassID, ClassNumber, EntryCount)
                                VALUES (?, ?, ?, ?, ?)
                            """
                            try:
                                cursor.execute(insert_query, trialclass_id_value, trial_id, class_id, class_number, entry_count)
                                operations_count += 1
                                trialclass_id = trialclass_id_value
                                class_key_to_id[trialclass_key] = trialclass_id
                            except pyodbc.IntegrityError as e:
                                # Handle duplicate - may have been inserted by another process
                                error_msg = str(e).lower()
                                if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
                                    # Try to get the existing ID
                                    cursor.execute(check_query, trial_id, class_id, class_number)
                                    row = cursor.fetchone()
                                    if row:
                                        trialclass_id = row[0]
                                        class_key_to_id[trialclass_key] = trialclass_id
                                else:
                                    raise
                        else:
                            # TrialClassID is IDENTITY, don't include it in INSERT
                            insert_query = """
                                INSERT INTO [sResults].[TrialClass]
                                (TrialListID, ClassID, ClassNumber, EntryCount)
                                VALUES (?, ?, ?, ?)
                            """
                            try:
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
                            except pyodbc.IntegrityError as e:
                                # Handle duplicate - may have been inserted by another process
                                error_msg = str(e).lower()
                                if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
                                    # Try to get the existing ID
                                    cursor.execute(check_query, trial_id, class_id, class_number)
                                    row = cursor.fetchone()
                                    if row:
                                        trialclass_id = row[0]
                                        class_key_to_id[trialclass_key] = trialclass_id
                                else:
                                    raise
                        
                        if trialclass_id and operations_count % commit_interval == 0:
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
                    
                    # Check if placement already exists
                    # Note: Column name is TrialPlacementsID (with 's'), not TrialPlacementID
                    check_query = """
                        SELECT TrialPlacementsID FROM [sResults].[TrialPlacements]
                        WHERE TrialClassID = ? AND DogID = ? AND Result = ?
                    """
                    cursor.execute(check_query, trialclass_id, dog_id, result.placement)
                    if cursor.fetchone():
                        continue  # Already exists, skip duplicate
                    
                    # Check if TrialPlacementsID is IDENTITY, if not get next available ID
                    trialplacement_id_value = None
                    try:
                        cursor.execute("""
                            SELECT is_identity 
                            FROM sys.columns 
                            WHERE object_id = OBJECT_ID('sResults.TrialPlacements') 
                            AND name = 'TrialPlacementsID'
                        """)
                        row = cursor.fetchone()
                        is_identity = bool(row[0]) if row else True  # Default to True if can't check
                        
                        if not is_identity:
                            # Get next available TrialPlacementsID
                            cursor.execute("SELECT ISNULL(MAX([TrialPlacementsID]), 0) + 1 FROM [sResults].[TrialPlacements]")
                            row = cursor.fetchone()
                            if row and row[0] is not None:
                                trialplacement_id_value = int(row[0])
                    except Exception as e:
                        # If we can't check, assume it's IDENTITY
                        pass
                    
                    # Insert TrialPlacements (schema: TrialPlacementsID, TrialListID, TrialClassID, DogID, Result)
                    # Note: TrialListID is required, not optional
                    if trialplacement_id_value is not None:
                        # TrialPlacementsID is not IDENTITY, include it in INSERT
                        insert_query = """
                            INSERT INTO [sResults].[TrialPlacements]
                            (TrialPlacementsID, TrialListID, TrialClassID, DogID, Result)
                            VALUES (?, ?, ?, ?, ?)
                        """
                        try:
                            cursor.execute(insert_query, (trialplacement_id_value, trial_id, trialclass_id, dog_id, result.placement))
                            operations_count += 1
                            if operations_count % commit_interval == 0:
                                conn.commit()
                        except pyodbc.IntegrityError as e:
                            # Handle duplicate - may have been inserted by another process
                            error_msg = str(e).lower()
                            if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
                                # Duplicate detected - skip this insert
                                continue
                            else:
                                raise
                    else:
                        # TrialPlacementsID is IDENTITY, don't include it in INSERT
                        insert_query = """
                            INSERT INTO [sResults].[TrialPlacements]
                            (TrialListID, TrialClassID, DogID, Result)
                            VALUES (?, ?, ?, ?)
                        """
                        try:
                            cursor.execute(insert_query, (trial_id, trialclass_id, dog_id, result.placement))
                            operations_count += 1
                            if operations_count % commit_interval == 0:
                                conn.commit()
                        except pyodbc.IntegrityError as e:
                            # Handle duplicate - may have been inserted by another process
                            error_msg = str(e).lower()
                            if 'duplicate' in error_msg or 'unique' in error_msg or 'primary key' in error_msg:
                                # Duplicate detected - skip this insert
                                continue
                            else:
                                raise
        
        if operations_count % commit_interval != 0:
            conn.commit()
        
        print(f"  Trial results populated: {len(trial_results)} results, {len(by_trial)} trials")
        
    except Exception as e:
        print(f"  ERROR populating trial results: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def is_year_processed(conn: pyodbc.Connection, year: str) -> bool:
    """Check if a trial results year has already been processed by checking trial results tables.
    
    Checks trial results tables (NOT catalog entries):
    - TrialList (trial list) - has Year column, where trials are inserted
    - TrialClass (trial classes) - linked to TrialList via TrialListID
    - TrialPlacements (trial placements) - linked to TrialClass via TrialClassID
    
    Returns True if any of these tables have data for this year.
    Note: CatalogEntry is NOT checked - that's for catalog entries only.
    Note: TrialResults table is NOT checked - trial results are inserted into TrialList, TrialClass, and TrialPlacements.
    """
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check TrialList table (trial results - parent table where trials are inserted)
        trial_list_processed = False
        try:
            table_check_query = """
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'TrialList'
            """
            cursor.execute(table_check_query)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                check_query = """
                    SELECT COUNT(*) FROM [sResults].[TrialList]
                    WHERE Year = ?
                """
                cursor.execute(check_query, year)
                count = cursor.fetchone()[0]
                trial_list_processed = count > 0
        except pyodbc.Error:
            # TrialList table doesn't exist or error - assume not processed
            trial_list_processed = False
        
        # Check TrialClass table (linked to TrialList)
        trial_class_processed = False
        try:
            table_check_query = """
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'TrialClass'
            """
            cursor.execute(table_check_query)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                # Join with TrialList to check Year
                check_query = """
                    SELECT COUNT(*) FROM [sResults].[TrialClass] tc
                    INNER JOIN [sResults].[TrialList] tl ON tc.TrialListID = tl.TrialListID
                    WHERE tl.Year = ?
                """
                cursor.execute(check_query, year)
                count = cursor.fetchone()[0]
                trial_class_processed = count > 0
        except pyodbc.Error:
            # TrialClass table doesn't exist or error - assume not processed
            trial_class_processed = False
        
        # Check TrialPlacements table (linked to TrialClass -> TrialList)
        trial_placements_processed = False
        try:
            table_check_query = """
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'sResults' AND TABLE_NAME = 'TrialPlacements'
            """
            cursor.execute(table_check_query)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                # Join through TrialClass to TrialList to check Year
                check_query = """
                    SELECT COUNT(*) FROM [sResults].[TrialPlacements] tp
                    INNER JOIN [sResults].[TrialClass] tc ON tp.TrialClassID = tc.TrialClassID
                    INNER JOIN [sResults].[TrialList] tl ON tc.TrialListID = tl.TrialListID
                    WHERE tl.Year = ?
                """
                cursor.execute(check_query, year)
                count = cursor.fetchone()[0]
                trial_placements_processed = count > 0
        except pyodbc.Error:
            # TrialPlacements table doesn't exist or error - assume not processed
            trial_placements_processed = False
        
        # Year is processed if any trial results tables have data for this year
        # (TrialList, TrialClass, or TrialPlacements - NOT CatalogEntry which is for catalog entries only)
        return trial_list_processed or trial_class_processed or trial_placements_processed
        
    except pyodbc.Error as e:
        # If there's an error (table doesn't exist, permission issue, etc.), 
        # assume year is not processed and continue
        if 'Invalid object name' in str(e) or '42S02' in str(e):
            # Table doesn't exist - this is fine, just means schema hasn't been created yet
            return False
        # For other errors, log a warning but assume not processed
        print(f"  Warning: Could not check if year {year} is processed: {e}")
        return False


def is_catalog_year_processed(conn: pyodbc.Connection, year: str) -> bool:
    """Check if catalog entries for this year are already loaded."""
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM [sResults].[CatalogEntry]
            WHERE Year = ?
            """,
            year,
        )
        return cursor.fetchone()[0] > 0
    except pyodbc.Error as e:
        if 'Invalid object name' in str(e) or '42S02' in str(e):
            return False
        print(f"  Warning: Could not check if catalog year {year} is processed: {e}")
        return False


def load_catalog_data(conn: Optional[pyodbc.Connection] = None, 
                     skip_years: Optional[Set[str]] = None,
                     auto_skip_processed: bool = False) -> tuple:
    """Load catalog data using parse_catalog.py logic and write incrementally to database.
    
    Args:
        conn: Database connection. If provided, data is written to database as each year is processed.
        skip_years: Set of years to skip (e.g., {'2020', '2021'}). If None, no years are skipped.
        auto_skip_processed: If True, automatically skip years that are already in the database.
    
    Returns:
        Tuple of (classes, dogs, relationships, years)
    """
    import glob
    import os
    import re
    
    print("=" * 80)
    print("FINDING CATALOG FILES")
    print("=" * 80)
    
    # Track IDs across all years if writing incrementally
    entity_ctx: Optional[CatalogEntityContext] = None
    if conn:
        division_name_to_id = {}
        section_name_to_id = {}
        class_name_to_id = {}
        all_merged_dogs = {}  # Track merged dogs across years
        all_relationships = {}  # Accumulate relationships
        print("Preloading existing dog+owner pairs from database (trial results)...")
        entity_ctx = preload_dogs_and_owners_from_db(conn)
        print(
            f"  Loaded {len(entity_ctx.db_dog_owner_records):,} dog+owner pairs, "
            f"{len(entity_ctx.owner_name_to_id):,} owners"
        )
    
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
        
        # Check if this year should be skipped
        should_skip = False
        skip_reason = None
        
        if skip_years and year in skip_years:
            should_skip = True
            skip_reason = "explicitly in skip_years"
        elif year.isdigit() and (
            int(year) < CATALOG_YEAR_MIN or int(year) > CATALOG_YEAR_MAX
        ):
            should_skip = True
            skip_reason = f"outside catalog year range {CATALOG_YEAR_MIN}-{CATALOG_YEAR_MAX}"
        elif auto_skip_processed and conn and is_catalog_year_processed(conn, year):
            should_skip = True
            skip_reason = "already processed in database"
        
        if should_skip:
            print(f"\n{'=' * 80}")
            print(f"Skipping {filepath} (Year: {year}) - {skip_reason}")
            print("=" * 80)
            continue
        
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
                                     entity_ctx,
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
                print(f"  Relationships for {len(new_relationships)} dogs written to database")
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
            print(f"  Final relationships written to database")
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


def load_trial_results_data(conn: Optional[pyodbc.Connection] = None,
                            skip_files: Optional[Set[str]] = None,
                            file_timeout: Optional[int] = None,
                            skip_years: Optional[Set[str]] = None) -> List[TrialResult]:
    """Load trial results data using scrape_trial_results.py logic.
    
    Args:
        conn: Database connection. If provided, results are written to database as each file is processed.
        skip_files: Set of filenames (basenames) to skip (e.g., {'Battleborn Bonanza IX.txt'})
        file_timeout: Maximum seconds to wait for a file to process before skipping (None = no timeout)
        skip_years: Set of years to skip (e.g., {'2020', '2021'}). If None, no years are skipped.
    
    Returns:
        List of TrialResult objects
    """
    print("Loading trial results data...")
    
    import re
    import time
    
    # Check for PDF support (matching scrape_trial_results.py logic)
    # Initialize both variables first to avoid NameError if PyPDF2 succeeds
    HAS_PYPDF2 = False
    HAS_PDFPLUMBER = False
    try:
        import PyPDF2
        HAS_PYPDF2 = True
    except ImportError:
        # Try pdfplumber as alternative
        try:
            import pdfplumber
            HAS_PDFPLUMBER = True
        except ImportError:
            pass
    
    # Scan local subfolders for trial result files (matching scrape_trial_results.py)
    print("Scanning local subfolders for trial result files...")
    local_files = scan_local_subfolders(".")
    print(f"Found {len(local_files)} local trial result files")
    
    all_results = []
    seen_trials = set()  # (trial_name, date) tuples for duplicate checking
    
    # If writing incrementally, set up tracking dictionaries
    if conn:
        trial_name_to_id = {}
        division_name_to_id = {}
        class_name_to_id = {}
        owner_name_to_id = {}
        dog_name_to_id = {}
        class_key_to_id = {}
    
    start_time = time.time()
    processed_count = 0
    
    # Initialize skip_files set if not provided
    if skip_files is None:
        skip_files = set()
    
    # Process local files first (matching scrape_trial_results.py logic exactly)
    for file_path, year, source_folder in local_files:
        # Check if this year should be skipped
        if skip_years and year in skip_years:
            print(f"  Skipping {os.path.basename(file_path)} from year {year} (in skip_years list)")
            continue
        
        # Check if this file should be skipped (populate_trialresults_database.py specific)
        file_basename = os.path.basename(file_path)
        if file_basename in skip_files:
            print(f"  Skipping {file_basename} (in skip list)")
            continue
        
        # Extract trial name and date from file to check for duplicates
        # This works for both text/HTML and PDF files (matching scrape_trial_results.py)
        trial_name = None
        date = ""
        
        # First, try to extract trial name from filename as a fallback
        filename_base = os.path.splitext(os.path.basename(file_path))[0]
        # Clean up filename (remove common prefixes, replace underscores with spaces)
        filename_trial_name = filename_base.replace('_', ' ').replace('-', ' ')
        filename_trial_name = re.sub(r'^(debug_trialvault_|debug_trial_|debug_)', '', filename_trial_name, flags=re.IGNORECASE)
        
        try:
            # For PDF files, extract text first
            content = None
            if file_path.lower().endswith('.pdf'):
                if HAS_PYPDF2 or HAS_PDFPLUMBER:
                    page_text = extract_text_from_pdf(file_path)
                    if page_text and page_text.strip():
                        # Read first 2000 chars to get trial name/date (PDFs may have more header text)
                        content = page_text[:2000]
                    else:
                        # PDF extraction returned empty - still process it via parse_local_trial_file
                        # which will handle PDF extraction internally
                        content = ""
                else:
                    print(f"  Skipping PDF {file_path}: No PDF library available")
                    continue
            else:
                # For text/HTML files, read normally
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)  # Read first 2000 chars to get trial name/date
            
            # Ensure content is set (should always be set by now, but safety check)
            if content is None:
                content = ""
            
            # Try to extract trial name and date
            trial_match = re.search(r'([A-Z][^0-9]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)?)', content)
            date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', content)
            trial_name = trial_match.group(1).strip() if trial_match else None
            date = date_match.group(1).strip() if date_match else ""
            
            # Validate trial name - skip if it contains HTML/JavaScript code markers
            if trial_name:
                if any(marker in trial_name for marker in ['/*', '*/', '<script', '</script>', 'function(', 'http://', 'https://', 'Dynamic Drive', 'DHTML', 'code library']):
                    trial_name = None  # Reject malformed trial name
            
            # If we didn't get trial name from content, try filename (but be more lenient)
            if not trial_name and filename_trial_name and len(filename_trial_name) > 3:
                # Use filename as trial name if it looks reasonable
                trial_name = filename_trial_name
            
            # Check for duplicates using trial name (from content or filename) and date
            # Also check using just the filename base (for cases where date extraction fails)
            if trial_name:
                # Check by trial name + date
                if date:
                    if is_duplicate_trial(trial_name, date, seen_trials):
                        print(f"  Skipping duplicate trial: {trial_name} ({date}) from {source_folder} ({file_basename})")
                        continue
                    seen_trials.add((normalize_name(trial_name), date))
                else:
                    # If no date, check by normalized filename (for files with same base name)
                    normalized_filename = normalize_name(filename_trial_name)
                    # Check if we've seen this filename before (without date)
                    filename_key = (normalized_filename, "")
                    if filename_key in seen_trials:
                        print(f"  Skipping duplicate trial (by filename): {trial_name} from {source_folder} ({file_basename})")
                        continue
                    seen_trials.add(filename_key)
        except Exception as e:
            print(f"  Warning: Could not check for duplicates in {file_path}: {e}")
            # Try filename-based duplicate check as fallback
            normalized_filename = normalize_name(filename_trial_name)
            filename_key = (normalized_filename, "")
            if filename_key in seen_trials:
                print(f"  Skipping duplicate trial (by filename): {filename_trial_name} from {source_folder} ({os.path.basename(file_path)})")
                continue
            seen_trials.add(filename_key)
        
        print(f"\nProcessing local file: {os.path.basename(file_path)} from {source_folder} ({year})")
        results, judges_info = parse_local_trial_file(file_path, year, source_folder)
        if results:
            # If we didn't get trial name/date from the preview, try to get it from results
            if not trial_name and results:
                trial_name = results[0].trial_name if results[0].trial_name else "Unknown Trial"
                date = results[0].date if results[0].date else ""
                if trial_name and date and trial_name != "Unknown Trial":
                    # Check again for duplicates with the extracted name/date
                    if is_duplicate_trial(trial_name, date, seen_trials):
                        print(f"  Skipping duplicate trial (from results): {trial_name} ({date}) from {source_folder} ({os.path.basename(file_path)})")
                        continue
                    # Add to seen_trials to prevent processing duplicate files
                    seen_trials.add((normalize_name(trial_name), date))
            
            # Store judge information for this trial (matching scrape_trial_results.py)
            # Note: In populate_trialresults_database.py, we write to database instead of collecting
            if conn:
                try:
                    populate_trial_results_data(conn, results, 
                                               trial_name_to_id, division_name_to_id,
                                               class_name_to_id, owner_name_to_id,
                                               dog_name_to_id, class_key_to_id)
                except Exception as e:
                    print(f"  Error writing to database: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            else:
                # Collect for later (matching scrape_trial_results.py behavior when no conn)
                all_results.extend(results)
            
            print(f"  Extracted {len(results)} results")
        
        processed_count += 1
    
    if conn:
        print(f"  Processed {len(local_files)} trial files (written incrementally)")
        return []  # Already written, return empty list
    else:
        print(f"  Loaded {len(all_results)} trial results total")
    return all_results


def main():
    """Main function to populate database.
    
    Command-line arguments:
        --skip-years YEAR1,YEAR2,...     : Skip processing these years for both catalog and trial results (comma-separated)
        --auto-skip-processed            : Automatically skip catalog years already in database
        --skip-catalog                   : Completely skip catalog entry processing (only process trial results)
        --skip-trial-files FILE1,FILE2   : Skip processing these trial files (comma-separated filenames)
        --trial-file-timeout SECONDS     : Maximum seconds to wait per trial file before skipping (prevents hangs)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate sResults schema tables')
    parser.add_argument('--skip-years', type=str, default=None,
                       help='Comma-separated list of catalog years to skip (e.g., "2020,2021,2022")')
    parser.add_argument('--auto-skip-processed', action='store_true',
                       help='Automatically skip catalog years that are already in the database')
    parser.add_argument('--skip-trial-files', type=str, default=None,
                       help='Comma-separated list of trial filenames to skip (e.g., "file1.txt,file2.html")')
    parser.add_argument('--trial-file-timeout', type=int, default=None,
                       help='Maximum seconds to wait for a trial file to process before skipping (default: no timeout)')
    parser.add_argument('--skip-catalog', action='store_true',
                       help='Completely skip catalog entry processing (only process trial results)')
    parser.add_argument('--clear-trialresults', action='store_true',
                       help='Clear existing trial results data (TrialPlacements, TrialClass, TrialList) before loading. By default, existing data is preserved.')
    args = parser.parse_args()
    
    # Parse skip_years if provided
    skip_years = None
    if args.skip_years:
        skip_years = set(year.strip() for year in args.skip_years.split(','))
        print(f"Will skip years (catalog and trial results): {', '.join(sorted(skip_years))}")
    
    if args.auto_skip_processed:
        print("Will automatically skip catalog years already in database")
    
    if args.skip_catalog:
        print("Will completely skip catalog entry processing")
    
    # Parse skip_trial_files if provided
    skip_trial_files = None
    if args.skip_trial_files:
        skip_trial_files = set(f.strip() for f in args.skip_trial_files.split(','))
        print(f"Will skip trial files: {', '.join(sorted(skip_trial_files))}")
    
    if args.trial_file_timeout:
        print(f"Trial file timeout: {args.trial_file_timeout} seconds per file")
    
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
        # Clear trial results tables only if --clear-trialresults is specified
        if args.clear_trialresults:
            clear_trial_results_tables(conn)
        else:
            print("\n" + "=" * 80)
            print("KEEPING EXISTING TRIAL RESULTS DATA")
            print("=" * 80)
            print("(Use --clear-trialresults to clear existing data)")
            print("=" * 80)
        
        # Load catalog data and write incrementally to database
        # Relationships are already written incrementally during load_catalog_data
        # Note: skip_years and auto_skip_processed only affect catalog processing
        if args.skip_catalog:
            print("\n" + "=" * 80)
            print("SKIPPING CATALOG PROCESSING")
            print("=" * 80)
            print("Catalog entry processing is disabled (--skip-catalog)")
            print("=" * 80)
            classes, dogs, relationships, years = {}, {}, {}, []
        else:
            classes, dogs, relationships, years = load_catalog_data(
                conn, 
                skip_years=skip_years,
                auto_skip_processed=args.auto_skip_processed
            )
        
        # Load trial results data and write incrementally to database
        # Always process ALL trial results files, regardless of catalog skip settings
        print("\n" + "=" * 80)
        print("PROCESSING TRIAL RESULTS")
        print("=" * 80)
        if skip_years:
            print(f"Note: Skipping years: {', '.join(sorted(skip_years))}")
        else:
            print("Note: Processing ALL trial results files for all years")
        print("=" * 80)
        trial_results = load_trial_results_data(conn, 
                                                skip_files=skip_trial_files,
                                                file_timeout=args.trial_file_timeout,
                                                skip_years=skip_years)
        
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

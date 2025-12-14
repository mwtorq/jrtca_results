#!/usr/bin/env python3
"""
Populate sResults schema tables in TrialResults database with data from catalog and trial results.
Uses the logic from parse_catalog.py and scrape_trial_results.py to extract and insert all data.
"""

import pyodbc
import sys
import os
from typing import List, Dict, Optional, Set
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
    """Get existing ID or create new record and return ID."""
    if not name or not name.strip():
        return None
    
    if id_column is None:
        id_column = table.rstrip('s') + 'ID'  # e.g., Division -> DivisionID
    
    # Try to find existing record
    query = f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?"
    cursor.execute(query, name.strip())
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Create new record
    if create_columns is None:
        create_columns = {name_column: name.strip()}
    else:
        create_columns = create_columns.copy()
        create_columns[name_column] = name.strip()
    
    columns = ", ".join([f"[{k}]" for k in create_columns.keys()])
    placeholders = ", ".join(["?" for _ in create_columns])
    values = list(create_columns.values())
    
    insert_query = f"INSERT INTO [sResults].[{table}] ({columns}) VALUES ({placeholders})"
    cursor.execute(insert_query, *values)
    
    # Get the generated ID
    cursor.execute(f"SELECT [{id_column}] FROM [sResults].[{table}] WHERE [{name_column}] = ?", name.strip())
    row = cursor.fetchone()
    if row:
        return row[0]
    return None


def populate_catalog_data(conn: pyodbc.Connection, classes: Dict[str, ClassInfo], 
                         dogs: Dict[str, Dog], years: List[str]):
    """Populate catalog data into database."""
    print("\nPopulating catalog data...")
    cursor = conn.cursor()
    
    try:
        # Track inserted dogs and owners to avoid duplicates
        dog_name_to_id = {}
        owner_name_to_id = {}
        division_name_to_id = {}
        class_name_to_id = {}  # (normalized_class_name, div_id, section) -> class_id
        
        # Process divisions and classes first
        print("  Processing divisions and classes...")
        for class_key, class_info in classes.items():
            # Get or create division
            if class_info.division:
                div_id = division_name_to_id.get(class_info.division)
                if div_id is None:
                    div_id = get_or_create_id(cursor, 'Division', 'DivisionName', 
                                             normalize_division_name(class_info.division))
                    if div_id:
                        division_name_to_id[class_info.division] = div_id
                
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
                                'Section': class_info.section
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


def populate_relationships(conn: pyodbc.Connection, relationships: Dict[str, List[str]], dogs: Dict[str, Dog]):
    """Populate relationship data into database."""
    print("\nPopulating relationship data...")
    cursor = conn.cursor()
    
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
        
        # Track processed relationships to avoid duplicates
        processed_relationships = set()
        
        relationship_count = 0
        
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
                
                # Create unique key for this relationship to avoid duplicates
                rel_key = (dog_id, relationship_type, related_dog_name, via_dog_name)
                if rel_key in processed_relationships:
                    continue
                processed_relationships.add(rel_key)
                
                # Check if relationship already exists in database
                check_query = """
                    SELECT RelationshipID FROM [sResults].[Relationship]
                    WHERE DogID = ? AND RelationshipType = ? AND RelatedDogName = ?
                """
                if via_dog_name:
                    check_query += " AND ViaDogName = ?"
                else:
                    check_query += " AND ViaDogName IS NULL"
                
                check_params = [dog_id, relationship_type, related_dog_name]
                if via_dog_name:
                    check_params.append(via_dog_name)
                
                cursor.execute(check_query, *check_params)
                if cursor.fetchone():
                    continue  # Already exists
                
                # Insert relationship
                insert_query = """
                    INSERT INTO [sResults].[Relationship]
                    (DogID, RelatedDogID, RelatedDogName, RelationshipType, ViaDogName, RelatedDogSex)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query,
                             dog_id,
                             related_dog_id,
                             related_dog_name,
                             relationship_type,
                             via_dog_name,
                             related_dog_sex)
                
                relationship_count += 1
        
        conn.commit()
        print(f"  Relationships populated: {relationship_count} relationships")
        
    except Exception as e:
        print(f"  ERROR populating relationships: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def populate_relationships(conn: pyodbc.Connection, relationships: Dict[str, List[str]], dogs: Dict[str, Dog]):
    """Populate relationship data into database."""
    print("\nPopulating relationship data...")
    cursor = conn.cursor()
    
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
        
        # Track processed relationships to avoid duplicates
        processed_relationships = set()
        
        relationship_count = 0
        
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
                
                # Create unique key for this relationship to avoid duplicates
                rel_key = (dog_id, relationship_type, related_dog_name, via_dog_name)
                if rel_key in processed_relationships:
                    continue
                processed_relationships.add(rel_key)
                
                # Check if relationship already exists in database
                check_query = """
                    SELECT RelationshipID FROM [sResults].[Relationship]
                    WHERE DogID = ? AND RelationshipType = ? AND RelatedDogName = ?
                """
                if via_dog_name:
                    check_query += " AND ViaDogName = ?"
                else:
                    check_query += " AND ViaDogName IS NULL"
                
                check_params = [dog_id, relationship_type, related_dog_name]
                if via_dog_name:
                    check_params.append(via_dog_name)
                
                cursor.execute(check_query, *check_params)
                if cursor.fetchone():
                    continue  # Already exists
                
                # Insert relationship
                insert_query = """
                    INSERT INTO [sResults].[Relationship]
                    (DogID, RelatedDogID, RelatedDogName, RelationshipType, ViaDogName, RelatedDogSex)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query,
                             dog_id,
                             related_dog_id,
                             related_dog_name,
                             relationship_type,
                             via_dog_name,
                             related_dog_sex)
                
                relationship_count += 1
        
        conn.commit()
        print(f"  Relationships populated: {relationship_count} relationships")
        
    except Exception as e:
        print(f"  ERROR populating relationships: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def populate_trial_results_data(conn: pyodbc.Connection, trial_results: List[TrialResult]):
    """Populate trial results data into database."""
    print("\nPopulating trial results data...")
    cursor = conn.cursor()
    
    try:
        # Track inserted records
        trial_name_to_id = {}
        owner_name_to_id = {}
        division_name_to_id = {}
        class_name_to_id = {}  # (normalized_class_name, div_id, section) -> class_id
        class_key_to_id = {}  # (trial_id, class_id, class_number) -> trialclass_id
        dog_name_to_id = {}
        
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
                if division:
                    div_id = division_name_to_id.get(division)
                    if div_id is None:
                        div_id = get_or_create_id(cursor, 'Division', 'DivisionName', division)
                        if div_id:
                            division_name_to_id[division] = div_id
                
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
                                'Section': result.section
                            }
                        )
                        if class_id:
                            class_name_to_id[class_lookup_key] = class_id
                
                # Group by class for this trial
                if class_id:
                    class_key = (trial_id, class_id, result.class_number)
                    by_class[class_key].append(result)
            
            conn.commit()
            
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
                    
                    # Get generated ID
                    cursor.execute("""
                        SELECT TrialClassID FROM [sResults].[TrialClass]
                        WHERE TrialListID = ? AND ClassID = ? AND ClassNumber = ?
                    """, trial_id, class_id, class_number)
                    row = cursor.fetchone()
                    if row:
                        trialclass_id = row[0]
                        class_key_to_id[trialclass_key] = trialclass_id
                
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
                    insert_query = """
                        INSERT INTO [sResults].[TrialPlacements]
                        (TrialClassID, DogID, DogName, Result, OwnerID)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, trialclass_id, dog_id, result.dog_name, 
                                 result.placement, owner_id)
            
            conn.commit()
        
        print(f"  Trial results populated: {len(trial_results)} results, {len(by_trial)} trials")
        
    except Exception as e:
        print(f"  ERROR populating trial results: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise


def load_catalog_data() -> tuple:
    """Load catalog data using parse_catalog.py logic - same as main() function."""
    import glob
    import os
    import re
    
    print("=" * 80)
    print("FINDING CATALOG FILES")
    print("=" * 80)
    
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
    
    for filepath in catalog_files:
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
        
        # Store classes and dogs by year
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


def load_trial_results_data() -> List[TrialResult]:
    """Load trial results data using scrape_trial_results.py logic."""
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
            
            all_results.extend(results)
            if results:
                print(f"      Extracted {len(results)} results")
            
        except Exception as e:
            print(f"    Error processing {filepath}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
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
        # Load catalog data
        classes, dogs, relationships, years = load_catalog_data()
        
        # Load trial results data
        trial_results = load_trial_results_data()
        
        # Populate database
        if classes or dogs:
            populate_catalog_data(conn, classes, dogs, years)
            if relationships:
                populate_relationships(conn, relationships, dogs)
        
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

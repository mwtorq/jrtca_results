#!/usr/bin/env python3
"""Test script to find relationships for Cairnbrae Minx"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from parse_catalog import parse_catalog, find_relationships, normalize_name, merge_dogs_across_years, extract_text_from_file
import glob
import re

def extract_year_from_filename(filename):
    """Extract year from filename like '2009_Entries_Catalog.doc'"""
    match = re.search(r'(\d{4})', filename)
    return match.group(1) if match else None

# Find all extracted text files (preferred) or catalog files
extracted_files = sorted(glob.glob('extracted_text_*.txt'))
catalog_files = sorted(glob.glob("*Entries_Catalog*.doc") + glob.glob("*Entries_Catalog*.pdf") + 
                      glob.glob("*entries_catalog*.doc") + glob.glob("*entries_catalog*.pdf") + 
                      glob.glob("*Catalog*.pdf") + glob.glob("*catalog*.pdf"))

print(f"Found {len(extracted_files)} extracted text file(s)")
print(f"Found {len(catalog_files)} catalog file(s)")

# Parse all files - structure by year for merge_dogs_across_years
all_dogs_by_year = {}
all_classes = {}
years_processed = set()

# Process extracted text files first
for filepath in extracted_files:
    year = extract_year_from_filename(filepath)
    if year:
        years_processed.add(year)
        print(f"Parsing {filepath} (year: {year})...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            if len(text) > 1000:  # Only process substantial files
                classes, dogs = parse_catalog(text, year)  # Pass text and year, not filepath
                all_classes.update(classes)
                all_dogs_by_year[year] = dogs  # Store by year
                print(f"  Parsed {len(classes)} classes, {len(dogs)} dogs")
        except Exception as e:
            print(f"  Error parsing {filepath}: {e}")
            import traceback
            traceback.print_exc()

# Process catalog files for years not yet processed
for filepath in catalog_files:
    year = extract_year_from_filename(filepath)
    if year and year not in years_processed:
        print(f"Extracting and parsing {filepath} (year: {year})...")
        try:
            text = extract_text_from_file(filepath)
            if len(text) > 1000:
                classes, dogs = parse_catalog(text, year)  # Pass text and year, not filepath
                all_classes.update(classes)
                all_dogs_by_year[year] = dogs  # Store by year
                print(f"  Parsed {len(classes)} classes, {len(dogs)} dogs")
        except Exception as e:
            print(f"  Error processing {filepath}: {e}")
            import traceback
            traceback.print_exc()

total_dogs_before_merge = sum(len(dogs) for dogs in all_dogs_by_year.values())
print(f"\nTotal dogs parsed (before merge): {total_dogs_before_merge} across {len(all_dogs_by_year)} years")

# Merge dogs across years
print("Merging dogs across years...")
merged_dogs = merge_dogs_across_years(all_dogs_by_year)
print(f"After merging: {len(merged_dogs)} unique dogs")

# Find Cairnbrae Minx
target = 'Cairnbrae Minx'
normalized = normalize_name(target)

matching_keys = []
for k in merged_dogs.keys():
    if normalize_name(k) == normalized or normalize_name(merged_dogs[k].name) == normalized:
        matching_keys.append(k)

if not matching_keys:
    print(f"\nERROR: Could not find {target} in catalog files")
    print("Trying partial matches...")
    for k in merged_dogs.keys():
        if 'minx' in normalize_name(merged_dogs[k].name).lower():
            print(f"  Found: {merged_dogs[k].name}")
    sys.exit(1)

print(f"\nFound {len(matching_keys)} entry(ies) for {target}:")
for key in matching_keys:
    dog = merged_dogs[key]
    print(f"  Key: {key}")
    print(f"  Name: {dog.name}")
    print(f"  Sire: {dog.sire}")
    print(f"  Dam: {dog.dam}")
    print(f"  Sex: {dog.sex}")

# Use first matching key
canonical_key = matching_keys[0]
print(f"\nUsing canonical key: {canonical_key}")

# Find relationships
print("\nFinding relationships...")
relationships = find_relationships(merged_dogs)

if canonical_key in relationships:
    rels = relationships[canonical_key]
    print(f"\nFound {len(rels)} relationship(s) for {target}:")
    
    # Group by relationship type
    by_type = {}
    for rel in rels:
        rel_type = rel.split(':')[0].strip()
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel)
    
    # Print summary
    print("\nRelationship Summary:")
    for rel_type in sorted(by_type.keys()):
        print(f"  {rel_type}: {len(by_type[rel_type])}")
    
    # Print detailed relationships grouped by type
    print("\nDetailed Relationships:")
    for rel_type in sorted(by_type.keys()):
        print(f"\n{rel_type} ({len(by_type[rel_type])}):")
        for rel in sorted(by_type[rel_type]):
            print(f"  - {rel}")
else:
    print(f"\nNo relationships found for {target}")





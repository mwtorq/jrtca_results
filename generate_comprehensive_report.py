#!/usr/bin/env python3
"""
Comprehensive report generator that combines catalog data and trial results.

This script:
1. Optionally generates catalog data (parse_catalog.py functionality)
2. Optionally generates trial results (scrape_trial_results.py functionality)
3. Correlates dog and family information from both sources
4. Generates a unified comprehensive report

Usage:
    python generate_comprehensive_report.py [--regenerate-catalog] [--regenerate-trials] [--regenerate-all]
    
Options:
    --regenerate-catalog    Force regeneration of catalog report (Entries_Catalog_Report_*.txt)
    --regenerate-trials     Force regeneration of trial results report (Trial_Results_Report.txt)
    --regenerate-all        Force regeneration of both reports
"""

import sys
import os
import argparse
import glob
import re
from typing import Dict, List, Optional
from collections import defaultdict

# Import from parse_catalog.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from parse_catalog import (
        Dog, ClassInfo, normalize_name, names_are_similar,
        find_relationships, merge_dogs_across_years,
        infer_sex_from_relationships, generate_report as generate_catalog_report,
        extract_year_from_filename, parse_catalog, extract_text_from_doc,
        infer_sex_from_classes
    )
    import parse_catalog as catalog_module
except ImportError as e:
    print(f"ERROR: Could not import from parse_catalog.py: {e}")
    print("Make sure parse_catalog.py is in the same directory.")
    sys.exit(1)

# Import from scrape_trial_results.py
try:
    from scrape_trial_results import (
        TrialResult, get_page, find_trial_result_links,
        parse_trial_results_page, parse_local_trial_file,
        scan_local_subfolders, generate_trial_results_report,
        extract_text_from_pdf, parse_individual_trial_page_content
    )
    import scrape_trial_results as trial_module
except ImportError as e:
    print(f"ERROR: Could not import from scrape_trial_results.py: {e}")
    print("Make sure scrape_trial_results.py is in the same directory.")
    sys.exit(1)


def parse_catalog_report(report_file: str) -> tuple[Dict[str, ClassInfo], Dict[str, Dog], Dict[str, List[str]], List[str]]:
    """
    Parse an existing catalog report file to extract data structures.
    
    Args:
        report_file: Path to the catalog report file
    
    Returns:
        Tuple of (classes, dogs, relationships, years_processed)
    """
    print(f"Parsing existing catalog report: {report_file}")
    
    classes: Dict[str, ClassInfo] = {}
    dogs: Dict[str, Dog] = {}
    relationships: Dict[str, List[str]] = {}
    years_processed = []
    
    try:
        print(f"  Reading file...")
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"  Read {len(content):,} characters")
    except Exception as e:
        print(f"Error reading catalog report: {e}")
        return {}, {}, {}, []
    
    lines = content.split('\n')
    print(f"  Processing {len(lines):,} lines...")
    print(f"  Total lines in report: {len(lines):,}")
    
    # Extract years from header
    year_match = re.search(r'\(([^)]+)\)', lines[1] if len(lines) > 1 else "")
    if year_match:
        years_str = year_match.group(1)
        years_processed = [y.strip() for y in years_str.split(',')]
        print(f"  Years found: {', '.join(years_processed)}")
    
    # Parse dogs from "DOGS BY CLASS ENTRY" section
    in_dogs_section = False
    current_dog = None
    current_dog_name = None
    dogs_parsed = 0
    
    print("  Parsing dogs from catalog report...")
    for i, line in enumerate(lines):
        if i > 0 and i % 10000 == 0:
            print(f"    Processed {i:,}/{len(lines):,} lines ({100*i//len(lines)}%)... {dogs_parsed} dogs found so far")
        line_stripped = line.strip()
        
        # Check if we're in the dogs section
        if "DOGS BY CLASS ENTRY" in line:
            in_dogs_section = True
            continue
        
        if not in_dogs_section:
            continue
        
        # Check if we've moved to relationships section
        if "FAMILY RELATIONSHIPS" in line:
            break
        
        # Dog name line (starts with dog name, no indentation)
        if line_stripped and not line_stripped.startswith(' ') and not line_stripped.startswith('\t'):
            # Check if it's a dog name (not a section header)
            if (not line_stripped.startswith('=') and 
                not line_stripped.startswith('-') and
                ':' not in line_stripped[:50] and
                len(line_stripped) > 2):
                # This is a dog name
                current_dog_name = line_stripped
                dog_normalized = normalize_name(current_dog_name)
                
                if dog_normalized not in dogs:
                    current_dog = Dog(
                        number="",  # Not in this format
                        name=current_dog_name,
                        sex=None,
                        sire=None,
                        dam=None,
                        owner=None,
                        classes=[]
                    )
                    dogs[dog_normalized] = current_dog
                    dogs_parsed += 1
                    if dogs_parsed % 100 == 0:
                        print(f"    Parsed {dogs_parsed} dogs...")
                else:
                    current_dog = dogs[dog_normalized]
        
        # Parse dog attributes
        if current_dog and line_stripped.startswith('  '):
            if line_stripped.startswith('  Sex:'):
                sex = line_stripped.replace('  Sex:', '').strip()
                if sex != 'unknown':
                    current_dog.sex = sex
            elif line_stripped.startswith('  Sire:'):
                sire = line_stripped.replace('  Sire:', '').strip()
                current_dog.sire = sire
            elif line_stripped.startswith('  Dam:'):
                dam = line_stripped.replace('  Dam:', '').strip()
                current_dog.dam = dam
            elif line_stripped.startswith('  Owner:'):
                owner = line_stripped.replace('  Owner:', '').strip()
                current_dog.owner = owner
            elif line_stripped.startswith('  Classes entered:'):
                classes_str = line_stripped.replace('  Classes entered:', '').strip()
                if classes_str != 'None':
                    # Parse class entries like "Class 1: Name (2008), Class 2: Name (2009)"
                    class_entries = [c.strip() for c in classes_str.split(',')]
                    for class_entry in class_entries:
                        # Extract class name and year
                        year_match = re.search(r'\((\d{4})\)', class_entry)
                        if year_match:
                            year = year_match.group(1)
                            class_name = class_entry[:class_entry.rfind('(')].strip()
                            current_dog.classes.append((class_name, year))
    
    print(f"  Finished parsing dogs section: {len(dogs)} unique dogs found")
    
    # Parse relationships from "FAMILY RELATIONSHIPS" section
    in_relationships_section = False
    current_relationship_dog = None
    relationships_parsed = 0
    
    print("  Parsing relationships from catalog report...")
    for i, line in enumerate(lines):
        if i > 0 and i % 10000 == 0:
            print(f"    Processed {i:,}/{len(lines):,} lines ({100*i//len(lines)}%)... {relationships_parsed} relationships found so far")
        line_stripped = line.strip()
        
        if "FAMILY RELATIONSHIPS" in line:
            in_relationships_section = True
            continue
        
        if not in_relationships_section:
            continue
        
        # Dog name line (starts with dog name, no indentation, may have sex/owner info)
        if line_stripped and not line_stripped.startswith('  ') and not line_stripped.startswith('-'):
            if (not line_stripped.startswith('=') and 
                not line_stripped.startswith('No family') and
                ':' not in line_stripped[:30]):  # Dog name shouldn't have colon early
                # Extract dog name (may have " (sex) - Owner: ..." suffix)
                dog_name = line_stripped
                if ' (' in dog_name:
                    dog_name = dog_name[:dog_name.index(' (')]
                if ' - Owner:' in dog_name:
                    dog_name = dog_name[:dog_name.index(' - Owner:')]
                
                current_relationship_dog = normalize_name(dog_name)
                if current_relationship_dog not in relationships:
                    relationships[current_relationship_dog] = []
        
        # Relationship line (starts with "  - ")
        if current_relationship_dog and line_stripped.startswith('  - '):
            rel = line_stripped.replace('  - ', '').strip()
            if rel:
                relationships[current_relationship_dog].append(rel)
                relationships_parsed += 1
    
    print(f"  Completed parsing:")
    print(f"    - {len(dogs):,} dogs found")
    print(f"    - {len(relationships):,} dogs with relationships")
    print(f"    - {sum(len(rels) for rels in relationships.values()):,} total relationships")
    print(f"    - Years: {', '.join(years_processed) if years_processed else 'Unknown'}")
    return classes, dogs, relationships, years_processed


def parse_trial_results_report(report_file: str) -> List[TrialResult]:
    """
    Parse an existing trial results report file to extract trial results.
    
    Args:
        report_file: Path to the trial results report file
    
    Returns:
        List of TrialResult objects
    """
    print(f"Parsing existing trial results report: {report_file}")
    
    results = []
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading trial results report: {e}")
        return []
    
    lines = content.split('\n')
    print(f"  Total lines in report: {len(lines):,}")
    
    # Parse trial results from "TRIAL RESULTS BY YEAR" section
    in_trials_section = False
    current_year = None
    current_trial_name = None
    current_trial_date = None
    current_class_name = None
    current_class_number = None
    results_parsed = 0
    
    print("  Parsing trial results from report...")
    for i, line in enumerate(lines):
        if i > 0 and i % 50000 == 0:
            print(f"    Processed {i:,}/{len(lines):,} lines ({100*i//len(lines)}%)... {results_parsed:,} results found so far")
        line_stripped = line.strip()
        
        # Check if we're in the trials section
        if "TRIAL RESULTS BY YEAR" in line:
            in_trials_section = True
            continue
        
        if not in_trials_section:
            continue
        
        # Check if we've moved to results by dog section
        if "RESULTS SUMMARY BY DOG" in line:
            break
        
        # Year header
        if line_stripped.startswith("YEAR "):
            year_match = re.search(r'YEAR (\d{4})', line_stripped)
            if year_match:
                current_year = year_match.group(1)
            continue
        
        # Trial name (indented with 2 spaces, may have "Main Page: " prefix or other prefixes)
        # Check original line for indentation, not stripped version
        if line.startswith('  ') and not line.startswith('    '):
            line_stripped = line.strip()
            # Check if it's a trial name (not "Date:" or "Results:")
            if (not line_stripped.startswith('Date:') and 
                not line_stripped.startswith('Results:')):
                # Extract trial name, removing prefixes like "Main Page: "
                trial_name = line_stripped
                # Remove common prefixes
                for prefix in ['Main Page: ', 'Trial: ']:
                    if trial_name.startswith(prefix):
                        trial_name = trial_name[len(prefix):].strip()
                if trial_name:  # Only set if we have a name
                    current_trial_name = trial_name
                    current_trial_date = None
                    current_class_name = None
                    current_class_number = None
        
        # Trial date (4 spaces indentation)
        if line.startswith('    ') and line_stripped.startswith('Date:'):
            date_str = line_stripped.replace('Date:', '').strip()
            current_trial_date = date_str
            continue
        
        # Class name (6 spaces indentation)
        if line.startswith('      ') and line_stripped.startswith('Class:'):
            class_str = line_stripped.replace('Class:', '').strip()
            # Extract class number if present
            class_num_match = re.search(r'Class\s+(\d+):', class_str)
            if class_num_match:
                current_class_number = int(class_num_match.group(1))
            else:
                current_class_number = None
            current_class_name = class_str
            continue
        
        # Result line (placement: dog name - Owner: owner)
        # Results are indented with 8 spaces (2 levels of 4 spaces)
        # Check original line for indentation
        if line.startswith('        ') and ':' in line_stripped:
            # Format: "1st: Dog Name - Owner: Owner Name" or "Best: Dog Name - Owner: Owner Name"
            # Also handle "Best: Dog Name, owned by Owner Name" format
            parts = line_stripped.split(':', 1)
            if len(parts) == 2:
                placement = parts[0].strip()
                rest = parts[1].strip()
                
                # Extract dog name and owner
                dog_name = None
                owner = None
                
                # Handle " - Owner:" format
                if ' - Owner:' in rest:
                    dog_name = rest[:rest.index(' - Owner:')].strip()
                    owner = rest[rest.index(' - Owner:') + len(' - Owner:'):].strip()
                # Handle ", owned by" format (from "Best:" lines)
                elif ', owned by ' in rest:
                    dog_name = rest[:rest.index(', owned by ')].strip()
                    owner = rest[rest.index(', owned by ') + len(', owned by '):].strip()
                else:
                    dog_name = rest.strip()
                
                # Only add if we have a dog name and context
                if dog_name and len(dog_name) > 1 and current_trial_name and current_year:
                    result = TrialResult(
                        trial_name=current_trial_name,
                        date=current_trial_date or "",
                        year=current_year,
                        class_name=current_class_name,
                        class_number=current_class_number,
                        placement=placement,
                        dog_name=dog_name,
                        owner=owner
                    )
                    results.append(result)
                    results_parsed += 1
                    if results_parsed % 10000 == 0:
                        print(f"    Parsed {results_parsed:,} trial results...")
    
    print(f"  Completed parsing:")
    print(f"    - {len(results):,} trial results found")
    if len(results) > 0:
        # Show some statistics
        unique_trials = len(set(r.trial_name for r in results if r.trial_name))
        unique_dogs = len(set(r.dog_name for r in results if r.dog_name))
        years_found = sorted(set(r.year for r in results if r.year))
        print(f"    - {unique_trials:,} unique trials")
        print(f"    - {unique_dogs:,} unique dogs")
        print(f"    - Years: {', '.join(years_found[:10])}{'...' if len(years_found) > 10 else ''}")
    else:
        print("  WARNING: No results parsed. Checking first few lines...")
        # Debug: show first 50 lines to understand format
        for i, line in enumerate(lines[:50]):
            if "TRIAL RESULTS BY YEAR" in line or i >= 12:  # Start from section
                print(f"    Line {i}: {repr(line[:100])}")
    return results


def run_catalog_processing(regenerate: bool = False) -> tuple[Dict[str, ClassInfo], Dict[str, Dog], Dict[str, List[str]], List[str]]:
    """
    Run catalog processing (parse_catalog.py functionality).
    
    Args:
        regenerate: If True, force regeneration even if output file exists
    
    Returns:
        Tuple of (classes, dogs, relationships, years_processed)
    """
    print("=" * 80)
    print("PROCESSING CATALOG DATA")
    print("=" * 80)
    print()
    
    # Check if catalog report already exists
    catalog_files = glob.glob("Entries_Catalog_Report*.txt")
    skip_report_generation = False
    if catalog_files and not regenerate:
        print(f"Catalog report already exists: {catalog_files[0]}")
        print("Parsing existing catalog report instead of processing .doc files...")
        print()
        # Try to parse the existing report
        classes, dogs, relationships, years = parse_catalog_report(catalog_files[0])
        if dogs:  # If we successfully parsed data
            print(f"Successfully loaded {len(dogs)} dogs from existing catalog report.")
            return classes, dogs, relationships, years
        else:
            print("Warning: Could not parse existing report. Will process .doc files instead.")
            print()
    
    # Run catalog processing by calling the main function logic
    # We'll extract the core logic from parse_catalog.py's main()
    import glob as glob_module
    
    catalog_doc_files = sorted(glob_module.glob("*Entries_Catalog*.doc"))
    
    if not catalog_doc_files:
        print("No catalog files found. Looking for files matching *Entries_Catalog*.doc")
        return {}, {}, {}, []
    
    print(f"Found {len(catalog_doc_files)} catalog file(s): {', '.join(catalog_doc_files)}")
    
    all_classes: Dict[str, ClassInfo] = {}
    all_dogs_by_year: Dict[str, Dict[str, Dog]] = {}
    years_processed = []
    
    for filepath in catalog_doc_files:
        year = extract_year_from_filename(filepath)
        years_processed.append(year)
        
        print(f"\n{'=' * 80}")
        print(f"Processing {filepath} (Year: {year})")
        print("=" * 80)
        
        extracted_text_file = f"extracted_text_{year}.txt"
        
        # Try to use existing extracted text file first (unless regenerating)
        text = None
        if os.path.exists(extracted_text_file) and not regenerate:
            try:
                file_size = os.path.getsize(extracted_text_file)
                if file_size > 1000:
                    print(f"Reading from existing {extracted_text_file} ({file_size} bytes)...")
                    with open(extracted_text_file, "r", encoding="utf-8") as f:
                        text = f.read()
                    print(f"Read {len(text)} characters of text.")
                else:
                    print(f"Existing {extracted_text_file} is too small. Re-extracting...")
                    text = None
            except Exception as e:
                print(f"Error reading {extracted_text_file}: {e}. Re-extracting...")
                text = None
        elif regenerate:
            print(f"Regenerating: will re-extract from .doc file (ignoring {extracted_text_file} if it exists)...")
        else:
            print(f"No cached extracted text file found. Will extract from .doc file...")
        
        if not text:
            print(f"Extracting text from {filepath}...")
            try:
                text = extract_text_from_doc(filepath)
                print(f"Extracted {len(text)} characters of text.")
            except Exception as e:
                print(f"Error extracting text: {e}")
                print("Skipping this file...")
                continue
            
            # Save extracted text
            if text and len(text) > 0:
                try:
                    with open(extracted_text_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"Saved extracted text to {extracted_text_file}")
                except Exception as e:
                    print(f"Error saving extracted text: {e}")
        
        if not text or len(text) < 100:
            print(f"WARNING: Text is empty or too short. Skipping...")
            continue
        
        print(f"Parsing catalog for year {year}...")
        try:
            classes, dogs = parse_catalog(text, year)
            print(f"Found {len(classes)} classes and {len(dogs)} dogs for {year}.")
        except Exception as e:
            print(f"Error parsing catalog for {year}: {e}")
            import traceback
            traceback.print_exc()
            print("Skipping this file...")
            continue
        
        all_classes.update(classes)
        all_dogs_by_year[year] = dogs
    
    if not all_dogs_by_year:
        print("No catalog files processed.")
        return {}, {}, {}, []
    
    print(f"\n{'=' * 80}")
    print("Merging dogs across years and inferring sex...")
    print("=" * 80)
    
    # Merge dogs across years
    merged_dogs = merge_dogs_across_years(all_dogs_by_year)
    print(f"Total unique dogs after merging: {len(merged_dogs)}")
    
    # Infer sex from relationships
    print("\nInferring sex from relationships...")
    max_iterations = 10
    for iteration in range(max_iterations):
        updated_count = infer_sex_from_relationships(merged_dogs)
        if updated_count == 0:
            break
        print(f"  Iteration {iteration + 1}: Updated sex for {updated_count} dogs")
    
    # Update class entries to reference merged dogs
    print("\nUpdating class entries to use merged dogs...")
    for class_key, class_info in all_classes.items():
        updated_entries = []
        for dog in class_info.entries:
            dog_normalized_name = normalize_name(dog.name)
            if dog_normalized_name in merged_dogs:
                updated_entries.append(merged_dogs[dog_normalized_name])
            else:
                updated_entries.append(dog)
        class_info.entries = updated_entries
    
    print("\nFinding relationships...")
    relationships = find_relationships(merged_dogs)
    
    # Re-infer sex after finding relationships
    print("\nRe-inferring sex from relationships after relationship finding...")
    for iteration in range(max_iterations):
        updated_count = infer_sex_from_relationships(merged_dogs)
        if updated_count == 0:
            break
        print(f"  Iteration {iteration + 1}: Updated sex for {updated_count} dogs")
    
    # Final update of class entries
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
    
    # Generate and save catalog report (unless skipping)
    if not skip_report_generation:
        print("\nGenerating catalog report...")
        catalog_report = generate_catalog_report(all_classes, merged_dogs, relationships, years_processed)
        
        output_file = "Entries_Catalog_Report.txt"
        if years_processed:
            years_str = "_".join(sorted(years_processed))
            output_file = f"Entries_Catalog_Report_{years_str}.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(catalog_report)
        
        print(f"Catalog report saved to {output_file}")
    else:
        print("\nSkipping catalog report generation (report already exists).")
    
    return all_classes, merged_dogs, relationships, years_processed


def run_trial_results_processing(regenerate: bool = False) -> List[TrialResult]:
    """
    Run trial results processing (scrape_trial_results.py functionality).
    
    Args:
        regenerate: If True, force regeneration even if output file exists
    
    Returns:
        List of TrialResult objects
    """
    print("=" * 80)
    print("PROCESSING TRIAL RESULTS")
    print("=" * 80)
    print()
    
    # Check if trial results report already exists
    trial_report_file = "Trial_Results_Report.txt"
    skip_report_generation = False
    if os.path.exists(trial_report_file) and not regenerate:
        print(f"Trial results report already exists: {trial_report_file}")
        print("Parsing existing trial results report instead of processing files...")
        print()
        # Try to parse the existing report
        trial_results = parse_trial_results_report(trial_report_file)
        if trial_results:  # If we successfully parsed data
            print(f"Successfully loaded {len(trial_results)} trial results from existing report.")
            # Still generate the report if needed, but we have the data
            return trial_results
        else:
            print("Warning: Could not parse existing report. Will process trial files instead.")
            print()
    
    # Check if requests library is available
    try:
        import requests
        from bs4 import BeautifulSoup
        HAS_REQUESTS = True
    except ImportError:
        HAS_REQUESTS = False
        print("WARNING: requests library not available. Web scraping will be skipped.")
        print("Only local files will be processed.")
    
    all_trial_results = []
    
    # Track processed URLs and trials to avoid duplicates
    processed_urls = set()
    seen_trials = set()
    
    # First, scan and process local subfolders
    print("Scanning local subfolders for trial result files...")
    local_files = scan_local_subfolders(".")
    print(f"Found {len(local_files)} local trial result files")
    
    # Process local files
    for file_path, year, source_folder in local_files:
        trial_name = None
        date = ""
        
        try:
            # For PDF files, extract text first
            if file_path.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    HAS_PYPDF2 = True
                except ImportError:
                    try:
                        import pdfplumber
                        HAS_PDFPLUMBER = True
                        HAS_PYPDF2 = False
                    except ImportError:
                        HAS_PDFPLUMBER = False
                        HAS_PYPDF2 = False
                
                if HAS_PYPDF2 or HAS_PDFPLUMBER:
                    page_text = extract_text_from_pdf(file_path)
                    if page_text:
                        content = page_text[:2000]
                    else:
                        continue
                else:
                    print(f"  Skipping PDF {file_path}: No PDF library available")
                    continue
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)
            
            # Try to extract trial name and date
            import re
            trial_match = re.search(r'([A-Z][^0-9]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)?)', content)
            date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', content)
            trial_name = trial_match.group(1).strip() if trial_match else None
            date = date_match.group(1).strip() if date_match else ""
            
            # Validate trial name
            if trial_name:
                if any(marker in trial_name for marker in ['/*', '*/', '<script', '</script>', 'function(', 'http://', 'https://']):
                    trial_name = None
            
            # Check for duplicates
            if trial_name and date:
                normalized_name = normalize_name(trial_name)
                if (normalized_name, date) in seen_trials:
                    print(f"  Skipping duplicate trial: {trial_name} ({date})")
                    continue
                seen_trials.add((normalized_name, date))
        except Exception as e:
            print(f"  Warning: Could not check for duplicates in {file_path}: {e}")
        
        print(f"\nProcessing local file: {os.path.basename(file_path)} from {source_folder} ({year})")
        results = parse_local_trial_file(file_path, year, source_folder)
        if results:
            if not trial_name and results:
                trial_name = results[0].trial_name if results[0].trial_name else "Unknown Trial"
                date = results[0].date if results[0].date else ""
                if trial_name and date and trial_name != "Unknown Trial":
                    seen_trials.add((normalize_name(trial_name), date))
            
            all_trial_results.extend(results)
            print(f"  Extracted {len(results)} results")
    
    # Then, find and process web links (if requests is available)
    if HAS_REQUESTS:
        base_url = "https://www.jrtcayearbook.com/"
        print("\nFinding trial result links from website...")
        trial_links = find_trial_result_links(base_url)
        print(f"Found {len(trial_links)} trial result links")
        
        # Process web links
        for link_text, url, year in trial_links:
            if url in processed_urls:
                continue
            processed_urls.add(url)
            
            print(f"\nProcessing: {url} ({year})")
            results = parse_trial_results_page(url, year)
            if results:
                all_trial_results.extend(results)
                print(f"  Extracted {len(results)} results")
    
    print(f"\n{'=' * 80}")
    print(f"Total trial results extracted: {len(all_trial_results)}")
    print(f"{'=' * 80}\n")
    
    # Generate and save trial results report (unless skipping)
    if not skip_report_generation:
        print("Generating trial results report...")
        # Load catalog data for correlation (if available)
        catalog_dogs = {}
        catalog_files = glob.glob("Entries_Catalog_Report*.txt")
        if catalog_files:
            # Try to load catalog dogs (simplified - in production you might parse the report)
            # For now, we'll generate the report without full catalog correlation
            pass
        
        trial_report = generate_trial_results_report(all_trial_results, catalog_dogs)
        
        with open(trial_report_file, 'w', encoding='utf-8') as f:
            f.write(trial_report)
        
        print(f"Trial results report saved to {trial_report_file}")
    else:
        print("Skipping trial results report generation (report already exists).")
    
    print()
    
    return all_trial_results


def generate_comprehensive_report(
    classes: Dict[str, ClassInfo],
    dogs: Dict[str, Dog],
    relationships: Dict[str, List[str]],
    trial_results: List[TrialResult],
    years: List[str]
) -> str:
    """
    Generate a comprehensive report combining catalog data and trial results.
    
    Args:
        classes: Dictionary of class information
        dogs: Dictionary of dog information
        relationships: Dictionary of dog relationships
        trial_results: List of trial result entries
        years: List of years processed
    
    Returns:
        Comprehensive report as a string
    """
    print("=" * 80)
    print("GENERATING COMPREHENSIVE REPORT")
    print("=" * 80)
    print()
    
    report = []
    
    years_str = ", ".join(sorted(years)) if years else "Unknown"
    report.append("=" * 80)
    report.append(f"JRTCA COMPREHENSIVE REPORT - CATALOG & TRIAL RESULTS ({years_str})")
    report.append("=" * 80)
    report.append("")
    
    # Summary statistics
    print("Step 1: Calculating summary statistics...")
    report.append("SUMMARY STATISTICS")
    report.append("-" * 80)
    report.append(f"Years: {years_str}")
    report.append(f"Total Classes: {len(classes)}")
    report.append(f"Total Dogs in Catalog: {len(dogs):,}")
    report.append(f"Total Trial Results: {len(trial_results):,}")
    
    unique_dogs_in_trials = len(set(r.dog_name for r in trial_results if r.dog_name))
    unique_owners_in_trials = len(set(r.owner for r in trial_results if r.owner))
    
    report.append(f"Unique Dogs in Trials: {unique_dogs_in_trials:,}")
    report.append(f"Unique Owners in Trials: {unique_owners_in_trials:,}")
    report.append("")
    
    print(f"  - {len(dogs):,} dogs in catalog")
    print(f"  - {len(trial_results):,} trial results")
    print(f"  - {unique_dogs_in_trials:,} unique dogs in trials")
    print(f"  - {unique_owners_in_trials:,} unique owners")
    print()
    
    # Group trial results by dog (using normalized names)
    print("Step 2: Grouping trial results by dog...")
    trial_results_by_dog = defaultdict(list)
    for i, result in enumerate(trial_results):
        if result.dog_name:
            normalized = normalize_name(result.dog_name)
            trial_results_by_dog[normalized].append(result)
        if (i + 1) % 50000 == 0:
            print(f"  Processed {i+1:,}/{len(trial_results):,} trial results ({100*(i+1)//len(trial_results)}%)...")
    
    print(f"  Grouped into {len(trial_results_by_dog):,} unique dogs")
    print()
    
    # Match trial results with catalog dogs
    print("Step 3: Matching trial results with catalog dogs...")
    dogs_with_trials = set()
    total_matches = 0
    for i, (normalized_name, results) in enumerate(trial_results_by_dog.items()):
        # Try to find matching dog in catalog
        for dog_key, dog in dogs.items():
            dog_normalized = normalize_name(dog.name)
            if dog_normalized == normalized_name or names_are_similar(results[0].dog_name, dog.name):
                dogs_with_trials.add(dog_key)
                total_matches += 1
                break
        if (i + 1) % 1000 == 0:
            print(f"  Matched {i+1:,}/{len(trial_results_by_dog):,} trial dogs ({100*(i+1)//len(trial_results_by_dog)}%)... {total_matches} matches found")
    
    print(f"  Found {len(dogs_with_trials):,} catalog dogs with matching trial results")
    print()
    
    report.append("=" * 80)
    report.append("DOGS WITH CATALOG ENTRIES AND TRIAL RESULTS")
    report.append("=" * 80)
    report.append("")
    report.append(f"Total dogs with both catalog entries and trial results: {len(dogs_with_trials)}")
    report.append("")
    
    # Sort dogs by name
    print("Step 4: Generating report entries for each dog...")
    sorted_dogs = sorted(dogs.items(), key=lambda x: x[1].name.lower())
    
    dogs_processed = 0
    dogs_with_data = 0
    
    for dog_key, dog in sorted_dogs:
        dogs_processed += 1
        if dogs_processed % 100 == 0:
            print(f"  Processed {dogs_processed:,}/{len(sorted_dogs):,} dogs ({100*dogs_processed//len(sorted_dogs)}%)... {dogs_with_data} with data so far")
        dog_normalized = normalize_name(dog.name)
        
        # Get trial results for this dog
        dog_trial_results = []
        for normalized_name, results in trial_results_by_dog.items():
            if normalized_name == dog_normalized or names_are_similar(dog.name, results[0].dog_name):
                dog_trial_results.extend(results)
                break
        
        # Only show dogs with trial results or significant catalog data
        if not dog_trial_results and not dog.classes:
            continue
        
        dogs_with_data += 1
        if dogs_with_data % 50 == 0:
            print(f"    Generated entries for {dogs_with_data:,} dogs with data...")
        
        report.append("=" * 80)
        report.append(f"DOG: {dog.name}")
        report.append("=" * 80)
        
        # Catalog information
        report.append("CATALOG INFORMATION:")
        report.append(f"  Sex: {dog.sex or 'unknown'}")
        if dog.sire:
            report.append(f"  Sire: {dog.sire}")
        if dog.dam:
            report.append(f"  Dam: {dog.dam}")
        if dog.owner:
            report.append(f"  Owner: {dog.owner}")
        if dog.classes:
            class_strings = [f"{cls_name} ({year})" for cls_name, year in dog.classes]
            report.append(f"  Classes entered: {', '.join(class_strings)}")
        report.append("")
        
        # Relationships
        if relationships.get(dog_normalized):
            report.append("FAMILY RELATIONSHIPS:")
            rels = relationships[dog_normalized]
            sorted_rels = sorted(rels, key=lambda r: (
                0 if r.startswith("Sire:") else
                1 if r.startswith("Dam:") else
                2
            ))
            for rel in sorted_rels:
                report.append(f"  - {rel}")
            report.append("")
        
        # Trial results
        if dog_trial_results:
            report.append("TRIAL RESULTS:")
            report.append(f"  Total Results: {len(dog_trial_results)}")
            
            # Group by year
            by_year = defaultdict(list)
            for result in dog_trial_results:
                by_year[result.year].append(result)
            
            for year in sorted(by_year.keys(), reverse=True):
                year_results = by_year[year]
                report.append(f"  {year}:")
                
                # Group by trial
                by_trial = defaultdict(list)
                for result in year_results:
                    by_trial[result.trial_name].append(result)
                
                for trial_name in sorted(by_trial.keys()):
                    trial_results_list = by_trial[trial_name]
                    report.append(f"    {trial_name} ({trial_results_list[0].date or 'Unknown date'}):")
                    
                    # Sort by placement
                    def get_placement_sort_key(placement: str) -> int:
                        if not placement:
                            return 999
                        placement_lower = placement.lower()
                        if 'champion' in placement_lower:
                            return 0
                        if 'best' in placement_lower:
                            return 1
                        if 'reserve' in placement_lower:
                            return 2
                        import re
                        numeric_match = re.search(r'(\d+)', placement)
                        if numeric_match:
                            return 10 + int(numeric_match.group(1))
                        if 'dq' in placement_lower:
                            return 98
                        return 99
                    
                    sorted_results = sorted(trial_results_list, key=lambda r: get_placement_sort_key(r.placement or ""))
                    
                    for result in sorted_results:
                        placement_str = result.placement or "N/A"
                        class_str = result.class_name or "N/A"
                        if result.class_number is not None:
                            class_str = f"Class {result.class_number}: {class_str}"
                        report.append(f"      {placement_str} in {class_str}")
        else:
            report.append("TRIAL RESULTS: None")
        
        report.append("")
    
    print(f"  Completed: Generated entries for {dogs_with_data:,} dogs with catalog and/or trial data")
    print()
    
    # Dogs with trial results but no catalog entry
    print("Step 5: Finding dogs with trial results but no catalog entry...")
    report.append("=" * 80)
    report.append("DOGS WITH TRIAL RESULTS BUT NO CATALOG ENTRY")
    report.append("=" * 80)
    report.append("")
    
    dogs_in_trials_only = []
    checked = 0
    for normalized_name, results in trial_results_by_dog.items():
        checked += 1
        if checked % 1000 == 0:
            print(f"  Checked {checked:,}/{len(trial_results_by_dog):,} trial dogs ({100*checked//len(trial_results_by_dog)}%)... {len(dogs_in_trials_only)} trial-only dogs found")
        found_in_catalog = False
        for dog_key, dog in dogs.items():
            dog_normalized = normalize_name(dog.name)
            if dog_normalized == normalized_name or names_are_similar(results[0].dog_name, dog.name):
                found_in_catalog = True
                break
        
        if not found_in_catalog:
            dogs_in_trials_only.append((normalized_name, results))
    
    print(f"  Found {len(dogs_in_trials_only):,} dogs with trial results but no catalog entry")
    print()
    
    if dogs_in_trials_only:
        report.append(f"Total: {len(dogs_in_trials_only)} dogs")
        report.append("")
        for normalized_name, results in sorted(dogs_in_trials_only, key=lambda x: x[1][0].dog_name or ""):
            dog_name = results[0].dog_name
            report.append(f"  {dog_name}")
            report.append(f"    Total Results: {len(results)}")
            # Show sample results
            for result in results[:5]:  # Show first 5 results
                placement_str = result.placement or "N/A"
                report.append(f"      {result.year} - {result.trial_name}: {placement_str}")
            if len(results) > 5:
                report.append(f"      ... and {len(results) - 5} more results")
            report.append("")
    else:
        report.append("None")
        report.append("")
    
    print("Step 6: Finalizing report...")
    print(f"  Total report lines: {len(report):,}")
    print(f"  Total report size: ~{sum(len(line) for line in report):,} characters")
    print()
    
    return "\n".join(report)


def main():
    """Main function for comprehensive report generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive JRTCA report combining catalog and trial results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report using existing data (if available)
  python generate_comprehensive_report.py
  
  # Regenerate catalog data only
  python generate_comprehensive_report.py --regenerate-catalog
  
  # Regenerate trial results only
  python generate_comprehensive_report.py --regenerate-trials
  
  # Regenerate everything
  python generate_comprehensive_report.py --regenerate-all
        """
    )
    
    parser.add_argument(
        '--regenerate-catalog',
        action='store_true',
        help='Force regeneration of catalog report (Entries_Catalog_Report_*.txt)'
    )
    parser.add_argument(
        '--regenerate-trials',
        action='store_true',
        help='Force regeneration of trial results report (Trial_Results_Report.txt)'
    )
    parser.add_argument(
        '--regenerate-all',
        action='store_true',
        help='Force regeneration of both catalog and trial results reports'
    )
    
    args = parser.parse_args()
    
    # Determine regeneration flags
    regenerate_catalog = args.regenerate_all or args.regenerate_catalog
    regenerate_trials = args.regenerate_all or args.regenerate_trials
    
    print("=" * 80)
    print("JRTCA COMPREHENSIVE REPORT GENERATOR")
    print("=" * 80)
    print()
    print(f"Regenerate catalog: {regenerate_catalog}")
    print(f"Regenerate trials: {regenerate_trials}")
    print()
    
    # Step 1: Process catalog data
    classes, dogs, relationships, years = run_catalog_processing(regenerate=regenerate_catalog)
    
    if not dogs:
        print("WARNING: No catalog data available. Report will only include trial results.")
    
    # Step 2: Process trial results
    trial_results = run_trial_results_processing(regenerate=regenerate_trials)
    
    if not trial_results:
        print("WARNING: No trial results available. Report will only include catalog data.")
    
    # Step 3: Generate comprehensive report
    print("=" * 80)
    print("GENERATING COMPREHENSIVE REPORT")
    print("=" * 80)
    print()
    
    comprehensive_report = generate_comprehensive_report(
        classes, dogs, relationships, trial_results, years
    )
    
    # Save comprehensive report
    print("Saving comprehensive report to file...")
    output_file = "Comprehensive_Report.txt"
    report_lines = comprehensive_report.split("\n")
    print(f"  Writing {len(report_lines):,} lines to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write in chunks to show progress for large files
        chunk_size = 10000
        for i in range(0, len(report_lines), chunk_size):
            chunk = report_lines[i:i+chunk_size]
            f.write("\n".join(chunk))
            if i + chunk_size < len(report_lines):
                f.write("\n")
            if (i + chunk_size) % 50000 == 0 or i + chunk_size >= len(report_lines):
                print(f"    Written {min(i+chunk_size, len(report_lines)):,}/{len(report_lines):,} lines ({100*min(i+chunk_size, len(report_lines))//len(report_lines)}%)...")
    
    file_size = os.path.getsize(output_file)
    print(f"  Report saved successfully ({file_size:,} bytes, ~{file_size//1024//1024} MB)")
    print()
    print("=" * 80)
    print("REPORT PREVIEW (first 100 lines):")
    print("=" * 80)
    print("\n".join(report_lines[:100]))
    if len(report_lines) > 100:
        print(f"\n... (report continues, see {output_file} for full report)")
    
    print()
    print("=" * 80)
    print("COMPREHENSIVE REPORT GENERATION COMPLETE!")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Total lines: {len(report_lines):,}")
    print(f"File size: {file_size:,} bytes (~{file_size//1024//1024} MB)")
    print()
    print("Done!")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Parse catalog .doc and .pdf files and extract structured data about dog show entries.
Supports multiple years (2008-2025) and tracks sex information across years.
"""

import re
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple

# Try to import libraries for reading .doc files
try:
    import textract  # type: ignore
    HAS_TEXTRACT = True
except ImportError:
    HAS_TEXTRACT = False

try:
    from docx import Document  # type: ignore
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False

# Try to import libraries for reading .pdf files
try:
    import pdfplumber  # type: ignore
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2  # type: ignore
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from pypdf import PdfReader  # type: ignore
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


@dataclass
class Dog:
    """Represents a dog entry."""
    number: str
    name: str
    sire: Optional[str] = None
    dam: Optional[str] = None
    owner: Optional[str] = None
    sex: Optional[str] = None  # "dog" or "bitch"
    classes: List[Tuple[str, str]] = field(default_factory=list)  # List of (class_name, year) tuples


@dataclass
class ClassInfo:
    """Represents a class with its entries."""
    name: str
    year: str  # Year this class is from
    division: Optional[str] = None
    section: Optional[str] = None
    entry_count: int = 0
    entries: List[Dog] = field(default_factory=list)


def extract_text_from_doc(filepath: str) -> str:
    """Extract text from a .doc file using available methods."""
    # Convert to absolute path
    abs_filepath = os.path.abspath(filepath)
    
    # Try textract first (most reliable for .doc files)
    if HAS_TEXTRACT:
        try:
            print(f"  Trying textract...")
            text = textract.process(abs_filepath).decode('utf-8')
            if text and len(text) > 100:
                print(f"  textract succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  textract returned empty or too short text ({len(text) if text else 0} chars)")
        except Exception as e:
            print(f"  textract failed: {e}")
    
    # Try win32com (Windows only) - use different method to get text
    if HAS_WIN32COM:
        word = None
        doc = None
        try:
            print(f"  Trying win32com...")
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0  # Suppress alerts
            # Use ReadOnly to avoid lock issues
            doc = word.Documents.Open(abs_filepath, ReadOnly=True)
            
            # Try multiple methods to get text
            text = None
            try:
                # Method 1: Content.Text (most common)
                text = doc.Content.Text
            except:
                try:
                    # Method 2: Range.Text
                    text = doc.Range().Text
                except:
                    try:
                        # Method 3: Get text from all paragraphs
                        paragraphs = []
                        for para in doc.Paragraphs:
                            paragraphs.append(para.Range.Text)
                        text = '\n'.join(paragraphs)
                    except Exception as e2:
                        print(f"  All win32com text extraction methods failed: {e2}")
            
            if text and len(text) > 100:
                doc.Close(SaveChanges=False)
                word.Quit(SaveChanges=False)
                print(f"  win32com succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  win32com returned empty or too short text ({len(text) if text else 0} chars)")
                if doc:
                    doc.Close(SaveChanges=False)
                if word:
                    word.Quit(SaveChanges=False)
        except Exception as e:
            print(f"  win32com failed: {e}")
            if doc:
                try:
                    doc.Close(SaveChanges=False)
                except:
                    pass
            if word:
                try:
                    word.Quit(SaveChanges=False)
                except:
                    pass
    
    # Try python-docx (might work for some .doc files)
    if HAS_DOCX:
        try:
            doc = Document(abs_filepath)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"python-docx failed: {e}")
    
    raise Exception("No method available to extract text from .doc file. "
                   "Please install textract, python-docx, or pywin32.")


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a .pdf file using available methods."""
    # Convert to absolute path
    abs_filepath = os.path.abspath(filepath)
    
    # Try pdfplumber first (best for extracting text with layout preservation)
    if HAS_PDFPLUMBER:
        try:
            print(f"  Trying pdfplumber...")
            text_parts = []
            with pdfplumber.open(abs_filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = '\n'.join(text_parts)
            if text and len(text) > 100:
                print(f"  pdfplumber succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  pdfplumber returned empty or too short text ({len(text) if text else 0} chars)")
        except Exception as e:
            print(f"  pdfplumber failed: {e}")
    
    # Try pypdf (newer version of PyPDF2)
    if HAS_PYPDF:
        try:
            print(f"  Trying pypdf...")
            text_parts = []
            with open(abs_filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = '\n'.join(text_parts)
            if text and len(text) > 100:
                print(f"  pypdf succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  pypdf returned empty or too short text ({len(text) if text else 0} chars)")
        except Exception as e:
            print(f"  pypdf failed: {e}")
    
    # Try PyPDF2 (older version, fallback)
    if HAS_PYPDF2:
        try:
            print(f"  Trying PyPDF2...")
            text_parts = []
            with open(abs_filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = '\n'.join(text_parts)
            if text and len(text) > 100:
                print(f"  PyPDF2 succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  PyPDF2 returned empty or too short text ({len(text) if text else 0} chars)")
        except Exception as e:
            print(f"  PyPDF2 failed: {e}")
    
    # Try textract as fallback (supports PDFs too)
    if HAS_TEXTRACT:
        try:
            print(f"  Trying textract for PDF...")
            text = textract.process(abs_filepath).decode('utf-8')
            if text and len(text) > 100:
                print(f"  textract succeeded: {len(text)} characters extracted")
                return text
            else:
                print(f"  textract returned empty or too short text ({len(text) if text else 0} chars)")
        except Exception as e:
            print(f"  textract failed: {e}")
    
    raise Exception("No method available to extract text from .pdf file. "
                   "Please install pdfplumber, pypdf, PyPDF2, or textract.")


def extract_text_from_file(filepath: str) -> str:
    """Extract text from a file (.doc or .pdf) using available methods.
    
    Args:
        filepath: Path to the file (supports .doc and .pdf extensions)
    
    Returns:
        Extracted text as a string
    """
    filepath_lower = filepath.lower()
    
    if filepath_lower.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filepath_lower.endswith('.doc') or filepath_lower.endswith('.docx'):
        return extract_text_from_doc(filepath)
    else:
        # Try to detect file type by extension or try both
        if '.pdf' in filepath_lower:
            return extract_text_from_pdf(filepath)
        elif '.doc' in filepath_lower:
            return extract_text_from_doc(filepath)
        else:
            # Unknown extension, try PDF first, then DOC
            try:
                return extract_text_from_pdf(filepath)
            except:
                return extract_text_from_doc(filepath)


_DIVISION_LETTER_PREFIX_RE = re.compile(
    r'^DIVISION\s+[A-Z]\s*[—–\-]\s*(.+)$',
    re.IGNORECASE,
)

CATALOG_YEAR_MIN = 2008
CATALOG_YEAR_MAX = 2025


def extract_catalog_division_label(line: str) -> str:
    """Strip catalog letter prefix (e.g. 'DIVISION A — RACING' -> 'RACING')."""
    if not line:
        return line
    cleaned = clean_catalog_text(line).strip()
    match = _DIVISION_LETTER_PREFIX_RE.match(cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def normalize_division_name(division: str) -> str:
    """Normalize division names to canonical forms, similar to SQL stored procedure logic.
    
    Args:
        division: Raw division name from catalog
    
    Returns:
        Normalized division name
    """
    if not division:
        return division
    
    label = extract_catalog_division_label(division)
    division_upper = label.upper().strip()
    division_base = re.sub(r'\s*\([^)]*\)\s*$', '', division_upper).strip()
    
    # Division normalization mapping (based on SQL stored procedure CASE statement)
    division_map = {
        # Agility
        'AGILILITY': 'AGILITY DIVISION',
        'AGILITY DIVISION': 'AGILITY DIVISION',
        'AGILITY DIVISON': 'AGILITY DIVISION',
        'AGILITY': 'AGILITY DIVISION',
        
        # Ball Retrieval/Toss
        'BALL RETRIEVAL': 'BALL RETRIEVAL',
        'BALL TOSS': 'BALL TOSS',
        'BALL TOSS CHAMPION & RESERVE': 'BALL TOSS',
        
        # Barn Hunt
        'BARN HUNT': 'BARN HUNT',
        'BARN HUNT (NON-SANCTIONED)': 'BARN HUNT',
        'BARN HUNT DIVISION (NON-SANCTIONED)': 'BARN HUNT',
        'BARN HUNT DIVISION': 'BARN HUNT',
        
        # Brush Hunt
        'BRUSH HUNT': 'BRUSH HUNT',
        'BRUSH HUNT DIVISION': 'BRUSH HUNT',
        'BRUSH HUNT (NON SANCTIONED)': 'BRUSH HUNT',
        'BRUSH HUNT: SATURDAY': 'BRUSH HUNT: SATURDAY',
        'BRUSH HUNT: SUNDAY': 'BRUSH HUNT: SUNDAY',
        
        # Conformation
        'CONFORMATION': 'CONFORMATION',
        'CONFORMATION DIVISION:': 'CONFORMATION',
        'CONFORMATION DIVISION': 'CONFORMATION',
        'CONFORMATION DIVISON': 'CONFORMATION',
        'WORKING TERRIER CONFORMATION': 'CONFORMATION',
        
        # Doggie Fun Zone
        'DOGGIE FUN ZONE (NON-SANCTIONED)': 'DOGGIE FUN ZONE (NON-SANCTIONED)',
        'DOGGIE FUN ZONE': 'DOGGIE FUN ZONE (NON-SANCTIONED)',
        'DOGGIE FUN ZONE DIVISION (NON-SANCTIONED)': 'DOGGIE FUN ZONE (NON-SANCTIONED)',
        'DOGGIE FUN ZONE DIVISION': 'DOGGIE FUN ZONE (NON-SANCTIONED)',
        
        # Lure Coursing
        'LURE COURSING': 'LURE COURSING',
        'FIELD LURE COURSING': 'LURE COURSING',
        'FIELD LURE COURSING (NON-SANCTIONED)': 'LURE COURSING',
        
        # Flat Races
        'FLAT RACES:': 'FLAT RACES',
        'FLAT RACES': 'FLAT RACES',
        'FLAT RACING': 'FLAT RACES',
        'FLATS RACING': 'FLAT RACES',
        'FLATS': 'FLAT RACES',
        
        # Go-To-Ground
        'GO-TO GROUND': 'GO-TO-GROUND',
        'GO-TO- GROUND': 'GO-TO-GROUND',
        'GO-TO-GOUND DIVISION': 'GO-TO-GROUND',
        'GO-TO-GROUND': 'GO-TO-GROUND',
        'GO-TO-GROUND DIVISIION': 'GO-TO-GROUND',
        'GO-TO-GROUND DIVISION': 'GO-TO-GROUND',
        'GO-TO-GROUND DIVISON': 'GO-TO-GROUND',
        'GO-TO-TO-GROUND': 'GO-TO-GROUND',
        'GTG': 'GO-TO-GROUND',
        'GO TO GROUND': 'GO-TO-GROUND',
        
        # High Jump
        'HIGH JUMP': 'HIGH JUMP',
        'HIGH JUMP DIVISION': 'HIGH JUMP',
        'SUNDAY HIGH JUMP': 'HIGH JUMP',
        'HIGH JUMP HIGH SCORE & RESERVE': 'HIGH JUMP',
        
        # Hurdle/Steeplechase
        'HURDLE': 'STEEPLECHASE RACES',
        'HURDLE RACE': 'STEEPLECHASE RACES',
        'HURDLE RACES': 'STEEPLECHASE RACES',
        'HURDLES': 'STEEPLECHASE RACES',
        'HURDLES RACES': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACES': 'STEEPLECHASE RACES',
        'STEELPECHASE RACES': 'STEEPLECHASE RACES',
        'STEEPLECHASE': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACE': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACING': 'STEEPLECHASE RACES',
        'HURDLES RACING': 'STEEPLECHASE RACES',
        
        # Jumpers
        'JUMPERS DIVISION': 'JUMPERS DIVISION',
        
        # Nose Work
        'NOSE WORK': 'NOSE WORK',
        'NOSE WORK DIVISION': 'NOSE WORK',
        'NOSE WORK (SCENTING)': 'NOSE WORK',
        'NOSEWORK': 'NOSE WORK',
        
        # Obedience
        'OBEDIENCE': 'OBEDIENCE DIVISION',
        'OBEDIENCE DIVISION': 'OBEDIENCE DIVISION',
        'OBEDIENCE DIVISON': 'OBEDIENCE DIVISION',
        'OBEDIENCE HIGH SCORE & RESERVE': 'OBEDIENCE DIVISION',
        
        # Racing
        'RACING': 'RACING DIVISION',
        'RACING DIVISION': 'RACING DIVISION',
        'RACING DIVISION FLAT RACES': 'RACING DIVISION',
        'RACING DIVISON': 'RACING DIVISION',
        
        # Rally Obedience
        'RALLY OBEDIENCE': 'RALLY OBEDIENCE DIVISION',
        'RALLY OBEDIENCE DIVISION': 'RALLY OBEDIENCE DIVISION',
        'RALLY-O': 'RALLY OBEDIENCE DIVISION',
        'RALLY-OBEDIENCE': 'RALLY OBEDIENCE DIVISION',
        'RALLY-O HIGH SCORE & RESERVE': 'RALLY OBEDIENCE DIVISION',
        
        # Super Earth
        'SUPER EARTH': 'SUPER EARTH',
        'SUPER EARTH DIVISION': 'SUPER EARTH',
        'SUPER EARTH GTG DIVISION': 'SUPER EARTH',
        'SUPER EARTH STAKES': 'SUPER EARTH',
        'SUPER GTG': 'SUPER EARTH',
        'SUPER SENIOR': 'SUPER EARTH',
        'SUPEREARTH': 'SUPER EARTH',
        'SUPER EARTH GO-TO-GROUND DIVISION': 'SUPER EARTH',
        
        # Thunder Tunnel
        'THUNDER TUNNEL': 'THUNDER TUNNEL',
        'THUNDER TUNNEL DIVISION': 'THUNDER TUNNEL',
        
        # Trailing
        'TRAILING': 'TRAILING & LOCATING',
        'TRAILING & LOCATING': 'TRAILING & LOCATING',
        'TRAILING & LOCATING DIVISION': 'TRAILING & LOCATING',
        'TRAILING & LOCATING DIVISON': 'TRAILING & LOCATING',
        'TRAILING/LOCATING DIVISION': 'TRAILING & LOCATING',
        'TRAILING AND LOCATING': 'TRAILING & LOCATING',
        'TRAILING AND LOCATING DIVISION': 'TRAILING & LOCATING',
        'TRAIL': 'TRAILING & LOCATING',
        
        # Top Dog/Gun
        'TOP DOG': 'TOP DOG',
        'TOP GUN': 'TOP GUN',
        'TOP GUN CHALLENGE': 'TOP GUN',
        'TOP DOG (NON-SANCTIONED)': 'TOP GUN',
        
        # Stakes Tunnel Race
        'STAKES TUNNEL RACE': 'STAKES TUNNEL RACE',
        
        # Youth
        'YOUTH DIVISION': 'YOUTH DIVISION',
        'YOUTH DIVISON': 'YOUTH DIVISION',
        'YOUTH HIGH POINT': 'YOUTH DIVISION',
        'YOUTH': 'YOUTH DIVISION',
        'YOUTH HANDLER': 'YOUTH DIVISION',
    }
    
    if division_base in division_map:
        return division_map[division_base]
    if division_upper in division_map:
        return division_map[division_upper]
    return label


def clean_catalog_text(line: str) -> str:
    """Clean and normalize catalog text, similar to SQL stored procedure REPLACE operations.
    
    Args:
        line: Raw line from catalog
    
    Returns:
        Cleaned line
    """
    if not line:
        return line
    
    # Remove various special characters and normalize spacing (based on SQL stored procedure)
    cleaned = line
    # Replace pipe characters
    cleaned = cleaned.replace('|', '')
    # Replace multiple spaces with single space
    cleaned = re.sub(r' +', ' ', cleaned)
    # Replace " :  " with ": " (normalize spacing around colons)
    cleaned = cleaned.replace(' :  ', ': ')
    # Remove various Unicode characters that appear in corrupted text
    # (These are based on the SQL's REPLACE operations)
    cleaned = cleaned.replace('\ufeff', '')  # BOM
    cleaned = cleaned.replace('\u200b', '')  # Zero-width space
    cleaned = cleaned.replace('\u200c', '')  # Zero-width non-joiner
    cleaned = cleaned.replace('\u200d', '')  # Zero-width joiner
    
    return cleaned.strip()


def parse_catalog(text: str, year: str) -> tuple[Dict[str, ClassInfo], Dict[str, Dog]]:
    """Parse the catalog text and extract structured data.
    
    Args:
        text: The extracted text from the catalog document
        year: The year of the catalog (extracted from filename)
    
    Returns:
        Tuple of (classes dict, dogs dict)
    """
    classes: Dict[str, ClassInfo] = {}
    dogs: Dict[str, Dog] = {}  # keyed by dog number
    
    current_division = None
    current_section = None
    current_class = None
    current_class_info = None
    
    if not text or len(text) < 100:
        print(f"  WARNING: parse_catalog received empty or very short text ({len(text) if text else 0} chars)")
        print(f"  parse_catalog returning: {len(classes)} classes, {len(dogs)} dogs (early return due to empty text)")
        return classes, dogs
    
    lines = text.split('\n')
    print(f"  Parsing {len(lines)} lines of text for year {year}")
    
    # Debug: check first few lines for class patterns
    class_lines_found = [l for l in lines[:50] if 'Class' in l and re.search(r'Class\s+\d+:', l)]
    print(f"  Found {len(class_lines_found)} lines with 'Class' pattern in first 50 lines")
    if len(class_lines_found) > 0:
        print(f"  First class line: {class_lines_found[0][:100]}")
    
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            i += 1
            continue
        
        # Clean the line first (similar to SQL stored procedure text cleaning)
        line_cleaned = clean_catalog_text(line)
        line_stripped = line_cleaned.strip()
        
        # Check for division (format: "DIVISION A — RACING")
        division_match = re.match(r'^DIVISION\s+[A-Z]\s*[—–-]\s*(.+)$', line_stripped, re.IGNORECASE)
        if division_match:
            current_division = normalize_division_name(division_match.group(1))
            current_section = None
            current_class = None
            i += 1
            continue
        
        # Also check for division names directly (without "DIVISION A —" prefix)
        # This matches the SQL stored procedure logic which checks for division names in an IN list
        division_label = extract_catalog_division_label(line_stripped)
        division_normalized = normalize_division_name(division_label)
        if division_normalized != division_label:
            # This line matched a known division name pattern
            current_division = division_normalized
            current_section = None
            current_class = None
            i += 1
            continue
        
        # Check for section (format: "Section 1. 	Flat Races")
        section_match = re.match(r'^Section\s+\d+\.\s*(.+)$', line_stripped, re.IGNORECASE)
        if section_match:
            current_section = line_stripped
            current_class = None
            i += 1
            continue
        
        # Check for class name (format: "Class 1:		Pups, 6 up to 9 months, up to 12½"	Entries:	11")
        # Also handle classes without "Entries:" on same line (e.g., "Class 19:	Up to 12½" Puppy Champion & Reserve.")
        # Also handle indented classes (e.g., "  Class 22:       Dogs, 1 year and older...")
        # Also handle "Class: " prefix format (based on SQL stored procedure: @Entry LIKE 'Class: %')
        # Note: Need to use original line to preserve tabs, but allow leading whitespace
        # First try pattern with Entries: on same line
        class_match = re.match(r'^\s*Class\s+(\d+):[\s\t]+(.+?)[\s\t]+Entries:[\s\t]+(\d+)', line, re.IGNORECASE)
        if class_match:
            class_num = class_match.group(1)
            class_desc = class_match.group(2).strip()
            entry_count = int(class_match.group(3))
        else:
            # Try pattern without Entries: (for Champion/Reserve classes)
            class_match = re.match(r'^\s*Class\s+(\d+):[\s\t]+(.+?)(?:\s*\.?\s*)$', line, re.IGNORECASE)
            if class_match:
                class_num = class_match.group(1)
                class_desc = class_match.group(2).strip().rstrip('.')
                entry_count = 0  # Champion/Reserve classes don't have entry counts
            else:
                # Try "Class: " prefix format (SQL stored procedure handles this)
                class_match = re.match(r'^\s*Class:\s*(.+)$', line_stripped, re.IGNORECASE)
                if class_match:
                    class_desc = class_match.group(1).strip()
                    # Try to extract class number from description if present
                    num_match = re.search(r'^(\d+):', class_desc)
                    if num_match:
                        class_num = num_match.group(1)
                        class_desc = class_desc[len(num_match.group(0)):].strip()
                    else:
                        # No number found, use description as class name
                        class_num = None
                        class_desc = class_desc
                    entry_count = 0
        
        if class_match:
            # Create full class name
            current_class = f"Class {class_num}: {class_desc}"
            
            # Use year-specific class key to handle same class number in different years
            class_key = f"{year}:{current_class}"
            
            if class_key not in classes:
                classes[class_key] = ClassInfo(
                    name=current_class,
                    year=year,
                    division=current_division,
                    section=current_section,
                    entry_count=entry_count
                )
            current_class_info = classes[class_key]
            i += 1
            continue
        
        # Check for dog entry (format: "	94	Smilin' Jack Kia, by Firestorm Blast out of Smilin' Jack Khaki (Charles & Sally Hickey)")
        # Entry starts with tab, spaces, or directly with number, then tab/spaces, then rest
        # Handle entries that start with:
        #   - Tab: "\t94\t..."
        #   - Spaces: "  68\t..." or "  68  ..."
        #   - Direct number: "267\t..." or "267  ..."
        # Check if line starts with whitespace followed by digit, OR starts directly with digit
        is_dog_entry = False
        if re.match(r'^[\s\t]+\d+', line):
            # Line starts with whitespace (tab or spaces) followed by digit
            is_dog_entry = True
        elif re.match(r'^\d+[\s\t]', line):
            # Line starts directly with digit followed by whitespace
            is_dog_entry = True
        
        if is_dog_entry:
            # Try to match dog entry patterns - use stripped line for regex (but tabs may remain)
            # Pattern 1: Full entry with sire and dam: "94	Smilin' Jack Kia, by Firestorm Blast out of Smilin' Jack Khaki (Charles & Sally Hickey)"
            # The pattern needs to match: number, name (up to comma before "by"), "by", sire, "out of", dam, owner in parens
            # NOTE: The dog name should include " of ..." if present (e.g., "Southland Chigurh of Timberwilde")
            #       This will be used for display. For relationship matching, normalize_name() removes " of ..."
            
            # Initialize variables
            dog_num = None
            dog_name = None
            sire = None
            dam = None
            owner = None
            parsed = False
            
            # FIRST: Use split-based parsing when ", by " is present - this is more reliable than regex
            # This matches the SQL stored procedure logic which uses SUBSTRING and CHARINDEX
            # SQL: @DogNumber=LTRIM(RTRIM(SUBSTRING(@Entry,1,CHARINDEX(' ',@Entry,1)-1)))
            if ', by ' in line_stripped:
                # Extract dog number (first part before first space, similar to SQL SUBSTRING logic)
                first_space_idx = line_stripped.find(' ')
                if first_space_idx > 0:
                    dog_num_str = line_stripped[:first_space_idx].strip()
                    if dog_num_str.isdigit():
                        dog_num = dog_num_str
                        rest = line_stripped[first_space_idx:].strip()
                    else:
                        # Fallback to regex if no space found before number
                        num_match = re.match(r'^(\d+)[\s\t]+', line_stripped)
                        if num_match:
                            dog_num = num_match.group(1)
                            rest = line_stripped[len(num_match.group(0)):].strip()
                        else:
                            i += 1
                            continue
                else:
                    # No space found, try regex
                    num_match = re.match(r'^(\d+)[\s\t]+', line_stripped)
                    if num_match:
                        dog_num = num_match.group(1)
                        rest = line_stripped[len(num_match.group(0)):].strip()
                    else:
                        i += 1
                        continue
                
                # Split on ", by " to get name - matches SQL: CHARINDEX(', by ',@Entry,1)
                # SQL: @Dog=...SUBSTRING(@Entry,CHARINDEX(' ',@Entry,1)+LEN(' '),CHARINDEX(', by ',@Entry,1)-...)
                parts = rest.split(', by ', 1)
                dog_name = parts[0].strip()
                after_by = parts[1]
                
                # Now parse the rest: "sire out of dam (owner)" or "sire (owner)"
                # SQL logic: Check for "out of" first, then "(" for owner
                if ' out of ' in after_by:
                    # Full entry: name, by sire out of dam (owner)
                    # SQL: @Sire=...SUBSTRING(@Entry,CHARINDEX(', by ',@Entry,1)+LEN(', by '),CHARINDEX(' out of ',@Entry,1)-...)
                    sire_dam_parts = after_by.split(' out of ', 1)
                    sire = sire_dam_parts[0].strip()
                    after_out_of = sire_dam_parts[1]
                    
                    # Extract dam and owner from "dam (owner)"
                    # SQL: @Dam=...SUBSTRING(@Entry,CHARINDEX(' out of ',@Entry,1)+LEN(' out of '),CHARINDEX(' (',@Entry,1)-...)
                    if ' (' in after_out_of:
                        dam_owner_parts = after_out_of.split(' (', 1)
                        dam = dam_owner_parts[0].strip()
                        owner = dam_owner_parts[1].rstrip(')').strip()
                    else:
                        dam = after_out_of.strip()
                        owner = None
                    parsed = True
                elif ' (' in after_by:
                    # Sire only: name, by sire (owner)
                    # SQL: @Sire=...SUBSTRING(@Entry,CHARINDEX(', by ',@Entry,1)+LEN(', by '),CHARINDEX(' (',@Entry,1)-...)
                    sire_owner_parts = after_by.split(' (', 1)
                    sire = sire_owner_parts[0].strip()
                    owner = sire_owner_parts[1].rstrip(')').strip()
                    dam = None
                    parsed = True
                else:
                    # Has "by" but no "out of" and no owner - just sire
                    sire = after_by.strip()
                    dam = None
                    owner = None
                    parsed = True
            
            # If split method didn't work, try regex patterns
            if not parsed:
                full_match = re.match(r'^(\d+)[\s\t]+(.+?),\s+by\s+(.+?)\s+out\s+of\s+(.+?)\s+\(([^)]+)\)$', line_stripped)
                if full_match:
                    dog_num = full_match.group(1)
                    dog_name = full_match.group(2).strip()
                    sire = full_match.group(3).strip()
                    dam = full_match.group(4).strip()
                    owner = full_match.group(5).strip()
                    
                    # Validate and fix: dog_name should not contain "by" or "out of"
                    # If it does, it means the regex captured too much - take only the part before ", by"
                    if ', by ' in dog_name:
                        dog_name = dog_name.split(', by ')[0].strip()
                    elif ' by ' in dog_name:
                        dog_name = dog_name.split(' by ')[0].strip()
                    if ' out of ' in dog_name:
                        dog_name = dog_name.split(' out of ')[0].strip()
                    parsed = True
                else:
                    # Pattern 2: With sire only: "94	Dog Name, by Sire Name (Owner)"
                    sire_only_match = re.match(r'^(\d+)[\s\t]+(.+?),\s+by\s+(.+?)\s+\(([^)]+)\)$', line_stripped)
                    if sire_only_match:
                        dog_num = sire_only_match.group(1)
                        dog_name = sire_only_match.group(2).strip()
                        sire = sire_only_match.group(3).strip()
                        dam = None
                        owner = sire_only_match.group(4).strip()
                        # Ensure dog name doesn't contain "by"
                        if ', by ' in dog_name:
                            dog_name = dog_name.split(', by ')[0].strip()
                        elif ' by ' in dog_name:
                            dog_name = dog_name.split(' by ')[0].strip()
                        parsed = True
                    else:
                        # Pattern 3: With dam only: "94	Dog Name, out of Dam Name (Owner)"
                        dam_only_match = re.match(r'^(\d+)[\s\t]+(.+?),\s+out\s+of\s+(.+?)\s+\(([^)]+)\)$', line_stripped)
                        if dam_only_match:
                            dog_num = dam_only_match.group(1)
                            dog_name = dam_only_match.group(2).strip()
                            sire = None
                            dam = dam_only_match.group(3).strip()
                            owner = dam_only_match.group(4).strip()
                            # Ensure dog name doesn't contain "out of"
                            if ', out of ' in dog_name:
                                dog_name = dog_name.split(', out of ')[0].strip()
                            elif ' out of ' in dog_name:
                                dog_name = dog_name.split(' out of ')[0].strip()
                            parsed = True
                        else:
                            # Pattern 4: Name and owner only: "94	Dog Name (Owner)"
                            # SQL logic: @Entry NOT LIKE '%, by %' AND @Entry LIKE '% (%'
                            # Only match if the line doesn't contain "by" or "out of" (those should match Pattern 1, 2, or 3)
                            if ', by ' not in line_stripped and ' out of ' not in line_stripped:
                                # SQL: @Dog=...SUBSTRING(@Entry,CHARINDEX(' ',@Entry,1)+1,CHARINDEX(' (',@Entry,1)-...)
                                # SQL: @Owner=...SUBSTRING(@Entry,CHARINDEX(' (',@Entry,1)+LEN(' ('),CHARINDEX(')',@Entry,1)-...)
                                if ' (' in line_stripped:
                                    first_space_idx = line_stripped.find(' ')
                                    paren_start_idx = line_stripped.find(' (')
                                    paren_end_idx = line_stripped.rfind(')')
                                    
                                    if first_space_idx > 0 and paren_start_idx > first_space_idx and paren_end_idx > paren_start_idx:
                                        # Extract dog number (before first space)
                                        dog_num_str = line_stripped[:first_space_idx].strip()
                                        if dog_num_str.isdigit():
                                            dog_num = dog_num_str
                                            # Extract dog name (between first space and " (")
                                            dog_name = line_stripped[first_space_idx+1:paren_start_idx].strip()
                                            # Extract owner (between " (" and ")")
                                            owner = line_stripped[paren_start_idx+2:paren_end_idx].strip()
                                            sire = None
                                            dam = None
                                            parsed = True
                                        else:
                                            # Fallback to regex
                                            simple_match = re.match(r'^(\d+)[\s\t]+(.+?)\s+\(([^)]+)\)$', line_stripped)
                                            if simple_match:
                                                dog_num = simple_match.group(1)
                                                dog_name = simple_match.group(2).strip()
                                                sire = None
                                                dam = None
                                                owner = simple_match.group(3).strip()
                                                parsed = True
                                            else:
                                                # Pattern 5: Just number and name: "94	Dog Name"
                                                # SQL logic doesn't explicitly handle this, but we should
                                                first_space_idx = line_stripped.find(' ')
                                                if first_space_idx > 0:
                                                    dog_num_str = line_stripped[:first_space_idx].strip()
                                                    if dog_num_str.isdigit():
                                                        dog_num = dog_num_str
                                                        dog_name = line_stripped[first_space_idx+1:].strip()
                                                        sire = None
                                                        dam = None
                                                        owner = None
                                                        parsed = True
                                                if not parsed:
                                                    # Fallback to regex
                                                    name_only_match = re.match(r'^(\d+)[\s\t]+(.+?)$', line_stripped)
                                                    if name_only_match:
                                                        dog_num = name_only_match.group(1)
                                                        dog_name = name_only_match.group(2).strip()
                                                        sire = None
                                                        dam = None
                                                        owner = None
                                                        parsed = True
                                
                                if not parsed:
                                    # Skip lines that don't match (like "1st: ________")
                                    i += 1
                                    continue
                                # Line has "by" or "out of" but didn't match earlier patterns - try manual parsing
                                if ', by ' in line_stripped or ' out of ' in line_stripped:
                                    print(f"  WARNING: Entry with 'by' or 'out of' didn't match expected patterns, trying manual parse: {line_stripped[:100]}")
                                    # Try to manually parse: "521	Southland Chigurh, by The Hollow AfterMax out of Texas Star Yellow Rose (Mark & Heather Waelterman)"
                                    num_match = re.match(r'^(\d+)[\s\t]+', line_stripped)
                                    if num_match:
                                        dog_num = num_match.group(1)
                                        rest = line_stripped[len(num_match.group(0)):].strip()
                                        # Try to find ", by " and " out of " and " ("
                                        if ', by ' in rest and ' out of ' in rest and ' (' in rest:
                                            # Full entry: name, by sire out of dam (owner)
                                            name_part = rest.split(', by ')[0].strip()
                                            after_by = rest.split(', by ', 1)[1]
                                            if ' out of ' in after_by:
                                                sire_part = after_by.split(' out of ', 1)[0].strip()
                                                after_out_of = after_by.split(' out of ', 1)[1]
                                                if ' (' in after_out_of:
                                                    dam_part = after_out_of.split(' (', 1)[0].strip()
                                                    owner_part = after_out_of.split(' (', 1)[1].rstrip(')').strip()
                                                else:
                                                    dam_part = after_out_of.strip()
                                                    owner_part = None
                                            else:
                                                sire_part = after_by.split(' (', 1)[0].strip() if ' (' in after_by else after_by.strip()
                                                dam_part = None
                                                owner_part = after_by.split(' (', 1)[1].rstrip(')').strip() if ' (' in after_by else None
                                            dog_name = name_part
                                            sire = sire_part
                                            dam = dam_part
                                            owner = owner_part
                                            parsed = True
                                        else:
                                            # Fallback: just extract number and treat rest as name
                                            dog_name = rest
                                            sire = None
                                            dam = None
                                            owner = None
                                            parsed = True
                                    else:
                                        # Skip lines that don't match (like "1st: ________")
                                        i += 1
                                        continue
            
            # Only proceed if we successfully parsed a dog entry
            if not parsed or not dog_num or not dog_name:
                                i += 1
                                continue
            
            # Determine sex from class name
            sex = None
            if current_class:
                class_lower = current_class.lower()
                # Check for bitches first (more specific)
                # Match "bitch", "bitches", "bitch pups", etc.
                if 'bitch' in class_lower or 'bitches' in class_lower:
                    sex = 'bitch'
                # Then check for dogs (males) - look for "dogs", "dog pups", "dog " (with spaces), etc.
                elif 'bitch' not in class_lower:
                    # Check for "dog pups", "dogs", " dog " (with spaces), or starts with "dog "
                    if ('dog pups' in class_lower or 'dogs' in class_lower or 
                        ' dog ' in class_lower or class_lower.startswith('dog ') or 
                        ', dog' in class_lower):
                        sex = 'dog'
                # Also check for "Pups" - need to infer from context or leave as None
            
            # Create or update dog entry
            if dog_num not in dogs:
                dogs[dog_num] = Dog(
                    number=dog_num,
                    name=dog_name,
                    sire=sire,
                    dam=dam,
                    owner=owner,
                    sex=sex
                )
            
            dog = dogs[dog_num]
            # Update sex if not set, or if current is 'unknown' and we have a better value
            if sex and (not dog.sex or dog.sex == 'unknown'):
                dog.sex = sex
            # Update other fields if not set (prefer existing data)
            if not dog.sire and sire:
                dog.sire = sire
            if not dog.dam and dam:
                dog.dam = dam
            if not dog.owner and owner:
                dog.owner = owner
            
            # Add class to dog's class list with year
            if current_class:
                class_entry = (current_class, year)
                if class_entry not in dog.classes:
                    dog.classes.append(class_entry)
            
            # Add dog to class
            if current_class_info:
                # Check if dog is already in this class's entries
                if dog not in current_class_info.entries:
                    current_class_info.entries.append(dog)
                    current_class_info.entry_count = len(current_class_info.entries)
        
        i += 1
    
    print(f"  parse_catalog returning: {len(classes)} classes, {len(dogs)} dogs")
    return classes, dogs


def normalize_for_matching(name: str) -> str:
    """Collapse whitespace and treat '&' as 'and' for name/owner matching."""
    if not name:
        return ''
    text = re.sub(r'\s+', ' ', name.strip().lower())
    text = re.sub(r"[''`]", '', text)
    text = re.sub(r'\s*&\s*', ' and ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_name(name: str) -> str:
    """Normalize dog name by removing ' of ...' suffix for relationship matching."""
    if not name:
        return name
    # Remove " of ..." suffix (case-insensitive)
    # Match " of " followed by any characters until end of string
    normalized = re.sub(r'\s+of\s+.*$', '', name, flags=re.IGNORECASE).strip()
    return normalized


def extract_trailing_letter_id(name: str) -> str | None:
    """Extract a single-letter kennel suffix like \"Q\" or trailing Q."""
    if not name:
        return None
    text = name.strip()
    match = re.search(r'"([A-Za-z])"\s*$', text)
    if match:
        return match.group(1).upper()
    match = re.search(r'\s([A-Za-z])\s*$', text)
    if match:
        return match.group(1).upper()
    return None


def same_prefix_different_letter_ids(name1: str, name2: str) -> bool:
    """True when names share a prefix but have different single-letter IDs (Q vs R)."""
    id1 = extract_trailing_letter_id(name1)
    id2 = extract_trailing_letter_id(name2)
    if not id1 or not id2 or id1 == id2:
        return False
    base1 = re.sub(r'\s*"?[A-Za-z]"?\s*$', '', name1).strip()
    base2 = re.sub(r'\s*"?[A-Za-z]"?\s*$', '', name2).strip()
    return (
        normalize_for_matching(normalize_name(base1))
        == normalize_for_matching(normalize_name(base2))
    )


def names_are_similar(name1: str, name2: str) -> bool:
    """Check if two dog names are similar (handling spaces, plurals, etc.).
    
    Examples:
    - "White Gate Bardot" vs "Whitegate Bardot" -> True
    - "Iron Spring Grace Note" vs "Iron Springs Grace Note" -> True
    - "Dog Name" vs "Different Dog Name" -> False
    """
    if not name1 or not name2:
        return False

    if same_prefix_different_letter_ids(name1, name2):
        return False
    
    # Normalize both names first (remove " of ..." suffix, unify &/and)
    norm1 = normalize_for_matching(normalize_name(name1))
    norm2 = normalize_for_matching(normalize_name(name2))
    
    # Exact match after normalization
    if norm1 == norm2:
        return True

    # Litter-style names (e.g. Harmony Chase Briggs/Bragg/Brooks) differ only in
    # the last word. Require an exact last-word match when the prefix is identical.
    words1 = norm1.split()
    words2 = norm2.split()
    if len(words1) >= 3 and len(words2) >= 3 and len(words1) == len(words2):
        if words1[:-1] == words2[:-1] and words1[-1] != words2[-1]:
            return False
    
    # Remove all spaces and compare
    no_space1 = re.sub(r'\s+', '', norm1)
    no_space2 = re.sub(r'\s+', '', norm2)
    if no_space1 == no_space2:
        return True
    
    # Handle singular/plural variations
    # Remove trailing 's' or 'es' and compare
    def remove_plural(word):
        if word.endswith('es'):
            return word[:-2]
        elif word.endswith('s'):
            return word[:-1]
        return word
    
    # Split into words and compare
    words1 = norm1.split()
    words2 = norm2.split()
    
    # If different number of words, try removing spaces and comparing
    if len(words1) != len(words2):
        # Try comparing without spaces
        if no_space1 == no_space2:
            return True
        # Try comparing with plural handling
        words1_no_plural = [remove_plural(w) for w in words1]
        words2_no_plural = [remove_plural(w) for w in words2]
        if words1_no_plural == words2_no_plural:
            return True
        # Try comparing without spaces and with plural handling
        no_space1_no_plural = ''.join(words1_no_plural)
        no_space2_no_plural = ''.join(words2_no_plural)
        if no_space1_no_plural == no_space2_no_plural:
            return True
    else:
        # Same number of words - compare word by word
        all_match = True
        for w1, w2 in zip(words1, words2):
            w1_base = remove_plural(w1)
            w2_base = remove_plural(w2)
            if w1_base != w2_base and w1 != w2:
                all_match = False
                break
        if all_match:
            return True
    
    # Use Levenshtein-like similarity for close matches
    # If names are very similar (only 1-2 character differences), consider them the same
    def simple_edit_distance(s1: str, s2: str) -> int:
        """Simple edit distance calculation."""
        if len(s1) < len(s2):
            return simple_edit_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    # Compare without spaces for edit distance
    edit_dist = simple_edit_distance(no_space1, no_space2)
    max_len = max(len(no_space1), len(no_space2))
    
    # If edit distance is small relative to length, consider similar
    # Allow up to 2 character differences for short names, or 1-2% difference for longer names
    if max_len > 0:
        similarity_ratio = 1 - (edit_dist / max_len)
        # For names like "Whitegate" vs "White Gate" (9 vs 10 chars), edit distance is 1
        # For "Iron Spring" vs "Iron Springs" (11 vs 12 chars), edit distance is 1
        if edit_dist <= 2 and similarity_ratio >= 0.85:
            return True
    
    return False


def find_canonical_name_for_similar_names(names: List[str]) -> str:
    """Find the canonical name for a group of similar names.
    
    Prefers:
    1. Name with " of ..." suffix (more complete)
    2. Longer name
    3. Name that appears first
    """
    if not names:
        return ""
    
    # Prefer names with " of ..." suffix
    names_with_suffix = [n for n in names if ' of ' in n.lower()]
    if names_with_suffix:
        # Among those, prefer the longest
        return max(names_with_suffix, key=len)
    
    # Otherwise, prefer the longest name
    return max(names, key=len)


# Global cache for similar name lookups to avoid redundant iterations
_similar_name_cache: Dict[str, Optional[str]] = {}
_similar_name_cache_initialized = False
# Global similarity map for fast lookups (set at start of find_relationships)
_similarity_map: Optional[Dict[str, str]] = None

def find_similar_name_in_dogs(name: str, dogs: Dict[str, Dog], normalized_name_to_keys: Dict[str, List[str]], 
                              similarity_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    global _similarity_map
    if similarity_map is None:
        similarity_map = _similarity_map
    """Find a similar name in the dogs dictionary.
    
    Returns the canonical key if a similar name is found, None otherwise.
    
    Args:
        name: The name to search for
        dogs: Dictionary of all dogs
        normalized_name_to_keys: Mapping of normalized names to dog keys
        similarity_map: Pre-computed similarity mapping (name -> canonical_key). If provided, uses this instead of iterating.
    """
    if not name:
        return None
    
    # Use cache if available
    cache_key = normalize_name(name)
    if cache_key in _similar_name_cache:
        return _similar_name_cache[cache_key]
    
    normalized_search = normalize_name(name)
    
    # First try exact normalized match
    if normalized_search in normalized_name_to_keys:
        result = normalized_name_to_keys[normalized_search][0]  # Return first match
        _similar_name_cache[cache_key] = result
        return result
    
    # Use pre-computed similarity map if provided (much faster)
    if similarity_map:
        if name in similarity_map:
            result = similarity_map[name]
            _similar_name_cache[cache_key] = result
            return result
        # Also check normalized version
        if normalized_search in similarity_map:
            result = similarity_map[normalized_search]
            _similar_name_cache[cache_key] = result
            return result
    
    # Then try similar name matching (slower, but only if similarity_map not provided)
    for norm_name, keys in normalized_name_to_keys.items():
        # Get actual dog name from first key
        if keys:
            dog = dogs[keys[0]]
            if names_are_similar(name, dog.name):
                result = keys[0]  # Return first match
                _similar_name_cache[cache_key] = result
                return result
    
    # Cache the None result too
    _similar_name_cache[cache_key] = None
    return None


def find_dog_keys_with_similar_matching(name: str, dogs: Dict[str, Dog], normalized_name_to_dog_nums: Dict[str, List[str]], 
                                        similarity_map: Optional[Dict[str, str]] = None) -> List[str]:
    global _similarity_map
    if similarity_map is None:
        similarity_map = _similarity_map
    """Find dog keys for a given name using both exact and similar name matching.
    
    Args:
        name: The name to search for
        dogs: Dictionary of all dogs
        normalized_name_to_dog_nums: Mapping of normalized names to dog keys
        similarity_map: Pre-computed similarity mapping (name -> canonical_key). If provided, uses this for faster lookups.
    
    Returns:
        List of dog keys that match the name (exact or similar)
    """
    if not name:
        return []
    
    # First try exact normalized match
    normalized_name = normalize_name(name)
    dog_keys = normalized_name_to_dog_nums.get(normalized_name, [])
    
    # If no exact match, try similar name matching
    if not dog_keys:
        similar_key = find_similar_name_in_dogs(name, dogs, normalized_name_to_dog_nums, similarity_map)
        if similar_key:
            dog_keys = [similar_key]
    
    return dog_keys


def is_parent_of(parent_name: str, child_sire: Optional[str], child_dam: Optional[str]) -> bool:
    """Check if a parent name matches a child's sire or dam using normalized and similar name matching.
    
    Args:
        parent_name: The name of the potential parent
        child_sire: The child's sire name (may be None)
        child_dam: The child's dam name (may be None)
    
    Returns:
        True if parent_name matches child_sire or child_dam (using normalized or similar matching)
    """
    if not parent_name:
        return False
    
    parent_normalized = normalize_name(parent_name)
    
    # Check sire
    if child_sire:
        child_sire_normalized = normalize_name(child_sire)
        if parent_normalized == child_sire_normalized:
            return True
        if names_are_similar(parent_name, child_sire):
            return True
    
    # Check dam
    if child_dam:
        child_dam_normalized = normalize_name(child_dam)
        if parent_normalized == child_dam_normalized:
            return True
        if names_are_similar(parent_name, child_dam):
            return True
    
    return False


def build_similarity_map(dogs: Dict[str, Dog], normalized_name_to_dog_nums: Dict[str, List[str]]) -> Dict[str, str]:
    """Pre-compute a similarity mapping to avoid redundant iterations.
    
    Returns a dict mapping: name -> canonical_key for all similar names.
    """
    print(f"  Pre-computing similarity mappings...")
    similarity_map = {}
    
    # Build initial mapping: each name maps to its canonical key
    name_list = []
    for dog_key, dog in dogs.items():
        normalized_name = normalize_name(dog.name)
        canonical_key = dog_key if dog_key == normalized_name else normalized_name
        similarity_map[dog.name] = canonical_key
        similarity_map[normalized_name] = canonical_key
        name_list.append((dog.name, normalized_name, canonical_key))
    
    # Group names by normalized prefix to reduce comparisons
    # Use first 8 characters of normalized name as grouping key
    name_groups = defaultdict(list)
    for name, normalized, canonical in name_list:
        prefix = normalized[:8] if len(normalized) >= 8 else normalized
        name_groups[prefix].append((name, normalized, canonical))
    
    # Only check for similar names within groups and adjacent groups
    # This dramatically reduces the number of comparisons
    processed = 0
    total = len(name_list)
    similar_count = 0
    
    # Sort groups for consistent processing
    sorted_groups = sorted(name_groups.items())
    
    for group_idx, (prefix, names_in_group) in enumerate(sorted_groups):
        # Check within group
        for i, (name1, norm1, canon1) in enumerate(names_in_group):
            for j, (name2, norm2, canon2) in enumerate(names_in_group[i+1:], start=i+1):
                # Skip if already mapped to same canonical key
                if similarity_map.get(name1) == similarity_map.get(name2):
                    continue
                if names_are_similar(name1, name2):
                    # Map name1 to name2's canonical key (use the one that's already in normalized_name_to_dog_nums)
                    if norm2 in normalized_name_to_dog_nums:
                        similarity_map[name1] = canon2
                        similarity_map[norm1] = canon2
                        similar_count += 1
                    elif norm1 in normalized_name_to_dog_nums:
                        similarity_map[name2] = canon1
                        similarity_map[norm2] = canon1
                        similar_count += 1
            processed += 1
            if processed % 1000 == 0:
                print(f"    Processed {processed}/{total} names, found {similar_count} similar matches...")
        
        # Also check adjacent groups (names might be similar across prefix boundaries)
        if group_idx < len(sorted_groups) - 1:
            next_prefix, next_names = sorted_groups[group_idx + 1]
            # Only check if prefixes are similar (e.g., "timberwil" vs "timberwi")
            if len(prefix) >= 6 and len(next_prefix) >= 6:
                if prefix[:6] == next_prefix[:6]:
                    for name1, norm1, canon1 in names_in_group:
                        for name2, norm2, canon2 in next_names:
                            if names_are_similar(name1, name2):
                                if norm2 in normalized_name_to_dog_nums:
                                    similarity_map[name1] = canon2
                                    similarity_map[norm1] = canon2
                                    similar_count += 1
                                elif norm1 in normalized_name_to_dog_nums:
                                    similarity_map[name2] = canon1
                                    similarity_map[norm2] = canon1
                                    similar_count += 1
    
    print(f"  Similarity mapping complete: {len(similarity_map)} total entries, {similar_count} similar matches found")
    return similarity_map


def find_relationships(dogs: Dict[str, Dog]) -> Dict[str, List[str]]:
    """Find family relationships between dogs."""
    relationships = defaultdict(list)
    
    print(f"  Building relationship mapping for {len(dogs)} dogs...")
    
    # Create a mapping of normalized dog names to dog numbers for faster lookup
    # Also create reverse mapping from normalized name to all possible name variations
    normalized_name_to_dog_nums = defaultdict(list)
    name_to_normalized = {}
    
    # Build mapping - keys in dogs dict are now normalized names
    for dog_key, dog in dogs.items():
        # dog_key is either a normalized name or a dog number
        # Normalize the dog's name to get the canonical key
        normalized_name = normalize_name(dog.name)
        # If the key is already a normalized name, use it; otherwise use the normalized name
        if dog_key == normalized_name:
            canonical_key = dog_key
        else:
            canonical_key = normalized_name
        normalized_name_to_dog_nums[normalized_name].append(canonical_key)
        name_to_normalized[dog.name] = normalized_name
    
    # Pre-compute similarity mapping for faster lookups
    global _similarity_map, _similar_name_cache
    _similarity_map = build_similarity_map(dogs, normalized_name_to_dog_nums)
    
    # Clear the cache to start fresh
    _similar_name_cache.clear()
    
    # Build reverse indexes: sire/dam -> list of dogs (for O(1) lookups instead of O(N) loops)
    print(f"  Building reverse indexes (sire/dam -> dogs)...")
    sire_to_dogs = defaultdict(list)  # Maps normalized sire name -> list of (dog_key, dog)
    dam_to_dogs = defaultdict(list)   # Maps normalized dam name -> list of (dog_key, dog)
    
    for dog_key, dog in dogs.items():
        canonical_key = normalize_name(dog.name) if dog_key != normalize_name(dog.name) else dog_key
        if dog.sire:
            # Use normalized sire name as the key (this is what we'll look up later)
            sire_normalized = normalize_name(dog.sire)
            sire_to_dogs[sire_normalized].append((canonical_key, dog))
        if dog.dam:
            # Use normalized dam name as the key (this is what we'll look up later)
            dam_normalized = normalize_name(dog.dam)
            dam_to_dogs[dam_normalized].append((canonical_key, dog))
    
    print(f"  Finding relationships for each dog...")
    total_dogs = len(dogs)
    processed = 0
    
    for dog_key, dog in dogs.items():
        processed += 1
        
        # Get canonical key (normalized name)
        dog_normalized_name = normalize_name(dog.name)
        canonical_key = dog_normalized_name if dog_key == dog_normalized_name else dog_normalized_name
        
        # Track relationships count before processing this dog
        relationships_before = len(relationships.get(canonical_key, []))
        
        # Display dog information
        dog_info = f"  [{processed}/{total_dogs}] {dog.name}"
        if dog.sex:
            dog_info += f" ({dog.sex})"
        if dog.sire:
            dog_info += f" | Sire: {dog.sire}"
        if dog.dam:
            dog_info += f" | Dam: {dog.dam}"
        if dog.owner:
            dog_info += f" | Owner: {dog.owner}"
        print(dog_info)
        
        dog_normalized_sire = normalize_name(dog.sire) if dog.sire else None
        dog_normalized_dam = normalize_name(dog.dam) if dog.dam else None
        
        # IMPORTANT: Find parents FIRST (sire and dam) - these should be listed first
        # Find parents (dogs that are the sire or dam of this dog, using normalized names and similar names)
        # Always add sire/dam to relationships if they exist, even if not found in catalog
        if dog.sire:
            # Check if normalized sire name matches any normalized dog name in catalog
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            
            if sire_dog_keys:
                # Parent found in catalog
                for sire_dog_key in sire_dog_keys:
                    if sire_dog_key != canonical_key:  # Don't relate to self
                        sire_dog = dogs[sire_dog_key]
                        sire_sex = sire_dog.sex or 'unknown'
                        relationships[canonical_key].append(f"Sire: {sire_dog.name} ({sire_sex})")
                        # Update dog's sire field to use the more complete name from catalog
                        # Prefer name with " of ..." suffix if available
                        if sire_dog.name:
                            if not dog.sire:
                                # No sire set, use the one from catalog
                                dog.sire = sire_dog.name
                            else:
                                # If catalog entry has more complete name (with " of ..."), use it
                                if ' of ' in sire_dog.name.lower() and ' of ' not in (dog.sire or '').lower():
                                    dog.sire = sire_dog.name
                                # If both have " of ..." or neither does, prefer the catalog entry's name
                                # (it's the authoritative source) if they normalize to the same name
                                elif normalize_name(sire_dog.name) == normalize_name(dog.sire):
                                    dog.sire = sire_dog.name
            else:
                # Parent not found in catalog, but still add to relationships (name is in dog's entry)
                relationships[canonical_key].append(f"Sire: {dog.sire}")
        
        if dog.dam:
            # Check if normalized dam name matches any normalized dog name in catalog
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            
            if dam_dog_keys:
                # Parent found in catalog
                for dam_dog_key in dam_dog_keys:
                    if dam_dog_key != canonical_key:  # Don't relate to self
                        dam_dog = dogs[dam_dog_key]
                        dam_sex = dam_dog.sex or 'unknown'
                        relationships[canonical_key].append(f"Dam: {dam_dog.name} ({dam_sex})")
                        # Update dog's dam field to use the more complete name from catalog
                        # Prefer name with " of ..." suffix if available
                        if dam_dog.name:
                            if not dog.dam:
                                # No dam set, use the one from catalog
                                dog.dam = dam_dog.name
                            else:
                                # If catalog entry has more complete name (with " of ..."), use it
                                if ' of ' in dam_dog.name.lower() and ' of ' not in (dog.dam or '').lower():
                                    dog.dam = dam_dog.name
                                # If both have " of ..." or neither does, prefer the catalog entry's name
                                # (it's the authoritative source) if they normalize to the same name
                                elif normalize_name(dam_dog.name) == normalize_name(dog.dam):
                                    dog.dam = dam_dog.name
            else:
                # Parent not found in catalog, but still add to relationships (name is in dog's entry)
                relationships[canonical_key].append(f"Dam: {dog.dam}")
        
        # Find siblings (full siblings: same sire AND same dam, or half-siblings: same sire OR same dam)
        # Use indexes instead of looping through all dogs
        siblings_by_sire = {}  # Maps canonical_key -> dog
        siblings_by_dam = {}   # Maps canonical_key -> dog
        
        if dog_normalized_sire:
            # Use the normalized sire name to look up in the index
            if dog_normalized_sire in sire_to_dogs:
                for other_canonical_key, other_dog in sire_to_dogs[dog_normalized_sire]:
                    if other_canonical_key != canonical_key:
                        siblings_by_sire[other_canonical_key] = other_dog
        
        if dog_normalized_dam:
            # Use the normalized dam name to look up in the index
            if dog_normalized_dam in dam_to_dogs:
                for other_canonical_key, other_dog in dam_to_dogs[dog_normalized_dam]:
                    if other_canonical_key != canonical_key:
                        siblings_by_dam[other_canonical_key] = other_dog
        
        # Full siblings: in both dicts
        full_siblings_keys = set(siblings_by_sire.keys()) & set(siblings_by_dam.keys())
        for other_canonical_key in full_siblings_keys:
            other = siblings_by_sire[other_canonical_key]
            other_sex = other.sex or 'unknown'
            relationships[canonical_key].append(f"Sibling: {other.name} ({other_sex})")
        
        # Half-siblings: in one dict but not both
        half_siblings_sire_keys = set(siblings_by_sire.keys()) - set(siblings_by_dam.keys())
        for other_canonical_key in half_siblings_sire_keys:
            other = siblings_by_sire[other_canonical_key]
            other_sex = other.sex or 'unknown'
            relationships[canonical_key].append(f"Half-sibling (same sire): {other.name} ({other_sex})")
        
        half_siblings_dam_keys = set(siblings_by_dam.keys()) - set(siblings_by_sire.keys())
        for other_canonical_key in half_siblings_dam_keys:
            other = siblings_by_dam[other_canonical_key]
            other_sex = other.sex or 'unknown'
            relationships[canonical_key].append(f"Half-sibling (same dam): {other.name} ({other_sex})")
        
        # Find offspring (children) - dogs where this dog is the sire or dam
        # Use reverse indexes for O(1) lookup instead of O(N) loop
        dog_normalized_name = normalize_name(dog.name)
        children = []
        
        # Find children where this dog is the sire
        if canonical_key in sire_to_dogs:
            for child_canonical_key, child_dog in sire_to_dogs[canonical_key]:
                if child_canonical_key != canonical_key:
                    child_sex = child_dog.sex or 'unknown'
                    if child_sex == 'dog':
                        relationships[canonical_key].append(f"Offspring (son): {child_dog.name} ({child_sex})")
                    elif child_sex == 'bitch':
                        relationships[canonical_key].append(f"Offspring (daughter): {child_dog.name} ({child_sex})")
                    else:
                        relationships[canonical_key].append(f"Offspring: {child_dog.name} ({child_sex})")
                    if child_dog not in children:
                        children.append(child_dog)
        
        # Find children where this dog is the dam
        if canonical_key in dam_to_dogs:
            for child_canonical_key, child_dog in dam_to_dogs[canonical_key]:
                if child_canonical_key != canonical_key:
                    child_sex = child_dog.sex or 'unknown'
                    if child_dog not in children:  # Avoid duplicates
                        if child_sex == 'dog':
                            relationships[canonical_key].append(f"Offspring (son): {child_dog.name} ({child_sex})")
                        elif child_sex == 'bitch':
                            relationships[canonical_key].append(f"Offspring (daughter): {child_dog.name} ({child_sex})")
                        else:
                            relationships[canonical_key].append(f"Offspring: {child_dog.name} ({child_sex})")
                        children.append(child_dog)
        
        # Find nieces and nephews (sibling's children)
        # Use the siblings we already found, then use indexes to find their children
        all_siblings_keys = full_siblings_keys | half_siblings_sire_keys | half_siblings_dam_keys
        for sibling_canonical_key in all_siblings_keys:
            # Get the sibling dog object
            if sibling_canonical_key in siblings_by_sire:
                sibling = siblings_by_sire[sibling_canonical_key]
            elif sibling_canonical_key in siblings_by_dam:
                sibling = siblings_by_dam[sibling_canonical_key]
            else:
                continue
            # Find children of this sibling using indexes
            if sibling_canonical_key in sire_to_dogs:
                for niece_nephew_key, niece_nephew in sire_to_dogs[sibling_canonical_key]:
                    if niece_nephew_key != canonical_key:
                        niece_nephew_sex = niece_nephew.sex or 'unknown'
                        if niece_nephew_sex == 'dog':
                            relationships[canonical_key].append(f"Nephew (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
                        elif niece_nephew_sex == 'bitch':
                            relationships[canonical_key].append(f"Niece (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
                        else:
                            relationships[canonical_key].append(f"Niece/Nephew (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
            
            if sibling_canonical_key in dam_to_dogs:
                for niece_nephew_key, niece_nephew in dam_to_dogs[sibling_canonical_key]:
                    if niece_nephew_key != canonical_key:
                        niece_nephew_sex = niece_nephew.sex or 'unknown'
                        if niece_nephew_sex == 'dog':
                            relationships[canonical_key].append(f"Nephew (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
                        elif niece_nephew_sex == 'bitch':
                            relationships[canonical_key].append(f"Niece (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
                        else:
                            relationships[canonical_key].append(f"Niece/Nephew (via {sibling.name}): {niece_nephew.name} ({niece_nephew_sex})")
        
        # Find grandchildren (children's children)
        # Use indexes, but need to check all possible name variations
        grandchildren = []
        for child in children:
            child_canonical_key = normalize_name(child.name)
            # Find all possible keys for this child (to handle name variations in sire/dam fields)
            child_sire_keys = find_dog_keys_with_similar_matching(child.name, dogs, normalized_name_to_dog_nums)
            # Also check the normalized name directly
            child_lookup_keys = set([child_canonical_key])
            for key in child_sire_keys:
                child_lookup_keys.add(normalize_name(dogs[key].name) if key in dogs else normalize_name(child.name))
            
            # Find children of this child using indexes (check all name variations)
            for lookup_key in child_lookup_keys:
                if lookup_key in sire_to_dogs:
                    for grandchild_key, grandchild in sire_to_dogs[lookup_key]:
                        if grandchild_key != canonical_key:
                            grandchild_sex = grandchild.sex or 'unknown'
                            if grandchild_sex == 'dog':
                                relationships[canonical_key].append(f"Grandson (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            elif grandchild_sex == 'bitch':
                                relationships[canonical_key].append(f"Granddaughter (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            else:
                                relationships[canonical_key].append(f"Grandchild (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            if grandchild not in grandchildren:
                                grandchildren.append(grandchild)
                
                if lookup_key in dam_to_dogs:
                    for grandchild_key, grandchild in dam_to_dogs[lookup_key]:
                        if grandchild_key != canonical_key:
                            grandchild_sex = grandchild.sex or 'unknown'
                            if grandchild_sex == 'dog':
                                relationships[canonical_key].append(f"Grandson (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            elif grandchild_sex == 'bitch':
                                relationships[canonical_key].append(f"Granddaughter (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            else:
                                relationships[canonical_key].append(f"Grandchild (via {child.name}): {grandchild.name} ({grandchild_sex})")
                            if grandchild not in grandchildren:
                                grandchildren.append(grandchild)
        
        # Find great-grandchildren (grandchildren's children)
        # Use indexes to find children of each grandchild
        great_grandchildren = []
        for grandchild in grandchildren:
            grandchild_canonical_key = normalize_name(grandchild.name)
            
            # Find children of this grandchild using indexes
            if grandchild_canonical_key in sire_to_dogs:
                for gg_child_key, gg_child in sire_to_dogs[grandchild_canonical_key]:
                    if gg_child_key != canonical_key:
                        gg_child_sex = gg_child.sex or 'unknown'
                        relationships[canonical_key].append(f"Great-grandchild (via {grandchild.name}): {gg_child.name} ({gg_child_sex})")
                        if gg_child not in great_grandchildren:
                            great_grandchildren.append(gg_child)
            
            if grandchild_canonical_key in dam_to_dogs:
                for gg_child_key, gg_child in dam_to_dogs[grandchild_canonical_key]:
                    if gg_child_key != canonical_key:
                        gg_child_sex = gg_child.sex or 'unknown'
                        relationships[canonical_key].append(f"Great-grandchild (via {grandchild.name}): {gg_child.name} ({gg_child_sex})")
                        if gg_child not in great_grandchildren:
                            great_grandchildren.append(gg_child)
        
        # Find great-great-grandchildren (great-grandchildren's children)
        # Use indexes, but need to check all possible name variations
        great_great_grandchildren = []
        for great_grandchild in great_grandchildren:
            great_grandchild_canonical_key = normalize_name(great_grandchild.name)
            # Find all possible keys for this great-grandchild (to handle name variations in sire/dam fields)
            great_grandchild_sire_keys = find_dog_keys_with_similar_matching(great_grandchild.name, dogs, normalized_name_to_dog_nums)
            great_grandchild_lookup_keys = set([great_grandchild_canonical_key])
            for key in great_grandchild_sire_keys:
                great_grandchild_lookup_keys.add(normalize_name(dogs[key].name) if key in dogs else normalize_name(great_grandchild.name))
            
            # Find children of this great-grandchild using indexes (check all name variations)
            for lookup_key in great_grandchild_lookup_keys:
                if lookup_key in sire_to_dogs:
                    for ggg_child_key, ggg_child in sire_to_dogs[lookup_key]:
                        if ggg_child_key != canonical_key:
                            ggg_child_sex = ggg_child.sex or 'unknown'
                            relationships[canonical_key].append(f"Great-great-grandchild (via {great_grandchild.name}): {ggg_child.name} ({ggg_child_sex})")
                            if ggg_child not in great_great_grandchildren:
                                great_great_grandchildren.append(ggg_child)
                
                if lookup_key in dam_to_dogs:
                    for ggg_child_key, ggg_child in dam_to_dogs[lookup_key]:
                        if ggg_child_key != canonical_key:
                            ggg_child_sex = ggg_child.sex or 'unknown'
                            relationships[canonical_key].append(f"Great-great-grandchild (via {great_grandchild.name}): {ggg_child.name} ({ggg_child_sex})")
                            if ggg_child not in great_great_grandchildren:
                                great_great_grandchildren.append(ggg_child)
        
        # Find great-great-great-grandchildren (great-great-grandchildren's children)
        # Use indexes, but need to check all possible name variations
        for great_great_grandchild in great_great_grandchildren:
            great_great_grandchild_canonical_key = normalize_name(great_great_grandchild.name)
            # Find all possible keys for this great-great-grandchild (to handle name variations in sire/dam fields)
            great_great_grandchild_sire_keys = find_dog_keys_with_similar_matching(great_great_grandchild.name, dogs, normalized_name_to_dog_nums)
            great_great_grandchild_lookup_keys = set([great_great_grandchild_canonical_key])
            for key in great_great_grandchild_sire_keys:
                great_great_grandchild_lookup_keys.add(normalize_name(dogs[key].name) if key in dogs else normalize_name(great_great_grandchild.name))
            
            # Find children of this great-great-grandchild using indexes (check all name variations)
            for lookup_key in great_great_grandchild_lookup_keys:
                if lookup_key in sire_to_dogs:
                    for gggg_child_key, gggg_child in sire_to_dogs[lookup_key]:
                        if gggg_child_key != canonical_key:
                            gggg_child_sex = gggg_child.sex or 'unknown'
                            relationships[canonical_key].append(f"Great-great-great-grandchild (via {great_great_grandchild.name}): {gggg_child.name} ({gggg_child_sex})")
                
                if lookup_key in dam_to_dogs:
                    for gggg_child_key, gggg_child in dam_to_dogs[lookup_key]:
                        if gggg_child_key != canonical_key:
                            gggg_child_sex = gggg_child.sex or 'unknown'
                            relationships[canonical_key].append(f"Great-great-great-grandchild (via {great_great_grandchild.name}): {gggg_child.name} ({gggg_child_sex})")
        
        # Find grandparents (parent's parent)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Grandsire (sire's sire)
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                grandsire_sex = grandsire_dog.sex or 'unknown'
                                relationships[canonical_key].append(f"Grandsire: {grandsire_dog.name} ({grandsire_sex})")
                    # Granddam (sire's dam)
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                granddam_sex = granddam_dog.sex or 'unknown'
                                relationships[canonical_key].append(f"Granddam: {granddam_dog.name} ({granddam_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Grandsire (dam's sire)
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                grandsire_sex = grandsire_dog.sex or 'unknown'
                                relationships[canonical_key].append(f"Grandsire: {grandsire_dog.name} ({grandsire_sex})")
                    # Granddam (dam's dam)
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(dam_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                granddam_sex = granddam_dog.sex or 'unknown'
                                relationships[canonical_key].append(f"Granddam: {granddam_dog.name} ({granddam_sex})")
        
        # Find great-grandparents (grandparent's parent)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Great-grandsire (sire's sire's sire/dam)
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            gg_sex = gg_sire_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-grandsire: {gg_sire_dog.name} ({gg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            gg_sex = gg_dam_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-granddam: {gg_dam_dog.name} ({gg_sex})")
                    # Great-grandsire (sire's dam's sire/dam)
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            gg_sex = gg_sire_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-grandsire: {gg_sire_dog.name} ({gg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            gg_sex = gg_dam_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-granddam: {gg_dam_dog.name} ({gg_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Great-grandsire (dam's sire's sire/dam)
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            gg_sex = gg_sire_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-grandsire: {gg_sire_dog.name} ({gg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            gg_sex = gg_dam_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-granddam: {gg_dam_dog.name} ({gg_sex})")
                    # Great-grandsire (dam's dam's sire/dam)
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(dam_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            gg_sex = gg_sire_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-grandsire: {gg_sire_dog.name} ({gg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            gg_sex = gg_dam_dog.sex or 'unknown'
                                            relationships[canonical_key].append(f"Great-granddam: {gg_dam_dog.name} ({gg_sex})")
        
        # Find great-great-grandparents (great-grandparent's parent)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Great-great-grandsire (sire's great-grandparents)
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                # Great-great-grandsire (sire's sire's great-grandparents)
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                    # Great-great-grandsire (sire's dam's great-grandparents)
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Great-great-grandsire (dam's great-grandparents) - similar logic
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(dam_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        ggg_sex = ggg_sire_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-grandsire: {ggg_sire_dog.name} ({ggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        ggg_sex = ggg_dam_dog.sex or 'unknown'
                                                        relationships[canonical_key].append(f"Great-great-granddam: {ggg_dam_dog.name} ({ggg_sex})")
        
        # Find great-great-great-grandparents (great-great-grandparent's parent)
        # This follows the same pattern but goes one generation further
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
        
        # Find great-great-great-grandparents (dam's side)
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                if grandsire_dog.sire:
                                    gg_sire_normalized = normalize_name(grandsire_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                if grandsire_dog.dam:
                                    gg_dam_normalized = normalize_name(grandsire_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(grandsire_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(dam_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                if granddam_dog.sire:
                                    gg_sire_normalized = normalize_name(granddam_dog.sire)
                                    gg_sire_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.sire, dogs, normalized_name_to_dog_nums)
                                    for gg_sire_dog_key in gg_sire_dog_keys:
                                        if gg_sire_dog_key != canonical_key:
                                            gg_sire_dog = dogs[gg_sire_dog_key]
                                            if gg_sire_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_sire_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_sire_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_sire_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                if granddam_dog.dam:
                                    gg_dam_normalized = normalize_name(granddam_dog.dam)
                                    gg_dam_dog_keys = find_dog_keys_with_similar_matching(granddam_dog.dam, dogs, normalized_name_to_dog_nums)
                                    for gg_dam_dog_key in gg_dam_dog_keys:
                                        if gg_dam_dog_key != canonical_key:
                                            gg_dam_dog = dogs[gg_dam_dog_key]
                                            if gg_dam_dog.sire:
                                                ggg_sire_normalized = normalize_name(gg_dam_dog.sire)
                                                ggg_sire_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                for ggg_sire_dog_key in ggg_sire_dog_keys:
                                                    if ggg_sire_dog_key != canonical_key:
                                                        ggg_sire_dog = dogs[ggg_sire_dog_key]
                                                        if ggg_sire_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_sire_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_sire_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_sire_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_sire_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
                                            if gg_dam_dog.dam:
                                                ggg_dam_normalized = normalize_name(gg_dam_dog.dam)
                                                ggg_dam_dog_keys = find_dog_keys_with_similar_matching(gg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                for ggg_dam_dog_key in ggg_dam_dog_keys:
                                                    if ggg_dam_dog_key != canonical_key:
                                                        ggg_dam_dog = dogs[ggg_dam_dog_key]
                                                        if ggg_dam_dog.sire:
                                                            gggg_sire_normalized = normalize_name(ggg_dam_dog.sire)
                                                            gggg_sire_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.sire, dogs, normalized_name_to_dog_nums)
                                                            for gggg_sire_dog_key in gggg_sire_dog_keys:
                                                                if gggg_sire_dog_key != canonical_key:
                                                                    gggg_sire_dog = dogs[gggg_sire_dog_key]
                                                                    gggg_sex = gggg_sire_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-grandsire: {gggg_sire_dog.name} ({gggg_sex})")
                                                        if ggg_dam_dog.dam:
                                                            gggg_dam_normalized = normalize_name(ggg_dam_dog.dam)
                                                            gggg_dam_dog_keys = find_dog_keys_with_similar_matching(ggg_dam_dog.dam, dogs, normalized_name_to_dog_nums)
                                                            for gggg_dam_dog_key in gggg_dam_dog_keys:
                                                                if gggg_dam_dog_key != canonical_key:
                                                                    gggg_dam_dog = dogs[gggg_dam_dog_key]
                                                                    gggg_sex = gggg_dam_dog.sex or 'unknown'
                                                                    relationships[canonical_key].append(f"Great-great-great-granddam: {gggg_dam_dog.name} ({gggg_sex})")
        
        # Find aunts/uncles (parent's siblings)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Find siblings of sire (aunts/uncles)
                    for other_key, other in dogs.items():
                        other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                        if canonical_key != other_canonical_key and other_canonical_key != sire_dog_key:
                            other_normalized_sire = normalize_name(other.sire) if other.sire else None
                            other_normalized_dam = normalize_name(other.dam) if other.dam else None
                            sire_normalized_sire = normalize_name(sire_dog.sire) if sire_dog.sire else None
                            sire_normalized_dam = normalize_name(sire_dog.dam) if sire_dog.dam else None
                            # Check if other is a sibling of sire (same parents) using similar name matching
                            same_parents = False
                            if (sire_normalized_sire and sire_normalized_dam and 
                                other_normalized_sire and other_normalized_dam):
                                if (other_normalized_sire == sire_normalized_sire and 
                                other_normalized_dam == sire_normalized_dam):
                                    same_parents = True
                                elif ((other.sire and sire_dog.sire and names_are_similar(other.sire, sire_dog.sire)) and
                                      (other.dam and sire_dog.dam and names_are_similar(other.dam, sire_dog.dam))):
                                    same_parents = True
                            
                            if same_parents:
                                other_sex = other.sex or 'unknown'
                                if other_sex == 'dog':
                                    relationships[canonical_key].append(f"Uncle: {other.name} ({other_sex})")
                                elif other_sex == 'bitch':
                                    relationships[canonical_key].append(f"Aunt: {other.name} ({other_sex})")
                                else:
                                    relationships[canonical_key].append(f"Aunt/Uncle: {other.name} ({other_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Find siblings of dam (aunts/uncles)
                    for other_key, other in dogs.items():
                        other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                        if canonical_key != other_canonical_key and other_canonical_key != dam_dog_key:
                            other_normalized_sire = normalize_name(other.sire) if other.sire else None
                            other_normalized_dam = normalize_name(other.dam) if other.dam else None
                            dam_normalized_sire = normalize_name(dam_dog.sire) if dam_dog.sire else None
                            dam_normalized_dam = normalize_name(dam_dog.dam) if dam_dog.dam else None
                            # Check if other is a sibling of dam (same parents) using similar name matching
                            same_parents = False
                            if (dam_normalized_sire and dam_normalized_dam and 
                                other_normalized_sire and other_normalized_dam):
                                if (other_normalized_sire == dam_normalized_sire and 
                                other_normalized_dam == dam_normalized_dam):
                                    same_parents = True
                                elif ((other.sire and dam_dog.sire and names_are_similar(other.sire, dam_dog.sire)) and
                                      (other.dam and dam_dog.dam and names_are_similar(other.dam, dam_dog.dam))):
                                    same_parents = True
                            
                            if same_parents:
                                other_sex = other.sex or 'unknown'
                                if other_sex == 'dog':
                                    relationships[canonical_key].append(f"Uncle: {other.name} ({other_sex})")
                                elif other_sex == 'bitch':
                                    relationships[canonical_key].append(f"Aunt: {other.name} ({other_sex})")
                                else:
                                    relationships[canonical_key].append(f"Aunt/Uncle: {other.name} ({other_sex})")
        
        # Find great-aunts/uncles (grandparent's siblings)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Check grandsire's siblings
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                # Find siblings of grandsire
                                for other_key, other in dogs.items():
                                    other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                                    if canonical_key != other_canonical_key and other_canonical_key != grandsire_dog_key:
                                        other_normalized_sire = normalize_name(other.sire) if other.sire else None
                                        other_normalized_dam = normalize_name(other.dam) if other.dam else None
                                        gs_normalized_sire = normalize_name(grandsire_dog.sire) if grandsire_dog.sire else None
                                        gs_normalized_dam = normalize_name(grandsire_dog.dam) if grandsire_dog.dam else None
                                        if (gs_normalized_sire and gs_normalized_dam and 
                                            other_normalized_sire == gs_normalized_sire and 
                                            other_normalized_dam == gs_normalized_dam):
                                            other_sex = other.sex or 'unknown'
                                            if other_sex == 'dog':
                                                relationships[canonical_key].append(f"Great-uncle: {other.name} ({other_sex})")
                                            elif other_sex == 'bitch':
                                                relationships[canonical_key].append(f"Great-aunt: {other.name} ({other_sex})")
                                            else:
                                                relationships[canonical_key].append(f"Great-aunt/uncle: {other.name} ({other_sex})")
                    # Check granddam's siblings
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                # Find siblings of granddam
                                for other_key, other in dogs.items():
                                    other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                                    if canonical_key != other_canonical_key and other_canonical_key != granddam_dog_key:
                                        other_normalized_sire = normalize_name(other.sire) if other.sire else None
                                        other_normalized_dam = normalize_name(other.dam) if other.dam else None
                                        gd_normalized_sire = normalize_name(granddam_dog.sire) if granddam_dog.sire else None
                                        gd_normalized_dam = normalize_name(granddam_dog.dam) if granddam_dog.dam else None
                                        # Check if other is a sibling of granddam using similar name matching
                                        same_granddam_parents = False
                                        if (gd_normalized_sire and gd_normalized_dam and 
                                            other_normalized_sire and other_normalized_dam):
                                            if (other_normalized_sire == gd_normalized_sire and 
                                            other_normalized_dam == gd_normalized_dam):
                                                same_granddam_parents = True
                                            elif ((other.sire and granddam_dog.sire and names_are_similar(other.sire, granddam_dog.sire)) and
                                                  (other.dam and granddam_dog.dam and names_are_similar(other.dam, granddam_dog.dam))):
                                                same_granddam_parents = True
                                        
                                        if same_granddam_parents:
                                            other_sex = other.sex or 'unknown'
                                            if other_sex == 'dog':
                                                relationships[canonical_key].append(f"Great-uncle: {other.name} ({other_sex})")
                                            elif other_sex == 'bitch':
                                                relationships[canonical_key].append(f"Great-aunt: {other.name} ({other_sex})")
                                            else:
                                                relationships[canonical_key].append(f"Great-aunt/uncle: {other.name} ({other_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Check grandsire's siblings
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                # Find siblings of grandsire
                                for other_key, other in dogs.items():
                                    other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                                    if canonical_key != other_canonical_key and other_canonical_key != grandsire_dog_key:
                                        other_normalized_sire = normalize_name(other.sire) if other.sire else None
                                        other_normalized_dam = normalize_name(other.dam) if other.dam else None
                                        gs_normalized_sire = normalize_name(grandsire_dog.sire) if grandsire_dog.sire else None
                                        gs_normalized_dam = normalize_name(grandsire_dog.dam) if grandsire_dog.dam else None
                                        if (gs_normalized_sire and gs_normalized_dam and 
                                            other_normalized_sire == gs_normalized_sire and 
                                            other_normalized_dam == gs_normalized_dam):
                                            other_sex = other.sex or 'unknown'
                                            if other_sex == 'dog':
                                                relationships[canonical_key].append(f"Great-uncle: {other.name} ({other_sex})")
                                            elif other_sex == 'bitch':
                                                relationships[canonical_key].append(f"Great-aunt: {other.name} ({other_sex})")
                                            else:
                                                relationships[canonical_key].append(f"Great-aunt/uncle: {other.name} ({other_sex})")
                    # Check granddam's siblings
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                # Find siblings of granddam
                                for other_key, other in dogs.items():
                                    other_canonical_key = normalize_name(other.name) if other_key != normalize_name(other.name) else other_key
                                    if canonical_key != other_canonical_key and other_canonical_key != granddam_dog_key:
                                        other_normalized_sire = normalize_name(other.sire) if other.sire else None
                                        other_normalized_dam = normalize_name(other.dam) if other.dam else None
                                        gd_normalized_sire = normalize_name(granddam_dog.sire) if granddam_dog.sire else None
                                        gd_normalized_dam = normalize_name(granddam_dog.dam) if granddam_dog.dam else None
                                        # Check if other is a sibling of granddam using similar name matching
                                        same_granddam_parents = False
                                        if (gd_normalized_sire and gd_normalized_dam and 
                                            other_normalized_sire and other_normalized_dam):
                                            if (other_normalized_sire == gd_normalized_sire and 
                                            other_normalized_dam == gd_normalized_dam):
                                                same_granddam_parents = True
                                            elif ((other.sire and granddam_dog.sire and names_are_similar(other.sire, granddam_dog.sire)) and
                                                  (other.dam and granddam_dog.dam and names_are_similar(other.dam, granddam_dog.dam))):
                                                same_granddam_parents = True
                                        
                                        if same_granddam_parents:
                                            other_sex = other.sex or 'unknown'
                                            if other_sex == 'dog':
                                                relationships[canonical_key].append(f"Great-uncle: {other.name} ({other_sex})")
                                            elif other_sex == 'bitch':
                                                relationships[canonical_key].append(f"Great-aunt: {other.name} ({other_sex})")
                                            else:
                                                relationships[canonical_key].append(f"Great-aunt/uncle: {other.name} ({other_sex})")
        
        # Find 1st cousins (parent's sibling's children)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Find siblings of sire
                    for aunt_uncle_key, aunt_uncle in dogs.items():
                        au_canonical_key = normalize_name(aunt_uncle.name) if aunt_uncle_key != normalize_name(aunt_uncle.name) else aunt_uncle_key
                        if canonical_key != au_canonical_key and au_canonical_key != sire_dog_key:
                            au_normalized_sire = normalize_name(aunt_uncle.sire) if aunt_uncle.sire else None
                            au_normalized_dam = normalize_name(aunt_uncle.dam) if aunt_uncle.dam else None
                            sire_normalized_sire = normalize_name(sire_dog.sire) if sire_dog.sire else None
                            sire_normalized_dam = normalize_name(sire_dog.dam) if sire_dog.dam else None
                            # Check if aunt_uncle is a sibling of sire using similar name matching
                            same_sire_parents = False
                            if sire_normalized_sire and sire_normalized_dam and au_normalized_sire and au_normalized_dam:
                                if (au_normalized_sire == sire_normalized_sire and 
                                au_normalized_dam == sire_normalized_dam):
                                    same_sire_parents = True
                                elif ((aunt_uncle.sire and sire_dog.sire and names_are_similar(aunt_uncle.sire, sire_dog.sire)) and
                                      (aunt_uncle.dam and sire_dog.dam and names_are_similar(aunt_uncle.dam, sire_dog.dam))):
                                    same_sire_parents = True
                            
                            if same_sire_parents:
                                # Find children of this aunt/uncle (1st cousins) using indexes
                                aunt_uncle_canonical = normalize_name(aunt_uncle.name)
                                # Find all possible keys for this aunt/uncle (to handle name variations)
                                aunt_uncle_keys = find_dog_keys_with_similar_matching(aunt_uncle.name, dogs, normalized_name_to_dog_nums)
                                aunt_uncle_lookup_keys = set([aunt_uncle_canonical])
                                for key in aunt_uncle_keys:
                                    aunt_uncle_lookup_keys.add(normalize_name(dogs[key].name) if key in dogs else normalize_name(aunt_uncle.name))
                                
                                # Use indexes to find children of this aunt/uncle
                                for lookup_key in aunt_uncle_lookup_keys:
                                    if lookup_key in sire_to_dogs:
                                        for cousin_key, cousin in sire_to_dogs[lookup_key]:
                                            if cousin_key != canonical_key:
                                                cousin_sex = cousin.sex or 'unknown'
                                                parent_relation = "sire's" if dog.sire and normalize_name(dog.sire) == normalize_name(sire_dog.name) else "dam's"
                                                relationships[canonical_key].append(f"1st Cousin (via {parent_relation} sibling {aunt_uncle.name}): {cousin.name} ({cousin_sex})")
                                    
                                    if lookup_key in dam_to_dogs:
                                        for cousin_key, cousin in dam_to_dogs[lookup_key]:
                                            if cousin_key != canonical_key:
                                                cousin_sex = cousin.sex or 'unknown'
                                                parent_relation = "sire's" if dog.sire and normalize_name(dog.sire) == normalize_name(sire_dog.name) else "dam's"
                                                relationships[canonical_key].append(f"1st Cousin (via {parent_relation} sibling {aunt_uncle.name}): {cousin.name} ({cousin_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Find siblings of dam
                    for aunt_uncle_key, aunt_uncle in dogs.items():
                        au_canonical_key = normalize_name(aunt_uncle.name) if aunt_uncle_key != normalize_name(aunt_uncle.name) else aunt_uncle_key
                        if canonical_key != au_canonical_key and au_canonical_key != dam_dog_key:
                            au_normalized_sire = normalize_name(aunt_uncle.sire) if aunt_uncle.sire else None
                            au_normalized_dam = normalize_name(aunt_uncle.dam) if aunt_uncle.dam else None
                            dam_normalized_sire = normalize_name(dam_dog.sire) if dam_dog.sire else None
                            dam_normalized_dam = normalize_name(dam_dog.dam) if dam_dog.dam else None
                            # Check if aunt_uncle is a sibling of dam using similar name matching
                            same_dam_parents = False
                            if dam_normalized_sire and dam_normalized_dam and au_normalized_sire and au_normalized_dam:
                                if (au_normalized_sire == dam_normalized_sire and 
                                au_normalized_dam == dam_normalized_dam):
                                    same_dam_parents = True
                                elif ((aunt_uncle.sire and dam_dog.sire and names_are_similar(aunt_uncle.sire, dam_dog.sire)) and
                                      (aunt_uncle.dam and dam_dog.dam and names_are_similar(aunt_uncle.dam, dam_dog.dam))):
                                    same_dam_parents = True
                            
                            if same_dam_parents:
                                # Find children of this aunt/uncle (1st cousins) using indexes
                                aunt_uncle_canonical = normalize_name(aunt_uncle.name)
                                # Find all possible keys for this aunt/uncle (to handle name variations)
                                aunt_uncle_keys = find_dog_keys_with_similar_matching(aunt_uncle.name, dogs, normalized_name_to_dog_nums)
                                aunt_uncle_lookup_keys = set([aunt_uncle_canonical])
                                for key in aunt_uncle_keys:
                                    aunt_uncle_lookup_keys.add(normalize_name(dogs[key].name) if key in dogs else normalize_name(aunt_uncle.name))
                                
                                # Use indexes to find children of this aunt/uncle
                                for lookup_key in aunt_uncle_lookup_keys:
                                    if lookup_key in sire_to_dogs:
                                        for cousin_key, cousin in sire_to_dogs[lookup_key]:
                                            if cousin_key != canonical_key:
                                                cousin_sex = cousin.sex or 'unknown'
                                                relationships[canonical_key].append(f"1st Cousin (via dam's sibling {aunt_uncle.name}): {cousin.name} ({cousin_sex})")
                                    
                                    if lookup_key in dam_to_dogs:
                                        for cousin_key, cousin in dam_to_dogs[lookup_key]:
                                            if cousin_key != canonical_key:
                                                cousin_sex = cousin.sex or 'unknown'
                                                relationships[canonical_key].append(f"1st Cousin (via dam's sibling {aunt_uncle.name}): {cousin.name} ({cousin_sex})")
        
        # Find 2nd cousins (grandparent's sibling's grandchildren)
        if dog.sire:
            sire_dog_keys = find_dog_keys_with_similar_matching(dog.sire, dogs, normalized_name_to_dog_nums)
            for sire_dog_key in sire_dog_keys:
                if sire_dog_key != canonical_key:
                    sire_dog = dogs[sire_dog_key]
                    # Check grandsire's siblings
                    if sire_dog.sire:
                        grandsire_normalized = normalize_name(sire_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(sire_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                # Find siblings of grandsire (great-aunts/uncles)
                                for great_au_key, great_au in dogs.items():
                                    gau_canonical_key = normalize_name(great_au.name) if great_au_key != normalize_name(great_au.name) else great_au_key
                                    if canonical_key != gau_canonical_key and gau_canonical_key != grandsire_dog_key:
                                        gau_normalized_sire = normalize_name(great_au.sire) if great_au.sire else None
                                        gau_normalized_dam = normalize_name(great_au.dam) if great_au.dam else None
                                        gs_normalized_sire = normalize_name(grandsire_dog.sire) if grandsire_dog.sire else None
                                        gs_normalized_dam = normalize_name(grandsire_dog.dam) if grandsire_dog.dam else None
                                        if (gs_normalized_sire and gs_normalized_dam and 
                                            gau_normalized_sire == gs_normalized_sire and 
                                            gau_normalized_dam == gs_normalized_dam):
                                            # Find children of great-aunt/uncle (1st cousins once removed)
                                            for cousin1_key, cousin1 in dogs.items():
                                                c1_canonical_key = normalize_name(cousin1.name) if cousin1_key != normalize_name(cousin1.name) else cousin1_key
                                                if canonical_key != c1_canonical_key:
                                                    # Check if great-aunt/uncle is parent of cousin1 using helper function
                                                    if is_parent_of(great_au.name, cousin1.sire, cousin1.dam):
                                                        # Find children of these 1st cousins once removed (2nd cousins)
                                                        for cousin2_key, cousin2 in dogs.items():
                                                            cousin2_canonical_key = normalize_name(cousin2.name) if cousin2_key != normalize_name(cousin2.name) else cousin2_key
                                                            if canonical_key != cousin2_canonical_key:
                                                                # Check if cousin1 is parent of cousin2 using helper function
                                                                if is_parent_of(cousin1.name, cousin2.sire, cousin2.dam):
                                                                    cousin2_sex = cousin2.sex or 'unknown'
                                                                    # Show relationship: 2nd cousin = grandparent's sibling's grandchild
                                                                    relationships[canonical_key].append(f"2nd Cousin (via grandparent's sibling {great_au.name}): {cousin2.name} ({cousin2_sex})")
                    # Check granddam's siblings
                    if sire_dog.dam:
                        granddam_normalized = normalize_name(sire_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(sire_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                # Find siblings of granddam (great-aunts/uncles)
                                for great_au_key, great_au in dogs.items():
                                    gau_canonical_key = normalize_name(great_au.name) if great_au_key != normalize_name(great_au.name) else great_au_key
                                    if canonical_key != gau_canonical_key and gau_canonical_key != granddam_dog_key:
                                        gau_normalized_sire = normalize_name(great_au.sire) if great_au.sire else None
                                        gau_normalized_dam = normalize_name(great_au.dam) if great_au.dam else None
                                        gd_normalized_sire = normalize_name(granddam_dog.sire) if granddam_dog.sire else None
                                        gd_normalized_dam = normalize_name(granddam_dog.dam) if granddam_dog.dam else None
                                        # Check if great_au is a sibling of granddam using similar name matching
                                        same_granddam_parents = False
                                        if (gd_normalized_sire and gd_normalized_dam and 
                                            gau_normalized_sire and gau_normalized_dam):
                                            if (gau_normalized_sire == gd_normalized_sire and 
                                            gau_normalized_dam == gd_normalized_dam):
                                                same_granddam_parents = True
                                            elif ((great_au.sire and granddam_dog.sire and names_are_similar(great_au.sire, granddam_dog.sire)) and
                                                  (great_au.dam and granddam_dog.dam and names_are_similar(great_au.dam, granddam_dog.dam))):
                                                same_granddam_parents = True
                                        
                                        if same_granddam_parents:
                                            # Find children of great-aunt/uncle (1st cousins once removed)
                                            for cousin1_key, cousin1 in dogs.items():
                                                c1_canonical_key = normalize_name(cousin1.name) if cousin1_key != normalize_name(cousin1.name) else cousin1_key
                                                if canonical_key != c1_canonical_key:
                                                    # Check if great-aunt/uncle is parent of cousin1 using helper function
                                                    if is_parent_of(great_au.name, cousin1.sire, cousin1.dam):
                                                        # Find children of these 1st cousins once removed (2nd cousins)
                                                        for cousin2_key, cousin2 in dogs.items():
                                                            cousin2_canonical_key = normalize_name(cousin2.name) if cousin2_key != normalize_name(cousin2.name) else cousin2_key
                                                            if canonical_key != cousin2_canonical_key:
                                                                # Check if cousin1 is parent of cousin2 using helper function
                                                                if is_parent_of(cousin1.name, cousin2.sire, cousin2.dam):
                                                                    cousin2_sex = cousin2.sex or 'unknown'
                                                                    # Show relationship: 2nd cousin = grandparent's sibling's grandchild
                                                                    relationships[canonical_key].append(f"2nd Cousin (via grandparent's sibling {great_au.name}): {cousin2.name} ({cousin2_sex})")
        
        if dog.dam:
            dam_dog_keys = find_dog_keys_with_similar_matching(dog.dam, dogs, normalized_name_to_dog_nums)
            for dam_dog_key in dam_dog_keys:
                if dam_dog_key != canonical_key:
                    dam_dog = dogs[dam_dog_key]
                    # Check grandsire's siblings
                    if dam_dog.sire:
                        grandsire_normalized = normalize_name(dam_dog.sire)
                        grandsire_dog_keys = find_dog_keys_with_similar_matching(dam_dog.sire, dogs, normalized_name_to_dog_nums)
                        for grandsire_dog_key in grandsire_dog_keys:
                            if grandsire_dog_key != canonical_key:
                                grandsire_dog = dogs[grandsire_dog_key]
                                # Find siblings of grandsire (great-aunts/uncles)
                                for great_au_key, great_au in dogs.items():
                                    gau_canonical_key = normalize_name(great_au.name) if great_au_key != normalize_name(great_au.name) else great_au_key
                                    if canonical_key != gau_canonical_key and gau_canonical_key != grandsire_dog_key:
                                        gau_normalized_sire = normalize_name(great_au.sire) if great_au.sire else None
                                        gau_normalized_dam = normalize_name(great_au.dam) if great_au.dam else None
                                        gs_normalized_sire = normalize_name(grandsire_dog.sire) if grandsire_dog.sire else None
                                        gs_normalized_dam = normalize_name(grandsire_dog.dam) if grandsire_dog.dam else None
                                        if (gs_normalized_sire and gs_normalized_dam and 
                                            gau_normalized_sire == gs_normalized_sire and 
                                            gau_normalized_dam == gs_normalized_dam):
                                            # Find children of great-aunt/uncle (1st cousins once removed)
                                            for cousin1_key, cousin1 in dogs.items():
                                                c1_canonical_key = normalize_name(cousin1.name) if cousin1_key != normalize_name(cousin1.name) else cousin1_key
                                                if canonical_key != c1_canonical_key:
                                                    # Check if great-aunt/uncle is parent of cousin1 using helper function
                                                    if is_parent_of(great_au.name, cousin1.sire, cousin1.dam):
                                                        # Find children of these 1st cousins once removed (2nd cousins)
                                                        for cousin2_key, cousin2 in dogs.items():
                                                            cousin2_canonical_key = normalize_name(cousin2.name) if cousin2_key != normalize_name(cousin2.name) else cousin2_key
                                                            if canonical_key != cousin2_canonical_key:
                                                                # Check if cousin1 is parent of cousin2 using helper function
                                                                if is_parent_of(cousin1.name, cousin2.sire, cousin2.dam):
                                                                    cousin2_sex = cousin2.sex or 'unknown'
                                                                    # Show relationship: 2nd cousin = grandparent's sibling's grandchild
                                                                    relationships[canonical_key].append(f"2nd Cousin (via grandparent's sibling {great_au.name}): {cousin2.name} ({cousin2_sex})")
                    # Check granddam's siblings
                    if dam_dog.dam:
                        granddam_normalized = normalize_name(dam_dog.dam)
                        granddam_dog_keys = find_dog_keys_with_similar_matching(dam_dog.dam, dogs, normalized_name_to_dog_nums)
                        for granddam_dog_key in granddam_dog_keys:
                            if granddam_dog_key != canonical_key:
                                granddam_dog = dogs[granddam_dog_key]
                                # Find siblings of granddam (great-aunts/uncles)
                                for great_au_key, great_au in dogs.items():
                                    gau_canonical_key = normalize_name(great_au.name) if great_au_key != normalize_name(great_au.name) else great_au_key
                                    if canonical_key != gau_canonical_key and gau_canonical_key != granddam_dog_key:
                                        gau_normalized_sire = normalize_name(great_au.sire) if great_au.sire else None
                                        gau_normalized_dam = normalize_name(great_au.dam) if great_au.dam else None
                                        gd_normalized_sire = normalize_name(granddam_dog.sire) if granddam_dog.sire else None
                                        gd_normalized_dam = normalize_name(granddam_dog.dam) if granddam_dog.dam else None
                                        # Check if great_au is a sibling of granddam using similar name matching
                                        same_granddam_parents = False
                                        if (gd_normalized_sire and gd_normalized_dam and 
                                            gau_normalized_sire and gau_normalized_dam):
                                            if (gau_normalized_sire == gd_normalized_sire and 
                                            gau_normalized_dam == gd_normalized_dam):
                                                same_granddam_parents = True
                                            elif ((great_au.sire and granddam_dog.sire and names_are_similar(great_au.sire, granddam_dog.sire)) and
                                                  (great_au.dam and granddam_dog.dam and names_are_similar(great_au.dam, granddam_dog.dam))):
                                                same_granddam_parents = True
                                        
                                        if same_granddam_parents:
                                            # Find children of great-aunt/uncle (1st cousins once removed)
                                            for cousin1_key, cousin1 in dogs.items():
                                                c1_canonical_key = normalize_name(cousin1.name) if cousin1_key != normalize_name(cousin1.name) else cousin1_key
                                                if canonical_key != c1_canonical_key:
                                                    # Check if great-aunt/uncle is parent of cousin1 using helper function
                                                    if is_parent_of(great_au.name, cousin1.sire, cousin1.dam):
                                                        # Find children of these 1st cousins once removed (2nd cousins)
                                                        for cousin2_key, cousin2 in dogs.items():
                                                            cousin2_canonical_key = normalize_name(cousin2.name) if cousin2_key != normalize_name(cousin2.name) else cousin2_key
                                                            if canonical_key != cousin2_canonical_key:
                                                                # Check if cousin1 is parent of cousin2 using helper function
                                                                if is_parent_of(cousin1.name, cousin2.sire, cousin2.dam):
                                                                    cousin2_sex = cousin2.sex or 'unknown'
                                                                    # Show relationship: 2nd cousin = grandparent's sibling's grandchild
                                                                    relationships[canonical_key].append(f"2nd Cousin (via grandparent's sibling {great_au.name}): {cousin2.name} ({cousin2_sex})")
                                                                    # Find children of 2nd cousins (3rd cousins)
                                                                    for cousin3_key, cousin3 in dogs.items():
                                                                        cousin3_canonical_key = normalize_name(cousin3.name) if cousin3_key != normalize_name(cousin3.name) else cousin3_key
                                                                        if canonical_key != cousin3_canonical_key:
                                                                            # Check if cousin2 is parent of cousin3 using helper function
                                                                            if is_parent_of(cousin2.name, cousin3.sire, cousin3.dam):
                                                                                cousin3_sex = cousin3.sex or 'unknown'
                                                                                # Show relationship: 3rd cousin = great-grandparent's sibling's great-grandchild
                                                                                relationships[canonical_key].append(f"3rd Cousin (via great-grandparent's sibling {great_au.name}): {cousin3.name} ({cousin3_sex})")
        
        # Track relationships count after processing this dog
        relationships_after = len(relationships.get(canonical_key, []))
        relationships_found = relationships_after - relationships_before
        
        # Show breakdown of relationship types found
        if relationships_found > 0:
            rel_list = relationships.get(canonical_key, [])
            # Count by type
            rel_types = {}
            for rel in rel_list:
                # Extract relationship type (first word before colon or space)
                rel_type = rel.split(':')[0].split(' ')[0] if ':' in rel or ' ' in rel else rel
                if rel_type not in rel_types:
                    rel_types[rel_type] = 0
                rel_types[rel_type] += 1
            
            type_summary = ", ".join([f"{count} {rtype}" for rtype, count in sorted(rel_types.items())])
            print(f"      -> Found {relationships_found} relationship(s) for {dog.name}: {type_summary}")
        else:
            print(f"      -> No relationships found for {dog.name}")
    
    print(f"  Completed finding relationships. Found relationships for {len([k for k, v in relationships.items() if v])} dogs.")
    return relationships


def organize_relationships(rels: List[str]) -> List[str]:
    """Organize relationships by type and sort alphabetically within each type.
    
    Returns relationships in a logical order:
    1. Parents (Sire, Dam)
    2. Siblings (Sibling, Half-sibling)
    3. Offspring
    4. Grandparents (Grandsire, Granddam)
    5. Grandchildren
    6. Great-grandparents
    7. Great-grandchildren
    8. Great-great-grandparents
    9. Great-great-grandchildren
    10. Great-great-great-grandparents
    11. Great-great-great-grandchildren
    12. Aunts/Uncles
    13. Great-aunts/uncles
    14. Nieces/Nephews
    15. Cousins (1st, 2nd, 3rd)
    """
    # Define relationship type order - check in order of specificity
    type_patterns = [
        ("Sire:", 1),
        ("Dam:", 2),
        ("Sibling:", 3),
        ("Half-sibling (same sire):", 4),
        ("Half-sibling (same dam):", 5),
        ("Offspring (son):", 6),
        ("Offspring (daughter):", 6),
        ("Offspring:", 6),
        ("Grandsire:", 7),
        ("Granddam:", 8),
        ("Grandson", 9),
        ("Granddaughter", 10),
        ("Grandchild", 11),
        ("Great-grandsire:", 12),
        ("Great-granddam:", 13),
        ("Great-grandchild", 14),
        ("Great-great-grandsire:", 15),
        ("Great-great-granddam:", 16),
        ("Great-great-grandchild", 17),
        ("Great-great-great-grandsire:", 18),
        ("Great-great-great-granddam:", 19),
        ("Great-great-great-grandchild", 20),
        ("Aunt:", 21),
        ("Uncle:", 22),
        ("Aunt/Uncle:", 23),
        ("Great-aunt:", 24),
        ("Great-uncle:", 25),
        ("Great-aunt/uncle:", 26),
        ("Niece (via", 27),
        ("Nephew (via", 28),
        ("Niece/Nephew (via", 29),
        ("1st Cousin", 30),
        ("2nd Cousin", 31),
        ("3rd Cousin", 32),
    ]
    
    # Group relationships by type
    grouped = {}
    for rel in rels:
        # Determine the relationship type by checking patterns in order
        rel_type_order = None
        for pattern, order in type_patterns:
            if rel.startswith(pattern):
                rel_type_order = order
                break
        
        if rel_type_order is None:
            # Unknown type, put at end
            rel_type_order = 999
        
        if rel_type_order not in grouped:
            grouped[rel_type_order] = []
        grouped[rel_type_order].append(rel)
    
    # Sort each group alphabetically
    for rel_type_order in grouped:
        grouped[rel_type_order].sort()
    
    # Build sorted list in order
    sorted_rels = []
    for order in sorted(grouped.keys()):
        sorted_rels.extend(grouped[order])
    
    return sorted_rels


def generate_report(classes: Dict[str, ClassInfo], dogs: Dict[str, Dog], relationships: Dict[str, List[str]], years: List[str]) -> str:
    """Generate a comprehensive report."""
    report = []
    years_str = ", ".join(sorted(years))
    report.append("=" * 80)
    report.append(f"ENTRIES CATALOG - COMPREHENSIVE REPORT ({years_str})")
    report.append("=" * 80)
    report.append("")
    
    # Summary statistics
    report.append("SUMMARY STATISTICS")
    report.append("-" * 80)
    report.append(f"Years: {years_str}")
    report.append(f"Total Classes: {len(classes)}")
    report.append(f"Total Dogs: {len(dogs)}")
    report.append(f"Total Entries: {sum(len(c.entries) for c in classes.values())}")
    report.append("")
    
    # Class summaries - group by year, then division, then section
    report.append("=" * 80)
    report.append("CLASS SUMMARIES")
    report.append("=" * 80)
    report.append("")
    
    # Group classes by year, division, and section
    by_year = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for class_key, class_info in classes.items():
        year = class_info.year
        div = class_info.division or "Unknown Division"
        sec = class_info.section or "Unknown Section"
        by_year[year][div][sec].append((class_info.name, class_info))
    
    def extract_class_number(class_name):
        """Extract class number from class name for numeric sorting."""
        match = re.search(r'Class\s+(\d+):', class_name)
        if match:
            return int(match.group(1))
        return 9999  # Put classes without numbers at the end
    
    for year in sorted(by_year.keys()):
        report.append(f"\n{'=' * 80}")
        report.append(f"YEAR {year}")
        report.append("=" * 80)
        for division in sorted(by_year[year].keys()):
            report.append(f"\n{division}")
            report.append("-" * 80)
            for section in sorted(by_year[year][division].keys()):
                report.append(f"\n  {section}")
                report.append("  " + "-" * 78)
                for class_name, class_info in sorted(by_year[year][division][section], key=lambda x: extract_class_number(x[0])):
                    report.append(f"\n  {class_name} ({year})")
                    report.append(f"    Entries: {class_info.entry_count}")
                    report.append(f"    Dogs:")
                    for dog in class_info.entries:
                        report.append(f"      #{dog.number}: {dog.name} ({dog.sex or 'unknown'})")
                        if dog.owner:
                            report.append(f"        Owner: {dog.owner}")
                        if dog.sire:
                            report.append(f"        Sire: {dog.sire}")
                        if dog.dam:
                            report.append(f"        Dam: {dog.dam}")
                    report.append("")
    
    # Dog entries by class
    report.append("=" * 80)
    report.append("DOGS BY CLASS ENTRY")
    report.append("=" * 80)
    report.append("")
    
    # Sort by dog name (case-insensitive) - don't use dog number as it's year-specific
    sorted_dogs = sorted(dogs.items(), key=lambda x: x[1].name.lower())
    for dog_key, dog in sorted_dogs:
        report.append(f"{dog.name}")
        report.append(f"  Sex: {dog.sex or 'unknown'}")
        if dog.sire:
            report.append(f"  Sire: {dog.sire}")
        if dog.dam:
            report.append(f"  Dam: {dog.dam}")
        if dog.owner:
            report.append(f"  Owner: {dog.owner}")
        # Format classes with year information
        if dog.classes:
            class_strings = [f"{cls_name} ({year})" for cls_name, year in dog.classes]
            report.append(f"  Classes entered: {', '.join(class_strings)}")
        else:
            report.append(f"  Classes entered: None")
        # Get canonical key for relationships lookup
        dog_canonical_key = normalize_name(dog.name)
        if relationships.get(dog_canonical_key):
            report.append(f"  Relationships:")
            # Organize relationships by type and sort alphabetically within each type
            rels = relationships[dog_canonical_key]
            organized_rels = organize_relationships(rels)
            for rel in organized_rels:
                report.append(f"    - {rel}")
        report.append("")
    
    # Family relationships summary
    report.append("=" * 80)
    report.append("FAMILY RELATIONSHIPS")
    report.append("=" * 80)
    report.append("")
    
    has_relationships = False
    # Sort by dog name (case-insensitive)
    # Get canonical keys for relationship lookup
    dogs_with_relationships = []
    for dog_key, dog in dogs.items():
        dog_canonical_key = normalize_name(dog.name)
        if relationships.get(dog_canonical_key):
            dogs_with_relationships.append((dog_key, dog))
    dogs_with_relationships.sort(key=lambda x: x[1].name.lower())
    
    for dog_key, dog in dogs_with_relationships:
        has_relationships = True
        dog_sex = dog.sex or 'unknown'
        owner_info = f" - Owner: {dog.owner}" if dog.owner else ""
        report.append(f"{dog.name} ({dog_sex}){owner_info}")
        dog_canonical_key = normalize_name(dog.name)
        # Organize relationships by type and sort alphabetically within each type
        rels = relationships[dog_canonical_key]
        organized_rels = organize_relationships(rels)
        for rel in organized_rels:
            report.append(f"  - {rel}")
        report.append("")
    
    if not has_relationships:
        report.append("No family relationships found.")
        report.append("")
    
    return "\n".join(report)


def extract_year_from_filename(filename: str) -> str:
    """Extract year from catalog filename."""
    match = re.search(r'(\d{4})', filename)
    if match:
        return match.group(1)
    return "Unknown"


def infer_sex_from_classes(classes: List[Tuple[str, str]]) -> Optional[str]:
    """Infer sex from class names across all years."""
    # Check all classes to find the most definitive sex indicator
    # Prioritize bitches since it's more specific
    for class_name, year in classes:
        class_lower = class_name.lower()
        if 'bitch' in class_lower or 'bitches' in class_lower:
            return 'bitch'
    
    # Then check for dogs (males)
    for class_name, year in classes:
        class_lower = class_name.lower()
        # Look for "dogs" or "dog" in class name (but not "bitch")
        if 'bitch' not in class_lower:
            if 'dogs' in class_lower or (class_lower.startswith('dog ') or ', dog' in class_lower):
                return 'dog'
    
    return None


def infer_sex_from_relationships(dogs: Dict[str, Dog]) -> int:
    """Infer sex from relationships and update dogs.
    
    Rules:
    - If a dog is listed as a sire of another dog, it must be a "dog" (male)
    - If a dog is listed as a dam of another dog, it must be a "bitch" (female)
    
    Returns:
        Number of dogs whose sex was inferred/updated
    """
    updated_count = 0
    
    # Create mapping of normalized names to dog keys
    normalized_name_to_keys = {}
    for dog_key, dog in dogs.items():
        normalized_name = normalize_name(dog.name)
        if normalized_name not in normalized_name_to_keys:
            normalized_name_to_keys[normalized_name] = []
        normalized_name_to_keys[normalized_name].append(dog_key)
    
    # First pass: infer from being listed as sire/dam
    for dog_key, dog in dogs.items():
        if dog.sex and dog.sex != 'unknown':
            continue  # Already has known sex
        
        # Check if this dog is listed as a sire of any other dog
        for other_key, other in dogs.items():
            if other.sire:
                other_sire_normalized = normalize_name(other.sire)
                dog_normalized = normalize_name(dog.name)
                if other_sire_normalized == dog_normalized:
                    # This dog is a sire, so it must be a "dog"
                    dog.sex = 'dog'
                    updated_count += 1
                    break
        
        # Check if this dog is listed as a dam of any other dog
        if not dog.sex or dog.sex == 'unknown':
            for other_key, other in dogs.items():
                if other.dam:
                    other_dam_normalized = normalize_name(other.dam)
                    dog_normalized = normalize_name(dog.name)
                    if other_dam_normalized == dog_normalized:
                        # This dog is a dam, so it must be a "bitch"
                        dog.sex = 'bitch'
                        updated_count += 1
                        break
    
    # Second pass: propagate known sex to dogs with same normalized name
    # (in case one variation has known sex and another doesn't)
    for normalized_name, dog_keys in normalized_name_to_keys.items():
        known_sex = None
        # Find if any dog with this normalized name has known sex
        for dog_key in dog_keys:
            dog = dogs[dog_key]
            if dog.sex and dog.sex != 'unknown':
                known_sex = dog.sex
                break
        
        # Apply known sex to all dogs with this normalized name
        if known_sex:
            for dog_key in dog_keys:
                dog = dogs[dog_key]
                if not dog.sex or dog.sex == 'unknown':
                    dog.sex = known_sex
                    updated_count += 1
    
    return updated_count


def merge_dogs_across_years(all_dogs_by_year: Dict[str, Dict[str, Dog]]) -> Dict[str, Dog]:
    """Merge dogs from multiple years, preserving and inferring sex information.
    
    Dogs with the same normalized name (with or without " of ..." suffix) are treated
    as the same dog across all years, even if they have different entry numbers.
    """
    merged_dogs: Dict[str, Dog] = {}
    
    # First pass: collect all dogs by normalized name
    # This handles:
    # - Same dog with different entry numbers across years
    # - Same dog with/without " of ..." suffix (e.g., "Dog Name" and "Dog Name of Somewhere")
    name_to_dogs = defaultdict(list)
    for year, dogs in all_dogs_by_year.items():
        for dog_num, dog in dogs.items():
            normalized_name = normalize_name(dog.name)
            name_to_dogs[normalized_name].append((year, dog_num, dog))
    
    # Second pass: merge groups with similar names (e.g., "White Gate" vs "Whitegate", "Iron Spring" vs "Iron Springs")
    # BUT only if they have additional evidence they're the same dog (same sire/dam)
    # This prevents merging different dogs that just happen to have similar names
    # OPTIMIZED: Only check similar names if they're likely to match (same first word, etc.)
    print("Checking for similar names (this may take a while)...")
    normalized_names = list(name_to_dogs.keys())
    similar_name_groups = []
    processed = set()
    total_checks = len(normalized_names) * (len(normalized_names) - 1) // 2
    checks_done = 0
    
    for i, norm_name1 in enumerate(normalized_names):
        if norm_name1 in processed:
            continue
        
        # Find all names similar to this one
        similar_group = [norm_name1]
        processed.add(norm_name1)
        
        # Get all dogs from the first group
        dogs1 = name_to_dogs[norm_name1]
        dog1_name = dogs1[0][2].name
        dog1_words = normalize_name(dog1_name).lower().split()
        if not dog1_words:
            continue
        first_word1 = dog1_words[0]
        
        # Check against all other names - OPTIMIZATION: only check if first word matches
        for norm_name2 in normalized_names[i+1:]:
            if norm_name2 in processed:
                continue
            
            checks_done += 1
            if checks_done % 1000 == 0:
                print(f"  Progress: {checks_done}/{total_checks} checks ({100*checks_done//total_checks}%)")
            
            # Get all dogs from the second group
            dogs2 = name_to_dogs[norm_name2]
            dog2_name = dogs2[0][2].name
            dog2_words = normalize_name(dog2_name).lower().split()
            if not dog2_words:
                continue
            first_word2 = dog2_words[0]
            
            # Quick filter: only check if first words are similar (removes most comparisons)
            if not names_are_similar(first_word1, first_word2) and first_word1 != first_word2:
                continue
            
            if names_are_similar(dog1_name, dog2_name):
                # Additional validation: check if they have the same sire/dam
                # This helps ensure we're not merging different dogs with similar names
                should_merge = False
                
                # Check if any dog from group 1 has same sire/dam as any dog from group 2
                for _, _, d1 in dogs1:
                    for _, _, d2 in dogs2:
                        # If both have same sire AND same dam, definitely merge
                        if d1.sire and d2.sire and d1.dam and d2.dam:
                            if (normalize_name(d1.sire) == normalize_name(d2.sire) and
                                normalize_name(d1.dam) == normalize_name(d2.dam)):
                                should_merge = True
                                break
                        # Same sire (normalized) - weaker evidence, but still valid
                        elif d1.sire and d2.sire:
                            if normalize_name(d1.sire) == normalize_name(d2.sire):
                                should_merge = True
                                break
                        # Same dam (normalized) - weaker evidence, but still valid
                        elif d1.dam and d2.dam:
                            if normalize_name(d1.dam) == normalize_name(d2.dam):
                                should_merge = True
                                break
                    if should_merge:
                        break
                
                # Only merge if we have additional evidence (same sire/dam)
                if should_merge:
                    similar_group.append(norm_name2)
                    processed.add(norm_name2)
        
        if len(similar_group) > 1:
            similar_name_groups.append(similar_group)
    
    print(f"Found {len(similar_name_groups)} groups of similar names to merge.")
    
    # Merge similar name groups
    for similar_group in similar_name_groups:
        # Find canonical name for the group
        all_names = []
        for norm_name in similar_group:
            for year, dog_num, dog in name_to_dogs[norm_name]:
                all_names.append(dog.name)
        
        canonical_name = find_canonical_name_for_similar_names(all_names)
        canonical_normalized = normalize_name(canonical_name)
        
        # Merge all dogs from similar groups into the canonical group
        merged_entries = []
        for norm_name in similar_group:
            merged_entries.extend(name_to_dogs[norm_name])
            # Remove the old group (but keep the canonical one)
            if norm_name != canonical_normalized:
                del name_to_dogs[norm_name]
        
        # Update the canonical group with all merged entries
        name_to_dogs[canonical_normalized] = merged_entries
    
    # Third pass: merge dogs with the same normalized name (or similar names that were just merged)
    # Use normalized name as the key to avoid conflicts when same number used in different years
    for normalized_name, dog_entries in name_to_dogs.items():
        # Find canonical name from all dog names in this group
        all_names_in_group = [dog.name for _, _, dog in dog_entries]
        canonical_name = find_canonical_name_for_similar_names(all_names_in_group)
        # Use the first dog number as the primary number for display
        # (same dog may have different numbers in different years)
        primary_num = dog_entries[0][1]
        primary_dog = dog_entries[0][2]
        
        # Merge sex information - collect all sex info and classes, then infer from all available data
        all_classes = []
        all_sexes = []
        
        for year, dog_num, dog in dog_entries:
            all_classes.extend(dog.classes)
            if dog.sex:
                all_sexes.append(dog.sex)
        
        # Infer sex from all classes across all years
        inferred_sex = infer_sex_from_classes(all_classes)
        
        # Determine best sex: prefer known sex over unknown, prefer inferred over unknown
        merged_sex = None
        if all_sexes:
            # Filter out 'unknown' and see if we have any known sexes
            known_sexes = [s for s in all_sexes if s != 'unknown']
            if known_sexes:
                # Use the first known sex (they should all be the same if data is consistent)
                merged_sex = known_sexes[0]
            elif inferred_sex:
                # No known sex, but we can infer from classes
                merged_sex = inferred_sex
            else:
                # Only unknown sexes available, but try to infer from classes
                if inferred_sex:
                    merged_sex = inferred_sex
                else:
                    merged_sex = 'unknown'
        elif inferred_sex:
            # No sex info from dogs, but can infer from classes
            merged_sex = inferred_sex
        else:
            # No sex info at all
            merged_sex = 'unknown'
        
        # Final check: if we ended up with 'unknown' but can infer, use inferred
        if merged_sex == 'unknown' and inferred_sex:
            merged_sex = inferred_sex
        
        # Merge other information (prefer non-None values, and normalize to handle " of ..." variations)
        merged_sire = primary_dog.sire
        merged_dam = primary_dog.dam
        merged_owner = primary_dog.owner
        merged_name = primary_dog.name  # Prefer longer name (with " of ..." if available)
        
        # Track normalized sire/dam names to merge variations
        merged_sire_normalized = normalize_name(merged_sire) if merged_sire else None
        merged_dam_normalized = normalize_name(merged_dam) if merged_dam else None
        
        for year, dog_num, dog in dog_entries[1:]:
            # Merge sire - check if it's the same dog (normalized) and prefer longer name
            if dog.sire:
                dog_sire_normalized = normalize_name(dog.sire)
                if not merged_sire:
                    # No sire yet, use this one
                    merged_sire = dog.sire
                    merged_sire_normalized = dog_sire_normalized
                elif merged_sire_normalized and dog_sire_normalized == merged_sire_normalized:
                    # Same sire (normalized), prefer longer name (with " of ...")
                    if ' of ' in dog.sire.lower() and ' of ' not in (merged_sire or '').lower():
                        merged_sire = dog.sire
                        # Normalized version stays the same, but update for consistency
                        merged_sire_normalized = dog_sire_normalized
                elif not merged_sire_normalized:
                    # merged_sire exists but wasn't normalized (shouldn't happen, but handle it)
                    merged_sire_normalized = normalize_name(merged_sire)
                    if merged_sire_normalized == dog_sire_normalized:
                        # Same sire, prefer longer name
                        if ' of ' in dog.sire.lower() and ' of ' not in (merged_sire or '').lower():
                            merged_sire = dog.sire
            
            # Merge dam - check if it's the same dog (normalized) and prefer longer name
            if dog.dam:
                dog_dam_normalized = normalize_name(dog.dam)
                if not merged_dam:
                    # No dam yet, use this one
                    merged_dam = dog.dam
                    merged_dam_normalized = dog_dam_normalized
                elif merged_dam_normalized and dog_dam_normalized == merged_dam_normalized:
                    # Same dam (normalized), prefer longer name (with " of ...")
                    if ' of ' in dog.dam.lower() and ' of ' not in (merged_dam or '').lower():
                        merged_dam = dog.dam
                        # Normalized version stays the same, but update for consistency
                        merged_dam_normalized = dog_dam_normalized
                elif not merged_dam_normalized:
                    # merged_dam exists but wasn't normalized (shouldn't happen, but handle it)
                    merged_dam_normalized = normalize_name(merged_dam)
                    if merged_dam_normalized == dog_dam_normalized:
                        # Same dam, prefer longer name
                        if ' of ' in dog.dam.lower() and ' of ' not in (merged_dam or '').lower():
                            merged_dam = dog.dam
            
            if not merged_owner and dog.owner:
                merged_owner = dog.owner
            # Prefer name with " of ..." suffix (more complete)
            if ' of ' in dog.name.lower() and ' of ' not in merged_name.lower():
                merged_name = dog.name
        
        # Use canonical name if we found one, otherwise use merged_name
        final_name = canonical_name if canonical_name else merged_name
        
        # Create merged dog
        merged_dog = Dog(
            number=primary_num,
            name=final_name,
            sire=merged_sire,
            dam=merged_dam,
            owner=merged_owner,
            sex=merged_sex,
            classes=all_classes
        )
        
        # Use normalized name as key to ensure uniqueness and avoid conflicts
        # when same number is used by different dogs in different years
        merged_dogs[normalized_name] = merged_dog
    
    return merged_dogs


def main():
    # Find all catalog files in the current directory (.doc and .pdf)
    import glob
    print("=" * 80)
    print("FINDING CATALOG FILES")
    print("=" * 80)
    
    # Try multiple patterns to find catalog files
    doc_files = sorted(glob.glob("*Entries_Catalog*.doc") + glob.glob("*entries_catalog*.doc") + 
                       glob.glob("*Entries*catalog*.doc") + glob.glob("*entries*catalog*.doc"))
    pdf_files = sorted(glob.glob("*Entries_Catalog*.pdf") + glob.glob("*entries_catalog*.pdf") + 
                       glob.glob("*Entries*catalog*.pdf") + glob.glob("*entries*catalog*.pdf") +
                       glob.glob("*Catalog*.pdf") + glob.glob("*catalog*.pdf"))
    
    # Remove duplicates while preserving order
    doc_files = sorted(list(dict.fromkeys(doc_files)))
    pdf_files = sorted(list(dict.fromkeys(pdf_files)))
    catalog_files = sorted(doc_files + pdf_files)
    
    # Debug: Show all PDF files in directory if none found
    if len(pdf_files) == 0:
        print("\nDebug: Searching for PDF files...")
        all_pdfs = sorted(glob.glob("*.pdf"))
        if all_pdfs:
            print(f"  Found {len(all_pdfs)} PDF file(s) in current directory:")
            for pdf in all_pdfs[:10]:  # Show first 10
                print(f"    - {pdf}")
            if len(all_pdfs) > 10:
                print(f"    ... and {len(all_pdfs) - 10} more")
        else:
            print("  No PDF files found in current directory")
            # Try searching in subdirectories
            print("  Searching in subdirectories...")
            subdir_pdfs = sorted(glob.glob("**/*.pdf", recursive=True))
            if subdir_pdfs:
                print(f"  Found {len(subdir_pdfs)} PDF file(s) in subdirectories:")
                for pdf in subdir_pdfs[:10]:  # Show first 10
                    print(f"    - {pdf}")
                if len(subdir_pdfs) > 10:
                    print(f"    ... and {len(subdir_pdfs) - 10} more")
                # Check if any match catalog pattern
                catalog_like = [f for f in subdir_pdfs if 'catalog' in f.lower() or 'entries' in f.lower()]
                if catalog_like:
                    print(f"\n  Found {len(catalog_like)} PDF file(s) that might be catalog files:")
                    for pdf in catalog_like:
                        print(f"    - {pdf}")
    
    if not catalog_files:
        print("No catalog files found. Looking for files matching *Entries_Catalog*.doc or *Entries_Catalog*.pdf")
        sys.exit(1)
    
    print(f"\nFound {len(doc_files)} .doc file(s):")
    for f in doc_files:
        year = extract_year_from_filename(f)
        print(f"  - {f} (Year: {year})")
    
    print(f"\nFound {len(pdf_files)} .pdf file(s):")
    for f in pdf_files:
        year = extract_year_from_filename(f)
        print(f"  - {f} (Year: {year})")
    
    print(f"\nTotal: {len(catalog_files)} catalog file(s) to process")
    print("=" * 80)
    
    all_classes: Dict[str, ClassInfo] = {}
    all_dogs_by_year: Dict[str, Dict[str, Dog]] = {}
    years_processed = []
    
    for filepath in catalog_files:
        
        # Extract year from filename
        year = extract_year_from_filename(filepath)
        if year.isdigit() and (
            int(year) < CATALOG_YEAR_MIN or int(year) > CATALOG_YEAR_MAX
        ):
            print(f"\nSkipping {filepath} (Year: {year}) - outside {CATALOG_YEAR_MIN}-{CATALOG_YEAR_MAX}")
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
        print("No catalog files processed. Exiting.")
        sys.exit(1)
    
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
    
    print("\nGenerating report...")
    report = generate_report(all_classes, merged_dogs, relationships, years_processed)
    
    # Save report
    output_file = "Entries_Catalog_Report.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nReport saved to {output_file}")
    print("\n" + "=" * 80)
    print("REPORT PREVIEW (first 100 lines):")
    print("=" * 80)
    print("\n".join(report.split("\n")[:100]))
    if len(report.split("\n")) > 100:
        print(f"\n... (report continues, see {output_file} for full report)")


if __name__ == "__main__":
    main()


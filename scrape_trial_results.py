#!/usr/bin/env python3
"""
Scrape trial results from JRTCA Yearbook website and parse them.
"""

import re
import sys
import os
import time
import glob
import html
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("ERROR: requests and beautifulsoup4 are required. Install with: pip install requests beautifulsoup4")

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    # Try pdfplumber as alternative
    try:
        import pdfplumber
        HAS_PDFPLUMBER = True
        HAS_PYPDF2 = False
    except ImportError:
        HAS_PDFPLUMBER = False
        print("WARNING: PyPDF2 or pdfplumber not available. PDF files will be skipped. Install with: pip install PyPDF2 or pip install pdfplumber")


# Local utility functions (previously imported from parse_catalog.py)
def normalize_name(name: str) -> str:
    """Normalize dog name by removing ' of ...' suffix for relationship matching."""
    if not name:
        return name
    # Remove " of ..." suffix (case-insensitive)
    normalized = re.sub(r'\s+of\s+.*$', '', name, flags=re.IGNORECASE).strip()
    return normalized


def names_are_similar(name1: str, name2: str) -> bool:
    """Check if two dog names are similar (handling spaces, plurals, etc.).
    
    Examples:
    - "White Gate Bardot" vs "Whitegate Bardot" -> True
    - "Iron Spring Grace Note" vs "Iron Springs Grace Note" -> True
    - "Dog Name" vs "Different Dog Name" -> False
    """
    if not name1 or not name2:
        return False
    
    # Normalize both names first (remove " of ..." suffix)
    norm1 = normalize_name(name1).lower().strip()
    norm2 = normalize_name(name2).lower().strip()
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
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


# Type hint for Dog (used in function signatures)
# Note: Dog type from catalog is not imported to avoid dependency on parse_catalog.py
from typing import Any
Dog = Any  # Type alias for catalog Dog objects


BASE_URL = "https://www.jrtcayearbook.com/"


def normalize_division_name(division: str) -> str:
    """Normalize division names to canonical forms, based on SQL stored procedure logic.
    
    Args:
        division: Raw division name from trial results
    
    Returns:
        Normalized division name
    """
    if not division:
        return division
    
    division_upper = division.upper().strip()
    
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
        'HURDLES RACING': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACES': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACING': 'STEEPLECHASE RACES',
        'STEELPECHASE RACES': 'STEEPLECHASE RACES',
        'STEEPLECHASE': 'STEEPLECHASE RACES',
        'STEEPLECHASE RACE': 'STEEPLECHASE RACES',
        
        # Jumpers
        'JUMPERS DIVISION': 'JUMPERS DIVISION',
        
        # Nose Work
        'NOSE WORK': 'NOSE WORK',
        'NOSE WORK DIVISION': 'NOSE WORK',
        
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
        'TRAIL': 'TRAILING & LOCATING',
        
        # Top Dog/Gun
        'TOP DOG': 'TOP DOG',
        'TOP GUN': 'TOP GUN',
        'TOP GUN CHALLENGE': 'TOP GUN',
        'TOP DOG (NON-SANCTIONED)': 'TOP GUN',
        
        # Youth
        'YOUTH DIVISION': 'YOUTH DIVISION',
        'YOUTH DIVISON': 'YOUTH DIVISION',
        'YOUTH HIGH POINT': 'YOUTH DIVISION',
        'YOUTH': 'YOUTH DIVISION',
        'YOUTH HANDLER': 'YOUTH DIVISION',
    }
    
    return division_map.get(division_upper, division)


def clean_trial_text(text: str) -> str:
    """Clean and normalize trial results text, based on SQL stored procedure REPLACE operations.
    
    Args:
        text: Raw text from trial results (can be None)
    
    Returns:
        Cleaned text (empty string if input is None)
    """
    if not text:
        return ""
    
    # Strip HTML tags first - use BeautifulSoup if available for better HTML parsing
    if HAS_REQUESTS:
        try:
            # Use BeautifulSoup to properly strip HTML tags and decode entities
            soup = BeautifulSoup(text, 'html.parser')
            cleaned = soup.get_text(separator=' ', strip=False)
        except Exception:
            # Fallback to regex if BeautifulSoup fails
            cleaned = re.sub(r'<[^>]+>', '', text)
    else:
        # No BeautifulSoup available, use regex
        cleaned = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities (e.g., &amp; -> &, &lt; -> <, &gt; -> >, &nbsp; -> space)
    try:
        cleaned = html.unescape(cleaned)
    except Exception:
        # If html.unescape fails, try manual replacements for common entities
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')
        cleaned = cleaned.replace('&nbsp;', ' ')
        cleaned = cleaned.replace('&quot;', '"')
        cleaned = cleaned.replace('&#39;', "'")
        cleaned = cleaned.replace('&apos;', "'")
    
    # Remove URLs (http://, https://, www.)
    cleaned = re.sub(r'https?://[^\s]+', '', cleaned)
    cleaned = re.sub(r'www\.[^\s]+', '', cleaned)
    
    # Remove various special characters and normalize spacing (based on SQL stored procedure)
    # Replace pipe characters (SQL: REPLACE(...,'|',''))
    cleaned = cleaned.replace('|', '')
    # Replace multiple spaces with single space (SQL: REPLACE(...,'  ',' '))
    cleaned = re.sub(r' +', ' ', cleaned)
    # Replace " :  " with ": " (normalize spacing around colons) (SQL: REPLACE(...,' :  ',': '))
    cleaned = cleaned.replace(' :  ', ': ')
    # Remove various Unicode characters that appear in corrupted text
    # (SQL stored procedure has multiple REPLACE operations for special characters)
    cleaned = cleaned.replace('\ufeff', '')  # BOM
    cleaned = cleaned.replace('\u200b', '')  # Zero-width space
    cleaned = cleaned.replace('\u200c', '')  # Zero-width non-joiner
    cleaned = cleaned.replace('\u200d', '')  # Zero-width joiner
    
    return cleaned.strip()


def normalize_class_name(class_name: str) -> str:
    """Normalize class names, particularly handling variations of "12½" and other special characters.
    
    Based on SQL stored procedure spParseTrialResults class name normalization logic.
    
    Args:
        class_name: Raw class name from trial results (can be None)
    
    Returns:
        Normalized class name (empty string if input is None)
    """
    if not class_name:
        return ""
    
    normalized = class_name
    
    # Normalize various representations of "12½" to "12½"
    # SQL stored procedure has many REPLACE operations for this
    replacements = [
        ('121/2', '12½'),
        ('12 1/2', '12½'),
        ('12112', '12½'),
        ('12 112', '12½'),
        ('121h', '12½'),
        ("12'h", '12½'),
        ("12h'", '12½'),
        ("12W'", '12½'),
        ('121/z', '12½'),
        ('12.5', '12½'),
        ('12½', '12½'),  # Already correct, but ensure consistency
        # Handle spacing variations
        ('12 ½', '12½'),
        ('12½ ', '12½'),
    ]
    
    for old, new in replacements:
        if old in normalized:
            normalized = normalized.replace(old, new)
    
    # Normalize quote characters to standard double quote
    # Handle various quote characters: ", ", ", ", ", ", ", ", etc.
    normalized = re.sub(r'[""″‴]', '"', normalized)  # Replace all quote variants with standard "
    
    # Normalize spacing around quotes and numbers
    normalized = re.sub(r'(\d+)\s*[""″‴]', r'\1"', normalized)  # "12 " -> "12"
    normalized = re.sub(r'[""″‴]\s*(\d+)', r'"\1', normalized)  # "" 15" -> ""15"
    
    # Normalize height category patterns - preserve full patterns including age categories
    # Fix spacing issues first (e.g., "12½up" -> "12½" up")
    normalized = re.sub(r'(\d+½)\s*([""″‴]?)\s*up\s+to', r'\1" up to', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'(\d+½)\s*([""″‴]?)\s*([A-Z])', r'\1" \3', normalized)  # "12½"Adult" -> "12½" Adult"
    
    # Handle "10 up to 12½"" pattern first (note: "10" not "Up to")
    normalized = re.sub(r'10\s*[""″‴]?\s*up\s+to\s+12\s*½\s*[""″‴]', '10" up to 12½"', normalized, flags=re.IGNORECASE)
    # Handle "Over 12½ up to 15"" pattern - make sure we don't consume following text
    # Use word boundary or end of string to ensure we only match the height part
    normalized = re.sub(r'Over\s+12\s*½\s*up\s+to\s+15\s*[""″‴](?=\s|$)', 'Over 12½" up to 15"', normalized, flags=re.IGNORECASE)
    # Handle "Over 12½"" pattern (without "up to 15") - make sure we don't consume following text
    normalized = re.sub(r'Over\s+12\s*½\s*[""″‴](?=\s|$)', 'Over 12½"', normalized, flags=re.IGNORECASE)
    # Handle "Up to 12½"" pattern (standalone, only if not already part of "10 up to")
    # Check if it's not already normalized as "10" up to 12½""
    if '10" up to 12½"' not in normalized:
        normalized = re.sub(r'Up\s+to\s+12\s*½\s*[""″‴]', 'Up to 12½"', normalized, flags=re.IGNORECASE)
    
    # Normalize age categories (case-insensitive)
    # Standardize: Adult, Veteran, Senior (capitalize first letter)
    normalized = re.sub(r'\b(adult|veteran|senior|puppy)\b', lambda m: m.group(1).title(), normalized, flags=re.IGNORECASE)
    
    # Normalize spacing - collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Fix common typos
    normalized = normalized.replace('olde, r', 'older, ')
    
    # Remove stray special characters (SQL: REPLACE(@Class,'','') where @Class like '%%')
    # This handles corrupted Unicode characters
    normalized = re.sub(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\ufffe\uffff]', '', normalized)
    
    # Normalize "15½" to "15"" (SQL: REPLACE(@Class,'15','15"'))
    normalized = normalized.replace('15½', '15"')
    
    return normalized.strip()


def extract_placement_and_dog(placement_line: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract placement, dog name, and owner from a placement line.
    
    Based on SQL stored procedure spParseTrialResults parsing logic:
    - SQL: @Place=RTRIM(SUBSTRING(@Place,1,CHARINDEX(':',@Place,1)-1))
    - SQL: @Dog=...SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place))
    - SQL: @Owner=...SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog))
    
    Args:
        placement_line: Line containing placement (e.g., "1st: Dog Name, owned by Owner Name")
    
    Returns:
        Tuple of (placement, dog_name, owner) or (None, None, None) if parsing fails
    """
    if not placement_line:
        return None, None, None
    
    # Clean the line first
    placement_line = clean_trial_text(placement_line)
    
    # Check if line contains a placement pattern (based on SQL: LIKE '1st%' OR LIKE '2nd%' etc.)
    # Also check for: LIKE '%Best:%' OR LIKE '%Champ:%' OR LIKE '%Champion:%' OR LIKE '%Reserve:%'
    placement_pattern = r'^(\d+(?:st|nd|rd|th)?|Best|Champ|Champion|Reserve|High\s+Score)\s*:\s*(.+)$'
    match = re.match(placement_pattern, placement_line, re.IGNORECASE)
    
    if not match:
        # Try patterns without leading placement (e.g., just "Best:", "Champion:")
        placement_pattern2 = r'(Best|Champ|Champion|Reserve|High\s+Score)\s*:\s*(.+)$'
        match = re.search(placement_pattern2, placement_line, re.IGNORECASE)
        if match:
            placement = match.group(1).strip()
            after_colon = match.group(2).strip()
        else:
            return None, None, None
    else:
        placement = match.group(1).strip()
        after_colon = match.group(2).strip()
    
    # Extract dog name and owner (SQL logic: check for "owned by")
    # SQL: @Dog=...SUBSTRING(@Place,CHARINDEX(':',@Place,1)+1,LEN(@Place))
    dog_name = after_colon
    
    # SQL: @Owner=CASE WHEN @Dog LIKE '%owned by%' THEN ...SUBSTRING(@Dog,CHARINDEX('owned by ',@Dog,1)+LEN('owned by '),LEN(@Dog)) ELSE '' END
    owner = None
    if 'owned by' in dog_name.lower():
        owned_by_idx = dog_name.lower().find('owned by')
        if owned_by_idx >= 0:
            # Extract owner (after "owned by")
            owner = dog_name[owned_by_idx + len('owned by'):].strip()
            # Clean owner
            owner = re.sub(r'^[\s,]+', '', owner)  # Remove leading spaces/commas
            owner = clean_trial_text(owner)
            
            # Extract dog name (before "owned by")
            # SQL: @Dog=CASE WHEN @Dog LIKE '%owned by%' THEN ...SUBSTRING(@Dog,1,CHARINDEX('owned by',@Dog,1)-1) ELSE @Dog END
            dog_name = dog_name[:owned_by_idx].strip()
    
    # SQL: @Dog=CASE WHEN @Dog LIKE '%,' THEN SUBSTRING(@Dog,1,LEN(@Dog)-1) ELSE @Dog END
    # Remove trailing comma from dog name
    if dog_name and dog_name.endswith(','):
        dog_name = dog_name[:-1].strip()
    
    # Clean dog name
    dog_name = clean_trial_text(dog_name) if dog_name else None
    owner = clean_trial_text(owner) if owner else None
    
    return placement, dog_name, owner


@dataclass
class TrialResult:
    """Represents a trial result entry."""
    trial_name: str
    date: str
    year: str
    division: Optional[str] = None
    section: Optional[str] = None
    class_name: Optional[str] = None
    class_number: Optional[int] = None  # Numeric class number if available
    entry_count: Optional[int] = None  # Number of entries in the class
    placement: Optional[str] = None  # e.g., "1st", "2nd", "Champion", etc.
    dog_name: Optional[str] = None
    owner: Optional[str] = None
    sire: Optional[str] = None
    dam: Optional[str] = None


def get_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """Fetch and parse a web page."""
    if not HAS_REQUESTS:
        print("ERROR: requests library not available")
        return None
    
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"  Failed to fetch {url} after {retries} attempts")
                return None
    return None


def find_trial_result_links(base_url: str) -> List[Tuple[str, str, str]]:
    """Find all trial result page links from the main page.
    
    Returns:
        List of (link_text, url, year) tuples
    """
    print(f"Fetching main page: {base_url}")
    soup = get_page(base_url)
    if not soup:
        return []
    
    trial_links = []
    seen_urls = set()
    
    # First, check if the main page has individual trial links (for current year)
    print("  Checking main page for individual trial links...")
    main_trial_links = find_trial_links_from_archive(base_url)
    if main_trial_links:
        print(f"  Found {len(main_trial_links)} individual trial links on main page")
        # Extract year from current date or use current year
        from datetime import datetime
        current_year = str(datetime.now().year)
        for trial_name, trial_url, date_str in main_trial_links:
            # Try to extract year from date string
            year_match = re.search(r'(\d{4})', date_str)
            year = year_match.group(1) if year_match else current_year
            trial_links.append((f"Main Page: {trial_name}", trial_url, year))
            print(f"  Found trial on main page: {trial_name} ({date_str}) -> {trial_url}")
    
    # Look for links containing "Trial Results" or year patterns (archive pages)
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link['href']
        
        # Check for trial results links (e.g., "2024 Trial Results", "2023 Trial Results")
        if re.search(r'\d{4}\s+Trial\s+Results?', text, re.IGNORECASE):
            full_url = urljoin(base_url, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            year_match = re.search(r'(\d{4})', text)
            year = year_match.group(1) if year_match else "Unknown"
            trial_links.append((text, full_url, year))
            print(f"  Found archive page: {text} -> {full_url}")
    
    # Also check for navigation menus
    nav_menus = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu', re.I))
    for nav in nav_menus:
        for link in nav.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            if re.search(r'\d{4}\s+Trial\s+Results?', text, re.IGNORECASE):
                full_url = urljoin(base_url, href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                year_match = re.search(r'(\d{4})', text)
                year = year_match.group(1) if year_match else "Unknown"
                trial_links.append((text, full_url, year))
                print(f"  Found archive page: {text} -> {full_url}")
    
    # If no links found, try to construct URLs based on common patterns
    if not trial_links:
        print("  No trial result links found in navigation. Trying common URL patterns...")
        for year in range(2024, 2015, -1):  # 2024 down to 2016
            # Try common URL patterns
            patterns = [
                f"/{year}-trial-results/",
                f"/trial-results/{year}/",
                f"/{year}-trials/",
                f"/trial-results-{year}/",
            ]
            for pattern in patterns:
                test_url = urljoin(base_url, pattern)
                # Quick check if page exists
                test_soup = get_page(test_url)
                if test_soup and len(test_soup.get_text()) > 100:
                    trial_links.append((f"{year} Trial Results", test_url, str(year)))
                    print(f"  Found via pattern: {year} Trial Results -> {test_url}")
                    break
    
    return sorted(trial_links, key=lambda x: x[2], reverse=True)  # Sort by year, newest first


def find_pagination_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Find pagination links on a trial results page."""
    pagination_links = []
    
    # Look for pagination elements
    pagination = soup.find_all(['div', 'nav', 'ul'], class_=re.compile(r'pagination|page', re.I))
    for pag in pagination:
        for link in pag.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            # Check if it's a page number or "next" link
            if re.match(r'^\d+$', text) or 'next' in text.lower():
                full_url = urljoin(base_url, href)
                if full_url not in pagination_links:
                    pagination_links.append(full_url)
    
    return pagination_links


def find_jrtcc_trial_result_links(base_url: str = "https://www.jrtcc.ca/trials/#results") -> List[Tuple[str, str, str]]:
    """Find all trial result links from the JRTCC trials page.
    
    Returns:
        List of (trial_name, url, year) tuples
    """
    print(f"Fetching JRTCC trials page: {base_url}")
    soup = get_page(base_url)
    if not soup:
        return []
    
    trial_links = []
    seen_urls = set()
    
    # Find all links on the page that look like trial results
    # Look for PDF links and links with trial-related text
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        href = link['href']
        
        # Skip empty or non-relevant links
        if not text or len(text) < 5:
            continue
        
        # Build full URL
        full_url = urljoin(base_url, href)
        
        # Skip if already seen
        if full_url in seen_urls:
            continue
        
        # Check if it's a PDF file or trial results link
        is_pdf = href.lower().endswith('.pdf')
        is_trial_result = (
            'trial' in text.lower() or
            'national' in text.lower() or
            re.search(r'\d{4}', text)  # Contains a year
        )
        
        # Skip navigation and non-trial links
        if any(skip in text.lower() for skip in ['menu', 'navigation', 'skip to', 'back to top', 'facebook', 'contact']):
            continue
        
        # Extract year from text (e.g., "JRTCC 2024 National Trial")
        year = None
        year_match = re.search(r'(\d{4})', text)
        if year_match:
            year = year_match.group(1)
        else:
            # Try to extract from URL
            url_year_match = re.search(r'/(\d{4})/', full_url)
            if url_year_match:
                year = url_year_match.group(1)
        
        # If it's a trial result (PDF or trial-related text with year), add it
        if (is_pdf or is_trial_result) and year:
            seen_urls.add(full_url)
            # Clean up trial name
            trial_name = text.strip()
            # Remove file size indicators like "( 261 KB )"
            trial_name = re.sub(r'\s*\(\s*\d+\s*[KM]?B\s*\)\s*$', '', trial_name, flags=re.IGNORECASE).strip()
            trial_links.append((trial_name, full_url, year))
            print(f"  Found JRTCC trial: {trial_name} ({year}) -> {full_url}")
    
    return sorted(trial_links, key=lambda x: x[2], reverse=True)  # Sort by year, newest first


def find_trial_links_from_archive(url: str) -> List[Tuple[str, str, str]]:
    """Find all individual trial page links from an archive page or main page.
    
    Returns:
        List of (trial_name, trial_url, date) tuples
    """
    soup = get_page(url)
    if not soup:
        return []
    
    trial_links = []
    
    # Look for the list of trials - they're in a ul with class "lcp_catlist"
    trial_list = soup.find('ul', class_='lcp_catlist')
    if not trial_list:
        # Try alternative patterns
        trial_list = soup.find('ul', id='lcp_instance_0')
    
    # Also check for lists in the main content area
    if not trial_list:
        # Look for any ul that contains trial links
        content_area = soup.find('div', class_='entry-content')
        if content_area:
            # Look for lists with trial links
            for ul in content_area.find_all('ul'):
                # Check if this ul contains links that look like trial links
                links = ul.find_all('a', href=True)
                if links and len(links) > 0:
                    # Check if links look like trial names (not just navigation)
                    first_link_text = links[0].get_text(strip=True)
                    # Trial names typically don't contain "Trial Results" or year patterns
                    if (not re.search(r'Trial\s+Results?', first_link_text, re.IGNORECASE) and
                        not re.search(r'^\d{4}', first_link_text) and
                        len(first_link_text) > 5):
                        trial_list = ul
                        break
    
    if trial_list:
        for li in trial_list.find_all('li'):
            link = li.find('a')
            if link and link.get('href'):
                trial_name = link.get_text(strip=True)
                trial_url = urljoin(url, link['href'])
                # Extract date from the li text (after the link)
                date_text = li.get_text()
                # Remove the trial name from the date text
                date_text = date_text.replace(trial_name, '').strip()
                # Clean up date text (remove extra whitespace, etc.)
                date_text = re.sub(r'\s+', ' ', date_text).strip()
                trial_links.append((trial_name, trial_url, date_text))
                print(f"      Found trial: {trial_name} ({date_text}) -> {trial_url}")
    
    return trial_links


def parse_trial_results_page(url: str, year: str) -> List[TrialResult]:
    """Parse a trial results page and extract all trial result entries.
    
    This function handles both archive pages (which list trials) and individual trial pages.
    """
    print(f"\n  Parsing trial results page: {url}")
    soup = get_page(url)
    if not soup:
        return []
    
    results = []
    
    # Check if this is an archive page (lists individual trials)
    trial_links = find_trial_links_from_archive(url)
    if trial_links:
        print(f"    This is an archive page with {len(trial_links)} individual trial links")
        print(f"    Following links to individual trial pages...")
        
        # Follow each trial link and parse results
        for trial_name, trial_url, date_str in trial_links:
            print(f"      Parsing: {trial_name}")
            trial_results, _ = parse_individual_trial_page(trial_url, trial_name, date_str, year)
            results.extend(trial_results)
            time.sleep(0.5)  # Be polite to the server
        
        return results
    
    # Otherwise, treat this as an individual trial page
    results, _ = parse_individual_trial_page(url, "Unknown Trial", "", year)
    return results


def parse_individual_trial_page_content(page_text: str, trial_name: str, date_str: str, year: str) -> Tuple[List[TrialResult], Dict[str, str]]:
    """Parse trial results from page text content using sequential line-by-line parsing.
    
    This follows the stored procedure approach: process lines sequentially, maintain state
    (current division, current class), and associate placements with the current class only.
    
    Based on spParseTrialResults stored procedure logic.
    """
    # Clean up raw text: remove excessive newlines, normalize spaces
    cleaned_lines = []
    for line in page_text.split('\n'):
        stripped_line = line.strip()
        if stripped_line:
            cleaned_lines.append(re.sub(r'\s+', ' ', stripped_line))
    page_text = '\n'.join(cleaned_lines)
    page_text = re.sub(r'\n{3,}', '\n\n', page_text)  # Replace 3+ newlines with 2
    
    # Extract date from text
    page_date_str = date_str
    date_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4})', page_text)
    if date_match:
        page_date_str = date_match.group(1).strip()
    
    # Clean the text first (similar to SQL stored procedure text cleaning)
    # First, remove URLs from the entire text before processing
    page_text = re.sub(r'https?://[^\s]+', ' ', page_text)
    page_text = re.sub(r'www\.[^\s]+', ' ', page_text)
    page_text = re.sub(r'[A-Za-z0-9-]+\.(com|org|net|edu|gov|html|htm)[^\s]*', ' ', page_text, flags=re.IGNORECASE)
    page_text = re.sub(r'\?[A-Za-z0-9=&-]+', ' ', page_text)  # Remove query strings
    page_text = re.sub(r'X-Amz-[^\s]+', ' ', page_text, flags=re.IGNORECASE)  # Remove AWS signature fragments
    
    # Split long concatenated lines that contain multiple classes or results
    # Look for patterns like "Class \d+:" or division names that indicate new sections
    # Split on these patterns to break up concatenated content
    lines = []
    for line in page_text.split('\n'):
        cleaned_line = clean_trial_text(line)
        if not cleaned_line:
            continue
        
        # If line is very long and contains multiple "Class" markers, split it
        if len(cleaned_line) > 200:
            # Count how many "Class \d+:" patterns are in this line
            class_matches = list(re.finditer(r'Class\s+\d+[.:]', cleaned_line, re.IGNORECASE))
            if len(class_matches) > 1:
                # Split on "Class \d+:" patterns, keeping the marker with the following content
                parts = re.split(r'(Class\s+\d+[.:])', cleaned_line, flags=re.IGNORECASE)
                # Recombine: each "Class N:" should be with the content that follows it
                current_part = ""
                for i, part in enumerate(parts):
                    if re.match(r'Class\s+\d+[.:]', part, re.IGNORECASE):
                        # If we have accumulated content, save it
                        if current_part.strip():
                            lines.append(current_part.strip())
                        current_part = part
                else:
                        current_part += part
                # Don't forget the last part
                if current_part.strip():
                    lines.append(current_part.strip())
            else:
                # Also split on "Entries:" markers which often indicate new classes
                entries_matches = list(re.finditer(r'\bEntries?\s*:?\s*\d+', cleaned_line, re.IGNORECASE))
                if len(entries_matches) > 1:
                    # Split on "Entries:" patterns
                    parts = re.split(r'(\bEntries?\s*:?\s*\d+)', cleaned_line, flags=re.IGNORECASE)
                    # Group each "Entries: N" with the content before it
                    current_part = ""
                    for i, part in enumerate(parts):
                        if re.match(r'\bEntries?\s*:?\s*\d+', part, re.IGNORECASE):
                            # Save previous content + entries marker as a line
                            if current_part.strip():
                                lines.append((current_part + part).strip())
                            current_part = ""
                        else:
                            current_part += part
                    # Don't forget any remaining content
                    if current_part.strip():
                        lines.append(current_part.strip())
                else:
                    # Also split on division names if present
                    division_pattern = r'(' + '|'.join(re.escape(d) for d in ['FLAT RACES', 'STEEPLECHASE', 'GO-TO-GROUND', 'GTG', 'CONFORMATION', 'TRAILING', 'YOUTH', 'SUPER EARTH', 'AGILITY', 'NOSE WORK']) + r')\s*(?:DIVISION)?'
                    division_matches = list(re.finditer(division_pattern, cleaned_line, re.IGNORECASE))
                    if len(division_matches) > 1:
                        # Split on division boundaries
                        parts = re.split(division_pattern, cleaned_line, flags=re.IGNORECASE)
                        for i in range(0, len(parts), 3):
                            if i + 1 < len(parts):
                                combined = (parts[i] + parts[i+1] + (parts[i+2] if i+2 < len(parts) else '')).strip()
                                if combined:
                                    lines.append(combined)
                            elif parts[i].strip():
                                lines.append(parts[i].strip())
                    else:
                        lines.append(cleaned_line)
        else:
            lines.append(cleaned_line)
    
    # Post-process lines to split concatenated text and separate division names
    # This handles cases like "DivisionTunnellers", "2019)Judges:", "Super Earth Division" at end of line
    processed_lines = []
    for line in lines:
        # First, split on patterns where text is concatenated without spaces
        # Pattern 1: "Division" followed by capital letter (e.g., "DivisionTunnellers")
        line = re.sub(r'Division([A-Z])', r'Division \1', line)
        # Pattern 2: ")" followed by capital letter (e.g., "2019)Judges:")
        line = re.sub(r'\)([A-Z])', r') \1', line)
        # Pattern 3: Lowercase letter followed by capital letter (e.g., "KymDavis")
        line = re.sub(r'([a-z])([A-Z])', r'\1 \2', line)
        # Pattern 4: Date followed by text (e.g., "10/31/2019TrialVault")
        line = re.sub(r'(\d{1,2}/\d{1,2}/\d{4})([A-Za-z])', r'\1 \2', line)
        
        # Pattern 5: Division names and section headers at the end of lines
        # Check if line ends with a division name or section header
        division_end_patterns = [
            r'\s+(Super Earth Division|Agility Division|Conformation Division|Lure Coursing.*Division|Brush Hunt.*Division|Rumble Tunnel.*Division|Rally Obedience Division|Trailing.*Division|Nose Work Division|Go-To-Ground Division|GTG Division|Barn Hunt.*Division|Barn Hunt Rat Dash.*)\s*$',
            r'\s+(SUPER EARTH|AGILITY|CONFORMATION|LURE COURSING|BRUSH HUNT|RUMBLE TUNNEL|RALLY OBEDIENCE|TRAILING|NOSE WORK|GO-TO-GROUND|GTG|BARN HUNT)\s*(?:DIVISION)?\s*$',
        ]
        # Section headers that appear at end of lines
        section_header_patterns = [
            r'\s+(6 up to 12 Month Puppy|JRTCC Working Terrier|Suitability.*Judge.*Choice|Miscellaneous.*Veteran|Miscellaneous.*Spayed/Neutered|Open Adult|Family Classes|Foreign Bred Classes|Canadian Bred Classes|VETERAN\s*/\s*SENIOR|Rumble Tunnel|Senior|TALL SENIOR|TALL|SMALL)\s*$',
            r'\s+((?:Working Terrier|Open Adult|Family|Foreign Bred|Canadian Bred|Miscellaneous|Suitability|Judge.*Choice|Veteran|Spayed|Neutered|Senior|Puppy|Adult|VETERAN|SENIOR|Rumble Tunnel|TALL|SMALL).*?)\s*$',
        ]
        division_found = False
        for pattern in division_end_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Split the line: everything before the division name, then the division name separately
                division_text = match.group(1)
                before_division = line[:match.start()].strip()
                if before_division:
                    processed_lines.append(before_division)
                processed_lines.append(division_text)
                division_found = True
                break
        
        if not division_found:
            # Check for section headers
            for pattern in section_header_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Split the line: everything before the section header, then the section header separately
                    section_text = match.group(1)
                    before_section = line[:match.start()].strip()
                    if before_section:
                        processed_lines.append(before_section)
                    # Don't add section headers as separate lines - they're organizational only
                    # Just remove them from the line and keep the content before
                    if before_section:
                        processed_lines.append(before_section)
                    division_found = True
                    break
        
        if not division_found:
            # Pattern 6: Class numbers that appear inline (e.g., "162:", "172:", "238:")
            # Split on standalone class numbers (3+ digits) followed by colon
            # But not if it's part of "Class N:" pattern
            # Simple approach: find "NNN: " patterns and split on them
            parts = re.split(r'(\b\d{3,}:\s+)', line)
            if len(parts) > 1:
                # Parts will alternate: [text_before, class_num, text_after_class_num, class_num2, ...]
                # First part might be text before any class number
                if parts[0].strip():
                    processed_lines.append(parts[0].strip())
                # Then process pairs: (class_num, text_after)
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        # Combine class number with its content
                        class_line = (parts[i] + parts[i+1]).strip()
                        if class_line:
                            processed_lines.append(class_line)
                    elif parts[i].strip():
                        # Just a class number at the end
                        processed_lines.append(parts[i].strip())
            else:
                processed_lines.append(line)
    
    lines = [l for l in processed_lines if l.strip()]  # Remove empty lines
    
    # Clean trial name
    clean_trial_name = (trial_name or "Unknown Trial").strip()
    clean_trial_name = clean_trial_name.replace('\ufeff', '').replace('\u200b', '').strip()
    # Remove URLs from trial name
    clean_trial_name = re.sub(r'https?://[^\s]+', '', clean_trial_name)
    clean_trial_name = re.sub(r'www\.[^\s]+', '', clean_trial_name)
    clean_trial_name = re.sub(r'[A-Za-z0-9-]+\.(com|org|net|edu|gov|html|htm)[^\s]*', '', clean_trial_name, flags=re.IGNORECASE)
    clean_trial_name = re.sub(r'\?[A-Za-z0-9=&-]+', '', clean_trial_name)  # Remove query strings
    clean_trial_name = re.sub(r'X-Amz-[^\s]+', '', clean_trial_name, flags=re.IGNORECASE)  # Remove AWS signature fragments
    clean_trial_name = clean_trial_name.strip()
    
    results = []
    
    # Track processed placement lines to prevent duplicates
    # Key: (line_index, dog_name, placement, owner) - prevents same line from creating multiple results
    processed_placements = set()
    
    # State variables (like stored procedure variables)
    current_division = None
    current_championship = None  # For championship classes like "ADULT RACING CHAMPION & RESERVE"
    current_class = None
    current_entry_count = None  # Entry count for current class
    current_day = None  # Track day (Friday, Saturday, Sunday) for multi-day trials
    # Note: class numbers will be assigned during report generation based on order of first appearance
    
    # Parse judge information from the text
    # Check stored procedure logic: judges can appear in formats like:
    # "Judges: Name, Conformation; Name, Go-To-Ground"
    # The stored procedure extracts judge info from lines containing "judges:" pattern
    judges_info = {}  # division -> judge name
    for line in lines[:100]:  # Check first 100 lines for judge information (increase from 50)
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        line_upper = line_stripped.upper()
        # Check for "Judges:" or "Judge:" pattern (case-insensitive)
        if line_upper.startswith('JUDGES:') or line_upper.startswith('JUDGE:'):
            # Parse format like "Judges: Name, Division; Name, Division"
            # Example: "Judges: Linda Cowasjee, Conformation; Ted Ely, Go-to-Ground"
            judge_text = line_stripped
            if ':' in judge_text:
                judge_text = judge_text.split(':', 1)[1].strip()
            
            if not judge_text:
                continue
            
            # Split by semicolon first to get individual judge assignments
            judge_sections = re.split(r';\s*', judge_text)
            for section in judge_sections:
                section = section.strip()
                if not section:
                    continue
                # Each section should be "Name, Division" or just "Name"
                # Split by comma - last part is division, everything before is judge name
                parts = [p.strip() for p in section.split(',')]
                if len(parts) >= 2:
                    # Last part is the division, everything before is the judge name
                    # Handle cases like "Last, First" vs "First Last, Division"
                    # Common pattern: "Judge Name, Division"
                    # But also might be: "Last, First, Division"
                    # Strategy: if only 2 parts, treat as "Name, Division"
                    # If 3+ parts, last is division, join rest as judge name
                    if len(parts) == 2:
                        judge_name = parts[0].strip()
                        division_text = parts[1].strip()
                    else:
                        # Multiple commas - last is division, join all before as judge name
                        judge_name = ', '.join(parts[:-1]).strip()
                        division_text = parts[-1].strip()
                    
                    # Normalize division name (handles "Conformation", "Go-to-Ground", etc.)
                    division_name = normalize_division_name(division_text.upper())
                    
                    # Store if we got a valid division name back (non-empty)
                    if division_name and division_name.strip():
                        judges_info[division_name] = judge_name
                elif len(parts) == 1:
                    # Just a name, might be a general judge - store with a generic key
                    judges_info['GENERAL'] = parts[0].strip()
    
    # List of known division names (from stored procedure - exact matches)
    division_names_set = {
        'AGILILITY', 'AGILITY DIVISION', 'AGILITY DIVISON', 'AGILITY',
        'BALL RETRIEVAL',
        'BALL TOSS', 'BALL TOSS CHAMPION & RESERVE',
        'BARN HUNT', 'BARN HUNT (Non-Sanctioned)', 'BARN HUNT DIVISION (Non-Sanctioned)', 'BARN HUNT DIVISION',
        'BRUSH HUNT', 'BRUSH HUNT DIVISION', 'BRUSH HUNT (NON SANCTIONED)', 'BRUSH HUNT: SATURDAY', 'BRUSH HUNT: SUNDAY',
        'CONFORMATION', 'CONFORMATION DIVISION:', 'CONFORMATION DIVISION', 'CONFORMATION DIVISON',
        'DOGGIE FUN ZONE (Non-sanctioned)', 'DOGGIE FUN ZONE', 'DOGGIE FUN ZONE DIVISION (Non-sanctioned)', 'DOGGIE FUN ZONE DIVISION',
        'LURE COURSING', 'FIELD LURE COURSING', 'FIELD LURE COURSING (NON-SANCTIONED)',
        'FLAT RACES:', 'FLAT RACES', 'FLAT RACING', 'FLATS RACING', 'FLATS',
        'GAMES CLASSES',
        'GO-TO GROUND', 'GO-TO- GROUND', 'GO-TO-GOUND DIVISION', 'Go-To-Ground', 'GO-TO-GROUND DIVISIION', 'GO-TO-GROUND DIVISION', 'GO-TO-GROUND DIVISON', 'GO-TO-TO-GROUND', 'GTG',
        'HIGH JUMP', 'HIGH JUMP DIVISION', 'SUNDAY HIGH JUMP', 'HIGH JUMP HIGH SCORE & RESERVE',
        'HURDLE', 'Hurdle Race', 'HURDLE RACES', 'HURDLES', 'Hurdles Races',
        'JUMPERS DIVISION',
        'NON-SANCTIONED DIVISION',
        'NOSE WORK', 'NOSE WORK DIVISION',
        'OBEDIENCE', 'OBEDIENCE DIVISION', 'OBEDIENCE DIVISON', 'OBEDIENCE HIGH SCORE & RESERVE',
        'RACING', 'RACING DIVISION', 'RACING DIVISION FLAT RACES', 'RACING DIVISON',
        'RALLY OBEDIENCE', 'RALLY OBEDIENCE DIVISION', 'RALLY-O', 'RALLY-OBEDIENCE', 'RALLY-O HIGH SCORE & RESERVE',
        'STEEPLECHASE RACES', 'STEELPECHASE RACES', 'STEEPLECHASE', 'STEEPLECHASE RACE',
        'SUPER EARTH', 'SUPER EARTH DIVISION', 'SUPER EARTH GTG DIVISION', 'Super Earth Stakes', 'SUPER GTG', 'SUPER SENIOR', 'SUPEREARTH', 'SUPER EARTH GO-TO-GROUND DIVISION',
        'THUNDER TUNNEL', 'THUNDER TUNNEL DIVISION',
        'TRAILING', 'TRAILING & LOCATING', 'TRAILING & LOCATING DIVISION', 'TRAILING & LOCATING DIVISON', 'TRAILING/LOCATING DIVISION',
        'TOP DOG', 'TOP GUN', 'TOP GUN CHALLENGE', 'TOP DOG (NON-SANCTIONED)',
        'YOUTH DIVISION', 'YOUTH DIVISON', 'YOUTH HIGH POINT', 'YOUTH',
    }
    
    # Championship class names (from stored procedure)
    # These are class names that represent championships - they should be treated as championships, not regular classes
    championship_names_set = {
        'ADULT RACING CHAMPION & RESERVE', 'ADULT, RACING CHAMPION & RESERVE',
        'PUPPY RACING CHAMPION & RESERVE', 'PUPPY, RACING CHAMPION & RESERVE',
        'SENIORS RACING CHAMPION & RESERVE', 'SENIOR RACING CHAMPION & RESERVE', 'SENIOR, RACING CHAMPION & RESERVE',
        'VETERANS RACING CHAMPION & RESERVE', 'VETERAN RACING CHAMPION & RESERVE', 'VETERAN, RACING CHAMPION & RESERVE',
        'AGILITY HIGH SCORE CHAMPION & RESERVE', 'VETERAN AGILITY HIGH SCORE CHAMPION & RESERVE',
        'HIGH JUMP HIGH SCORE & RESERVE', 'BALL TOSS CHAMPION & RESERVE',
        'OBEDIENCE HIGH SCORE & RESERVE', 'RALLY-O HIGH SCORE & RESERVE',
        'SUPER EARTH CHAMPION & RESERVE', 'SUPER EARTH FASTEST TIME CHAMPION & RESERVE',
        'WORKING TERRIER CHAMPION & RESERVE', 'PUPPY CONFORMATION CHAMPION & RESERVE',
        'BEST OPEN TERRIER & RESERVE', 'BEST WORKING TERRIER & RESERVE',
        'BEST BITCH & RESERVE', 'BEST DOG & RESERVE',
        'BEST 6 UP TO 12 MONTH PUPPY DOG & RESERVE', 'BEST 4 UP TO 6 MONTH PUPPY & RESERVE',
        # Championship class names that appear without "& RESERVE" (e.g., "OVER 12½" UP TO 15″ PUPPY RACING CHAMPIONSHIP")
        'UP TO 12½" PUPPY RACING CHAMPIONSHIP',
        'OVER 12½" UP TO 15" PUPPY RACING CHAMPIONSHIP',
        'OVER 12½" UP TO 15" ADULT RACING CHAMPIONSHIP',
        'OVER 12½" UP TO 15" VETERAN RACING CHAMPIONSHIP',
        'OVER 12½" UP TO 15" SENIOR RACING CHAMPIONSHIP',
        '10" UP TO 12½" SENIOR RACING CHAMPIONSHIP',
        '10" UP TO 12½" VETERAN RACING CHAMPIONSHIP',
        'PUPPY CHAMPION AND RESERVE',
        'WORKING TERRIER CONFORMATION CHAMPION & RESERVE',
    }
    
    # Section headers that are organizational only (not divisions, not classes)
    # These appear within divisions and should be ignored (they're sub-sections)
    # Note: "GO-TO-GROUND" is a DIVISION, not a section header
    section_header_names_set = {
        'WORKING TERRIER CONFORMATION', 'OPEN ADULT CONFORMATION', 'FAMILY CLASSES',
        'MISCELLANEOUS', 'SUITABILITY',
    }
    
    # Process lines sequentially (like stored procedure WHILE loop)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        line_upper = line.upper().strip()
        
        # Check for day markers (Friday, Saturday, Sunday) - these indicate a new day of a multi-day trial
        # Pattern: "Friday (Date)", "Saturday (Date)", "Sunday (Date)", or just "Friday", "Saturday", "Sunday"
        day_match = re.match(r'^(Friday|Saturday|Sunday)(?:\s*\([^)]+\))?', line, re.IGNORECASE)
        if day_match:
            current_day = day_match.group(1).title()  # Capitalize: Friday, Saturday, Sunday
            # Update trial name to include day for separation in report
            if current_day and current_day not in clean_trial_name:
                clean_trial_name = f"{clean_trial_name} - {current_day}"
            # Also check if there's a date in parentheses
            date_in_parens = re.search(r'\(([^)]+)\)', line)
            if date_in_parens:
                # Update the date string to include the day
                page_date_str = f"{current_day} ({date_in_parens.group(1)})"
            i += 1
            continue
            
        # Check if line contains day-specific class names (e.g., "SUNDAY LURE COURSING CHAMPION")
        if re.search(r'\b(FRIDAY|SATURDAY|SUNDAY)\s+', line_upper):
            day_in_class = re.search(r'\b(FRIDAY|SATURDAY|SUNDAY)\s+', line_upper)
            if day_in_class:
                current_day = day_in_class.group(1).title()
                # Update trial name to include day for separation in report
                if current_day and current_day not in clean_trial_name:
                    clean_trial_name = f"{clean_trial_name} - {current_day}"
        
        # Check if this is a division name (SQL: IF RTRIM(LTRIM(@Result)) in (...))
        # Use exact match (case-insensitive)
        if line_upper in division_names_set:
            # Normalize division name
            normalized_division = normalize_division_name(line_upper)
            current_division = normalized_division
            current_championship = None
            current_class = None
            # Class numbers will be assigned during report generation
            i += 1
            continue
        
        # Check if this is a championship class name
        if line_upper in championship_names_set:
            current_championship = line_upper
            current_class = None  # Will be set when we see placements
            # Class numbers will be assigned during report generation
            i += 1
            continue
        
        # Check if this is a placement line first (SQL: @Result LIKE '1st%' OR LIKE '2nd%' OR LIKE '%Best:%' etc.)
        # SQL: @Result NOT LIKE '1st%' AND @Result NOT LIKE '2nd%' ... AND @Result NOT LIKE '%Best:%' etc.
        is_placement_line = (
            re.match(r'^\d+(?:st|nd|rd|th)?\s*:', line, re.IGNORECASE) or
            re.search(r'\b(Best|Champ|Champion|Reserve|High\s+Score)\s*:', line, re.IGNORECASE)
        )
        
        # Check if this is just "Entries: N" on its own line
        if re.match(r'^Entries?\s*:?\s*\d+', line, re.IGNORECASE):
            # This is just an entry count line - skip it (class name should be on previous line)
            i += 1
            continue
            
        # If not a placement line, check if it's a class name
        if not is_placement_line:
            # Skip section headers that are organizational only (like "WORKING TERRIER CONFORMATION")
            # These appear within divisions but are not actual classes or divisions
            if line_upper in section_header_names_set:
                # This is just an organizational header - skip it, don't reset class numbering
                i += 1
                continue
                
            # Check if this is a championship class name (pattern-based check)
            # Championship class names typically contain "CHAMPIONSHIP" or "CHAMPION & RESERVE" or "CHAMPION AND RESERVE"
            # "Championship Certificate" classes ARE championship classes, even if they have "Entries"
            # Examples of championship classes: 
            #   - "UP TO 12½" PUPPY RACING CHAMPIONSHIP" (no Entries)
            #   - "10 up to 12½" Adult Championship Certificate – Entries: 26" (has Entries, but still championship)
            is_championship_class = (
                line_upper in championship_names_set or
                # "Championship Certificate" classes are championship classes (even with Entries)
                'CHAMPIONSHIP CERTIFICATE' in line_upper or
                # Other championship patterns (without Entries check for these)
                ('CHAMPIONSHIP' in line_upper and not re.search(r'Entries', line, re.IGNORECASE)) or
                (('CHAMPION' in line_upper or 'CHAMP' in line_upper) and 
                 ('RESERVE' in line_upper or 'AND RESERVE' in line_upper) and
                 not re.search(r'Entries', line, re.IGNORECASE)) or
                # Pattern: "UP TO 12½" PUPPY RACING CHAMPIONSHIP" or "OVER 12½" UP TO 15″ PUPPY RACING CHAMPIONSHIP"
                (re.search(r'(UP TO|OVER).*RACING CHAMPIONSHIP', line_upper) and not re.search(r'Entries', line, re.IGNORECASE))
            )
            
            # If it's a championship class name, treat it as a championship
            if is_championship_class:
                # For "Championship Certificate" classes, extract the full class name and entry count
                # Match stored procedure logic EXACTLY (spParseTrialResults lines 2286-2363)
                if 'CHAMPIONSHIP CERTIFICATE' in line_upper:
                    # SQL: IF @Result LIKE '%Entries%'
                    # Find "Entries" position (SQL: CHARINDEX('Entries',@Result,1))
                    entries_pos = line.upper().find('Entries')
                    if entries_pos >= 0:
                        # SQL: SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-1)
                        # Get everything before "Entries"
                        class_name_before_rtrim = line[:entries_pos].strip()
                        
                        # SQL: RTRIM(SUBSTRING(...)) - remove trailing spaces first
                        # SQL line 2292-2296: CASE WHEN RTRIM(...) LIKE '%-' THEN SUBSTRING(...,1,CHARINDEX('Entries',...)-4)
                        # If RTRIM result ends with dash, remove 4 characters from original position (the " – " before Entries)
                        class_name_rtrimmed = class_name_before_rtrim.rstrip()
                        
                        # Check if RTRIM result ends with dash (SQL: LIKE '%-')
                        if class_name_rtrimmed.endswith('-') or class_name_rtrimmed.endswith('–'):
                            # SQL: SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-4)
                            # Remove 4 characters from the original entries_pos position
                            # This removes " – " (en-dash + space + space) before "Entries"
                            if entries_pos >= 4:
                                class_name_raw = line[:entries_pos - 4].strip()
                            else:
                                # Fallback: just remove trailing dash/spaces
                                class_name_raw = class_name_rtrimmed.rstrip('–- \t').strip()
                        else:
                            # SQL: ELSE RTRIM(SUBSTRING(...))
                            class_name_raw = class_name_rtrimmed
                        
                        # Now apply stored procedure normalization (lines 2298-2341)
                        # SQL: Multiple REPLACE operations that preserve full class name structure
                        class_name = class_name_raw
                        
                        # SQL lines 2298-2332: Simple string replacements (preserves structure)
                        replacements = [
                            ('121/2', '12½'),
                            ('12 1/2', '12½'),
                            ('12112', '12½'),
                            ('12 112', '12½'),
                            ('121h', '12½'),
                            ("12'h", '12½'),
                            ("12h'", '12½'),
                            ("12W'", '12½'),
                            ('121/z', '12½'),
                            ('12.5', '12½'),
                            ('12½', '12½'),  # Already correct
                            ('12 ½', '12½'),
                            ('olde, r', 'older, '),
                        ]
                        
                        for old, new in replacements:
                            if old in class_name:
                                class_name = class_name.replace(old, new)
                        
                        # SQL line 2340: replace(@Class,'15','15"') - normalize 15" quotes
                        # But first need to handle quote normalization
                        class_name = re.sub(r'[""″‴]', '"', class_name)
                        
                        # SQL lines 2334-2338: Remove special Unicode characters
                        # replace(@Class,'','') and replace(@Class,'','')
                        # These remove corrupted Unicode chars but preserve text
                        class_name = re.sub(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\ufffe\uffff]', '', class_name)
                        class_name = re.sub(r'\s+', ' ', class_name).strip()
                        
                        # Normalize age categories (capitalize) - preserves them
                        class_name = re.sub(r'\b(adult|veteran|senior|puppy)\b', lambda m: m.group(1).title(), class_name, flags=re.IGNORECASE)
                        
                        # Store as both championship and class name
                        current_championship = class_name.upper()
                        current_class = class_name
                        
                        # Extract entry count (SQL lines 2343-2356)
                        entry_text = line[entries_pos:].strip()
                        # SQL: Multiple IF statements checking for different "Entries:" patterns
                        entry_count_match = re.search(r'Entries?\s*:?\s*(\d+)', entry_text, re.IGNORECASE)
                        if entry_count_match:
                            try:
                                current_entry_count = int(entry_count_match.group(1))
                            except ValueError:
                                current_entry_count = None
                        else:
                            current_entry_count = None
                    else:
                        # No Entries found, use the full line as class name
                        class_name = normalize_class_name(line.strip())
                        current_championship = class_name.upper()
                        current_class = class_name
                        current_entry_count = None
                else:
                    # Other championship classes (without Certificate)
                    current_championship = line_upper
                    current_class = None
                    current_entry_count = None
                
                i += 1
                continue
                
            class_name = None
            entry_count = None
            extracted_class_number = None
            
            # Pattern 1: "Class: " prefix (SQL: @Entry LIKE 'Class: %')
            if re.match(r'^Class:\s*', line, re.IGNORECASE):
                class_name = re.sub(r'^Class:\s*', '', line, flags=re.IGNORECASE).strip()
            # Pattern 2: "Class N:" pattern
            elif re.match(r'^Class\s+\d+', line, re.IGNORECASE):
                class_match = re.match(r'^Class\s+(\d+)[.:\s-]+\s*(.+?)(?:\s*[–-]\s*Entries?:\s*\d+)?$', line, re.IGNORECASE)
                if class_match:
                    extracted_class_number = int(class_match.group(1))
                    class_name = class_match.group(2).strip()
            # Pattern 3: Contains "Entries" (SQL: @Result LIKE '%Entries%')
            # This is the primary way to identify classes - lines with "Entries" are always classes
            elif re.search(r'Entries', line, re.IGNORECASE):
                # Extract class name (everything before "Entries")
                # SQL: SUBSTRING(@Result,1,CHARINDEX('Entries',@Result,1)-1)
                entries_match = re.search(r'Entries', line, re.IGNORECASE)
                if entries_match:
                    class_name = line[:entries_match.start()].strip()
                    # SQL: CASE WHEN RTRIM(SUBSTRING(...)) LIKE '%-' THEN SUBSTRING(...,1,LEN(...)-4)
                    # Remove trailing dash or special characters
                    class_name = re.sub(r'[–-]\s*$', '', class_name).strip()
                    if class_name.endswith('–') or class_name.endswith('-'):
                        class_name = class_name[:-1].strip()
                    # Extract entry count
                    entry_text = line[entries_match.start():].strip()
                    entry_count_match = re.search(r'Entries?\s*:?\s*(\d+)', entry_text, re.IGNORECASE)
                    if entry_count_match:
                        entry_count = entry_count_match.group(1)
            # Pattern 4: Standalone class name (no "Entries" or "Class:" prefix)
            # SQL: ELSE - just use the line as class name (but check it's not a placement or division)
            # BUT: Only treat as class if it looks like a valid class name (not a section header)
            # Section headers are already filtered above, so if we get here it might be a class
            elif (line and 
                  not any(skip in line_upper for skip in ['CHAIR', 'JUDGES', 'ADMIN', 'LOCATION', 'OWNED BY']) and
                  not re.match(r'^\d+', line) and  # Doesn't start with a number
                  len(line) > 3):  # Has some content
                # Only treat as class if it's not obviously a section header
                # Most classes will have "Entries" (Pattern 3), so Pattern 4 should rarely match
                # If it does match, treat it as a class name (stored procedure logic)
                class_name = line.strip()
            
            # Process class_name if we found one from any pattern
                if class_name:
                # Remove URLs from class name (http://, https://, www.)
                    class_name = re.sub(r'https?://[^\s]+', '', class_name)
                class_name = re.sub(r'www\.[^\s]+', '', class_name)
                
                # Normalize class name (SQL: multiple REPLACE operations)
                class_name = normalize_class_name(class_name)
                
                # Remove placement patterns if present (shouldn't be in class name)
                if re.match(r'^\s*(Best|Champion|Reserve)\s*:', class_name, re.IGNORECASE):
                    # This is actually a placement, not a class name - skip it
                    i += 1
                    continue
                
                # Remove "Class N:" prefix if still present
                class_name = re.sub(r'^Class\s+\d+[.:\s-]+\s*', '', class_name, flags=re.IGNORECASE).strip()
                
                # Clean up any remaining URL fragments or malformed text
                # Remove any remaining URL-like patterns
                class_name = re.sub(r'[A-Za-z0-9-]+\.(com|org|net|edu|gov|html|htm)[^\s]*', '', class_name, flags=re.IGNORECASE)
                class_name = re.sub(r'\?[A-Za-z0-9=&-]+', '', class_name)  # Remove query strings
                class_name = re.sub(r'X-Amz-[^\s]+', '', class_name, flags=re.IGNORECASE)  # Remove AWS signature fragments
                
                # Remove section prefixes
                section_prefixes = [
                    r'^Super\s+Earth\s*[–-]\s*', r'^Conformation\s*[–-]\s*',
                    r'^Flat\s+Racing\s*[–-]\s*', r'^Steeplechase\s+Racing\s*[–-]\s*',
                    r'^GTG\s*[–-]\s*', r'^Trailing\s*[–-]\s*', r'^Youth\s*[–-]\s*',
                ]
                for prefix_pattern in section_prefixes:
                    class_name = re.sub(prefix_pattern, '', class_name, flags=re.IGNORECASE).strip()
                class_name = re.sub(r'^\s*[–-]\s*', '', class_name).strip()
                
                # Skip if class name is empty, just "Class", too short, or looks like a section header
                class_name_upper = class_name.upper().strip()
                # Check for incomplete class names (ends with number, single word, or common section header patterns)
                incomplete_patterns = [
                    r'^\d+$',  # Just a number
                    r'^(TALL|SMALL|SENIOR|VETERAN|ADULT|PUPPY|CLASS)$',  # Single section header word
                    r'^(TALL|SMALL|SENIOR|VETERAN|ADULT|PUPPY)\s*$',  # Single word with spaces
                    r'^BEST\s+\d+',  # "BEST 6" without completion
                    r'^BEST\s+\d+\s+up\s+to\s+\d+$',  # "BEST 6 up to 12" without completion
                ]
                is_incomplete = False
                for pattern in incomplete_patterns:
                    if re.match(pattern, class_name_upper):
                        is_incomplete = True
                        break
                
                if not class_name or class_name_upper == 'CLASS' or len(class_name_upper) < 3 or is_incomplete:
                    # Invalid or incomplete class name - skip this line
                    # If it looks like a section header, don't treat as class
                    i += 1
                continue
                
                # Check if this is actually a division name (not a class)
                if class_name_upper in division_names_set:
                    # This is a division name, not a class - treat it as a division
                    normalized_division = normalize_division_name(class_name_upper)
                    current_division = normalized_division
                    current_championship = None
                    current_class = None
                    i += 1
                continue
                
                # If class name contains GTG or go-to-ground, assign to GO-TO-GROUND division
                if 'GTG' in class_name_upper or 'GO-TO-GROUND' in class_name_upper or 'GO TO GROUND' in class_name_upper:
                    current_division = 'GO-TO-GROUND'
                    # Reset class numbering for the new division
                    current_championship = None
                # If class name contains NOSE WORK, assign to NOSE WORK division
                elif 'NOSE WORK' in class_name_upper:
                    current_division = 'NOSE WORK'
                    # Reset class numbering for the new division
                    current_championship = None
                
                # Set current class - don't assign class number here, will be assigned during report generation
                if class_name:  # Only set if we have a valid class name after cleaning
                    # Check if this is a different class from the current one
                    is_new_class = (current_class is None or current_class != class_name)
                    
                    if is_new_class:
                        # This is a new class - update current class (number will be assigned during report generation)
                        current_class = class_name
                        current_class_number = None  # Don't assign number during parsing
                        current_championship = None  # Clear championship when we see a regular class
                        # Store entry count for this class
                        if entry_count:
                            try:
                                current_entry_count = int(entry_count)
                            except ValueError:
                                current_entry_count = None
                        else:
                            current_entry_count = None
                    # If class_name matches current_class, keep the same class
                i += 1
                continue
            
        # Check if this is a placement line (SQL: @Result LIKE '1st%' OR LIKE '2nd%' OR LIKE '%Best:%' etc.)
        # First check if this is a height-prefixed championship line (e.g., "Up to 12½" Champion: ...")
        height_category = None
        if current_championship:
            # Check if the line starts with a height category before the placement
            # Handle various quote characters, fraction symbols (½, 1/2), and spacing
            # Use more flexible patterns that match the actual text format
            height_patterns = [
                (r'^Up\s+to\s+12\s*[½½1/2]\s*[""″]?\s*(Champion|Reserve)\s*:', r'Up to 12½"'),
                (r'^Over\s+12\s*[½½1/2]\s+up\s+to\s+15\s*[""″]?\s*(Champion|Reserve)\s*:', r'Over 12½ up to 15"'),
                (r'^10\s*[""″]?\s+up\s+to\s+12\s*[½½1/2]\s*[""″]?\s*(Champion|Reserve)\s*:', r'10" up to 12½"'),
                (r'^Over\s+12\s*[½½1/2]\s*[""″]?\s*(Champion|Reserve)\s*:', r'Over 12½"'),
            ]
            
            # Try matching with case-insensitive flag
            for pattern, height_label in height_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    height_category = height_label
                    break
            
            # If no match with the above patterns, try a simpler approach
            # Check if line starts with height indicators followed by Champion/Reserve
            if not height_category:
                if re.match(r'^Up\s+to\s+12', line, re.IGNORECASE) and re.search(r'\b(Champion|Reserve)\s*:', line, re.IGNORECASE):
                    height_category = r'Up to 12½"'
                elif re.match(r'^Over\s+12.*up\s+to\s+15', line, re.IGNORECASE) and re.search(r'\b(Champion|Reserve)\s*:', line, re.IGNORECASE):
                    height_category = r'Over 12½ up to 15"'
                elif re.match(r'^10.*up\s+to\s+12', line, re.IGNORECASE) and re.search(r'\b(Champion|Reserve)\s*:', line, re.IGNORECASE):
                    height_category = r'10" up to 12½"'
                elif re.match(r'^Over\s+12', line, re.IGNORECASE) and re.search(r'\b(Champion|Reserve)\s*:', line, re.IGNORECASE):
                    height_category = r'Over 12½"'
        
        placement, dog_name, owner = extract_placement_and_dog(line)
        
        if placement and dog_name:
            # We have a valid placement - associate it with current division and class
            if not current_division:
                # No division set yet - skip this placement
                i += 1
                continue
            
            # Check if we've already processed this exact placement line
            # This prevents duplicates from the same line being processed multiple times
            placement_key = (i, dog_name, placement, owner or "")
            if placement_key in processed_placements:
                # Already processed this line - skip to prevent duplicate
                i += 1
                continue
            processed_placements.add(placement_key)
                
            # Determine class name
            result_class_name = current_class
            result_class_number = None  # Will be assigned during report generation
            
            # If we have a championship, use it as the class name
            if current_championship:
                # For "Championship Certificate" classes, we already have current_class set with the full name
                # IMPORTANT: Always prefer current_class if it exists, as it contains the full name including age categories
                if current_class and 'CHAMPIONSHIP CERTIFICATE' in current_class.upper():
                    # Use the full class name (includes height and age category)
                    # Do NOT use height_category - it would only give us the height, losing the age category
                    result_class_name = current_class
                elif current_class:
                    # Regular class name exists, use it
                    result_class_name = current_class
                elif height_category:
                    # No current_class, but we have height_category - combine with championship
                    # (This is for old-style championships without explicit class names)
                    result_class_name = f"{current_championship} - {height_category}"
                else:
                    # No height category, use championship as-is (but try to preserve original case)
                    result_class_name = current_championship
                result_class_number = None  # Championships don't get numbered
            
            # If no class name yet, create a default
            if not result_class_name:
                result_class_name = "Unknown Class"
            
            # If class name contains GTG or go-to-ground, assign to GO-TO-GROUND division
            result_class_name_upper = result_class_name.upper()
            if 'GTG' in result_class_name_upper or 'GO-TO-GROUND' in result_class_name_upper or 'GO TO GROUND' in result_class_name_upper:
                current_division = 'GO-TO-GROUND'
            # If class name contains NOSE WORK, assign to NOSE WORK division
            elif 'NOSE WORK' in result_class_name_upper:
                current_division = 'NOSE WORK'
            
            # For child/youth handler entries, owner information does not apply
            is_handler_class = (
                'CHILD HANDLER' in result_class_name_upper or
                'YOUTH HANDLER' in result_class_name_upper or
                'HANDLER' in result_class_name_upper and ('CHILD' in result_class_name_upper or 'YOUTH' in result_class_name_upper)
            )
            if is_handler_class:
                owner = None  # Don't store owner information for handler classes
            
            # Convert division to section name for display (don't duplicate division)
            # Use a simplified section name, not the full division name
            section = None
            if current_division == 'FLAT RACES' or current_division == 'FLAT RACING':
                section = 'Flat Racing'
            elif current_division == 'STEEPLECHASE RACES' or current_division == 'STEEPLECHASE':
                section = 'Steeplechase Racing'
            elif current_division == 'GO-TO-GROUND' or current_division == 'GTG':
                        section = 'GTG'
            elif current_division == 'CONFORMATION' or current_division == 'CONFORMATION DIVISION':
                section = 'Conformation'
            elif current_division == 'TRAILING & LOCATING' or current_division == 'TRAILING':
                        section = 'Trailing'
            elif current_division == 'YOUTH DIVISION' or current_division == 'YOUTH':
                        section = 'Youth'
            elif current_division == 'SUPER EARTH':
                section = 'Super Earth'
            elif current_division == 'AGILITY DIVISION' or current_division == 'AGILITY':
                section = 'Agility'
            elif current_division == 'NOSE WORK':
                section = 'Nose Work'
            else:
                # Use a short version if possible
                section = current_division.replace(' DIVISION', '').title() if ' DIVISION' in current_division else current_division.title()
            
            # Create result
            # Include day in date if available
            result_date = page_date_str or date_str
            if current_day and current_day not in result_date:
                # Add day to date if not already present
                if result_date:
                    result_date = f"{current_day} ({result_date})"
                else:
                    result_date = current_day
            
            result = TrialResult(
                trial_name=clean_trial_name,
                date=result_date,
                year=year,
                division=current_division,
                section=section,
                class_name=result_class_name,
                class_number=result_class_number,
                entry_count=current_entry_count,
                placement=placement,
                dog_name=dog_name,
                owner=owner
            )
            results.append(result)
    
        i += 1
    
    return results, judges_info


def download_file(url: str, save_path: str) -> bool:
    """Download a file from a URL and save it to disk.
    
    Args:
        url: URL to download from
        save_path: Path where the file should be saved
    
    Returns:
        True if download was successful, False otherwise
    """
    if not HAS_REQUESTS:
        print("ERROR: requests library not available")
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(save_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Save file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"  ERROR: Could not download {url}: {e}")
        return False


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Extracted text as a string
    """
    text = ""
    try:
        if HAS_PYPDF2:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            print(f"        ERROR: No PDF library available to read {file_path}")
            return ""
    except Exception as e:
        print(f"        ERROR: Could not extract text from PDF {file_path}: {e}")
        return ""
    return text


def parse_local_trial_file(file_path: str, year: str = None, source_folder: str = None) -> Tuple[List[TrialResult], Dict[str, str]]:
    """Parse a local trial results file (text, HTML, or PDF).
    
    Args:
        file_path: Path to the file to parse
        year: Year of the trial (extracted from folder name if not provided)
        source_folder: Name of the source folder (for tracking)
    
    Returns:
        List of TrialResult objects
    """
    print(f"        Parsing local file: {os.path.basename(file_path)}")
    
    # Determine year from folder name if not provided
    if not year:
        folder_name = os.path.basename(os.path.dirname(file_path))
        if folder_name.isdigit() and len(folder_name) == 4:
            year = folder_name
        else:
            year = "Unknown"
    
    # Read file content based on file type
    if file_path.lower().endswith('.pdf'):
        # Extract text from PDF
        page_text = extract_text_from_pdf(file_path)
        if not page_text:
            return [], {}
    else:
        # Read text or HTML file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"        ERROR: Could not read file {file_path}: {e}")
            return [], {}
        
        # Parse HTML or text
        if file_path.lower().endswith(('.html', '.htm')):
            soup = BeautifulSoup(content, 'html.parser')
            page_text = soup.get_text(separator='\n', strip=False)
        else:
            page_text = content
    
    # Extract trial name and date from the beginning of the file
    lines = page_text.split('\n')
    trial_name = None
    date_str = None
    
    # Look for trial name in first few lines
    for i, line in enumerate(lines[:20]):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 3:
            continue
        
        # Skip common headers/navigation
        if any(skip in line_stripped.lower() for skip in ['skip to content', 'navigation', 'home', 'about', 'links']):
            continue
        
        # Skip HTML/JavaScript code patterns
        if any(marker in line_stripped for marker in ['/*', '*/', '<script', '</script>', 'function(', 'http://', 'https://', 'Dynamic Drive', 'DHTML code library']):
            continue
        
        # Trial name is usually the first substantial line
        if not trial_name and len(line_stripped) > 5 and not line_stripped.lower().startswith(('judges:', 'chair', 'admin')):
            # Check if it looks like a date
            date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', line_stripped)
            if date_match:
                date_str = date_match.group(1)
            elif not re.match(r'^\d{4}', line_stripped):  # Not just a year
                # Additional validation: skip if it contains HTML/JS markers or URLs
                if not any(marker in line_stripped for marker in ['/*', '*/', '<script', '</script>', 'function(', 'http://', 'https://']):
                    # Remove URLs from trial name if present
                    trial_name_candidate = re.sub(r'https?://[^\s]+', '', line_stripped)
                    trial_name_candidate = re.sub(r'www\.[^\s]+', '', trial_name_candidate)
                    trial_name_candidate = trial_name_candidate.strip()
                    if trial_name_candidate and len(trial_name_candidate) > 3:
                        trial_name = trial_name_candidate
                    # Extract date from same line if present
                    date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', line_stripped)
                    if date_match:
                        date_str = date_match.group(1)
                    break
    
    # If no trial name found, use filename
    if not trial_name:
        trial_name = os.path.splitext(os.path.basename(file_path))[0]
        # Clean up common prefixes
        trial_name = re.sub(r'^(debug_trial_|debug_)', '', trial_name, flags=re.IGNORECASE)
        trial_name = trial_name.replace('_', ' ').replace('-', ' ')
    
    # Use the extracted parsing logic
    results, judges_info = parse_individual_trial_page_content(page_text, trial_name, date_str or "", year)
    
    if results:
        print(f"        Extracted {len(results)} results from {os.path.basename(file_path)}")
    
    return results, judges_info


def parse_individual_trial_page(url: str, trial_name: str, date_str: str, year: str) -> Tuple[List[TrialResult], Dict[str, str]]:
    """Parse an individual trial results page."""
    # Check if we already have downloaded files for this trial
    soup = None
    page_text = None
    
    if "archive" not in url.lower():
        # Create year subfolder if it doesn't exist
        debug_dir = year
        os.makedirs(debug_dir, exist_ok=True)
        
        # Sanitize trial name for filename (remove invalid characters and limit length)
        safe_trial_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', trial_name)
        safe_trial_name = safe_trial_name.replace(' ', '_').replace('&', 'and').replace("'", '')
        safe_trial_name = safe_trial_name[:50]  # Limit length
        if not safe_trial_name:
            safe_trial_name = "unknown_trial"
        
        raw_text_file = os.path.join(debug_dir, f"debug_trial_{safe_trial_name}_raw.txt")
        debug_file = os.path.join(debug_dir, f"debug_trial_{safe_trial_name}.html")
        
        # Check if raw text file already exists
        if os.path.exists(raw_text_file):
            print(f"        Using existing file: {raw_text_file}")
            with open(raw_text_file, "r", encoding="utf-8") as f:
                page_text = f.read()
        # Check if HTML file exists (but not raw text)
        elif os.path.exists(debug_file):
            print(f"        Using existing file: {debug_file}")
            with open(debug_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            # Extract raw text from HTML
            page_text = soup.get_text(separator='\n', strip=False)
    
    # If we don't have existing files, download from web
    if page_text is None:
        soup = get_page(url)
        if not soup:
            return [], {}
        
        # Extract raw text from the entire page (strip all HTML)
        page_text = soup.get_text(separator='\n', strip=False)
        
        # Save HTML and raw text for debugging (only for individual trial pages)
        if "archive" not in url.lower() and soup:
            # Create year subfolder if it doesn't exist
            debug_dir = year
            os.makedirs(debug_dir, exist_ok=True)
            
            # Sanitize trial name for filename (remove invalid characters and limit length)
            safe_trial_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', trial_name)
            safe_trial_name = safe_trial_name.replace(' ', '_').replace('&', 'and').replace("'", '')
            safe_trial_name = safe_trial_name[:50]  # Limit length
            if not safe_trial_name:
                safe_trial_name = "unknown_trial"
            
            debug_file = os.path.join(debug_dir, f"debug_trial_{safe_trial_name}.html")
            raw_text_file = os.path.join(debug_dir, f"debug_trial_{safe_trial_name}_raw.txt")
            
            # Only save if files don't already exist
            if not os.path.exists(debug_file):
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(str(soup))
                print(f"        Saved page HTML to {debug_file} for debugging")
            
            if not os.path.exists(raw_text_file):
                # Clean up the text: remove extraneous line feeds and normalize whitespace
                # Replace multiple consecutive newlines with single newline
                cleaned_text = re.sub(r'\n{3,}', '\n\n', page_text)
                # Replace multiple consecutive spaces with single space
                cleaned_text = re.sub(r' +', ' ', cleaned_text)
                # Remove leading/trailing whitespace from each line
                lines = [line.strip() for line in cleaned_text.split('\n')]
                # Remove empty lines
                lines = [line for line in lines if line]
                # Rejoin with single newline
                cleaned_text = '\n'.join(lines)
                
                with open(raw_text_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                print(f"        Saved raw text to {raw_text_file} for debugging")
                page_text = cleaned_text
    
    # Clean up the text: remove extraneous line feeds and normalize whitespace
    # Replace multiple consecutive newlines with single newline
    page_text = re.sub(r'\n{3,}', '\n\n', page_text)
    # Replace multiple consecutive spaces with single space
    page_text = re.sub(r' +', ' ', page_text)
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in page_text.split('\n')]
    # Remove empty lines
    lines = [line for line in lines if line]
    # Rejoin with single newline
    page_text = '\n'.join(lines)
    
    # Use the extracted parsing function
    results, judges_info = parse_individual_trial_page_content(page_text, trial_name, date_str, year)
    return results, judges_info


def scan_local_subfolders(base_dir: str = ".") -> List[Tuple[str, str, str]]:
    """Scan local subfolders for trial result files.
    
    Returns:
        List of (file_path, year, source_folder) tuples
    """
    files_to_process = []
    
    # Year folders (1984-2018)
    for year in range(1984, 2019):
        year_folder = os.path.join(base_dir, str(year))
        if os.path.isdir(year_folder):
            for filename in os.listdir(year_folder):
                file_path = os.path.join(year_folder, filename)
                if os.path.isfile(file_path):
                    # Skip debug files
                    if filename.startswith('debug_'):
                        continue
                    # Process .txt, .html, .htm, and .pdf files
                    if filename.lower().endswith(('.txt', '.html', '.htm', '.pdf')):
                        files_to_process.append((file_path, str(year), str(year)))
    
    # Special folders
    special_folders = ['Gold Coast', 'JRTCC', 'MO Earthdogs']
    for folder_name in special_folders:
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    # Skip debug files
                    if filename.startswith('debug_'):
                        continue
                    # Process .txt, .html, .htm, and .pdf files
                    if filename.lower().endswith(('.txt', '.html', '.htm', '.pdf')):
                        # Try to extract year from filename or folder
                        year = "Unknown"
                        year_match = re.search(r'(\d{4})', filename)
                        if year_match:
                            year = year_match.group(1)
                        files_to_process.append((file_path, year, folder_name))
    
    return files_to_process


def is_duplicate_trial(trial_name: str, date: str, seen_trials: Set[Tuple[str, str]]) -> bool:
    """Check if a trial is a duplicate based on name and date.
    
    Args:
        trial_name: Name of the trial
        date: Date of the trial
        seen_trials: Set of (trial_name, date) tuples already seen
    
    Returns:
        True if this is a duplicate
    """
    # Normalize trial name for comparison
    normalized_name = normalize_name(trial_name)
    
    # Check exact match
    if (normalized_name, date) in seen_trials:
        return True
    
    # Check if similar name with same date exists
    for seen_name, seen_date in seen_trials:
        if seen_date == date and names_are_similar(trial_name, seen_name):
            return True
    
    return False


def merge_trial_results_with_catalog_data(trial_results: List[TrialResult], 
                                         catalog_dogs: Dict[str, Dog]) -> Dict[str, Dog]:
    """Merge trial results with existing catalog dog data."""
    merged_dogs = catalog_dogs.copy()
    
    # Create mapping of normalized names to dogs
    normalized_to_dogs = defaultdict(list)
    for dog_key, dog in catalog_dogs.items():
        normalized = normalize_name(dog.name)
        normalized_to_dogs[normalized].append((dog_key, dog))
    
    # Process trial results
    for trial_result in trial_results:
        if not trial_result.dog_name:
            continue
        
        dog_name = trial_result.dog_name.strip()
        normalized = normalize_name(dog_name)
        
        # Try to find existing dog
        found = False
        if normalized in normalized_to_dogs:
            for dog_key, dog in normalized_to_dogs[normalized]:
                # Update dog with trial result information
                if not dog.owner and trial_result.owner:
                    dog.owner = trial_result.owner
                found = True
                break
        
        # If not found, try similar name matching
        if not found:
            for norm_name, dogs_list in normalized_to_dogs.items():
                if dogs_list:
                    existing_dog = dogs_list[0][1]
                    if names_are_similar(dog_name, existing_dog.name):
                        # Update existing dog
                        if not existing_dog.owner and trial_result.owner:
                            existing_dog.owner = trial_result.owner
                        found = True
                        break
        
        # If still not found, create new dog entry (but we might not have all info)
        # For now, we'll skip creating new dogs from trial results alone
    
    return merged_dogs


def generate_trial_results_report(trial_results: List[TrialResult],
                                 catalog_dogs: Dict[str, Dog],
                                 trial_judges: Optional[Dict[str, Dict[str, str]]] = None) -> str:
    """Generate a comprehensive report of trial results with catalog data integration."""
    report = []
    
    report.append("=" * 80)
    report.append("JRTCA TRIAL RESULTS - COMPREHENSIVE REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Group by year
    by_year = defaultdict(list)
    for result in trial_results:
        by_year[result.year].append(result)
    
    # Summary statistics
    report.append("SUMMARY STATISTICS")
    report.append("-" * 80)
    report.append(f"Total Trial Results: {len(trial_results)}")
    report.append(f"Years Covered: {', '.join(sorted(by_year.keys()))}")
    report.append(f"Unique Dogs in Trials: {len(set(r.dog_name for r in trial_results if r.dog_name))}")
    report.append(f"Unique Owners in Trials: {len(set(r.owner for r in trial_results if r.owner))}")
    report.append("")
    
    # Trial results by year
    report.append("=" * 80)
    report.append("TRIAL RESULTS BY YEAR")
    report.append("=" * 80)
    report.append("")
    
    for year in sorted(by_year.keys(), reverse=True):
        year_results = by_year[year]
        report.append(f"\n{'=' * 80}")
        report.append(f"YEAR {year}")
        report.append("=" * 80)
        
        # Group by trial
        by_trial = defaultdict(list)
        for result in year_results:
            by_trial[result.trial_name].append(result)
        
        # Sort trials by date (calendar order), then by name if dates are the same
        def get_trial_sort_key(trial_name: str) -> tuple:
            """Get sort key for trial: (date_sort, trial_name)"""
            trial_results = by_trial[trial_name]
            # Get date from first result (all results in same trial should have same date)
            date_str = trial_results[0].date if trial_results and trial_results[0].date else ""
            
            # Parse date for sorting (e.g., "October 10, 2025" -> (2025, 10, 10))
            if date_str:
                try:
                    from datetime import datetime
                    # Try to parse common date formats
                    date_formats = [
                        "%B %d, %Y",      # "October 10, 2025"
                        "%b %d, %Y",      # "Oct 10, 2025"
                        "%B %d %Y",       # "October 10 2025"
                        "%b %d %Y",       # "Oct 10 2025"
                        "%m/%d/%Y",       # "10/10/2025"
                        "%d/%m/%Y",       # "10/10/2025"
                        "%Y-%m-%d",       # "2025-10-10"
                    ]
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_date:
                        return (parsed_date.year, parsed_date.month, parsed_date.day, trial_name)
                except Exception:
                    pass
            
            # If date parsing fails, sort by name
            return (9999, 12, 31, trial_name)  # Put unparseable dates at end
        
        # Sort trials by date
        sorted_trials = sorted(by_trial.keys(), key=get_trial_sort_key)
        
        for trial_name in sorted_trials:
            trial_results_list = by_trial[trial_name]
            report.append(f"\n  {trial_name}")
            if trial_results_list[0].date:
                report.append(f"    Date: {trial_results_list[0].date}")
            
            # Display judge information if available
            if trial_judges and trial_name in trial_judges:
                judges = trial_judges[trial_name]
                if judges:
                    judge_parts = []
                    for division, judge_name in sorted(judges.items()):
                        if division != 'GENERAL':
                            judge_parts.append(f"{judge_name}, {division}")
                        else:
                            judge_parts.append(judge_name)
                    if judge_parts:
                        report.append(f"    Judges: {'; '.join(judge_parts)}")
            
            report.append("    Results:")
            
            # First, remove duplicates across ALL results for this trial
            # A result should only appear once per trial, even if it was parsed multiple times
            seen_results = set()
            unique_trial_results = []
            for result in trial_results_list:
                # Create a unique key: dog, placement, owner, and class info
                result_key = (
                    result.dog_name,
                    result.placement,
                    result.owner,
                    result.division or "",
                    result.section or "",
                    result.class_number,
                    result.class_name or ""
                )
                if result_key not in seen_results:
                    seen_results.add(result_key)
                    unique_trial_results.append(result)
            trial_results_list = unique_trial_results
            
            # Group by class (division/section/class_name/class_number combination)
            by_class = defaultdict(list)
            
            for result in trial_results_list:
                # Normalize class name for display consistency (formatting only, preserve height/age distinctions)
                # Do NOT merge classes that differ in height or age categories
                # IMPORTANT: Championship Certificate classes are already normalized during parsing
                # using stored procedure logic, so don't re-normalize them (would risk removing age categories)
                if result.class_name:
                    # Check if this is a Championship Certificate class (already normalized during parsing)
                    is_champ_cert = 'CHAMPIONSHIP CERTIFICATE' in result.class_name.upper()
                    if is_champ_cert:
                        # Already normalized - just use as-is (might need minimal formatting cleanup)
                        normalized_class_name = result.class_name
                    else:
                        # Regular class - use normalize_class_name
                        normalized_class_name = normalize_class_name(result.class_name)
                    result.class_name = normalized_class_name  # Update result to use normalized name for display
                else:
                    normalized_class_name = ""
                
                # Use normalized class name for grouping (normalization preserves height/age distinctions)
                # Classes with different height or age should remain separate
                class_key_tuple = (
                    result.division or "",
                    result.section or "",
                    result.class_number if result.class_number is not None else None,
                    normalized_class_name,  # This preserves height/age differences
                )
                by_class[class_key_tuple].append(result)
            
            # Sort classes by class number (numeric), then by division/section/class_name
            def get_class_sort_key(class_key_tuple: tuple, results: List[TrialResult]) -> tuple:
                division, section, class_num, class_name = class_key_tuple
                # Sort by class number (numeric) first, then division, section, class_name
                class_num_sort = int(class_num) if class_num is not None else 999999
                return (class_num_sort, division or "", section or "", class_name or "")
            
            # Assign sequential class numbers across the entire trial (not per division)
            # Track the order classes first appear in the original results
            # Use normalized class names to merge duplicates
            class_first_appearance = {}  # (division, normalized_class_name) -> first_index
            for idx, result in enumerate(trial_results_list):
                if result.division and result.class_name:
                    # Championship Certificate classes are already normalized - use as-is
                    is_champ_cert = 'CHAMPIONSHIP CERTIFICATE' in result.class_name.upper()
                    if is_champ_cert:
                        normalized_class_name = result.class_name
                    else:
                        normalized_class_name = normalize_class_name(result.class_name)
                    key = (result.division, normalized_class_name)
                    if key not in class_first_appearance:
                        class_first_appearance[key] = idx
            
            # Collect all classes across all divisions
            all_classes = []
            for class_key, class_results in by_class.items():
                division, section, class_num, class_name = class_key
                all_classes.append((class_key, class_results))
            
            # Sort all classes by first appearance order (across all divisions)
            all_classes.sort(key=lambda x: class_first_appearance.get((x[0][0], x[0][3]), 999999))
            
            # Assign sequential numbers starting from 1 across all classes in the trial
            sorted_classes_with_numbers = []
            for class_num, (class_key, class_results) in enumerate(all_classes, start=1):
                # Update class_number in all results for this class
                for result in class_results:
                    result.class_number = class_num
                # Create new class_key with correct number
                new_class_key = (class_key[0], class_key[1], class_num, class_key[3])
                sorted_classes_with_numbers.append((new_class_key, class_results))
            
            # Display results grouped by class
            for class_key, class_results in sorted_classes_with_numbers:
                # Skip empty classes
                if not class_results:
                    continue
                
                # Remove duplicates within the class (same dog, same placement, same owner)
                seen_in_class = set()
                unique_class_results = []
                for result in class_results:
                    result_key = (result.dog_name, result.placement, result.owner, result.class_name)
                    if result_key not in seen_in_class:
                        seen_in_class.add(result_key)
                        unique_class_results.append(result)
                class_results = unique_class_results
                
                # Skip if all results were duplicates
                if not class_results:
                    continue
                
                # Validate placements: each placement should only appear once unless marked as "(tie)"
                placement_counts = defaultdict(list)
                for result in class_results:
                    # Extract base placement (without "(tie)" marker)
                    base_placement = result.placement or ""
                    is_tie = "(tie)" in base_placement.lower()
                    if is_tie:
                        # Remove "(tie)" for grouping purposes
                        base_placement = re.sub(r'\s*\(tie\)', '', base_placement, flags=re.IGNORECASE).strip()
                    placement_counts[base_placement].append((result, is_tie))
                
                # Filter out duplicate placements that aren't ties
                validated_results = []
                for base_placement, results_list in placement_counts.items():
                    ties = [r for r, is_tie in results_list if is_tie]
                    non_ties = [r for r, is_tie in results_list if not is_tie]
                    
                    # If there are ties, include all of them
                    if ties:
                        validated_results.extend(ties)
                    
                    # For non-ties, check if they're actually different dogs
                    if non_ties:
                        if len(non_ties) == 1:
                            validated_results.append(non_ties[0])
                        else:
                            # Multiple non-tie results with same placement
                            # Check if they're different dogs - if so, they might be unmarked ties
                            unique_dogs = set()
                            unique_dog_owner_pairs = set()
                            for result in non_ties:
                                if result.dog_name:
                                    unique_dogs.add(result.dog_name)
                                    dog_owner = (result.dog_name or "", result.owner or "")
                                    unique_dog_owner_pairs.add(dog_owner)
                            
                            # If all results are for the same dog (and same owner), it's a duplicate - keep only first
                            if len(unique_dogs) == 1 and len(unique_dog_owner_pairs) == 1:
                                validated_results.append(non_ties[0])
                            elif len(unique_dogs) > 1:
                                # Different dogs with same placement - include all of them
                                # They might be legitimate ties (even if not explicitly marked)
                                # or they might be duplicates that should have been caught during parsing
                                # For now, include all - the deduplication during parsing should prevent
                                # actual duplicates from being created
                                validated_results.extend(non_ties)
                            else:
                                # Same dog but different owners - likely a duplicate, keep first
                                validated_results.append(non_ties[0])
                
                # Validation: If there's a Champion, Reserve, or Best placement, there shouldn't be a 1st place
                has_champion = any(r.placement and 'champion' in r.placement.lower() for r in validated_results)
                has_best = any(r.placement and 'best' in r.placement.lower() and 'champion' not in r.placement.lower() for r in validated_results)
                has_reserve = any(r.placement and 'reserve' in r.placement.lower() for r in validated_results)
                
                # Also check if the class name indicates it's a championship class
                is_championship_class_by_name = False
                has_best_in_name = False
                if class_results:
                    class_name_for_check = (class_results[0].class_name or "").upper().strip()
                    has_best_in_name = class_name_for_check.startswith('BEST:') or 'BEST:' in class_name_for_check
                    is_championship_class_by_name = (
                        ('CHAMPION' in class_name_for_check or 'CHAMPIONSHIP' in class_name_for_check or
                         (class_name_for_check.startswith('BEST') and 'RESERVE' in class_name_for_check) or
                         has_best_in_name)
                        and not any(pattern in class_name_for_check for pattern in [
                            'DOGS, ONE YEAR', 'BITCHES, ONE YEAR', 'PUPS,', 'PUPPY',
                            'SENIOR DOGS', 'SENIOR BITCHES', 'ENTRIES:'
                        ])
                    )
                    if has_best_in_name:
                        has_best = True
                
                # Remove 1st place if Champion/Best/Reserve exist
                if (has_champion or has_best or has_reserve) or (is_championship_class_by_name and (has_champion or has_best)) or has_best_in_name:
                    validated_results = [r for r in validated_results if not (r.placement and re.match(r'^1(st)?', r.placement, re.IGNORECASE))]
                
                class_results = validated_results
                
                # Skip if no results left after validation
                if not class_results:
                    continue
                
                # Build display string for class header
                # Use section (simplified division name) instead of full division to avoid duplication
                class_parts = []
                if class_results[0].section:
                    class_parts.append(class_results[0].section)
                
                # Add class name with class number if available
                class_name_display = class_results[0].class_name or ""
                if class_name_display:
                    if class_results[0].class_number is not None:
                        class_parts.append(f"Class {class_results[0].class_number}: {class_name_display}")
                    else:
                        class_parts.append(class_name_display)
                elif class_results[0].class_number is not None:
                    class_parts.append(f"Class {class_results[0].class_number}")
                
                # Add entry count if available
                entry_count = class_results[0].entry_count
                if entry_count is not None:
                    class_parts.append(f"Entries: {entry_count}")
                
                class_display = " - ".join(class_parts) if class_parts else "Unknown Class"
                
                report.append(f"      {class_display}")
                
                # Sort results within class by placement (numeric order)
                def get_placement_sort_key(placement: str) -> int:
                    """Get numeric sort key for placement."""
                    if not placement:
                        return 999
                    placement_lower = placement.lower()
                    # Special placements (highest priority)
                    if 'champion' in placement_lower:
                        return 0
                    if 'best' in placement_lower:
                        return 1
                    if 'reserve' in placement_lower:
                        return 2
                    # Extract numeric placement (1st, 2nd, 3rd, etc.)
                    numeric_match = re.search(r'(\d+)', placement)
                    if numeric_match:
                        return 10 + int(numeric_match.group(1))  # 1st = 11, 2nd = 12, etc.
                    # DQ (low priority but before unknown)
                    if 'dq' in placement_lower or 'disqualified' in placement_lower:
                        return 98
                    # Unknown placement
                    return 99
                
                sorted_class_results = sorted(class_results, key=lambda r: get_placement_sort_key(r.placement or ""))
                
                for result in sorted_class_results:
                    placement_str = result.placement or "N/A"
                    dog_str = result.dog_name or "N/A"
                    # For child/youth handler classes, don't display owner information
                    class_name_upper = (result.class_name or "").upper()
                    is_handler_class = (
                        'CHILD HANDLER' in class_name_upper or
                        'YOUTH HANDLER' in class_name_upper or
                        'HANDLER' in class_name_upper and ('CHILD' in class_name_upper or 'YOUTH' in class_name_upper)
                    )
                    if is_handler_class:
                        report.append(f"        {placement_str}: {dog_str}")
                    else:
                        owner_str = result.owner or "N/A"
                        report.append(f"        {placement_str}: {dog_str} - Owner: {owner_str}")
        
    # Results summary by dog
    report.append("")
    report.append("=" * 80)
    report.append("RESULTS SUMMARY BY DOG")
    report.append("=" * 80)
    report.append("")
    
    # Group results by dog (using normalized names)
    by_dog = defaultdict(list)
    for result in trial_results:
        if result.dog_name:
            normalized = normalize_name(result.dog_name)
            by_dog[normalized].append(result)
    
    # Sort dogs by name
    for dog_normalized in sorted(by_dog.keys()):
        dog_results = by_dog[dog_normalized]
        
        # Get all name variations for this dog
        name_variations = set(r.dog_name for r in dog_results if r.dog_name)
        
        # Try to find this dog in the catalog
        catalog_dog = None
        catalog_key = None
        for key, dog in catalog_dogs.items():
            if normalize_name(dog.name) == dog_normalized or names_are_similar(dog_results[0].dog_name, dog.name):
                catalog_dog = dog
                catalog_key = key
                break
        
        # Display dog name(s)
        if len(name_variations) > 1:
            report.append(f"\n{'=' * 80}")
            report.append(f"Dog: {', '.join(sorted(name_variations))} (name variations)")
        else:
            report.append(f"\n{'=' * 80}")
            report.append(f"Dog: {list(name_variations)[0]}")
        
        # Display catalog information if available
        if catalog_dog:
            info_parts = []
            if catalog_dog.sex:
                info_parts.append(f"Sex: {catalog_dog.sex}")
            if catalog_dog.sire:
                info_parts.append(f"Sire: {catalog_dog.sire}")
            if catalog_dog.dam:
                info_parts.append(f"Dam: {catalog_dog.dam}")
            if catalog_dog.owner:
                info_parts.append(f"Owner: {catalog_dog.owner}")
            if info_parts:
                report.append(f"  Catalog Info: {', '.join(info_parts)}")
        
        # Sort results by year (most recent first), then trial, then class number (numeric), then division/section/class, then placement
        dog_results_sorted = sorted(dog_results, key=lambda r: (
            -int(r.year) if r.year and r.year.isdigit() else 0,  # Year (most recent first)
            r.trial_name or "",  # Trial name
            r.class_number if r.class_number is not None else 999999,  # Class number (numeric order, None goes last)
            r.division or "",  # Division
            r.section or "",  # Section
            r.class_name or "",  # Class name
            (
                0 if r.placement and 'Champion' in r.placement else
                1 if r.placement and 'Best' in r.placement else
                2 if r.placement and 'Reserve' in r.placement else
                3 if r.placement and '1st' in r.placement else
                4 if r.placement and '2nd' in r.placement else
                5 if r.placement and '3rd' in r.placement else
                6 if r.placement and '4th' in r.placement else
                98 if r.placement and 'DQ' in r.placement else
                99
            )
        ))
        
        report.append(f"  Total Results: {len(dog_results_sorted)}")
        report.append("  Results:")
        for result in dog_results_sorted:
            placement_str = result.placement or "N/A"
            # Build class/division/section string with class number
            class_parts = []
            if result.division:
                class_parts.append(result.division)
            if result.section:
                class_parts.append(result.section)
            if result.class_name:
                # Always show class number when available
                if result.class_number is not None:
                    class_parts.append(f"Class {result.class_number}: {result.class_name}")
                else:
                    class_parts.append(result.class_name)
            elif result.class_number is not None:
                # If we have a class number but no class name, still show the number
                class_parts.append(f"Class {result.class_number}")
            class_str = " - ".join(class_parts) if class_parts else "N/A"
            # For child/youth handler classes, don't display owner information
            class_name_upper = (result.class_name or "").upper()
            is_handler_class = (
                'CHILD HANDLER' in class_name_upper or
                'YOUTH HANDLER' in class_name_upper or
                'HANDLER' in class_name_upper and ('CHILD' in class_name_upper or 'YOUTH' in class_name_upper)
            )
            if is_handler_class:
                report.append(f"    {result.year} - {result.trial_name} ({result.date}): {placement_str} in {class_str}")
            else:
                owner_str = result.owner or "N/A"
                report.append(f"    {result.year} - {result.trial_name} ({result.date}): {placement_str} in {class_str} - Owner: {owner_str}")
    
    return '\n'.join(report)


def main():
    """Main function to scrape and process trial results."""
    if not HAS_REQUESTS:
        print("ERROR: Required libraries not installed.")
        print("Install with: pip install requests beautifulsoup4")
        sys.exit(1)
    
    print("=" * 80)
    print("JRTCA TRIAL RESULTS SCRAPER")
    print("=" * 80)
    print()
    
    all_trial_results = []
    trial_judges = {}  # trial_name -> {division -> judge_name}
    
    # Find trial result links from the website
    # Track processed URLs and trials to avoid duplicates
    processed_urls = set()
    seen_trials = set()  # (trial_name, date) tuples
    
    # First, scan and process local subfolders for trial result files
    print("Scanning local subfolders for trial result files...")
    local_files = scan_local_subfolders(".")
    print(f"Found {len(local_files)} local trial result files")
    
    # Process local files first
    for file_path, year, source_folder in local_files:
        # Extract trial name and date from file to check for duplicates
        # This works for both text/HTML and PDF files
        trial_name = None
        date = ""
        
        # First, try to extract trial name from filename as a fallback
        filename_base = os.path.splitext(os.path.basename(file_path))[0]
        # Clean up filename (remove common prefixes, replace underscores with spaces)
        filename_trial_name = filename_base.replace('_', ' ').replace('-', ' ')
        filename_trial_name = re.sub(r'^(debug_trial_|debug_)', '', filename_trial_name, flags=re.IGNORECASE)
        
        try:
            # For PDF files, extract text first
            if file_path.lower().endswith('.pdf'):
                if HAS_PYPDF2 or HAS_PDFPLUMBER:
                    page_text = extract_text_from_pdf(file_path)
                    if page_text:
                        # Read first 2000 chars to get trial name/date (PDFs may have more header text)
                        content = page_text[:2000]
                else:
                    print(f"  Skipping PDF {file_path}: No PDF library available")
                    continue
            else:
                # For text/HTML files, read normally
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)  # Read first 2000 chars to get trial name/date
            
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
                        print(f"  Skipping duplicate trial: {trial_name} ({date}) from {source_folder} ({os.path.basename(file_path)})")
                        continue
                    seen_trials.add((normalize_name(trial_name), date))
                else:
                    # If no date, check by normalized filename (for files with same base name)
                    normalized_filename = normalize_name(filename_trial_name)
                    # Check if we've seen this filename before (without date)
                    filename_key = (normalized_filename, "")
                    if filename_key in seen_trials:
                        print(f"  Skipping duplicate trial (by filename): {trial_name} from {source_folder} ({os.path.basename(file_path)})")
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
            
            all_trial_results.extend(results)
            # Store judge information for this trial
            if judges_info and trial_name:
                trial_judges[trial_name] = judges_info
            print(f"  Extracted {len(results)} results")
    
    # Then, find and process web links from jrtcayearbook.com
    base_url = "https://www.jrtcayearbook.com/"
    print("\nFinding trial result links from JRTCA Yearbook website...")
    trial_links = find_trial_result_links(base_url)
    print(f"Found {len(trial_links)} trial result links")
    
    # Process JRTCA Yearbook web links
    for link_text, url, year in trial_links:
        if url in processed_urls:
            continue
        processed_urls.add(url)
        
        print(f"\nProcessing: {url} ({year})")
        
        # Check if this is an archive page (contains "archive" in URL or link text)
        is_archive = "archive" in url.lower() or "archive" in link_text.lower()
        
        if is_archive:
            # Use parse_trial_results_page which handles archive pages by following individual trial links
            results = parse_trial_results_page(url, year)
            judges_info = {}
        else:
            # Individual trial page
            results, judges_info = parse_individual_trial_page(url, link_text, None, year)
        
        if results:
            all_trial_results.extend(results)
            # Store judge information for this trial
            if judges_info and link_text:
                trial_judges[link_text] = judges_info
            print(f"  Extracted {len(results)} results")
    
    # Also find and process links from JRTCC website
    print("\nFinding trial result links from JRTCC website...")
    jrtcc_links = find_jrtcc_trial_result_links("https://www.jrtcc.ca/trials/#results")
    print(f"Found {len(jrtcc_links)} JRTCC trial result links")
    
    # Process JRTCC links (mostly PDFs)
    for trial_name, url, year in jrtcc_links:
        if url in processed_urls:
            continue
        processed_urls.add(url)
        
        print(f"\nProcessing JRTCC: {trial_name} ({year})")
        print(f"  URL: {url}")
        
        # Check if this is a PDF file
        is_pdf = url.lower().endswith('.pdf')
        
        if is_pdf:
            # Download PDF and parse it
            # Create a temporary file path for downloading
            safe_trial_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', trial_name)
            safe_trial_name = safe_trial_name.replace(' ', '_').replace('&', 'and').replace("'", '')
            safe_trial_name = safe_trial_name[:50]  # Limit length
            
            # Check if we already have this file downloaded
            download_dir = os.path.join("jrtcc_downloads", year)
            os.makedirs(download_dir, exist_ok=True)
            pdf_file_path = os.path.join(download_dir, f"{safe_trial_name}.pdf")
            
            if not os.path.exists(pdf_file_path):
                print(f"  Downloading PDF...")
                if not download_file(url, pdf_file_path):
                    print(f"  Failed to download PDF, skipping")
                    continue
                print(f"  Downloaded to {pdf_file_path}")
            else:
                print(f"  Using existing file: {pdf_file_path}")
            
            # Parse the PDF file
            results, judges_info = parse_local_trial_file(pdf_file_path, year, "JRTCC")
        else:
            # HTML page - parse it directly
            results, judges_info = parse_individual_trial_page(url, trial_name, None, year)
        
        if results:
            all_trial_results.extend(results)
            # Store judge information for this trial
            if judges_info and trial_name:
                trial_judges[trial_name] = judges_info
            print(f"  Extracted {len(results)} results")
    
    print(f"\n{'=' * 80}")
    print(f"Total trial results extracted: {len(all_trial_results)}")
    print(f"{'=' * 80}\n")
    
    # Load catalog data if available
    catalog_dogs = {}
    catalog_files = glob.glob("Entries_Catalog_Report_*.txt")
    if catalog_files:
        print(f"Loading catalog data from {catalog_files[0]}...")
        # Parse catalog file (simplified - you may need to adjust based on your catalog format)
        try:
            with open(catalog_files[0], 'r', encoding='utf-8') as f:
                # This is a simplified parser - adjust based on your actual catalog format
                for line in f:
                    if 'Dog:' in line or 'Name:' in line:
                        # Extract dog information (simplified)
                        pass  # Add proper parsing logic here
        except Exception as e:
            print(f"  Warning: Could not parse catalog file: {e}")
    
    # Generate report
    print("Generating report...")
    report = generate_trial_results_report(all_trial_results, catalog_dogs, trial_judges)
    
    # Save report
    output_file = "Trial_Results_Report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to {output_file}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Extract trial results from Wayback Machine archives of jrtnnc.com
Focuses on:
- Cumberland Terrier Trial results (2002 and 2003)
- JRTNNC results (1990 onward)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
from collections import defaultdict

# Wayback Machine CDX API endpoint
CDX_API = "https://web.archive.org/cdx/search/cdx"
BASE_URL = "http://www.jrtnnc.com/"

def get_all_captures():
    """Get all captures of jrtnnc.com from Wayback Machine"""
    print("Fetching list of all captures from Wayback Machine...")
    print(f"CDX API: {CDX_API}")
    print(f"Base URL: {BASE_URL}")
    
    params = {
        'url': BASE_URL,
        'output': 'json',
        'collapse': 'urlkey',
        'limit': 10000
    }
    
    try:
        print(f"Making request to CDX API with params: {params}")
        response = requests.get(CDX_API, params=params, timeout=30)
        print(f"Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"Received {len(data)} rows from CDX API")
        
        # First row is headers
        if len(data) > 1:
            captures = []
            for row in data[1:]:
                if len(row) >= 3:
                    timestamp = row[1]
                    original_url = row[2]
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    captures.append({
                        'timestamp': timestamp,
                        'url': original_url,
                        'wayback_url': wayback_url,
                        'year': timestamp[:4] if len(timestamp) >= 4 else None
                    })
            print(f"Found {len(captures)} captures")
            return captures
        print("No data rows found in response")
        return []
    except Exception as e:
        print(f"Error fetching captures: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_archived_page(wayback_url):
    """Fetch an archived page from Wayback Machine"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(wayback_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {wayback_url}: {e}")
        return None

def extract_trial_results(html_content, url, year):
    """Extract trial results from HTML content"""
    results = []
    
    if not html_content:
        return results
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for various patterns that might indicate trial results
        # Check for Cumberland mentions
        is_cumberland = False
        if year in ['2002', '2003']:
            text_content = soup.get_text().lower()
            if 'cumberland' in text_content:
                is_cumberland = True
        
        # Check for JRTNNC mentions
        is_jrtnnc = False
        if year and int(year) >= 1990:
            text_content = soup.get_text().lower()
            if 'jrtnnc' in text_content or 'jack russell terrier national' in text_content:
                is_jrtnnc = True
        
        # Extract text content
        text = soup.get_text()
        
        # Look for results in tables
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text()
            if is_cumberland or is_jrtnnc:
                if any(keyword in table_text.lower() for keyword in ['1st', '2nd', '3rd', 'champion', 'reserve', 'winner', 'class']):
                    results.append({
                        'type': 'table',
                        'content': table_text,
                        'url': url,
                        'year': year,
                        'is_cumberland': is_cumberland,
                        'is_jrtnnc': is_jrtnnc
                    })
        
        # Look for results in lists
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            list_text = list_elem.get_text()
            if is_cumberland or is_jrtnnc:
                if any(keyword in list_text.lower() for keyword in ['1st', '2nd', '3rd', 'champion', 'reserve', 'winner']):
                    results.append({
                        'type': 'list',
                        'content': list_text,
                        'url': url,
                        'year': year,
                        'is_cumberland': is_cumberland,
                        'is_jrtnnc': is_jrtnnc
                    })
        
        # Extract all text if it contains relevant keywords
        if is_cumberland or is_jrtnnc:
            if any(keyword in text.lower() for keyword in ['trial', 'results', 'championship', 'winner', '1st', '2nd', '3rd']):
                # Split into paragraphs
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para and len(para) > 50:  # Only meaningful paragraphs
                        if any(keyword in para.lower() for keyword in ['1st', '2nd', '3rd', 'champion', 'reserve', 'class', 'owner']):
                            results.append({
                                'type': 'paragraph',
                                'content': para,
                                'url': url,
                                'year': year,
                                'is_cumberland': is_cumberland,
                                'is_jrtnnc': is_jrtnnc
                            })
        
        # Also extract the full page text for manual review
        if is_cumberland or is_jrtnnc:
            results.append({
                'type': 'full_page',
                'content': text,
                'url': url,
                'year': year,
                'is_cumberland': is_cumberland,
                'is_jrtnnc': is_jrtnnc
            })
    
    except Exception as e:
        print(f"Error parsing HTML from {url}: {e}")
    
    return results

def filter_relevant_captures(captures):
    """Filter captures to only relevant years"""
    filtered = []
    
    for capture in captures:
        year = capture.get('year')
        if not year:
            continue
        
        # Include Cumberland years (2002, 2003)
        if year in ['2002', '2003']:
            filtered.append(capture)
        # Include JRTNNC years (1990 onward)
        elif year and year.isdigit() and int(year) >= 1990:
            filtered.append(capture)
    
    return filtered

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Starting extraction of trial results from Wayback Machine...")
    sys.stdout.flush()
    print("=" * 70)
    sys.stdout.flush()
    
    # Get all captures
    all_captures = get_all_captures()
    
    if not all_captures:
        print("No captures found. Exiting.")
        return
    
    # Filter to relevant years
    relevant_captures = filter_relevant_captures(all_captures)
    print(f"\nFiltered to {len(relevant_captures)} relevant captures")
    
    # Group by year for better organization
    by_year = defaultdict(list)
    for capture in relevant_captures:
        year = capture.get('year', 'unknown')
        by_year[year].append(capture)
    
    print(f"\nCaptures by year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {len(by_year[year])} captures")
    
    # Extract results
    all_results = []
    processed = 0
    
    print(f"\nProcessing {len(relevant_captures)} captures...")
    
    for i, capture in enumerate(relevant_captures, 1):
        wayback_url = capture['wayback_url']
        year = capture.get('year', 'unknown')
        
        print(f"[{i}/{len(relevant_captures)}] Processing {year} - {wayback_url[:80]}...")
        
        # Fetch the archived page
        html_content = get_archived_page(wayback_url)
        
        if html_content:
            # Extract results
            results = extract_trial_results(html_content, wayback_url, year)
            all_results.extend(results)
            processed += 1
        
        # Be polite to the server
        time.sleep(0.5)
        
        # Save progress every 10 captures
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(relevant_captures)} processed, {len(all_results)} results extracted")
    
    print(f"\nExtraction complete!")
    print(f"Processed: {processed}/{len(relevant_captures)} captures")
    print(f"Total results extracted: {len(all_results)}")
    
    # Save results
    output_file = 'wayback_extracted_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Also create a text file with formatted results
    text_output = 'wayback_extracted_results.txt'
    with open(text_output, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("TRIAL RESULTS EXTRACTED FROM WAYBACK MACHINE\n")
        f.write("=" * 70 + "\n\n")
        
        # Group by year and type
        by_year_type = defaultdict(lambda: defaultdict(list))
        for result in all_results:
            year = result.get('year', 'unknown')
            result_type = result.get('type', 'unknown')
            by_year_type[year][result_type].append(result)
        
        for year in sorted(by_year_type.keys()):
            f.write(f"\n{'=' * 70}\n")
            f.write(f"YEAR: {year}\n")
            f.write(f"{'=' * 70}\n\n")
            
            for result_type in sorted(by_year_type[year].keys()):
                f.write(f"\n--- {result_type.upper()} ---\n\n")
                
                for result in by_year_type[year][result_type]:
                    is_cumberland = result.get('is_cumberland', False)
                    is_jrtnnc = result.get('is_jrtnnc', False)
                    
                    f.write(f"URL: {result['url']}\n")
                    if is_cumberland:
                        f.write("TYPE: Cumberland Terrier Trial\n")
                    if is_jrtnnc:
                        f.write("TYPE: JRTNNC\n")
                    f.write(f"\n{result['content']}\n")
                    f.write("\n" + "-" * 70 + "\n\n")
    
    print(f"Text results saved to: {text_output}")
    
    # Summary
    cumberland_count = sum(1 for r in all_results if r.get('is_cumberland'))
    jrtnnc_count = sum(1 for r in all_results if r.get('is_jrtnnc'))
    
    print(f"\nSummary:")
    print(f"  Cumberland results: {cumberland_count}")
    print(f"  JRTNNC results: {jrtnnc_count}")
    print(f"  Total results: {len(all_results)}")

if __name__ == '__main__':
    import sys
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


#!/usr/bin/env python3
"""
Extract trial results from Wayback Machine archives
Uses the URL pattern: https://web.archive.org/web/20250000000000*/http://www.jrtnnc.com/
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import sys

# Output files
OUTPUT_JSON = 'wayback_extracted_results.json'
OUTPUT_TEXT = 'wayback_extracted_results.txt'

def log(message):
    """Log message to both console and file"""
    print(message)
    sys.stdout.flush()
    with open('extraction_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()}: {message}\n")

def get_wayback_captures():
    """
    Get list of captures from Wayback Machine
    Since we know there are 130 captures, we'll try to get them via the CDX API
    """
    log("Fetching capture list from Wayback Machine CDX API...")
    
    url = "https://web.archive.org/cdx/search/cdx"
    params = {
        'url': 'http://www.jrtnnc.com/',
        'output': 'json',
        'limit': 200
    }
    
    captures = []
    try:
        log("Making request to CDX API (this may take a moment)...")
        response = requests.get(url, params=params, timeout=30)
        log(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            log("Parsing JSON response...")
            data = response.json()
            log(f"Received {len(data)} rows")
            
            if len(data) > 1:
                for row in data[1:]:
                    if len(row) >= 3:
                        timestamp = row[1]
                        original = row[2]
                        wayback_url = f"https://web.archive.org/web/{timestamp}/{original}"
                        year = timestamp[:4] if len(timestamp) >= 4 else None
                        captures.append({
                            'timestamp': timestamp,
                            'url': original,
                            'wayback_url': wayback_url,
                            'year': year
                        })
                log(f"Found {len(captures)} captures via CDX API")
                return captures
            else:
                log("No data rows in response")
        else:
            log(f"API returned status {response.status_code}")
    except requests.exceptions.Timeout:
        log("CDX API request timed out")
    except requests.exceptions.RequestException as e:
        log(f"CDX API request error: {e}")
    except Exception as e:
        log(f"CDX API error: {e}")
        import traceback
        log(traceback.format_exc())
    
    # If CDX fails, try alternative: use known years to construct URLs
    log("CDX API unavailable. Trying alternative method with known years...")
    captures = []
    years = list(range(1990, 2025))
    # Try a few dates per year
    for year in years:
        for month in [1, 6, 12]:  # Try beginning, middle, end of year
            for day in [1, 15]:
                timestamp = f"{year}{month:02d}{day:02d}000000"
                wayback_url = f"https://web.archive.org/web/{timestamp}/http://www.jrtnnc.com/"
                captures.append({
                    'timestamp': timestamp,
                    'url': 'http://www.jrtnnc.com/',
                    'wayback_url': wayback_url,
                    'year': str(year)
                })
    log(f"Generated {len(captures)} potential capture URLs")
    return captures

def fetch_page(wayback_url):
    """Fetch a single archived page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(wayback_url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def extract_results(html, wayback_url, year):
    """Extract trial results from HTML"""
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        text_lower = text.lower()
        
        # Determine if this is relevant
        is_cumberland = False
        is_jrtnnc = False
        
        if year in ['2002', '2003']:
            if 'cumberland' in text_lower:
                is_cumberland = True
        
        if year and year.isdigit() and int(year) >= 1990:
            if 'jrtnnc' in text_lower or 'jack russell terrier national' in text_lower:
                is_jrtnnc = True
        
        if not (is_cumberland or is_jrtnnc):
            return None
        
        # Check if it contains results
        has_results = any(kw in text_lower for kw in [
            '1st', '2nd', '3rd', 'champion', 'reserve', 'winner', 
            'class', 'owner', 'trial', 'results'
        ])
        
        if has_results:
            return {
                'year': year,
                'url': wayback_url,
                'is_cumberland': is_cumberland,
                'is_jrtnnc': is_jrtnnc,
                'content': text,
                'html': html
            }
    except Exception as e:
        log(f"Error extracting from {wayback_url}: {e}")
    
    return None

def main():
    log("=" * 70)
    log("Wayback Machine Results Extractor")
    log("=" * 70)
    
    # Get captures
    captures = get_wayback_captures()
    
    if not captures:
        log("\nNo captures found via API.")
        log("To use this script:")
        log("1. Visit: https://web.archive.org/web/20250000000000*/http://www.jrtnnc.com/")
        log("2. Note the specific capture URLs")
        log("3. Modify this script to include those URLs")
        log("\nAlternatively, you can manually browse the captures and copy the results.")
        return
    
    # Filter to relevant years
    relevant = [c for c in captures if (
        c.get('year') in ['2002', '2003'] or 
        (c.get('year') and c.get('year').isdigit() and int(c.get('year')) >= 1990)
    )]
    
    log(f"\nFound {len(relevant)} relevant captures")
    log(f"Processing captures...")
    
    results = []
    for i, capture in enumerate(relevant, 1):
        year = capture.get('year', 'unknown')
        url = capture['wayback_url']
        
        log(f"[{i}/{len(relevant)}] {year}: Fetching...")
        
        html = fetch_page(url)
        if html:
            result = extract_results(html, url, year)
            if result:
                results.append(result)
                log(f"  ✓ Found results")
            else:
                log(f"  ✗ No relevant results")
        else:
            log(f"  ✗ Failed to fetch")
        
        time.sleep(0.5)  # Rate limiting
    
    # Save results
    if results:
        log(f"\nSaving {len(results)} results...")
        
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            # Remove HTML from JSON to keep it smaller
            json_results = []
            for r in results:
                json_results.append({
                    'year': r['year'],
                    'url': r['url'],
                    'is_cumberland': r['is_cumberland'],
                    'is_jrtnnc': r['is_jrtnnc'],
                    'content': r['content']
                })
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        with open(OUTPUT_TEXT, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("TRIAL RESULTS FROM WAYBACK MACHINE\n")
            f.write("=" * 70 + "\n\n")
            
            for r in results:
                f.write(f"\n{'='*70}\n")
                f.write(f"YEAR: {r['year']}\n")
                f.write(f"URL: {r['url']}\n")
                if r['is_cumberland']:
                    f.write("TYPE: Cumberland Terrier Trial\n")
                if r['is_jrtnnc']:
                    f.write("TYPE: JRTNNC\n")
                f.write(f"\n{r['content']}\n")
        
        log(f"Results saved to {OUTPUT_JSON} and {OUTPUT_TEXT}")
    else:
        log("No results found.")
    
    log("\nExtraction complete!")

if __name__ == '__main__':
    main()


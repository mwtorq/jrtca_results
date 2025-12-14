#!/usr/bin/env python3
"""
Extract trial results from Wayback Machine using the known URL pattern
User found 130 captures at: https://web.archive.org/web/20250000000000*/http://www.jrtnnc.com/
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from collections import defaultdict
import sys

# Use Wayback Machine's web interface to get capture list
WAYBACK_BASE = "https://web.archive.org/web/"

def get_captures_from_wayback():
    """Get list of captures using Wayback Machine's timeline interface"""
    print("Fetching capture list from Wayback Machine...")
    sys.stdout.flush()
    
    # Use the timeline JSON API
    timeline_url = "https://web.archive.org/web/timemap/json/http://www.jrtnnc.com/"
    
    try:
        response = requests.get(timeline_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            captures = []
            for item in data:
                if len(item) >= 2:
                    timestamp = item[1]
                    original_url = item[0] if item[0] else "http://www.jrtnnc.com/"
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    year = timestamp[:4] if len(timestamp) >= 4 else None
                    captures.append({
                        'timestamp': timestamp,
                        'url': original_url,
                        'wayback_url': wayback_url,
                        'year': year
                    })
            print(f"Found {len(captures)} captures")
            return captures
    except Exception as e:
        print(f"Error with timeline API: {e}")
    
    # Fallback: manually construct URLs for known years
    print("Using fallback method: constructing URLs for known years...")
    captures = []
    years = list(range(1990, 2025))  # 1990 to 2024
    months = range(1, 13)
    
    # Create potential capture URLs (this is a simplified approach)
    # In reality, we'd need to query the actual capture dates
    for year in years:
        for month in months:
            # Try a few dates per month
            for day in [1, 15]:
                timestamp = f"{year}{month:02d}{day:02d}000000"
                wayback_url = f"https://web.archive.org/web/{timestamp}/{BASE_URL}"
                captures.append({
                    'timestamp': timestamp,
                    'url': BASE_URL,
                    'wayback_url': wayback_url,
                    'year': str(year)
                })
    
    print(f"Generated {len(captures)} potential capture URLs")
    return captures

BASE_URL = "http://www.jrtnnc.com/"

def get_archived_page(wayback_url):
    """Fetch an archived page from Wayback Machine"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(wayback_url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        return None

def extract_trial_results(html_content, url, year):
    """Extract trial results from HTML content"""
    results = []
    
    if not html_content:
        return results
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        text_lower = text.lower()
        
        # Check for Cumberland (2002-2003)
        is_cumberland = False
        if year in ['2002', '2003']:
            if 'cumberland' in text_lower:
                is_cumberland = True
        
        # Check for JRTNNC (1990 onward)
        is_jrtnnc = False
        if year and year.isdigit() and int(year) >= 1990:
            if 'jrtnnc' in text_lower or 'jack russell terrier national' in text_lower:
                is_jrtnnc = True
        
        # Only process if relevant
        if not (is_cumberland or is_jrtnnc):
            return results
        
        # Extract structured data
        # Look for results in various formats
        if any(keyword in text_lower for keyword in ['1st', '2nd', '3rd', 'champion', 'reserve', 'winner', 'class', 'owner']):
            results.append({
                'type': 'full_page',
                'content': text,
                'url': url,
                'year': year,
                'is_cumberland': is_cumberland,
                'is_jrtnnc': is_jrtnnc
            })
    
    except Exception as e:
        pass
    
    return results

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("Extracting Trial Results from Wayback Machine")
    print("=" * 70)
    sys.stdout.flush()
    
    # Get captures
    all_captures = get_captures_from_wayback()
    
    if not all_captures:
        print("No captures found. Exiting.")
        return
    
    # Filter to relevant years
    relevant = []
    for cap in all_captures:
        year = cap.get('year')
        if year in ['2002', '2003'] or (year and year.isdigit() and int(year) >= 1990):
            relevant.append(cap)
    
    print(f"\nProcessing {len(relevant)} relevant captures...")
    sys.stdout.flush()
    
    all_results = []
    processed = 0
    
    for i, capture in enumerate(relevant[:50], 1):  # Limit to first 50 for testing
        wayback_url = capture['wayback_url']
        year = capture.get('year', 'unknown')
        
        print(f"[{i}/{min(50, len(relevant))}] {year} - {wayback_url[:60]}...", end=' ')
        sys.stdout.flush()
        
        html = get_archived_page(wayback_url)
        if html:
            results = extract_trial_results(html, wayback_url, year)
            if results:
                all_results.extend(results)
                print(f"✓ Found {len(results)} results")
            else:
                print("✗ No results")
        else:
            print("✗ Failed to fetch")
        
        sys.stdout.flush()
        time.sleep(0.3)  # Be polite
    
    print(f"\n\nExtraction complete!")
    print(f"Total results: {len(all_results)}")
    
    # Save results
    if all_results:
        with open('wayback_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print("Saved to: wayback_results.json")
        
        with open('wayback_results.txt', 'w', encoding='utf-8') as f:
            for result in all_results:
                f.write(f"\n{'='*70}\n")
                f.write(f"Year: {result['year']}\n")
                f.write(f"URL: {result['url']}\n")
                f.write(f"Cumberland: {result['is_cumberland']}\n")
                f.write(f"JRTNNC: {result['is_jrtnnc']}\n")
                f.write(f"\n{result['content']}\n")
        print("Saved to: wayback_results.txt")

if __name__ == '__main__':
    main()






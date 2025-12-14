#!/usr/bin/env python3
"""Test script to verify Wayback Machine API access"""

import requests
import sys

print("Testing Wayback Machine API access...")
sys.stdout.flush()

CDX_API = "https://web.archive.org/cdx/search/cdx"
BASE_URL = "http://www.jrtnnc.com/"

params = {
    'url': BASE_URL,
    'output': 'json',
    'limit': 10
}

try:
    print(f"Making request to: {CDX_API}")
    print(f"URL: {BASE_URL}")
    sys.stdout.flush()
    
    response = requests.get(CDX_API, params=params, timeout=30)
    print(f"Status code: {response.status_code}")
    sys.stdout.flush()
    
    if response.status_code == 200:
        data = response.json()
        print(f"Received {len(data)} rows")
        sys.stdout.flush()
        
        if len(data) > 1:
            print(f"First capture: {data[1]}")
            sys.stdout.flush()
        else:
            print("No captures found")
            sys.stdout.flush()
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])
        sys.stdout.flush()
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

print("Test complete")
sys.stdout.flush()






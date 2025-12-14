# Extracting Results from Wayback Machine

You found 130 captures of jrtnnc.com at:
https://web.archive.org/web/20250000000000*/http://www.jrtnnc.com/

## Manual Extraction Method

Since the automated script may have issues, here's how to manually extract results:

1. **Visit the Wayback Machine URL**: 
   https://web.archive.org/web/20250000000000*/http://www.jrtnnc.com/

2. **Browse through the captures** - Click on different dates to view archived versions

3. **Look for results pages** - Navigate to pages containing:
   - Cumberland Terrier Trial results (2002-2003)
   - JRTNNC results (1990 onward)

4. **Copy the content** - For each relevant page:
   - Copy the HTML source or text content
   - Save it with a filename indicating the year and type

## Automated Extraction

Run the Python script:
```bash
python wayback_extractor.py
```

This will:
- Fetch all captures from the Wayback Machine
- Filter for Cumberland (2002-2003) and JRTNNC (1990 onward)
- Extract trial results from each page
- Save to `wayback_extracted_results.json` and `wayback_extracted_results.txt`

## Alternative: Direct URL Access

If you know specific capture URLs, you can modify the script to process them directly.

For example, if you find a capture from 2002:
```
https://web.archive.org/web/20020101120000/http://www.jrtnnc.com/results.html
```

You can add these URLs to the script for direct processing.






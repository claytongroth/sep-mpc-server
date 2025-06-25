#!/usr/bin/env python3
"""
Stanford Encyclopedia of Philosophy Webscraper
Scrapes entry links and downloads full HTML content for each entry.
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import time
from urllib.parse import urljoin, urlparse
import sys

# Configuration variables
BASE_URL = "https://plato.stanford.edu/archives/sum2025/contents.html"
BASE_DOWNLOAD_URL = "https://plato.stanford.edu/archives/sum2025"
DOWNLOAD_DIRECTORY = "../data"
DELAY_BETWEEN_REQUESTS = 1  # seconds - be respectful to the server
USER_AGENT = "Mozilla/5.0 (compatible; Python webscraper)"

def create_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def get_page_content(url):
    """Fetch page content with error handling."""
    headers = {'User-Agent': USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_entry_links(html_content):
    """Extract entry links matching the pattern."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all <a> tags with href matching "entries/something/"
    entry_links = []
    
    # Look for <a> tags containing <strong> elements
    links = soup.find_all('a', href=re.compile(r'entries/[^/]+/?$'))
    
    for link in links:
        href = link.get('href')
        strong_tag = link.find('strong')
        
        # Check if the link contains a <strong> tag
        if strong_tag and href:
            # Extract entry name from href (e.g., "entries/abduction/" -> "abduction")
            match = re.search(r'entries/([^/]+)/?$', href)
            if match:
                entry_name = match.group(1)
                entry_links.append({
                    'name': entry_name,
                    'href': href,
                    'text': strong_tag.get_text().strip()
                })
    
    return entry_links

def download_entry(entry_name, base_download_url, download_dir):
    """Download HTML content for a specific entry."""
    # Construct the full URL
    entry_url = f"{base_download_url}/entries/{entry_name}/"
    
    print(f"Downloading: {entry_name} from {entry_url}")
    
    # Get the HTML content
    html_content = get_page_content(entry_url)
    
    if html_content:
        # Save to file
        filename = os.path.join(download_dir, f"{entry_name}.html")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  ✓ Saved: {filename}")
            return True
        except IOError as e:
            print(f"  ✗ Error saving {filename}: {e}")
            return False
    else:
        print(f"  ✗ Failed to download content for {entry_name}")
        return False

def main():
    """Main function to orchestrate the scraping process."""
    print("Stanford Encyclopedia of Philosophy Webscraper")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Download URL: {BASE_DOWNLOAD_URL}")
    print(f"Download Directory: {DOWNLOAD_DIRECTORY}")
    print()
    
    # Create download directory
    create_directory(DOWNLOAD_DIRECTORY)
    
    # Get the main page content
    print("Fetching main page...")
    main_page_content = get_page_content(BASE_URL)
    
    if not main_page_content:
        print("Failed to fetch main page. Exiting.")
        sys.exit(1)
    
    # Extract entry links
    print("Extracting entry links...")
    entry_links = extract_entry_links(main_page_content)
    
    if not entry_links:
        print("No entry links found. Check the URL and pattern.")
        sys.exit(1)
    
    print(f"Found {len(entry_links)} entries to download.")
    print()
    
    # Download each entry
    successful_downloads = 0
    failed_downloads = 0
    
    for i, entry in enumerate(entry_links, 1):
        print(f"[{i}/{len(entry_links)}] Processing: {entry['name']}")
        
        success = download_entry(entry['name'], BASE_DOWNLOAD_URL, DOWNLOAD_DIRECTORY)
        
        if success:
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Be respectful - add delay between requests
        if i < len(entry_links):  # Don't sleep after the last request
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Summary
    print()
    print("=" * 50)
    print("Download Summary:")
    print(f"  Successful: {successful_downloads}")
    print(f"  Failed: {failed_downloads}")
    print(f"  Total: {len(entry_links)}")
    print(f"Files saved to: {DOWNLOAD_DIRECTORY}")

if __name__ == "__main__":
    main()
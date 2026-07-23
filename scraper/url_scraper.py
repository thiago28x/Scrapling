import csv
from datetime import datetime
import os
import re
import sys
import time
from urllib.parse import urljoin
from scrapling.fetchers import StealthySession

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://charhub.ai/'
CSV_FILEPATH = os.path.join(os.path.dirname(__file__), 'character_urls.csv')
CHARACTER_URL_PATTERN = re.compile(r'^https?://charhub\.ai/characters/\d+$')


def extract_character_urls(page, base_url=BASE_URL):
    """
    Extracts unique character URLs matching /characters/<id> from the page.
    """
    links = page.css('a[href*="/characters/"]')
    found_urls = set()
    for link in links:
        href = link.attrib.get('href', '')
        if href:
            full_url = urljoin(base_url, href)
            clean_url = full_url.split('?')[0].rstrip('/')
            if CHARACTER_URL_PATTERN.match(clean_url):
                found_urls.add(clean_url)
    return sorted(list(found_urls))


def load_url_records(filepath=CSV_FILEPATH):
    """
    Reads character_urls.csv into a dict mapping url -> {'scraped': bool, 'scraped_at': str}.
    Handles both old single-column CSVs and new 3-column CSVs seamlessly.
    """
    records = {}
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Handle plain single-column CSV without header or old header
            if reader.fieldnames and 'url' in reader.fieldnames:
                for row in reader:
                    u = (row.get('url') or '').strip()
                    if CHARACTER_URL_PATTERN.match(u):
                        scraped_val = (row.get('scraped') or 'false').lower() == 'true'
                        records[u] = {
                            'scraped': scraped_val,
                            'scraped_at': row.get('scraped_at') or ''
                        }
            else:
                # Fallback for plain lines
                f.seek(0)
                lines = f.read().splitlines()
                for line in lines:
                    u = line.strip()
                    if CHARACTER_URL_PATTERN.match(u):
                        records[u] = {'scraped': False, 'scraped_at': ''}
    return records


def save_url_records(records, filepath=CSV_FILEPATH):
    """
    Writes all URL records dict to character_urls.csv with columns: url, scraped, scraped_at.
    """
    fieldnames = ['url', 'scraped', 'scraped_at']
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for u in sorted(records.keys()):
            writer.writerow({
                'url': u,
                'scraped': 'true' if records[u]['scraped'] else 'false',
                'scraped_at': records[u]['scraped_at']
            })


def save_urls_to_csv(urls, filepath=CSV_FILEPATH):
    """
    Saves newly discovered character URLs to CSV with default 'scraped': false.
    Preserves existing scraped status for previously recorded URLs.
    """
    records = load_url_records(filepath)
    new_count = 0

    for u in urls:
        if u not in records:
            records[u] = {'scraped': False, 'scraped_at': ''}
            new_count += 1

    save_url_records(records, filepath)
    print(f"[SUCCESS] Updated {os.path.basename(filepath)}: {len(records)} total URLs recorded ({new_count} new).")
    return new_count


def mark_url_scraped(url, filepath=CSV_FILEPATH):
    """
    Marks a specific URL as scraped: true with timestamp in character_urls.csv.
    """
    records = load_url_records(filepath)
    url_clean = url.split('?')[0].rstrip('/')
    records[url_clean] = {
        'scraped': True,
        'scraped_at': datetime.now().isoformat()
    }
    save_url_records(records, filepath)


def get_pending_urls(filepath=CSV_FILEPATH):
    """
    Returns a list of character URLs that have scraped == False.
    """
    records = load_url_records(filepath)
    return [u for u, data in sorted(records.items()) if not data['scraped']]


def scrape_homepage_urls(max_pages=3, session=None):
    """
    Fetches character URLs across multiple homepage pagination pages.
    """
    print(f"[START] Scraping character URLs from homepage (first {max_pages} pages)...")
    all_collected_urls = set()

    def _scrape_with_session(sess):
        for page_num in range(1, max_pages + 1):
            target_url = f"{BASE_URL}?page={page_num}" if page_num > 1 else BASE_URL
            print(f"[INFO] Navigating to page {page_num}: {target_url}...")

            try:
                page_response = sess.fetch(target_url, network_idle=True)
                urls = extract_character_urls(page_response, base_url=target_url)
                print(f"[INFO] Found {len(urls)} character URLs on page {page_num}.")
                all_collected_urls.update(urls)

                nav_links = page_response.css('nav.pagy a')
                if nav_links and page_num == 1:
                    page_numbers = []
                    for nl in nav_links:
                        text = nl.get_all_text().strip()
                        if text.isdigit():
                            page_numbers.append(int(text))
                    if page_numbers:
                        print(f"[INFO] Detected pagination range: max page is ~{max(page_numbers)}")

            except Exception as err:
                print(f"[ERROR] Failed to fetch page {page_num}: {err}")
                break

            time.sleep(1)

    if session:
        _scrape_with_session(session)
    else:
        with StealthySession(headless=False, solve_cloudflare=True) as sess:
            _scrape_with_session(sess)

    print(f"\n================ HOMEPAGE SCRAPE SUMMARY ================")
    print(f"Total Unique URLs Collected across batch: {len(all_collected_urls)}")
    print("==========================================================\n")

    save_urls_to_csv(sorted(list(all_collected_urls)))
    return sorted(list(all_collected_urls))


if __name__ == '__main__':
    # Test run for first 3 pages batch
    scrape_homepage_urls(max_pages=3)

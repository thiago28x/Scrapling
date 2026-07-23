import argparse
import os
import sys
import time
from scrapling.fetchers import StealthySession


# python scraper/main_controller.py --pages 20 --max-profiles 600

from scraper import scrape_character_profile
from url_scraper import (
    get_pending_urls,
    mark_url_scraped,
    scrape_homepage_urls,
)

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def run_pipeline(max_pages=3, max_profiles=None, headless=False):
    """
    Main controller pipeline:
    1. Discovers character URLs from homepage pagination (max_pages).
    2. Identifies pending (unscraped) character URLs.
    3. Scrapes pending profiles reusing a single stealthy browser session.
    4. Marks scraped URLs as 'true' with timestamps in character_urls.csv.
    """
    start_time = time.time()
    print("=" * 60)
    print("🚀 STARTING CHARHUB PIPELINE RUN")
    print(f"Target Pages: {max_pages} | Max Profiles Cap: {max_profiles or 'Unlimited'} | Headless: {headless}")
    print("=" * 60 + "\n")

    # Reuse a single stealthy browser session across homepage & profile scraping
    with StealthySession(headless=headless, solve_cloudflare=True) as session:
        # Phase 1: URL Discovery
        print("[PHASE 1] Discovering character URLs from homepage...")
        scrape_homepage_urls(max_pages=max_pages, session=session)

        # Phase 2: Identify Pending URLs
        pending_urls = get_pending_urls()
        print(f"\n[PHASE 2] Found {len(pending_urls)} pending (unscraped) profiles.")

        if max_profiles and len(pending_urls) > max_profiles:
            print(f"[INFO] Capping profile batch to {max_profiles} for this run.")
            pending_urls = pending_urls[:max_profiles]

        if not pending_urls:
            print("[INFO] All discovered characters have already been scraped! Nothing to do.")
            return

        # Phase 3: Scrape Pending Profiles
        print(f"\n[PHASE 3] Scraping {len(pending_urls)} character profiles...\n")
        success_count = 0
        error_count = 0

        try:
            for idx, url in enumerate(pending_urls, start=1):
                print(f"[{idx}/{len(pending_urls)}] Scraping: {url} ...")
                try:
                    data = scrape_character_profile(url, session=session, headless=headless)
                    if data:
                        mark_url_scraped(url)
                        success_count += 1
                        print(f"   -> [SUCCESS] '{data.get('name')}' by {data.get('creator')} saved & marked as scraped.\n")
                    else:
                        print(f"   -> [WARN] Could not parse profile data from {url}\n")
                        error_count += 1
                except Exception as err:
                    print(f"   -> [ERROR] Failed scraping profile {url}: {err}\n")
                    error_count += 1

                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Pipeline run paused by user (KeyboardInterrupt). Progress saved cleanly!")

    elapsed = round(time.time() - start_time, 2)
    print("=" * 60)
    print("✅ PIPELINE RUN COMPLETED")
    print(f"Successfully Scraped: {success_count}")
    print(f"Errors/Skipped: {error_count}")
    print(f"Elapsed Time: {elapsed} seconds")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Charhub Twice-Daily Pipeline Controller")
    parser.add_argument('--pages', type=int, default=3, help="Number of homepage pagination pages to scan")
    parser.add_argument('--max-profiles', type=int, default=None, help="Max number of profiles to scrape per run")
    parser.add_argument('--headless', action='store_true', help="Run browser in headless mode")

    args = parser.parse_args()
    run_pipeline(max_pages=args.pages, max_profiles=args.max_profiles, headless=args.headless)

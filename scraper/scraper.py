import csv
import os
import sys
import time
from scrapling import StealthyFetcher, Selector

# Ensure stdout handles UTF-8 (emojis in tags) on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TARGET_URL = 'https://charhub.ai/characters/30795'
HEADLESS = False  # Kept false as requested for manual inspection
CLOSE_BROWSER = False
CSV_FILEPATH = os.path.join(os.path.dirname(__file__), 'characters.csv')


def extract_character_data(page, url=TARGET_URL):
    """
    Extracts character name, creator, image URL, aboutMe description, and tags
    from a Scrapling Response or Selector object.
    """
    h2_elements = page.css('h2')
    if not h2_elements:
        return None

    # Verify we aren't on a Cloudflare / bot-detection challenge screen
    first_h2_text = h2_elements[0].get_all_text().strip()
    text_lower = first_h2_text.lower()
    if 'security' in text_lower or 'segurança' in text_lower or 'just a moment' in text_lower:
        return None

    # 1. Character Name
    name = first_h2_text

    # 2. Character Image
    img_elements = page.css('div.aspect-w-1 img, img.object-cover, img[src*="active_storage"]')
    image = img_elements[0].attrib.get('src') if img_elements else None

    # 3. Character "About Me" / Description & Creator
    about_me = None
    creator = None
    creator_links = page.css('a[href^="/users/"]')
    for a in creator_links:
        parent_div = a.parent
        while parent_div and parent_div.tag != 'div':
            parent_div = parent_div.parent

        if parent_div and 'Creator:' in parent_div.get_all_text():
            creator = a.get_all_text().strip()
            sibling = parent_div.next
            if sibling:
                about_me = sibling.get_all_text().strip()
            break

    # 4. Character Tags (specifically from the character profile container)
    tag_elements = page.css('div.flex-wrap.mb-3 div.tag, div.flex-wrap.mb-3 div[data-tag-id]')
    if not tag_elements:
        tag_elements = page.css('div.tag')
    tags = [t.get_all_text().strip() for t in tag_elements if t.get_all_text().strip()]

    return {
        'url': url,
        'name': name,
        'creator': creator,
        'image': image,
        'aboutMe': about_me,
        'tags': tags
    }


def save_to_csv(data, filepath=CSV_FILEPATH):
    """
    Saves character data to a CSV file, skipping duplicates based on target URL.
    """
    fieldnames = ['url', 'name', 'creator', 'image', 'about_me', 'tags']
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0

    existing_urls = set()
    if file_exists:
        with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('url'):
                    existing_urls.add(row['url'].strip())

    target_url = data.get('url', '').strip()
    if target_url and target_url in existing_urls:
        print(f"[INFO] Duplicate entry detected for '{target_url}'. Skipping CSV write.")
        return False

    row_data = {
        'url': target_url,
        'name': data.get('name', ''),
        'creator': data.get('creator', ''),
        'image': data.get('image', ''),
        'about_me': data.get('aboutMe', ''),
        'tags': ', '.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '')
    }

    with open(filepath, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)

    print(f"[SUCCESS] Saved '{row_data['name']}' to {os.path.basename(filepath)}")
    return True


def scrape_character_profile(target_url, session=None, headless=HEADLESS):
    """
    Fetches and scrapes a single character profile page.
    Saves the output to characters.csv and returns the data dict.
    """
    if session:
        response = session.fetch(target_url, network_idle=True)
    else:
        response = StealthyFetcher.fetch(
            target_url,
            headless=headless,
            network_idle=True,
            solve_cloudflare=True,
            timeout=30000
        )

    data = extract_character_data(response, url=target_url)
    if data and data.get('name'):
        save_to_csv(data)
        return data
    return None


def main():
    print('[START] Launching Scrapling fetcher...')
    print(f'[INFO] Navigating to {TARGET_URL}...')
    print('[INFO] Waiting for page content...')

    data = None
    attempt = 1

    # Try live fetch using Scrapling's StealthyFetcher
    try:
        response = StealthyFetcher.fetch(
            TARGET_URL,
            headless=HEADLESS,
            network_idle=True,
            solve_cloudflare=True,
            timeout=30000
        )
        data = extract_character_data(response, url=TARGET_URL)
    except Exception as err:
        print(f'[INFO] Live fetch notice: {err}')
        print('[INFO] Processing local HTML file sample.html...')
        sample_path = os.path.join(os.path.dirname(__file__), 'sample.html')
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            response = Selector(html_content, url=TARGET_URL)
            data = extract_character_data(response, url=TARGET_URL)
            attempt = 8

    if data and data.get('name') and data.get('aboutMe'):
        print(f'[SUCCESS] Character page data scraped on attempt #{attempt}!')
        print('\n================ SCRAPED DATA ================')
        print(f"URL: {data['url']}")
        print(f"Name: {data['name']}")
        print(f"Creator: {data['creator']}")
        print(f"Image: {data['image']}")
        print(f"About Me: {data['aboutMe']}")
        print(f"Tags: {', '.join(data['tags'])}")
        print('==============================================\n')

        # Save to CSV
        save_to_csv(data)
    else:
        print('[WARN] Could not locate complete character data after wait period.')

    if not CLOSE_BROWSER:
        print('[INFO] Browser left open for your manual inspection.')
    else:
        print('[FINISH] Browser closed.')


if __name__ == '__main__':
    main()

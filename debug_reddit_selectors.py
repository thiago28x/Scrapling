#!/usr/bin/env python3
"""
Debug script to inspect Reddit page structure and find the right selectors.
"""

from scrapling.fetchers import StealthyFetcher

url = "https://www.reddit.com/r/opencodeCLI/comments/1ug2z4z/v4_flash_cost_is_unbelievable_pi_x_opencode_go/"

print(f"Fetching: {url}")
page = StealthyFetcher.fetch(url, headless=True)

print("\n" + "=" * 80)
print("SEARCHING FOR POST BODY CONTENT")
print("=" * 80)

# Try to find elements containing the post body text
search_texts = ["Bought opencode", "174M Tokens", "$0.001"]

for search_text in search_texts:
    print(f"\nSearching for: '{search_text}'")
    print("-" * 80)
    
    # Search in all elements
    all_elements = page.css('*')
    found = False
    
    for elem in all_elements[:100]:  # Check first 100 elements
        try:
            text = elem.get_all_text().strip()
            if search_text in text and len(text) > 20:
                tag = elem.tag
                classes = elem.attrib.get('class', '')
                testid = elem.attrib.get('data-testid', '')
                slot = elem.attrib.get('slot', '')
                
                print(f"  Found in <{tag}>")
                if classes:
                    print(f"    class: {classes[:100]}")
                if testid:
                    print(f"    data-testid: {testid}")
                if slot:
                    print(f"    slot: {slot}")
                print(f"    Text preview: {text[:200]}...")
                print()
                found = True
                break
        except:
            pass
    
    if not found:
        print("  Not found in first 100 elements")

# Try specific Reddit selectors
print("\n" + "=" * 80)
print("TRYING SPECIFIC SELECTORS")
print("=" * 80)

selectors_to_try = [
    'shreddit-post',
    '[slot="text-body"]',
    '[data-testid="post-content"]',
    '.md',
    '.usertext-content',
    'div[data-click-id="text"]',
    'div[data-testid="richtext"]',
]

for selector in selectors_to_try:
    try:
        elements = page.css(selector)
        if elements:
            print(f"\n✓ {selector}: Found {len(elements)} element(s)")
            for i, elem in enumerate(elements[:2]):  # Show first 2
                text = elem.get_all_text().strip()
                print(f"  [{i}] Text length: {len(text)}")
                print(f"      Preview: {text[:150]}...")
    except Exception as e:
        print(f"✗ {selector}: Error - {e}")

print("\n" + "=" * 80)
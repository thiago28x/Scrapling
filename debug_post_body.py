#!/usr/bin/env python3
"""
Debug script to find the post body content location.
"""

from scrapling.fetchers import StealthyFetcher

url = "https://www.reddit.com/r/opencodeCLI/comments/1ug2z4z/v4_flash_cost_is_unbelievable_pi_x_opencode_go/"

print(f"Fetching: {url}")
page = StealthyFetcher.fetch(url, headless=True)

print("\n" + "=" * 80)
print("SEARCHING ALL ELEMENTS FOR POST BODY")
print("=" * 80)

# Get all elements and search for the post body text
search_text = "Bought opencode"
all_elements = page.css('*')

print(f"\nSearching through all elements for: '{search_text}'\n")

found_elements = []
for i, elem in enumerate(all_elements):
    try:
        text = elem.get_all_text().strip()
        if search_text in text and len(text) > 30:
            tag = elem.tag
            classes = elem.attrib.get('class', '')
            testid = elem.attrib.get('data-testid', '')
            slot = elem.attrib.get('slot', '')
            id_attr = elem.attrib.get('id', '')
            
            found_elements.append({
                'index': i,
                'tag': tag,
                'classes': classes[:150] if classes else '',
                'testid': testid,
                'slot': slot,
                'id': id_attr,
                'text_length': len(text),
                'text_preview': text[:300]
            })
    except:
        pass

print(f"Found {len(found_elements)} elements containing '{search_text}':\n")
for elem_info in found_elements[:10]:  # Show first 10
    print(f"Element #{elem_info['index']}:")
    print(f"  Tag: <{elem_info['tag']}>")
    if elem_info['id']:
        print(f"  ID: {elem_info['id']}")
    if elem_info['classes']:
        print(f"  Class: {elem_info['classes']}")
    if elem_info['testid']:
        print(f"  data-testid: {elem_info['testid']}")
    if elem_info['slot']:
        print(f"  Slot: {elem_info['slot']}")
    print(f"  Text length: {elem_info['text_length']}")
    print(f"  Preview: {elem_info['text_preview']}")
    print()

# Also try to find the shreddit-post component and inspect its children
print("\n" + "=" * 80)
print("INSPECTING shreddit-post COMPONENT")
print("=" * 80)

shreddit_posts = page.css('shreddit-post')
if shreddit_posts:
    post = shreddit_posts[0]
    print(f"\nFound shreddit-post component")
    print(f"Attributes: {dict(post.attrib)}")
    
    # Get all children
    children = post.css('*')
    print(f"\nTotal children: {len(children)}")
    
    print("\nSearching children for post body...")
    for child in children:
        try:
            text = child.get_all_text().strip()
            if 'Bought opencode' in text and len(text) > 50:
                print(f"\n✓ Found in child <{child.tag}>")
                print(f"  Class: {child.attrib.get('class', '')[:100]}")
                print(f"  Slot: {child.attrib.get('slot', '')}")
                print(f"  data-testid: {child.attrib.get('data-testid', '')}")
                print(f"  Text: {text}")
                break
        except:
            pass

print("\n" + "=" * 80)
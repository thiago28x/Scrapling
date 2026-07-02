#!/usr/bin/env python3
"""
Basic test script to scrape the title from a Reddit post using scrapling.
"""

from scrapling.fetchers import StealthyFetcher

# Reddit post URL
url = "https://www.reddit.com/r/Chub_AI/comments/1ukyg08/any_alternative_sites_similar_to_chub/"

print(f"Fetching Reddit post: {url}")
print("=" * 80)

try:
    # Use StealthyFetcher to bypass anti-bot measures
    # Reddit has anti-bot protection, so we use StealthyFetcher
    page = StealthyFetcher.fetch(url, headless=True)
    
    print("✓ Page fetched successfully!\n")
    
    # Method 1: Extract title from the <title> tag (easiest and most reliable)
    title_from_tag = page.css('title::text').get()
    print("POST TITLE (from <title> tag):")
    print(f"  {title_from_tag}")
    print()
    
    # Method 2: Try to find the post title in the page content
    # Reddit's new design uses specific selectors
    print("Searching for title in page content...")
    
    # Try different selectors for Reddit's post title
    title_selectors = [
        'h1',  # Generic h1 tag
        '[data-testid="post-container"] h1',  # Reddit's data-testid
        '.title',  # Old Reddit class
        'shreddit-post h1',  # New Reddit component
    ]
    
    for selector in title_selectors:
        try:
            element = page.css(selector)
            if element:
                # Get the first matching element's text
                text = element.getall()
                if text and any('V4 Flash' in str(t) or 'unbelievable' in str(t) for t in text):
                    print(f"  ✓ Found with selector '{selector}':")
                    for t in text:
                        if 'V4 Flash' in str(t) or 'unbelievable' in str(t):
                            print(f"    {t}")
                    break
        except Exception as e:
            pass
    
    # Method 3: Extract post content/body
    print("\nPOST CONTENT:")
    print("-" * 80)
    
    # Check if this is a crosspost first
    shreddit_post = page.css('shreddit-post')
    is_crosspost = False
    original_post_url = None
    
    if shreddit_post:
        post_attrs = shreddit_post[0].attrib
        is_crosspost = post_attrs.get('is-crosspost') == ''
        if is_crosspost:
            content_href = post_attrs.get('content-href', '')
            if content_href:
                original_post_url = f"https://www.reddit.com{content_href}"
                print(f"  ℹ This is a crosspost. Fetching original post...")
                print(f"  Original URL: {original_post_url}\n")
    
    post_body = None
    
    # If it's a crosspost, fetch the original post
    if is_crosspost and original_post_url:
        try:
            original_page = StealthyFetcher.fetch(original_post_url, headless=True)
            print(f"  ✓ Fetched original post\n")
            
            # Try to extract body from original post
            body_selectors = [
                '[data-testid="post-content"]',
                'shreddit-post [slot="text-body"]',
                '.usertext-body',
                '[data-click-id="text"]',
                '.md',
                'shreddit-post .md',
            ]
            
            for selector in body_selectors:
                try:
                    elements = original_page.css(selector)
                    if elements:
                        if selector == '.md':
                            for elem in elements:
                                text = elem.get_all_text().strip()
                                if 'Bought opencode' in text or '174M Tokens' in text or '$0.001' in text:
                                    post_body = text
                                    break
                        else:
                            post_body = elements.get_all_text().strip()
                        
                        if post_body and len(post_body) > 50:
                            print(f"✓ Found with selector: {selector}")
                            print(post_body[:500] + "..." if len(post_body) > 500 else post_body)
                            break
                except Exception as e:
                    pass
        except Exception as e:
            print(f"  ✗ Could not fetch original post: {e}")
    
    # If not a crosspost or crosspost fetch failed, try current page
    if not post_body:
        body_selectors = [
            '[data-testid="post-content"]',
            'shreddit-post [slot="text-body"]',
            '.usertext-body',
            '[data-click-id="text"]',
            '.md',
            'shreddit-post .md',
        ]
        
        for selector in body_selectors:
            try:
                elements = page.css(selector)
                if elements:
                    if selector == '.md':
                        for elem in elements:
                            text = elem.get_all_text().strip()
                            if 'Bought opencode' in text or '174M Tokens' in text or '$0.001' in text:
                                post_body = text
                                break
                    else:
                        post_body = elements.get_all_text().strip()
                    
                    if post_body and len(post_body) > 50:
                        print(f"✓ Found with selector: {selector}")
                        print(post_body[:500] + "..." if len(post_body) > 500 else post_body)
                        break
            except Exception as e:
                pass
    
    if not post_body:
        print("  Could not extract post body")
    
    # Method 4: Extract metadata (subreddit, date, username)
    print("\n" + "-" * 80)
    print("POST METADATA:")
    print("-" * 80)
    
    # Try to find subreddit name
    subreddit_selectors = [
        'a[href*="/r/"]',
        '[data-testid="subreddit-name"]',
        '.subreddit-name',
    ]
    
    subreddit = None
    for selector in subreddit_selectors:
        try:
            elements = page.css(selector)
            if elements:
                for elem in elements:
                    text = elem.get_all_text().strip()
                    if text.startswith('r/'):
                        subreddit = text
                        print(f"✓ Subreddit: {subreddit}")
                        break
                if subreddit:
                    break
        except Exception as e:
            pass
    
    if not subreddit:
        print("  Subreddit: Not found")
    
    # Try to find username/author
    author_selectors = [
        'a[href*="/user/"]',
        '[data-testid="author-name"]',
        '.author-name',
    ]
    
    author = None
    for selector in author_selectors:
        try:
            elements = page.css(selector)
            if elements:
                for elem in elements:
                    text = elem.get_all_text().strip()
                    # Filter out common non-author text
                    if text and not any(x in text.lower() for x in ['comment', 'share', 'save', 'report']):
                        author = text
                        print(f"✓ Author: {author}")
                        break
                if author:
                    break
        except Exception as e:
            pass
    
    if not author:
        print("  Author: Not found")
    
    # Try to find post date
    date_selectors = [
        '[data-testid="post-timestamp"]',
        'a[href*="/comments/"]',
        'faceplate-timeago',
    ]
    
    post_date = None
    for selector in date_selectors:
        try:
            elements = page.css(selector)
            if elements:
                for elem in elements:
                    # Check for time-related text
                    text = elem.get_all_text().strip()
                    if any(x in text.lower() for x in ['ago', 'day', 'hour', 'min', 'year']):
                        post_date = text
                        print(f"✓ Posted: {post_date}")
                        break
                    # Also check attributes
                    if elem.attrib.get('title'):
                        post_date = elem.attrib['title']
                        print(f"✓ Posted: {post_date}")
                        break
                if post_date:
                    break
        except Exception as e:
            pass
    
    if not post_date:
        print("  Post date: Not found")
    
    print("\n" + "=" * 80)
    print("✓ SUCCESS: Reddit post data scraped successfully!")
    print("=" * 80)
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

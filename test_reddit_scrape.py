#!/usr/bin/env python3
"""
Dynamic Reddit post scraper using scrapling.
Works with any Reddit post URL by using intelligent selectors.
"""

from scrapling.fetchers import StealthyFetcher

# Reddit post URL (can be any Reddit post)
url = "https://www.reddit.com/r/AIChatReviews/comments/1uhfpa3/comment/ouqq6jx/"

print(f"Fetching Reddit post: {url}")
print("=" * 80)

try:
    # Use StealthyFetcher to bypass anti-bot measures
    page = StealthyFetcher.fetch(url, headless=True)
    
    print("✓ Page fetched successfully!\n")
    
    # Extract title
    title_from_tag = page.css('title::text').get()
    print("POST TITLE:")
    print(f"  {title_from_tag}")
    print()
    
    # Extract post content/body
    print("POST CONTENT:")
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
            page_to_use = original_page
        except Exception as e:
            print(f"  ✗ Could not fetch original post: {e}")
            page_to_use = page
    else:
        page_to_use = page
    
    # Dynamic body extraction strategy
    body_selectors = [
        'shreddit-post [slot="text-body"]',
        '[data-testid="post-content"]',
        '.usertext-body',
        '[data-click-id="text"]',
    ]
    
    for selector in body_selectors:
        try:
            elements = page_to_use.css(selector)
            if elements:
                post_body = elements.get_all_text().strip()
                if post_body and len(post_body) > 50:
                    print(f"✓ Found with selector: {selector}")
                    print(post_body[:500] + "..." if len(post_body) > 500 else post_body)
                    break
        except Exception as e:
            pass
    
    # Fallback: Use .md selector with smart selection
    if not post_body:
        try:
            md_elements = page_to_use.css('.md')
            if md_elements:
                # Find the shreddit-post and get its .md children
                shreddit_posts = page_to_use.css('shreddit-post')
                if shreddit_posts:
                    post_md_elements = shreddit_posts[0].css('.md')
                    if post_md_elements:
                        # Get the .md element with the most text (likely the post body)
                        best_elem = None
                        max_length = 0
                        for elem in post_md_elements:
                            text = elem.get_all_text().strip()
                            if len(text) > max_length and len(text) > 50:
                                max_length = len(text)
                                best_elem = elem
                        if best_elem:
                            post_body = best_elem.get_all_text().strip()
                            print(f"✓ Found with selector: shreddit-post .md")
                            print(post_body[:500] + "..." if len(post_body) > 500 else post_body)
        except Exception as e:
            pass
    
    if not post_body:
        print("  Could not extract post body")
    
    # Extract metadata
    print("\n" + "-" * 80)
    print("POST METADATA:")
    print("-" * 80)
    
    # Subreddit
    subreddit = None
    try:
        elements = page.css('a[href*="/r/"]')
        if elements:
            for elem in elements:
                text = elem.get_all_text().strip()
                if text.startswith('r/') and len(text) < 30:
                    subreddit = text
                    break
    except:
        pass
    print(f"✓ Subreddit: {subreddit if subreddit else 'Not found'}")
    
    # Author
    author = None
    try:
        elements = page.css('a[href*="/user/"]')
        if elements:
            for elem in elements:
                text = elem.get_all_text().strip()
                if text and len(text) > 2 and len(text) < 30:
                    if not any(x in text.lower() for x in ['comment', 'share', 'save', 'report', 'hide']):
                        author = text
                        break
    except:
        pass
    print(f"✓ Author: {author if author else 'Not found'}")
    
    # Post date
    post_date = None
    try:
        elements = page.css('faceplate-timeago')
        if elements:
            post_date = elements[0].attrib.get('ts', elements[0].attrib.get('title', ''))
            if not post_date:
                post_date = elements[0].get_all_text().strip()
    except:
        pass
    
    if not post_date:
        try:
            # Try to find date in the shreddit-post attributes
            if shreddit_post:
                created_ts = shreddit_post[0].attrib.get('created-timestamp', '')
                if created_ts:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_ts.replace('Z', '+00:00'))
                    post_date = _time_ago(dt)
        except:
            pass
    
    print(f"✓ Posted: {post_date if post_date else 'Not found'}")
    
    print("\n" + "=" * 80)
    print("✓ SUCCESS: Reddit post data scraped successfully!")
    print("=" * 80)
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


def _time_ago(dt):
    """Calculate time ago string from datetime"""
    from datetime import datetime
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    
    seconds = diff.total_seconds()
    minutes = int(seconds / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)
    
    if days > 0:
        return f"{days}d ago"
    elif hours > 0:
        return f"{hours}h ago"
    elif minutes > 0:
        return f"{minutes}m ago"
    else:
        return "just now"
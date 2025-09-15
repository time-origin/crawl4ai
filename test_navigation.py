import asyncio
from playwright.async_api import async_playwright

async def test_navigation():
    print("Starting navigation test...")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        print("Attempting to navigate to X.com login page...")
        print("Using commit wait strategy with 5 second timeout...")
        
        # Try with the most basic navigation first
        await page.goto("https://x.com/login", wait_until="commit", timeout=5000)
        print("Navigation successful!")
        
        # Check page details
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        title = await page.title()
        print(f"Page title: {title}")
        
        content = await page.content()
        print(f"Content length: {len(content)} characters")
        
    except Exception as e:
        print(f"Navigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_navigation())
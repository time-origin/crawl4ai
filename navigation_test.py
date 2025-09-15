import asyncio
from playwright.async_api import async_playwright

async def navigation_test():
    print("Starting navigation test...")
    try:
        playwright = await async_playwright().start()
        print("Playwright started")
        
        # Try launching with specific parameters
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ]
        )
        print("Browser launched")
        
        context = await browser.new_context()
        print("Context created")
        
        page = await context.new_page()
        print("Page created")
        
        print("Attempting to navigate to Google...")
        await page.goto("https://www.google.com", wait_until="commit", timeout=10000)
        print("Navigation to Google successful!")
        
        title = await page.title()
        print(f"Page title: {title}")
        
        print("Attempting to navigate to X.com...")
        await page.goto("https://x.com/login", wait_until="commit", timeout=10000)
        print("Navigation to X.com successful!")
        
        title = await page.title()
        print(f"X.com Page title: {title}")
        
        await browser.close()
        await playwright.stop()
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(navigation_test())
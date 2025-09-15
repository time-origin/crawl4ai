import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    print("Starting simple test...")
    try:
        playwright = await async_playwright().start()
        print("Playwright started")
        
        browser = await playwright.chromium.launch(headless=False)
        print("Browser launched")
        
        context = await browser.new_context()
        print("Context created")
        
        page = await context.new_page()
        print("Page created")
        
        print("Test completed successfully!")
        
        await browser.close()
        await playwright.stop()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
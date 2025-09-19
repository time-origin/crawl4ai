# crawl4ai/crawlers/x_com/production_crawler.py

import asyncio
import importlib
from pathlib import Path
from playwright.async_api import Page, async_playwright, expect
import os
from dotenv import load_dotenv

# Import the new output handler
from .output_handler import save_output

# For now, we will use placeholders until full integration.
class_logger = type("Logger", (), {"info": print, "warning": print, "error": print})
logger = class_logger()


# Define a path for storing the authentication state, relative to this file
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


class XProductionCrawler:
    """
    A production-ready crawler for X.com.
    """

    def __init__(self, config, browser_manager):
        self.config = config
        self.browser_manager = browser_manager
        self.username = self.config.get("X_USERNAME")
        self.password = self.config.get("X_PASSWORD")
        logger.info("XProductionCrawler initialized.")

    async def login(self):
        if not self.username or not self.password:
            logger.error("Cannot login: X_USERNAME or X_PASSWORD is not configured.")
            return

        logger.info("Attempting to log in to X.com...")
        page = await self.browser_manager.new_page(headless=False)
        if not page:
            logger.error("Failed to get a new page from BrowserManager for login.")
            return

        try:
            await page.goto("https://x.com/login")
            await page.locator('input[name="text"]').fill(self.username)
            await page.get_by_role("button", name="Next").click()
            try:
                username_input_again = page.locator('input[data-testid="ocfEnterTextTextInput"]')
                await username_input_again.wait_for(timeout=5000)
                if await username_input_again.is_visible():
                    await username_input_again.fill(self.username)
                    await page.get_by_role("button", name="Next").click()
            except: pass
            await page.locator('input[name="password"]').fill(self.password)
            await page.get_by_role("button", name="Log in").click()
            await expect(page.locator('[data-testid="primaryColumn"]')).to_be_visible(timeout=30000)
            await page.context.storage_state(path=AUTH_STATE_PATH)
            logger.info(f"Login successful! Auth state saved to {AUTH_STATE_PATH}")
        except Exception as e:
            logger.error(f"An error occurred during login: {e}")
        finally:
            await page.context.close()

    async def scrape(self, scene: str, **kwargs) -> list:
        if not AUTH_STATE_PATH.exists():
            logger.error(f"Authentication file not found at {AUTH_STATE_PATH}.")
            return []

        try:
            scene_module_name = f"crawl4ai.crawlers.x_com.scenes.{scene.lower()}_scene"
            scene_module = importlib.import_module(scene_module_name)
            scene_class_name = "".join(word.capitalize() for word in scene.split('_')) + "Scene"
            SceneClass = getattr(scene_module, scene_class_name)
            scene_instance = SceneClass()
        except (ImportError, AttributeError) as e:
            logger.error(f"Scene '{scene}' not found or module is malformed: {e}")
            return []

        page = await self.browser_manager.new_page(storage_state=str(AUTH_STATE_PATH))
        if not page:
            logger.error("Failed to get a new page from BrowserManager for scraping.")
            return []

        try:
            return await scene_instance.scrape(page, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred during scraping scene '{scene}': {e}")
            return []
        finally:
            await page.context.close()


# --- Test Harness for Standalone Execution ---

class MockConfig:
    def __init__(self):
        load_dotenv()
    def get(self, key):
        return os.getenv(key)

class MockBrowserManager:
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.playwright.stop()

    async def new_page(self, headless=True, storage_state=None):
        browser = await self.playwright.chromium.launch(headless=headless)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        original_close = page.close
        page.close = lambda: asyncio.gather(original_close(), context.close())
        return page

async def main():
    """
    Main function demonstrating the "Scan -> Detail -> Output" workflow.
    """
    print("--- Running XProductionCrawler in Standalone Test Mode ---")
    
    mock_config = MockConfig()
    async with MockBrowserManager() as mock_browser_manager:
        crawler = XProductionCrawler(config=mock_config, browser_manager=mock_browser_manager)

        # await crawler.login()

        if AUTH_STATE_PATH.exists():
            # Define the search keyword
            search_keyword = "OpenAI"

            # --- STAGE 1: SCAN ---
            print(f"\n--- STAGE 1: Scanning for URLs with keyword: '{search_keyword}' ---")
            tweet_urls = await crawler.scrape("search", query=search_keyword, scroll_count=1)

            # --- STAGE 2: DETAIL ---
            print(f"\n--- STAGE 2: Fetching details for {len(tweet_urls)} URLs ---")
            all_tweet_details = []
            for url in tweet_urls:
                detailed_data = await crawler.scrape(
                    "tweet_detail",
                    url=url,
                    include_replies=True,
                    max_replies=3
                )
                if detailed_data:
                    all_tweet_details.append(detailed_data)
            
            # --- STAGE 3: OUTPUT ---
            await save_output(data=all_tweet_details, keyword=search_keyword)

        else:
            print("\nAuth file not found. Please run the login task first.")

if __name__ == "__main__":
    asyncio.run(main())

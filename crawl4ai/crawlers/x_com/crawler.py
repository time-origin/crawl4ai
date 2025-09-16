# crawl4ai/crawlers/x_com/crawler.py

import asyncio
import importlib
from pathlib import Path
from playwright.async_api import async_playwright, Page, expect

from dotenv import load_dotenv
import os

# Define a path for storing the authentication state
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


class XCrawler:
    """
    A crawler designed to scrape data from X.com (formerly Twitter).

    This crawler acts as a coordinator, dispatching tasks to specific "scene"
    modules based on the desired page to scrape (e.g., home, explore, search).
    """

    def __init__(self, config=None, browser_manager=None):
        """
        Initializes the XCrawler.
        """
        self.config = config
        self.browser_manager = browser_manager

        load_dotenv()
        self.username = os.getenv("X_USERNAME")
        self.password = os.getenv("X_PASSWORD")

        if not self.username or not self.password:
            print("Warning: X_USERNAME or X_PASSWORD not found in .env file.")

    async def login(self):
        """
        Performs login to X.com and saves the session state.
        This method is typically run only once manually or when the session expires.
        """
        if not self.username or not self.password:
            print("Cannot login: Username or password is not set.")
            return

        print("Attempting to log in to X.com...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            try:
                await page.goto("https://x.com/login")
                await page.locator('''input[name="text"]''').fill(self.username)
                await page.get_by_role("button", name="Next").click()
                try:
                    username_input_again = page.locator('''input[data-testid="ocfEnterTextTextInput"]''')
                    await username_input_again.wait_for(timeout=5000)
                    if await username_input_again.is_visible():
                        await username_input_again.fill(self.username)
                        await page.get_by_role("button", name="Next").click()
                except: pass
                await page.locator('''input[name="password"]''').fill(self.password)
                await page.get_by_role("button", name="Log in").click()
                await expect(page.locator('''[data-testid="primaryColumn"]''')).to_be_visible(timeout=30000)
                await page.context.storage_state(path=AUTH_STATE_PATH)
                print(f"Login successful! Auth state saved to {AUTH_STATE_PATH}")
            except Exception as e:
                print(f"An error occurred during login: {e}")
            finally:
                await browser.close()

    async def scrape(self, scene: str, **kwargs):
        """
        Performs scraping for a given scene (e.g., 'home', 'explore', 'search').

        This method dynamically loads the appropriate scene module, launches a
        browser with the saved authentication state, and delegates the scraping
        task to the scene's scrape() method.

        Args:
            scene (str): The name of the scene to scrape.
            **kwargs: Additional parameters for the scene, like 'query' for search.

        Returns:
            list: The data scraped by the scene, or an empty list on error.
        """
        if not AUTH_STATE_PATH.exists():
            print(f"Error: Authentication file not found at {AUTH_STATE_PATH}.")
            print("Please run the login() method first to create the auth file.")
            return []

        try:
            # Dynamically import the scene module
            scene_module_name = f".scenes.{scene.lower()}_scene"
            scene_module = importlib.import_module(scene_module_name, package=__package__)
            
            # Find the scene class within the module (e.g., HomeScene)
            scene_class_name = f"{scene.capitalize()}Scene"
            SceneClass = getattr(scene_module, scene_class_name)
            scene_instance = SceneClass()
        except (ImportError, AttributeError):
            print(f"Error: Scene '{scene}' not found or module is malformed.")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) # Use headless for scraping
            # Create a new context with the saved authentication state
            context = await browser.new_context(storage_state=AUTH_STATE_PATH)
            page = await context.new_page()
            try:
                # Delegate the actual scraping to the scene object
                results = await scene_instance.scrape(page, **kwargs)
                return results
            except Exception as e:
                print(f"An error occurred during scraping scene '{scene}': {e}")
                return []
            finally:
                await browser.close()


async def main():
    """
    Standalone execution function to demonstrate scraping different scenes.
    To run: python -m crawl4ai.crawlers.x_com.crawler
    """
    crawler = XCrawler()

    # --- IMPORTANT --- 
    # Uncomment the line below and run the script once to log in and create the auth file.
    # await crawler.login()

    # Once logged in, you can run the scraping tasks.
    if AUTH_STATE_PATH.exists():
        print("\n--- Running Scrape Tasks ---")
        
        # 1. Scrape the home timeline
        home_tweets = await crawler.scrape("home")
        print(f"Scraped {len(home_tweets)} tweets from the home timeline.")

        # 2. Scrape the explore page
        # explore_trends = await crawler.scrape("explore")
        # print(f"Scraped {len(explore_trends)} items from the explore page.")

        # 3. Scrape a search query
        # search_results = await crawler.scrape("search", query="Python programming")
        # print(f"Scraped {len(search_results)} tweets for the search query.")

        print("--------------------------")
    else:
        print("\nAuth file not found. Please run the login process first by uncommenting 'await crawler.login()' in the main function.")


if __name__ == "__main__":
    asyncio.run(main())

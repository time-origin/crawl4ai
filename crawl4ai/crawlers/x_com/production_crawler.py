# crawl4ai/crawlers/x_com/production_crawler.py

import importlib
from pathlib import Path
from playwright.async_api import Page

# In production, we will rely on the project's shared modules.
# These imports assume the crawler is integrated into the main application.
# from crawl4ai.browser_manager import BrowserManager
# from crawl4ai.config import Config
# from crawl4ai.async_logger import logger

# For now, we will use placeholders until full integration.
class_logger = type("Logger", (), {"info": print, "warning": print, "error": print})
logger = class_logger()


# Define a path for storing the authentication state, relative to this file
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


class XProductionCrawler:
    """
    A production-ready crawler for X.com.

    This crawler coordinates scraping tasks by dispatching them to specific "scene"
    modules. It is designed to be integrated into the main crawl4ai application
    and relies on the application's shared BrowserManager and Config objects.
    """

    def __init__(self, config, browser_manager):
        """
        Initializes the XProductionCrawler.

        Args:
            config (Config): The application's configuration object.
            browser_manager (BrowserManager): The manager for browser instances.
        """
        self.config = config
        self.browser_manager = browser_manager
        self.username = self.config.get("X_USERNAME")
        self.password = self.config.get("X_PASSWORD")
        logger.info("XProductionCrawler initialized.")

    async def login(self):
        """
        Performs login to X.com and saves the session state.

        This method should be run manually via a separate script or CLI command
        as it may require manual intervention (e.g., for CAPTCHAs).
        """
        if not self.username or not self.password:
            logger.error("Cannot login: X_USERNAME or X_PASSWORD is not configured.")
            return

        logger.info("Attempting to log in to X.com...")
        # For login, we specifically need a headed instance.
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
                    logger.info("Handling unusual login prompt...")
                    await username_input_again.fill(self.username)
                    await page.get_by_role("button", name="Next").click()
            except: pass

            await page.locator('input[name="password"]').fill(self.password)
            await page.get_by_role("button", name="Log in").click()
            
            await page.locator('[data-testid="primaryColumn"]').wait_for(timeout=30000)
            
            await page.context.storage_state(path=AUTH_STATE_PATH)
            logger.info(f"Login successful! Auth state saved to {AUTH_STATE_PATH}")

        except Exception as e:
            logger.error(f"An error occurred during login: {e}")
        finally:
            await page.close()

    async def scrape(self, scene: str, **kwargs) -> list:
        """
        Performs scraping for a given scene (e.g., 'home', 'explore', 'search').
        """
        if not AUTH_STATE_PATH.exists():
            logger.error(f"Authentication file not found at {AUTH_STATE_PATH}.")
            return []

        try:
            scene_module_name = f".scenes.{scene.lower()}_scene"
            scene_module = importlib.import_module(scene_module_name, package=__package__)
            SceneClass = getattr(scene_module, f"{scene.capitalize()}Scene")
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
            await page.close()

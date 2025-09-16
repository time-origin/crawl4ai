# crawl4ai/crawlers/x_com/scenes/explore_scene.py

from playwright.async_api import Page, expect
from .base_scene import BaseScene


class ExploreScene(BaseScene):
    """
    A scene for scraping the content from the "Explore" page.
    """

    async def scrape(self, page: Page, **kwargs) -> list:
        """
        Scrapes the explore page for trending topics or tweets.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: Not used in this scene.

        Returns:
            list: A list of dictionaries representing scraped items.
        """
        print("--- Scraping Explore Scene ---")
        
        # Navigate to the explore page
        await page.goto("https://x.com/explore")
        print("Navigated to explore page.")

        # Wait for the primary column to be visible
        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column).to_be_visible(timeout=15000)
        print("Primary column is visible.")

        # The content on the explore page can vary. 
        # We will wait for a generic content container to be ready.
        # For this example, we'll look for trending item containers.
        await expect(primary_column.locator('[data-testid="trend"]')).to_have_count(1, timeout=15000)
        print("Found at least one trending item.")

        # Placeholder for data extraction logic
        trending_elements = await primary_column.locator('[data-testid="trend"]').all()
        print(f"Found {len(trending_elements)} trending items on the page.")

        scraped_data = []
        for trend_element in trending_elements:
            try:
                # Extracting text from a trend is different from a tweet
                trend_text = await trend_element.locator('div > div > div > span').first.inner_text()
                scraped_data.append({"trend": trend_text})
            except Exception as e:
                print(f"Could not extract text from a trend: {e}")

        print(f"--- Finished Scraping Explore Scene: {len(scraped_data)} items scraped ---")
        return scraped_data

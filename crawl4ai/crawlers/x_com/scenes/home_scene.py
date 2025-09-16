# crawl4ai/crawlers/x_com/scenes/home_scene.py

from playwright.async_api import Page, expect
from .base_scene import BaseScene


class HomeScene(BaseScene):
    """
    A scene for scraping the main home timeline of the logged-in user.
    """

    async def scrape(self, page: Page, **kwargs) -> list:
        """
        Scrapes the user's home timeline for recent tweets.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: Not used in this scene, but included for compatibility.

        Returns:
            list: A list of dictionaries representing the scraped tweets.
        """
        print("--- Scraping Home Scene ---")
        
        # Navigate to the home page
        await page.goto("https://x.com/home")
        print("Navigated to home timeline.")

        # Wait for the primary column containing tweets to be visible
        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column).to_be_visible(timeout=15000)
        print("Primary column is visible.")

        # Wait for at least one tweet to appear in the timeline
        # This is a more reliable way to ensure content has loaded
        await expect(primary_column.locator('article[data-testid="tweet"]')).to_have_count(1, timeout=15000)
        print("Found at least one tweet.")

        # Extract data from the tweets
        # This is a placeholder for the actual data extraction logic
        tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()
        print(f"Found {len(tweet_elements)} tweets on the page.")

        scraped_data = []
        for tweet_element in tweet_elements:
            try:
                tweet_text = await tweet_element.locator('[data-testid="tweetText"]').inner_text()
                scraped_data.append({"text": tweet_text})
            except Exception as e:
                print(f"Could not extract text from a tweet: {e}")

        print(f"--- Finished Scraping Home Scene: {len(scraped_data)} items scraped ---")
        return scraped_data

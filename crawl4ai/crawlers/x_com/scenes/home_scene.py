# crawl4ai/crawlers/x_com/scenes/home_scene.py

import asyncio
from playwright.async_api import Page, expect
from .base_scene import BaseScene


class HomeScene(BaseScene):
    """
    A scene for scanning the home timeline and scraping the URLs of the tweets.
    Its sole purpose is to quickly gather a list of tweet URLs for further processing.
    """

    async def scrape(self, page: Page, **kwargs) -> list:
        """
        Scrapes the home timeline for tweet URLs.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: See BaseScene for standard arguments.

        Returns:
            list: A list of unique tweet URL strings.
        """
        print("--- Scanning Home Scene for Tweet URLs ---")
        
        scroll_count = kwargs.get("scroll_count", 5)
        tweet_urls = set()

        await page.goto("https://x.com/home")
        print("Navigated to home timeline.")

        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column).to_be_visible(timeout=15000)
        await expect(primary_column.locator('article[data-testid="tweet"]').first).to_be_visible(timeout=15000)
        print("Initial tweets loaded.")

        for i in range(scroll_count):
            print(f"\n--- Scroll attempt {i + 1}/{scroll_count} ---")
            
            tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()

            for tweet_element in tweet_elements:
                try:
                    # The most reliable way to get a tweet's URL is from its timestamp link.
                    all_links = await tweet_element.locator('a[role="link"]').all()
                    for link in all_links:
                        if await link.locator("time").count() > 0:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href:
                                full_url = f"https://x.com{href}"
                                if full_url not in tweet_urls:
                                    tweet_urls.add(full_url)
                                    print(f"[URL Found]: {full_url}")
                                break # Move to the next tweet element

                except Exception as e:
                    print(f"Could not extract URL from a tweet element: {e}")

            print("Scrolling down...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

        print(f"\n--- Finished Scanning Home Scene: {len(tweet_urls)} unique URLs found ---")
        return list(tweet_urls)

# crawl4ai/crawlers/x_com/scenes/search_scene.py

import asyncio
from playwright.async_api import Page, expect
from .base_scene import BaseScene
import urllib.parse


class SearchScene(BaseScene):
    """
    A scene for performing a search and scraping the URLs of the resulting tweets.
    Its sole purpose is to quickly gather a list of tweet URLs for further processing.
    """

    async def scrape(self, page: Page, **kwargs) -> list:
        """
        Scrapes the search results page for tweet URLs.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: See BaseScene for standard arguments.

        Returns:
            list: A list of unique tweet URL strings.
        """
        print("--- Scanning Search Scene for Tweet URLs ---")
        query = kwargs.get("query")

        if not query:
            print("Error: Search scene requires a 'query' parameter.")
            return []

        scroll_count = kwargs.get("scroll_count", 5)
        filter_mode = kwargs.get("filter_mode", "top")

        encoded_query = urllib.parse.quote(query)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f={filter_mode}"
        
        await page.goto(search_url)
        print(f"Navigated to search page for query: '{query}' with filter: '{filter_mode}'")

        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column).to_be_visible(timeout=15000)
        await expect(primary_column.locator('article[data-testid="tweet"]').first).to_be_visible(timeout=15000)
        print("Initial search results loaded.")

        # --- URL Extraction Logic --- 
        tweet_urls = set()

        for i in range(scroll_count):
            print(f"\n--- Scroll attempt {i + 1}/{scroll_count} ---")
            
            tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()

            for tweet_element in tweet_elements:
                try:
                    # The most reliable way to get a tweet's URL is from its timestamp link.
                    # We find all links within the tweet, and filter for the one with a <time> element.
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

        print(f"\n--- Finished Scanning Search Scene: {len(tweet_urls)} unique URLs found ---")
        return list(tweet_urls)

# crawl4ai/crawlers/x_com/scenes/search_scene.py

from playwright.async_api import Page, expect
from .base_scene import BaseScene
import urllib.parse


class SearchScene(BaseScene):
    """
    A scene for performing a search and scraping the results.
    """

    async def scrape(self, page: Page, **kwargs) -> list:
        """
        Scrapes the search results page for a given query.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: Must contain a 'query' key with the search term.
                      e.g., `query="Playwright testing"`

        Returns:
            list: A list of dictionaries representing the scraped tweets.
        """
        print("--- Scraping Search Scene ---")
        query = kwargs.get("query")

        if not query:
            print("Error: Search scene requires a 'query' parameter.")
            return []

        # URL-encode the query to handle special characters safely
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
        
        await page.goto(search_url)
        print(f"Navigated to search page for query: '{query}'")

        # Wait for the primary column containing search results to be visible
        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column).to_be_visible(timeout=15000)
        print("Primary column for search results is visible.")

        # Wait for at least one tweet to appear in the search results
        await expect(primary_column.locator('article[data-testid="tweet"]')).to_have_count(1, timeout=15000)
        print("Found at least one tweet in search results.")

        # Placeholder for data extraction logic
        tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()
        print(f"Found {len(tweet_elements)} tweets on the search results page.")

        scraped_data = []
        for tweet_element in tweet_elements:
            try:
                tweet_text = await tweet_element.locator('[data-testid="tweetText"]').inner_text()
                scraped_data.append({"query": query, "text": tweet_text})
            except Exception as e:
                print(f"Could not extract text from a search result tweet: {e}")

        print(f"--- Finished Scraping Search Scene: {len(scraped_data)} items scraped ---")
        return scraped_data

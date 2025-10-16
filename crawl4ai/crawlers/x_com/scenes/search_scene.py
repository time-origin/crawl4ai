# crawl4ai/crawlers/x_com/scenes/search_scene.py

import asyncio
from playwright.async_api import Page, expect, TimeoutError
from .base_scene import BaseScene
import urllib.parse


class SearchScene(BaseScene):
    """
    An async generator scene that scans search results and yields tweet URLs in batches.
    """

    async def scrape(self, page: Page, **kwargs):
        """
        Scrapes the search results page and yields batches of tweet URLs.
        This is an async generator.
        """
        print("--- Scanning Search Scene for Tweet URLs ---")
        query = kwargs.get("query")
        if not query: return

        scroll_count = kwargs.get("scroll_count", 5)
        filter_mode = kwargs.get("filter_mode", "top")

        encoded_query = urllib.parse.quote(query)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f={filter_mode}"
        
        await page.goto(search_url, wait_until="domcontentloaded")
        print(f"Navigated to search page for query: '{query}' with filter: '{filter_mode}'")
        
        # 添加调试：等待页面加载
        await page.wait_for_timeout(3000)

        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column.locator('article[data-testid="tweet"]').first).to_be_visible(timeout=15000)
        print("Initial search results loaded.")

        scraped_urls_in_total = set()

        for i in range(scroll_count):
            print(f"\n--- Scan scroll attempt {i + 1}/{scroll_count} ---")
            
            tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()
            new_urls_in_this_batch = []

            for tweet_element in tweet_elements:
                try:
                    all_links = await tweet_element.locator('a[role="link"]').all()
                    for link in all_links:
                        if await link.locator("time").count() > 0:
                            href = await link.get_attribute("href")
                            if href and "/status/" in href:
                                full_url = f"https://x.com{href}"
                                if full_url not in scraped_urls_in_total:
                                    scraped_urls_in_total.add(full_url)
                                    new_urls_in_this_batch.append(full_url)
                                    print(f"[URL Found]: {full_url}")
                                break
                except Exception: pass

            # --- YIELD THE BATCH --- 
            # Instead of returning at the end, we yield each batch of new URLs as we find them.
            if new_urls_in_this_batch:
                print(f"Yielding a batch of {len(new_urls_in_this_batch)} new URLs.")
                yield new_urls_in_this_batch
            
            print("Scrolling down to find more URLs...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

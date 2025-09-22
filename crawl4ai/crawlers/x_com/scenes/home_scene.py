# crawl4ai/crawlers/x_com/scenes/home_scene.py

import asyncio
from playwright.async_api import Page, expect
from .base_scene import BaseScene


class HomeScene(BaseScene):
    """
    An async generator scene that scans the home timeline and yields tweet URLs in batches.
    """

    async def scrape(self, page: Page, **kwargs):
        """
        Scrapes the home timeline and yields batches of tweet URLs.
        This is an async generator.
        """
        print("--- Scanning Home Scene for Tweet URLs ---")
        
        scroll_count = kwargs.get("scroll_count", 5)
        scraped_urls_in_total = set()

        await page.goto("https://x.com/home", wait_until="domcontentloaded")
        print("Navigated to home timeline.")

        primary_column = page.locator('[data-testid="primaryColumn"]')
        await expect(primary_column.locator('article[data-testid="tweet"]').first).to_be_visible(timeout=15000)
        print("Initial tweets loaded.")

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

            if new_urls_in_this_batch:
                print(f"Yielding a batch of {len(new_urls_in_this_batch)} new URLs.")
                yield new_urls_in_this_batch

            print("Scrolling down to find more URLs...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

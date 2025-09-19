# crawl4ai/crawlers/x_com/scenes/tweet_detail_scene.py

from playwright.async_api import Page, expect
from .base_scene import BaseScene
import asyncio
import re

class TweetDetailScene(BaseScene):
    """
    A reusable scene designed to scrape all details from a single tweet's detail page.
    """

    async def scrape(self, page: Page, **kwargs) -> dict:
        """
        Scrapes a single tweet's detail page for its full content and all key metrics.
        """
        tweet_url = kwargs.get("url")
        if not tweet_url:
            print("Error: TweetDetailScene requires a 'url' parameter.")
            return {}

        print(f"--- Scraping Tweet Detail Scene for URL: {tweet_url} ---")
        
        await page.goto(tweet_url, wait_until="domcontentloaded", timeout=60000)
        
        primary_column = page.locator('[data-testid="primaryColumn"]')
        main_tweet_element = primary_column.locator('article[data-testid="tweet"]').first
        await expect(main_tweet_element).to_be_visible(timeout=15000)
        print("Main tweet element is visible.")

        core_data = await self._extract_tweet_data(main_tweet_element)
        metrics = await self._extract_all_metrics(main_tweet_element)

        replies = []
        if kwargs.get("include_replies", False):
            replies = await self._scrape_replies(page, primary_column, **kwargs)

        scraped_data = {
            "url": tweet_url,
            "author": core_data.get("author"),
            "full_text": core_data.get("text"),
            "reply_count": metrics.get("reply_count", "0"),
            "repost_count": metrics.get("repost_count", "0"),
            "like_count": metrics.get("like_count", "0"),
            "bookmark_count": metrics.get("bookmark_count", "0"),
            "view_count": metrics.get("view_count", "0"),
            "scraped_replies_count": len(replies),
            "replies": replies
        }

        print(f"--- Finished Scene. Author: {core_data.get('author')}, Replies: {metrics.get('reply_count')}, Reposts: {metrics.get('repost_count')}, Likes: {metrics.get('like_count')}, Views: {metrics.get('view_count')} ---")
        return scraped_data

    async def _extract_all_metrics(self, tweet_element):
        """The ultimate, robust metric extractor. Uses independent IFs and precise regex."""
        metrics = {}
        try:
            metric_candidates = await tweet_element.locator('[aria-label]').all()
            
            for candidate in metric_candidates:
                label = await candidate.get_attribute("aria-label")
                if not label: continue
                label_lower = label.lower()

                # --- THE FINAL FIX --- 
                # Use separate `if` statements for each metric to handle combined labels correctly.
                # Use a precise regex for each to extract the number associated with a keyword.

                if "reply_count" not in metrics:
                    match = re.search(r"([\d,.]+[KkMm]?)\s+(replies|reply)", label_lower)
                    if match: metrics["reply_count"] = match.group(1)

                if "repost_count" not in metrics:
                    match = re.search(r"([\d,.]+[KkMm]?)\s+(reposts|retweet)", label_lower)
                    if match: metrics["repost_count"] = match.group(1)

                if "like_count" not in metrics:
                    match = re.search(r"([\d,.]+[KkMm]?)\s+(likes|like)", label_lower)
                    if match: metrics["like_count"] = match.group(1)

                if "bookmark_count" not in metrics:
                    match = re.search(r"([\d,.]+[KkMm]?)\s+(bookmarks|bookmark)", label_lower)
                    if match: metrics["bookmark_count"] = match.group(1)

                if "view_count" not in metrics:
                    match = re.search(r"([\d,.]+[KkMm]?)\s+(views|view)", label_lower)
                    if match: metrics["view_count"] = match.group(1)

        except Exception as e:
            print(f"Error extracting metrics: {e}")
        return metrics

    async def _extract_tweet_data(self, tweet_element):
        author = ""
        text = ""
        try:
            author_element = tweet_element.locator('[data-testid="User-Name"]').first
            author = await author_element.locator("span").first.inner_text()
        except Exception: pass
        try:
            text_element = tweet_element.locator('[data-testid="tweetText"]')
            text = await text_element.inner_text()
        except Exception: pass
        return {"author": author, "text": text}

    async def _scrape_replies(self, page, primary_column, **kwargs):
        max_replies = kwargs.get("max_replies")
        reply_scroll_count = kwargs.get("reply_scroll_count", 5)
        
        replies = []
        scraped_reply_identifiers = set()

        for i in range(reply_scroll_count):
            all_tweet_elements = await primary_column.locator('article[data-testid="tweet"]').all()
            reply_elements = all_tweet_elements[1:]

            for reply_element in reply_elements:
                reply_data = await self._extract_tweet_data(reply_element)
                identifier = f"{reply_data['author']}-{reply_data['text']}"

                if reply_data["text"] and identifier not in scraped_reply_identifiers:
                    scraped_reply_identifiers.add(identifier)
                    replies.append(reply_data)
                    
                    if max_replies is not None and len(replies) >= max_replies:
                        break
            
            if max_replies is not None and len(replies) >= max_replies:
                break

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
        return replies

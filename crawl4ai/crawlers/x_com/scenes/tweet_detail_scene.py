# crawl4ai/crawlers/x_com/scenes/tweet_detail_scene.py

from playwright.async_api import Page, expect, TimeoutError
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

        # [修正] 确保数据一致性：reply_count 的值必须是实际抓取到的、有文本的回复列表的长度。
        final_reply_count = len(replies)

        scraped_data = {
            "id": tweet_url.split('/')[-1],
            "url": tweet_url,
            "author": core_data.get("author"),
            "full_text": core_data.get("text"),
            "reply_count": str(final_reply_count), # 使用过滤后的回复列表长度
            "repost_count": metrics.get("repost_count", "0"),
            "like_count": metrics.get("like_count", "0"),
            "bookmark_count": metrics.get("bookmark_count", "0"),
            "view_count": metrics.get("view_count", "0"),
            "scraped_replies_count": final_reply_count, # 此字段现在与 reply_count 意义相同
            "replies": replies
        }

        print(f"--- Finished Scene. Author: {core_data.get('author')}, Metadata Replies: {metrics.get('reply_count')}, Scraped Replies: {final_reply_count} ---")
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

        # [最终修复] 采用两步走策略：1. 定位回复容器 2. 等待容器内容加载
        try:
            # 步骤1: 精准定位到专门的回复时间线容器
            print("  [定位容器] 正在查找回复时间线容器...")
            reply_timeline = primary_column.locator('[aria-label*="Timeline:"]')
            await expect(reply_timeline).to_be_visible(timeout=10000)
            print("  [定位成功] 回复时间线容器已找到。")

            # 步骤2: 等待容器内的第一条回复加载出来，解决竞争条件
            print("  [等待内容] 正在等待第一条回复在容器内加载... (最长20秒)")
            first_reply_in_timeline = reply_timeline.locator('article[data-testid="tweet"]').first
            await first_reply_in_timeline.wait_for(timeout=20000) # [修正] 增加等待时间到20秒
            print("  [等待成功] 第一条回复已加载，开始抓取整个回复列表。")

        except TimeoutError:
            print("  [抓取失败] 未能找到回复容器或容器内无内容，将返回空列表。")
            return []

        for i in range(reply_scroll_count):
            # 既然我们已经确认回复容器和内容都存在，现在可以安全地在容器内进行抓取
            reply_elements = await reply_timeline.locator('article[data-testid="tweet"]').all()

            for reply_element in reply_elements:
                reply_data = await self._extract_tweet_data(reply_element)
                identifier = f"{reply_data['author']}-{reply_data['text']}"

                # [修正] 过滤掉没有文本的回复
                if reply_data["text"] and identifier not in scraped_reply_identifiers:
                    scraped_reply_identifiers.add(identifier)
                    replies.append(reply_data)
                    # print(f"    [回复抓取成功] 作者: {reply_data['author']}, 内容: {reply_data['text'][:30]}...")

                    if max_replies is not None and len(replies) >= max_replies:
                        break

            if max_replies is not None and len(replies) >= max_replies:
                break

            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

        return replies

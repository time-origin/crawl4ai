# crawl4ai/crawlers/x_com/production_crawler.py

import asyncio
import importlib
import sys
import os
from pathlib import Path
from playwright.async_api import Page, async_playwright, expect, TimeoutError
import argparse
import re
import inspect
from datetime import datetime

from playwright_stealth import stealth_async

# --- [FIX] Changed relative imports to absolute for PyInstaller compatibility ---
from crawl4ai.crawlers.x_com import config
from crawl4ai.crawlers.x_com.output_handler import save_batch_to_file
from crawl4ai.crawlers.x_com.kafka_manager import send_to_kafka, ensure_topic_exists
from aiokafka import AIOKafkaProducer

# --- Logic for Bundled Execution ---
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    browsers_path = os.path.join(sys._MEIPASS, 'ms-playwright')
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
    print(f"Running in bundled mode. Setting Playwright browsers path to: {browsers_path}")

class_logger = type("Logger", (), {"info": print, "warning": print, "error": print})
logger = class_logger()

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"

class XProductionCrawler:
    def __init__(self, config, browser_manager):
        self.config = config
        self.browser_manager = browser_manager
        self.username = self.config.X_USERNAME
        self.password = self.config.X_PASSWORD

    async def login(self):
        if not self.username or not self.password:
            print("Login credentials (X_USERNAME, X_PASSWORD) not found in environment variables.")
            return
        page = await self.browser_manager.new_page(headless=True)
        if not page: return
        try:
            await page.goto("https://x.com/login", wait_until="domcontentloaded")
            
            try:
                await page.locator('input[name="text"]').fill(self.username)
            except TimeoutError as e:
                print("\n---")
                print("🛑 DEBUGGING: Timeout occurred while finding the username input field.")
                page_html = await page.content()
                print("\n--- PAGE HTML CONTENT START ---")
                print(page_html)
                print("--- PAGE HTML CONTENT END ---\n")
                raise e

            next_button = (
                page.locator('[data-testid="ocfLoginNextLink"]')
                .or_(page.get_by_role("button", name="Next", exact=True))
                .or_(page.get_by_role("button", name="下一步", exact=True))
            )
            await next_button.click()

            try:
                await page.locator('input[name="password"]').wait_for(timeout=10000)
            except TimeoutError:
                verification_text_regex = re.compile("(unusual|verify|suspicious|验证|异常)", re.IGNORECASE)
                verification_locator = page.get_by_text(verification_text_regex)
                
                if await verification_locator.first.is_visible(timeout=1000):
                    print("\n---")
                    print("🛑 UNUSUAL ACTIVITY DETECTED BY X.COM 🛑")
                    print("Please manually verify your account in a browser.")
                    print("---\n")
                    return
                else:
                    print("\nLogin failed: The password field did not appear, and no known verification page was detected.")
                    raise
            
            await page.locator('input[name="password"]').fill(self.password)

            login_button = (
                page.locator('[data-testid="LoginForm_Login_Button"]')
                .or_(page.get_by_role("button", name="Log in", exact=True))
                .or_(page.get_by_role("button", name="登录", exact=True))
            )
            await login_button.click()

            await expect(page.locator('[data-testid="primaryColumn"]')).to_be_visible(timeout=30000)
            await page.context.storage_state(path=str(AUTH_STATE_PATH))
        finally:
            await page.context.close()

    async def scrape(self, scene: str, **kwargs):
        if not AUTH_STATE_PATH.exists():
            async def empty_generator(): yield
            return empty_generator() if scene in ["search", "home"] else {}
        
        page = await self.browser_manager.new_page(storage_state=str(AUTH_STATE_PATH))
        if not page: 
            async def empty_generator(): yield
            return empty_generator() if scene in ["search", "home"] else {}

        try:
            scene_module_name = f"crawl4ai.crawlers.x_com.scenes.{scene.lower()}_scene"
            scene_module = importlib.import_module(scene_module_name)
            scene_class_name = "".join(word.capitalize() for word in scene.split('_')) + "Scene"
            SceneClass = getattr(scene_module, scene_class_name)
            scene_instance = SceneClass()
        except (ImportError, AttributeError) as e:
            async def empty_generator(): yield
            return empty_generator() if scene in ["search", "home"] else {}

        result = scene_instance.scrape(page, **kwargs)
        if inspect.isasyncgen(result):
            async def page_managing_generator():
                try:
                    async for item in result:
                        yield item
                finally:
                    await page.context.close()
            return page_managing_generator()
        else:
            try:
                return await result
            finally:
                await page.context.close()

class MockBrowserManager:
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.playwright.stop()
    async def new_page(self, headless=True, storage_state=None):
        proxy_server = config.PROXY_SERVER
        launch_options = {"headless": headless}
        if proxy_server:
            launch_options["proxy"] = {"server": proxy_server}
            print(f"Using proxy server: {proxy_server}")

        browser = await self.playwright.chromium.launch(**launch_options)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        
        await stealth_async(page)

        original_close = page.close
        page.close = lambda: asyncio.gather(original_close(), context.close())
        return page

async def main(args):
    print("--- Running XProductionCrawler in Standalone Test Mode ---")
    kafka_producer = None
    run_output_dir = None

    if args.login:
        print("\nLogin-only mode. Attempting to log in and create auth file...")
        async with MockBrowserManager() as mock_browser_manager:
            crawler = XProductionCrawler(config=config, browser_manager=mock_browser_manager)
            await crawler.login()
            if AUTH_STATE_PATH.exists():
                print(f"Login successful. Auth file created/updated at {AUTH_STATE_PATH}")
            else:
                print("Login failed. Could not create auth file.")
        return

    if args.output_method == 'kafka':
        broker_url = config.KAFKA_BOOTSTRAP_SERVERS or "localhost:9092"
        kafka_topic = config.KAFKA_TOPIC or "x_com_scraped_data"
        topic_ready = await ensure_topic_exists(bootstrap_servers=broker_url, topic_name=kafka_topic)
        if not topic_ready: return
        kafka_producer = AIOKafkaProducer(bootstrap_servers=broker_url)
        await kafka_producer.start()
    else:
        run_output_dir = Path(__file__).parent / "out" / "scraped" / f"{args.output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Outputting batch files to: {run_output_dir}")

    try:
        async with MockBrowserManager() as mock_browser_manager:
            crawler = XProductionCrawler(config=config, browser_manager=mock_browser_manager)

            if not AUTH_STATE_PATH.exists():
                print("\nAuth file not found. Initiating automatic login...")
                await crawler.login()
                if not AUTH_STATE_PATH.exists():
                    print("\nAutomatic login failed. Could not create auth file. Please check credentials or manually verify account. Exiting.")
                    return
                print("Login successful. Auth file created. Proceeding with scraping...")

            batch_num = 0
            scanner = await crawler.scrape("search", query=args.keyword, scroll_count=args.scan_scrolls)
            
            should_fetch_replies = args.max_replies > 0

            async for url_batch in scanner:
                batch_num += 1
                print(f"\n--- PROCESSING BATCH {batch_num} ({len(url_batch)} URLs) ---")
                batch_details = []
                for url in url_batch:
                    detailed_data = await crawler.scrape(
                        "tweet_detail",
                        url=url,
                        include_replies=should_fetch_replies,
                        max_replies=args.max_replies,
                        reply_scroll_count=args.reply_scrolls
                    )
                    if detailed_data:
                        batch_details.append(detailed_data)
                
                if not batch_details: continue

                if args.output_method == 'kafka':
                    await send_to_kafka(producer=kafka_producer, topic=kafka_topic, data=batch_details, keyword=args.keyword, key_prefix=args.kafka_key_prefix)
                else:
                    batch_file_path = run_output_dir / f"batch_{batch_num}.json"
                    await save_batch_to_file(data=batch_details, keyword=args.keyword, file_path=batch_file_path)

            print("\n--- Streaming Workflow Complete ---")

    finally:
        if kafka_producer:
            print("Stopping Kafka producer...")
            await kafka_producer.stop()
            print("Kafka producer stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape X.com for tweets in real-time.")
    login_group = parser.add_argument_group('Authentication')
    login_group.add_argument("--login", action="store_true", help="Perform the login process and exit.")
    scrape_group = parser.add_argument_group('Scraping Options')
    scrape_group.add_argument("--keyword", type=str, help="The search keyword to use.")
    scrape_group.add_argument("--scan-scrolls", type=int, default=1, help="Number of scrolls during URL scan (default: 1).")
    scrape_group.add_argument("--max-replies", type=int, default=0, help="Max replies to fetch. > 0 enables reply scraping.")
    scrape_group.add_argument("--reply-scrolls", type=int, default=5, help="Max scrolls to find replies (default: 5).")
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--output-method", type=str, choices=['file', 'kafka'], default='file', help="Choose output method: file or kafka.")
    output_group.add_argument("--output-prefix", type=str, default="x_com_scrape", help="Prefix for the run-specific output directory.")
    output_group.add_argument("--kafka-key-prefix", type=str, default="x.com", help="Prefix for the Kafka message key (default: x.com).")
    parsed_args = parser.parse_args()
    if not parsed_args.login and not parsed_args.keyword:
        parser.error("the --keyword argument is required when not performing --login.")
    asyncio.run(main(parsed_args))

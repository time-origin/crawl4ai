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
from typing import List, Dict, Any

from playwright_stealth import stealth_async

# --- [FIX] Changed relative imports to absolute for PyInstaller compatibility ---
from crawl4ai.crawlers.x_com import config
from crawl4ai.crawlers.x_com.output_handler import save_batch_to_file
# [CHG] Import the new function for sending the task init message
from crawl4ai.crawlers.x_com.kafka_manager import send_to_kafka, ensure_topic_exists, send_task_init_message
from aiokafka import AIOKafkaProducer

# --- Logic for Bundled Execution ---
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    browsers_path = os.path.join(sys._MEIPASS, 'ms-playwright')
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
    print(f"Running in bundled mode. Setting Playwright browsers path to: {browsers_path}")

class_logger = type("Logger", (), {"info": print, "warning": print, "error": print})
logger = class_logger()

# --- Dynamically determine the auth state path ---
auth_json_path_from_config = getattr(config, 'AUTH_JSON_PATH', None)

if auth_json_path_from_config:
    AUTH_STATE_PATH = Path(auth_json_path_from_config)
    print(f"Using authentication file from config: {AUTH_STATE_PATH}")
else:
    AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"
    print(f"Using default authentication file: {AUTH_STATE_PATH}")


def filter_and_log_valid_tweets(all_detailed_tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    过滤推文列表，只保留那些实际抓取到回复内容的推文，并记录日志。
    
    Args:
        all_detailed_tweets: 包含所有已抓取推文详情的列表。

    Returns:
        一个只包含有效推文（即 replies 列表不为空）的新列表。
    """
    logger.info("--- [步骤 3/5] 开始过滤推文，只保留包含实际回复内容的推文 ---")
    
    valid_tweets = []
    for tweet_data in all_detailed_tweets:
        # 过滤条件：推文数据存在，且'replies'列表不为空
        if tweet_data and isinstance(tweet_data.get("replies"), list) and len(tweet_data["replies"]) > 0:
            valid_tweets.append(tweet_data)
        else:
            url_to_log = tweet_data.get('url', 'N/A') if tweet_data else 'N/A'
            logger.info(f"  [过滤] 推文 {url_to_log} 已被跳过，原因：在所有尝试后，仍未能抓取到任何实际的回复内容。")

    logger.info(f"--- 过滤完成。在 {len(all_detailed_tweets)} 条推文中，发现 {len(valid_tweets)} 条有效推文。 ---")

    # 如果存在有效推文，则打印其ID和URL列表
    if valid_tweets:
        logger.info("--- 以下是所有有效推文的列表 (ID 和 URL) ---")
        for tweet in valid_tweets:
            logger.info(f"  [有效] ID: {tweet.get('id', 'N/A')}, URL: {tweet.get('url', 'N/A')}")
    
    return valid_tweets


class XProductionCrawler:
    def __init__(self, config, browser_manager):
        self.config = config
        self.browser_manager = browser_manager
        self.username = self.config.X_USERNAME
        self.password = self.config.X_PASSWORD

    async def login(self):
        # This method is intended for local execution to generate the auth file.
        if not self.username or not self.password:
            print("Login credentials (X_USERNAME, X_PASSWORD) not found in environment variables.")
            return
        page = await self.browser_manager.new_page(headless=False) # Login should not be headless
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
                print("\nLogin failed: The password field did not appear.")
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
            print(f"Error dynamically importing scene '{scene}': {e}")
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
        
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]

        launch_options = {
            "headless": headless, 
            "args": browser_args
        }

        if proxy_server:
            launch_options["proxy"] = {"server": proxy_server}
            print(f"Using proxy server: {proxy_server}")

        browser = await self.playwright.chromium.launch(**launch_options)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        
        await stealth_async(page)

        return page

async def main(args):
    print("--- X.com 生产环境爬虫启动 ---")

    if args.login:
        print("\n仅执行登录模式，正在尝试生成认证文件...")
        async with MockBrowserManager() as mock_browser_manager:
            crawler = XProductionCrawler(config=config, browser_manager=mock_browser_manager)
            await crawler.login()
        if AUTH_STATE_PATH.exists():
            print(f"登录成功。认证文件已在 {AUTH_STATE_PATH} 创建/更新。")
        else:
            print("登录失败，未能创建认证文件。")
        return

    # --- 主抓取逻辑 ---
    kafka_producer = None
    run_output_dir = None
    broker_url = None
    kafka_topic = None

    try:
        print(f"\n正在检查认证文件: '{AUTH_STATE_PATH}'")
        if not AUTH_STATE_PATH.exists():
            print(f"❌ 认证文件未找到: '{AUTH_STATE_PATH}'.")
            print("请先在带有图形界面的机器上使用 --login 参数运行此脚本以生成认证文件，然后将其与可执行文件一起部署。")
            return
        else:
            print("✅ 认证文件已找到，开始抓取流程...")

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
            print(f"文件批次输出目录: {run_output_dir}")

        async with MockBrowserManager() as mock_browser_manager:
            crawler = XProductionCrawler(config=config, browser_manager=mock_browser_manager)
            
            # =============================================================================
            # 步骤 1/5: 扫描所有潜在的推文 URL
            # =============================================================================
            logger.info("--- [步骤 1/5] 开始扫描搜索结果页，获取所有推文的URL ---")
            scanner = await crawler.scrape("search", query=args.keyword, scroll_count=args.scan_scrolls)
            all_url_batches = [url_batch async for url_batch in scanner]
            all_urls = [url for batch in all_url_batches for url in batch]
            logger.info(f"--- URL扫描完成，共发现 {len(all_urls)} 条潜在的推文URL。 ---")

            # =============================================================================
            # 步骤 2/5: 抓取所有推文的详细数据 (包含重试逻辑)
            # =============================================================================
            logger.info("--- [步骤 2/5] 开始为所有URL抓取详细的推文数据（包含重试） ---")
            all_detailed_tweets = []
            should_fetch_replies = args.max_replies > 0
            max_retries = getattr(config, 'MAX_RETRIES_ON_FAILURE', 1)

            for i, url in enumerate(all_urls, 1):
                logger.info(f"  抓取进度: {i}/{len(all_urls)} - URL: {url}")
                
                detailed_data = None
                # 总尝试次数 = 1 (首次) + max_retries
                for attempt in range(1 + max_retries):
                    detailed_data = await crawler.scrape(
                        "tweet_detail",
                        url=url,
                        include_replies=should_fetch_replies,
                        max_replies=args.max_replies,
                        reply_scroll_count=args.reply_scrolls
                    )

                    # 成功条件：抓取到了至少一条回复
                    if detailed_data and detailed_data.get("replies"):
                        logger.info(f"    [抓取成功] 在第 {attempt + 1} 次尝试中成功抓取到 {len(detailed_data['replies'])} 条回复。")
                        break # 成功则退出重试循环
                    
                    # 失败且未到最后一次尝试，则记录并准备重试
                    if attempt < max_retries:
                        logger.warning(f"    [抓取失败] 第 {attempt + 1} 次尝试未能抓取到回复，即将重试...")
                        await asyncio.sleep(2) # 重试前短暂等待
                
                # 在所有尝试结束后，如果依然没有回复，记录最终失败状态
                if not (detailed_data and detailed_data.get("replies")):
                     logger.error(f"    [最终失败] 在 {1 + max_retries} 次尝试后，仍未能为URL {url} 抓取到任何回复。")

                all_detailed_tweets.append(detailed_data)

            logger.info("--- 所有URL的详细数据抓取完成。 ---")

            # =============================================================================
            # 步骤 3/5: 过滤推文并记录日志
            # =============================================================================
            all_filtered_tweets = filter_and_log_valid_tweets(all_detailed_tweets)

            # =============================================================================
            # 步骤 4/5: 计算最终数量并发送 TASK_INIT 消息
            # =============================================================================
            total_tweets = len(all_filtered_tweets)
            logger.info(f"--- [步骤 4/5] 计算有效推文总数完成，共 {total_tweets} 条。 ---")
            if args.output_method == 'kafka' and total_tweets > 0:
                task_control_topic = getattr(config, 'KAFKA_TASK_TOPIC', 'task_control_topic')
                topic_ready = await ensure_topic_exists(bootstrap_servers=broker_url, topic_name=task_control_topic)
                if topic_ready:
                    logger.info(f"--- 准备向主题 '{task_control_topic}' 发送 TASK_INIT 初始化消息 ---")
                    await send_task_init_message(
                        producer=kafka_producer,
                        topic=task_control_topic,
                        original_task_id=args.original_task_id,
                        total_tweets=total_tweets
                    )
            
            # =============================================================================
            # 步骤 5/5: 批处理并分发有效的推文数据
            # =============================================================================
            logger.info(f"--- [步骤 5/5] 开始批处理并分发 {total_tweets} 条有效推文。 ---")
            batch_size = 10 
            for i in range(0, total_tweets, batch_size):
                current_batch_tweets = all_filtered_tweets[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                logger.info(f"\n--- 正在处理第 {batch_num} 批，包含 {len(current_batch_tweets)} 条推文 ---")

                if args.output_method == 'kafka':
                    await send_to_kafka(
                        producer=kafka_producer,
                        topic=kafka_topic,
                        data=current_batch_tweets,
                        keyword=args.keyword,
                        original_task_id=args.original_task_id,
                        key_prefix=args.kafka_key_prefix
                    )
                else:
                    batch_file_path = run_output_dir / f"batch_{batch_num}.json"
                    await save_batch_to_file(data=current_batch_tweets, keyword=args.keyword, file_path=batch_file_path)

            logger.info("\n--- 所有批次处理完毕，流式工作流完成。 ---")

    finally:
        if kafka_producer:
            print("正在停止 Kafka 生产者...")
            await kafka_producer.stop()
            print("Kafka 生产者已停止。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape X.com for tweets in real-time.")
    
    # [ADD] New required argument for task identification
    task_group = parser.add_argument_group('Task Identification')
    task_group.add_argument("--original-task-id", type=int, required=True, help="The original task ID from the calling service.")

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

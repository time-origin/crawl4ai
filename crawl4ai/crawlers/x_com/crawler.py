# crawl4ai/crawlers/x_com/crawler.py

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# The real implementation will use the project's shared modules.
# For standalone execution, we use dotenv and a direct playwright call.
from dotenv import load_dotenv
import os

# Define a path for storing the authentication state
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"

# Create a simple logger
def log_to_file(message):
    """Log message to file"""
    with open("x_crawler_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{message}\n")


class XCrawler:
    """
    A crawler designed to scrape data from X.com (formerly Twitter).

    This crawler handles authentication, session management, and data extraction
    by leveraging the project's core browser and configuration management tools.
    """

    def __init__(self):
        """
        Initializes the XCrawler.
        """
        # For standalone login, load credentials directly from .env
        load_dotenv()
        self.username: str | None = os.getenv("X_USERNAME")
        self.password: str | None = os.getenv("X_PASSWORD")

        print(f"DEBUG: Username loaded: {self.username}")
        print(f"DEBUG: Password loaded: {self.password}")
        
        if not self.username or not self.password:
            print("Warning: X_USERNAME or X_PASSWORD not found in .env file.")


    async def login(self):
        """
        Performs fully automated login to X.com.
        This method handles the complete login flow including clicking Next buttons
        and entering credentials automatically.
        """
        log_to_file("=== 开始登录流程 ===")
        log_to_file(f"用户名: {self.username}")
        log_to_file(f"密码: {'*' * len(self.password) if self.password else 'None'}")
        
        if not self.username or not self.password:
            log_to_file("无法登录: 用户名或密码未设置")
            print("Cannot login: Username or password is not set.")
            return

        log_to_file("Starting X.com login...")
        print("Starting X.com login...")
        log_to_file("Initializing Playwright...")
        print("Initializing Playwright...")
        
        async with async_playwright() as p:
            log_to_file("Launching browser...")
            print("Launching browser...")
            # Launch browser with minimal args
            browser = await p.chromium.launch(headless=False)
            log_to_file("Browser launched successfully")
            print("Browser launched successfully")
            
            log_to_file("Creating new page...")
            print("Creating new page...")
            page = await browser.new_page()
            log_to_file("New page created successfully")
            print("New page created successfully")

            try:
                # 1. Navigate to login page
                log_to_file("导航到登录页面...")
                print("导航到登录页面...")
                log_to_file("正在打开浏览器并导航到X.com登录页面...")
                print("正在打开浏览器并导航到X.com登录页面...")
                
                # Simple navigation first
                await page.goto("https://httpbin.org/get", wait_until="load", timeout=10000)
                log_to_file("测试页面加载成功")
                print("测试页面加载成功")
                
                # Now try X.com
                await page.goto("https://x.com/login", wait_until="load", timeout=30000)
                log_to_file("已到达X.com登录页面")
                print("已到达X.com登录页面")
                
                # 等待页面稳定
                log_to_file("等待页面稳定...")
                print("等待页面稳定...")
                await page.wait_for_timeout(3000)
                
                # 检查当前URL
                current_url = page.url
                log_to_file(f"当前页面URL: {current_url}")
                print(f"当前页面URL: {current_url}")
                
                # 获取页面标题
                title = await page.title()
                log_to_file(f"页面标题: {title}")
                print(f"页面标题: {title}")
                
                # 获取页面内容长度
                content = await page.content()
                log_to_file(f"页面内容长度: {len(content)} 字符")
                print(f"页面内容长度: {len(content)} 字符")

                # 2. Enter username and click Next
                log_to_file("正在输入用户名...")
                print("正在输入用户名...")
                
                # Try multiple selector patterns for username input
                username_selectors = [
                    'input[autocomplete="username"]',
                    'input[name="text"]',
                    'input[type="text"]',
                    'input[data-testid="ocfEnterTextTextInput"]',
                    'input[data-testid*="username"]'
                ]
                
                username_input = None
                for selector in username_selectors:
                    try:
                        log_to_file(f"Trying selector: {selector}")
                        print(f"Trying selector: {selector}")
                        username_input = page.locator(selector)
                        await username_input.wait_for(timeout=5000)
                        if await username_input.is_visible() and await username_input.is_enabled():
                            log_to_file(f"Found username input with selector: {selector}")
                            print(f"Found username input with selector: {selector}")
                            break
                    except Exception as e:
                        log_to_file(f"Selector {selector} failed: {e}")
                        print(f"Selector {selector} failed: {e}")
                        continue
                
                if not username_input or not await username_input.is_visible():
                    # Take screenshot for debugging
                    await page.screenshot(path="login_debug.png")
                    raise Exception("找不到用户名输入框")
                
                # Add extra wait to ensure element is ready
                await page.wait_for_timeout(2000)
                log_to_file(f"Attempting to fill username: {self.username}")
                print(f"Attempting to fill username: {self.username}")
                
                # Try multiple approaches to fill the username
                try:
                    # Method 1: Direct fill
                    await username_input.fill(self.username)
                    log_to_file("用户名已通过fill方法输入")
                    print("用户名已通过fill方法输入")
                except Exception as e:
                    log_to_file(f"Direct fill failed: {e}")
                    print(f"Direct fill failed: {e}")
                    try:
                        # Method 2: Click then fill
                        await username_input.click()
                        await page.wait_for_timeout(1000)
                        await username_input.fill(self.username)
                        log_to_file("用户名已通过click+fill方法输入")
                        print("用户名已通过click+fill方法输入")
                    except Exception as e2:
                        log_to_file(f"Click+fill failed: {e2}")
                        print(f"Click+fill failed: {e2}")
                        try:
                            # Method 3: Type character by character
                            await username_input.click()
                            await page.wait_for_timeout(1000)
                            for char in self.username:
                                await page.keyboard.type(char, delay=100)
                            log_to_file("用户名已通过逐字符输入方法输入")
                            print("用户名已通过逐字符输入方法输入")
                        except Exception as e3:
                            log_to_file(f"Character-by-character typing failed: {e3}")
                            print(f"Character-by-character typing failed: {e3}")
                            raise Exception("无法将用户名填入输入框")

                # 3. Find and click Next button - multiple selector patterns
                log_to_file("寻找下一步按钮...")
                print("寻找下一步按钮...")
                next_button_selectors = [
                    'button[data-testid="ocfEnterTextNextButton"]',
                    'button:has-text("Next")',
                    'button[type="submit"]',
                    'div[role="button"]:has-text("Next")',
                    'button:has-text("下一步")',  # Chinese version
                    'button[data-testid*="next"]'
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    try:
                        log_to_file(f"Trying next button selector: {selector}")
                        print(f"Trying next button selector: {selector}")
                        next_button = page.locator(selector)
                        await next_button.wait_for(timeout=5000)
                        if await next_button.is_visible() and await next_button.is_enabled():
                            log_to_file(f"Found next button with selector: {selector}")
                            print(f"Found next button with selector: {selector}")
                            break
                    except Exception as e:
                        log_to_file(f"Next button selector {selector} failed: {e}")
                        print(f"Next button selector {selector} failed: {e}")
                        continue
                
                if not next_button or not await next_button.is_visible():
                    # Take screenshot for debugging
                    await page.screenshot(path="login_debug_next.png")
                    raise Exception("找不到下一步按钮")
                
                await next_button.click()
                log_to_file("已点击下一步")
                print("已点击下一步")

                # 4. Wait for password page and enter password
                log_to_file("等待密码页面加载...")
                print("等待密码页面加载...")
                
                # Wait for page transition
                await page.wait_for_timeout(5000)
                
                # Find password input with multiple selector patterns
                password_selectors = [
                    'input[data-testid="ocfEnterPasswordTextInput"]',
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[autocomplete="current-password"]',
                    'input[data-testid*="password"]'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        log_to_file(f"Trying password selector: {selector}")
                        print(f"Trying password selector: {selector}")
                        password_input = page.locator(selector)
                        await password_input.wait_for(timeout=10000)
                        if await password_input.is_visible() and await password_input.is_enabled():
                            log_to_file(f"Found password input with selector: {selector}")
                            print(f"Found password input with selector: {selector}")
                            break
                    except Exception as e:
                        log_to_file(f"Password selector {selector} failed: {e}")
                        print(f"Password selector {selector} failed: {e}")
                        continue
                
                if not password_input or not await password_input.is_visible():
                    # Check if we need to handle unusual login flow
                    log_to_file("检查是否需要处理异常登录流程...")
                    print("检查是否需要处理异常登录流程...")
                    unusual_selectors = [
                        'input[data-testid="ocfEnterTextTextInput"]',
                        'input[name="text"]',
                        'input[type="text"]'
                    ]
                    
                    unusual_handled = False
                    for selector in unusual_selectors:
                        try:
                            unusual_input = page.locator(selector)
                            await unusual_input.wait_for(timeout=5000)
                            if await unusual_input.is_visible():
                                log_to_file("处理异常登录提示...")
                                print("处理异常登录提示...")
                                # Try multiple methods to fill the unusual input
                                try:
                                    await unusual_input.fill(self.username)
                                except:
                                    await unusual_input.click()
                                    await page.wait_for_timeout(1000)
                                    await unusual_input.fill(self.username)
                                
                                # Click next button again
                                for next_selector in next_button_selectors:
                                    try:
                                        next_btn = page.locator(next_selector)
                                        await next_btn.wait_for(timeout=5000)
                                        if await next_btn.is_visible():
                                            await next_btn.click()
                                            log_to_file("已处理异常登录提示")
                                            print("已处理异常登录提示")
                                            unusual_handled = True
                                            break
                                    except:
                                        continue
                                
                                # Wait for password page after handling unusual login
                                await page.wait_for_timeout(5000)
                                break
                        except:
                            continue
                    
                    # If we handled unusual flow, try to find password input again
                    if unusual_handled:
                        for selector in password_selectors:
                            try:
                                password_input = page.locator(selector)
                                await password_input.wait_for(timeout=10000)
                                if await password_input.is_visible():
                                    break
                            except:
                                continue
                
                if not password_input or not await password_input.is_visible():
                    # Take screenshot for debugging
                    await page.screenshot(path="login_debug_password.png")
                    raise Exception("找不到密码输入框")
                
                log_to_file("输入密码...")
                print("输入密码...")
                await password_input.fill(self.password)
                log_to_file("密码已输入")
                print("密码已输入")

                # 5. Find and click Login button
                log_to_file("寻找登录按钮...")
                print("寻找登录按钮...")
                login_button_selectors = [
                    'button[data-testid="LoginForm_Login_Button"]',
                    'button:has-text("Log in")',
                    'button[type="submit"]',
                    'div[role="button"]:has-text("Log in")',
                    'button:has-text("登录")',  # Chinese version
                    'button[data-testid*="login"]'
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        log_to_file(f"Trying login button selector: {selector}")
                        print(f"Trying login button selector: {selector}")
                        login_button = page.locator(selector)
                        await login_button.wait_for(timeout=10000)
                        if await login_button.is_visible() and await login_button.is_enabled():
                            log_to_file(f"Found login button with selector: {selector}")
                            print(f"Found login button with selector: {selector}")
                            break
                    except Exception as e:
                        log_to_file(f"Login button selector {selector} failed: {e}")
                        print(f"Login button selector {selector} failed: {e}")
                        continue
                
                if not login_button or not await login_button.is_visible():
                    # Take screenshot for debugging
                    await page.screenshot(path="login_debug_login.png")
                    raise Exception("找不到登录按钮")
                
                await login_button.click()
                log_to_file("已点击登录")
                print("已点击登录")

                # 6. Wait for successful login and save session
                log_to_file("等待登录成功...")
                print("等待登录成功...")
                try:
                    # Wait for home timeline or user menu to appear
                    await page.wait_for_selector('[data-testid="primaryColumn"], [data-testid="SideNav_AccountSwitcher_Button"]', timeout=30000)
                    log_to_file("✅ 登录成功！")
                    print("✅ 登录成功！")

                    # Save authentication state
                    await page.context.storage_state(path=AUTH_STATE_PATH)
                    log_to_file(f"认证状态已保存到: {AUTH_STATE_PATH}")
                    print(f"认证状态已保存到: {AUTH_STATE_PATH}")
                    
                except Exception as e:
                    log_to_file(f"❌ 登录验证失败: {e}")
                    print(f"❌ 登录验证失败: {e}")
                    # Take screenshot for debugging
                    await page.screenshot(path="login_error.png")
                    log_to_file("已保存错误截图: login_error.png")
                    print("已保存错误截图: login_error.png")
                    raise Exception("登录验证超时，请检查账号和网络连接") from e

            finally:
                pass
        log_to_file("✅ 登录成功！")
        print("✅ 登录成功！")


    async def scrape_profile(self, profile_url: str, max_tweets: int = 20):
        """
        Scrapes a user's profile page for their recent tweets.

        This method uses a pre-authenticated browser context to ensure
        access to the page content.

        Args:
            profile_url (str): The URL of the user's profile to scrape.
            max_tweets (int, optional): Maximum number of tweets to scrape. Defaults to 20.

        Returns:
            list: A list of dictionaries, where each dictionary represents a tweet.
        """
        print(f"Scraping profile: {profile_url}")
        tweets = []
        
        try:
            async with async_playwright() as p:
                # 1. Launch browser in headless mode for production scraping
                browser = await p.chromium.launch(headless=True)
                
                # 2. Create a new context with the saved authentication state
                if not AUTH_STATE_PATH.exists():
                    print(f"Authentication state file not found at {AUTH_STATE_PATH}. Please run login first.")
                    return []
                
                context = await browser.new_context(storage_state=str(AUTH_STATE_PATH))
                page = await context.new_page()
                
                # 3. Navigate to the profile URL
                await page.goto(profile_url, wait_until="networkidle")
                print(f"Navigated to {profile_url}")
                
                # 4. Wait for the tweet feed to load
                print("Waiting for tweets to load...")
                try:
                    # Wait for the primary column to be visible
                    await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=30000)
                    
                    # Wait for tweet articles to appear
                    await page.wait_for_selector('article[data-testid="tweet"]', timeout=30000)
                    print("Tweets loaded successfully.")
                except Exception as e:
                    print(f"Error waiting for tweets: {e}")
                    # Check if we're on a valid profile page
                    if await page.locator('[data-testid="error-detail"]').count() > 0:
                        error_text = await page.locator('[data-testid="error-detail"]').inner_text()
                        print(f"Error on page: {error_text}")
                    return []
                
                # 5. Extract tweets
                print("Extracting tweets...")
                
                # Scroll to load more tweets if needed
                previous_tweet_count = 0
                scroll_attempts = 0
                
                while len(tweets) < max_tweets:
                    # Get all tweet articles currently on the page
                    tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
                    current_tweet_count = len(tweet_elements)
                    
                    # Process new tweets
                    for i in range(previous_tweet_count, current_tweet_count):
                        if len(tweets) >= max_tweets:
                            break
                            
                        tweet_element = tweet_elements[i]
                        tweet_data = {}
                        
                        try:
                            # Extract tweet text
                            text_element = await tweet_element.query_selector('[data-testid="tweetText"]')
                            if text_element:
                                tweet_data["text"] = await text_element.inner_text()
                            else:
                                tweet_data["text"] = ""  # Some tweets might be just media
                            
                            # Extract author information
                            author_element = await tweet_element.query_selector('div[data-testid="User-Name"]')
                            if author_element:
                                # Get display name
                                name_element = await author_element.query_selector('span')
                                if name_element:
                                    tweet_data["author_name"] = await name_element.inner_text()
                                
                                # Get username (@handle)
                                username_element = await author_element.query_selector('div[dir="ltr"] > span')
                                if username_element:
                                    tweet_data["author_username"] = await username_element.inner_text()
                            
                            # Extract timestamp
                            time_element = await tweet_element.query_selector('time')
                            if time_element:
                                tweet_data["timestamp"] = await time_element.get_attribute('datetime')
                            
                            # Extract tweet URL
                            link_element = await tweet_element.query_selector('a[href*="/status/"]')
                            if link_element:
                                href = await link_element.get_attribute('href')
                                tweet_data["url"] = f"https://x.com{href}"
                            
                            # Extract engagement metrics
                            metrics = {}
                            reply_element = await tweet_element.query_selector('[data-testid="reply"]')
                            if reply_element:
                                reply_text = await reply_element.inner_text()
                                metrics["replies"] = reply_text if reply_text else "0"
                                
                            retweet_element = await tweet_element.query_selector('[data-testid="retweet"]')
                            if retweet_element:
                                retweet_text = await retweet_element.inner_text()
                                metrics["retweets"] = retweet_text if retweet_text else "0"
                                
                            like_element = await tweet_element.query_selector('[data-testid="like"]')
                            if like_element:
                                like_text = await like_element.inner_text()
                                metrics["likes"] = like_text if like_text else "0"
                                
                            tweet_data["metrics"] = metrics
                            
                            # Add to our collection
                            tweets.append(tweet_data)
                            print(f"Extracted tweet {len(tweets)}/{max_tweets}")
                            
                        except Exception as e:
                            print(f"Error extracting tweet data: {e}")
                            continue
                    
                    # If we haven't collected enough tweets and there are no new tweets, scroll to load more
                    if len(tweets) < max_tweets and current_tweet_count == previous_tweet_count:
                        print("Scrolling to load more tweets...")
                        await page.evaluate("window.scrollBy(0, 1000)")
                        await page.wait_for_timeout(2000)  # Wait for new content to load
                        
                        # Safety check to prevent infinite loops
                        scroll_attempts += 1
                        if scroll_attempts > 5:
                            print("Reached maximum scroll attempts, stopping extraction.")
                            break
                    else:
                        previous_tweet_count = current_tweet_count
                        scroll_attempts = 0  # Reset scroll attempts when new tweets are found
                
                print(f"Extracted {len(tweets)} tweets in total.")
                await browser.close()
                
        except Exception as e:
            print(f"An error occurred during profile scraping: {e}")
        
        return tweets

# This main block allows running the login process directly
async def main():
    """
    Standalone execution function to perform the login.
    To run: python -m crawl4ai.crawlers.x_com.crawler
    """
    print("--- X.com Login Script ---")
    # In standalone mode, we don't need the full app's config or browser_manager
    crawler = XCrawler()

    # This will run the login process and save the auth_state.json file
    await crawler.login()
    print("--------------------------")


if __name__ == "__main__":
    # Before running, ensure you have:
    # 1. A .env file in the project root with X_USERNAME and X_PASSWORD.
    # 2. Installed dependencies: pip install playwright python-dotenv
    # 3. Downloaded browser drivers: python -m playwright install
    asyncio.run(main())

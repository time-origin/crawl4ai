# crawl4ai/crawlers/x_com/production_crawler.py
"""
Production X.com Crawler with Persistent Session
Based on the login logic from crawler.py but with continuous crawling capabilities
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os

# Define a path for storing the authentication state
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


class ProductionXCrawler:
    """
    Production X.com crawler that maintains persistent browser session
    Based on the proven login logic from the original crawler.py
    """

    def __init__(self):
        """
        Initializes the ProductionXCrawler.
        """
        # For standalone login, load credentials directly from .env
        load_dotenv()
        self.username: str | None = os.getenv("X_USERNAME")
        self.password: str | None = os.getenv("X_PASSWORD")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        print(f"DEBUG: Username loaded: {self.username}")
        print(f"DEBUG: Password loaded: {self.password}")
        
        if not self.username or not self.password:
            print("Warning: X_USERNAME or X_PASSWORD not found in .env file.")

    async def login(self):
        """
        Performs fully automated login to X.com.
        Based on the proven logic from the original crawler.py
        This method handles the complete login flow including clicking Next buttons
        and entering credentials automatically.
        """
        if not self.username or not self.password:
            print("Cannot login: Username or password is not set.")
            return

        print("Starting X.com login...")
        
        # Initialize playwright
        self.playwright = await async_playwright().start()
        
        # Launch browser with better configuration to avoid detection
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )
        
        # Create context with better settings
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        self.page = await self.context.new_page()

        try:
            # 1. Navigate to login page
            print("导航到登录页面...")
            print("正在打开浏览器并导航到X.com登录页面...")
            
            # Add browser information for debugging
            print(f"Browser version: {self.browser.version}")
            print(f"Browser connected: {self.browser.is_connected()}")
            
            # Try with shorter timeout and immediate return
            try:
                print("使用networkidle等待策略，超时时间10秒...")
                await self.page.goto("https://x.com/login", wait_until="networkidle", timeout=10000)
                print("已到达登录页面")
            except Exception as e:
                print(f"使用networkidle等待策略时出错: {e}")
                print("尝试使用load等待策略，超时时间10秒...")
                try:
                    await self.page.goto("https://x.com/login", wait_until="load", timeout=10000)
                    print("已到达登录页面 (使用load等待策略)")
                except Exception as e2:
                    print(f"使用load等待策略仍然失败: {e2}")
                    print("尝试使用domcontentloaded等待策略，超时时间10秒...")
                    try:
                        await self.page.goto("https://x.com/login", wait_until="domcontentloaded", timeout=10000)
                        print("已到达登录页面 (使用domcontentloaded等待策略)")
                    except Exception as e3:
                        print(f"使用domcontentloaded等待策略也失败了: {e3}")
                        print("尝试使用commit等待策略，超时时间10秒...")
                        try:
                            await self.page.goto("https://x.com/login", wait_until="commit", timeout=10000)
                            print("已到达登录页面 (使用commit等待策略)")
                            # 等待一点时间让页面加载
                            print("等待页面加载完成...")
                            await self.page.wait_for_timeout(3000)
                        except Exception as e4:
                            print(f"所有导航尝试都失败了: {e4}")
                            # Take screenshot for debugging
                            try:
                                await self.page.screenshot(path="navigation_error.png")
                                print("已保存错误截图: navigation_error.png")
                            except Exception as screenshot_error:
                                print(f"截图失败: {screenshot_error}")
                            raise Exception("无法导航到X.com登录页面，请检查网络连接")
            
            # 等待页面稳定
            print("等待页面稳定...")
            await self.page.wait_for_timeout(3000)
            
            # 检查当前URL
            current_url = self.page.url
            print(f"当前页面URL: {current_url}")
            
            # 获取页面标题
            title = await self.page.title()
            print(f"页面标题: {title}")
            
            # 获取页面内容长度
            content = await self.page.content()
            print(f"页面内容长度: {len(content)} 字符")

            # 2. Enter username and click Next
            print("正在输入用户名...")
            
            # Try multiple selector patterns for username input (same as original)
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
                    print(f"Trying selector: {selector}")
                    username_input = self.page.locator(selector)
                    await username_input.wait_for(timeout=5000)
                    if await username_input.is_visible() and await username_input.is_enabled():
                        print(f"Found username input with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not username_input or not await username_input.is_visible():
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_debug.png")
                    print("已保存调试截图: login_debug.png")
                except Exception as screenshot_error:
                    print(f"调试截图失败: {screenshot_error}")
                raise Exception("找不到用户名输入框")
            
            # Add extra wait to ensure element is ready
            await self.page.wait_for_timeout(2000)
            print(f"Attempting to fill username: {self.username}")
            
            # Try multiple approaches to fill the username (same as original)
            try:
                # Method 1: Direct fill
                await username_input.fill(self.username)
                print("用户名已通过fill方法输入")
            except Exception as e:
                print(f"Direct fill failed: {e}")
                try:
                    # Method 2: Click then fill
                    await username_input.click()
                    await self.page.wait_for_timeout(1000)
                    await username_input.fill(self.username)
                    print("用户名已通过click+fill方法输入")
                except Exception as e2:
                    print(f"Click+fill failed: {e2}")
                    try:
                        # Method 3: Type character by character
                        await username_input.click()
                        await self.page.wait_for_timeout(1000)
                        for char in self.username:
                            await self.page.keyboard.type(char, delay=100)
                        print("用户名已通过逐字符输入方法输入")
                    except Exception as e3:
                        print(f"Character-by-character typing failed: {e3}")
                        raise Exception("无法将用户名填入输入框")

            # 3. Find and click Next button (same as original)
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
                    print(f"Trying next button selector: {selector}")
                    next_button = self.page.locator(selector)
                    await next_button.wait_for(timeout=5000)
                    if await next_button.is_visible() and await next_button.is_enabled():
                        print(f"Found next button with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Next button selector {selector} failed: {e}")
                    continue
            
            if not next_button or not await next_button.is_visible():
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_debug_next.png")
                    print("已保存调试截图: login_debug_next.png")
                except Exception as screenshot_error:
                    print(f"调试截图失败: {screenshot_error}")
                raise Exception("找不到下一步按钮")
            
            await next_button.click()
            print("已点击下一步")

            # 4. Wait for password page and enter password (same as original)
            print("等待密码页面加载...")
            
            # Wait for page transition
            await self.page.wait_for_timeout(5000)
            
            # Check if page has crashed or changed unexpectedly
            try:
                current_url = self.page.url
                print(f"当前页面URL (after clicking next): {current_url}")
                
                title = await self.page.title()
                print(f"页面标题 (after clicking next): {title}")
            except Exception as e:
                print(f"页面状态检查失败: {e}")
                # Try to reload the page
                try:
                    await self.page.reload()
                    await self.page.wait_for_timeout(3000)
                except Exception as reload_error:
                    print(f"页面重载失败: {reload_error}")
            
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
                    print(f"Trying password selector: {selector}")
                    password_input = self.page.locator(selector)
                    await password_input.wait_for(timeout=10000)
                    if await password_input.is_visible() and await password_input.is_enabled():
                        print(f"Found password input with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Password selector {selector} failed: {e}")
                    # Check if the page has crashed
                    try:
                        # Try to get page status
                        current_url = self.page.url
                        print(f"页面URL检查: {current_url}")
                    except Exception as page_error:
                        print(f"页面状态检查失败: {page_error}")
                        # Page might have crashed, try to restart
                        raise Exception("页面已崩溃，请重试")
                    continue
            
            if not password_input or not await password_input.is_visible():
                # Check if we need to handle unusual login flow
                print("检查是否需要处理异常登录流程...")
                unusual_selectors = [
                    'input[data-testid="ocfEnterTextTextInput"]',
                    'input[name="text"]',
                    'input[type="text"]'
                ]
                
                unusual_handled = False
                for selector in unusual_selectors:
                    try:
                        unusual_input = self.page.locator(selector)
                        await unusual_input.wait_for(timeout=5000)
                        if await unusual_input.is_visible():
                            print("处理异常登录提示...")
                            # Try multiple methods to fill the unusual input
                            try:
                                await unusual_input.fill(self.username)
                            except:
                                await unusual_input.click()
                                await self.page.wait_for_timeout(1000)
                                await unusual_input.fill(self.username)
                            
                            # Click next button again
                            for next_selector in next_button_selectors:
                                try:
                                    next_btn = self.page.locator(next_selector)
                                    await next_btn.wait_for(timeout=5000)
                                    if await next_btn.is_visible():
                                        await next_btn.click()
                                        print("已处理异常登录提示")
                                        unusual_handled = True
                                        break
                                except:
                                    continue
                            
                            # Wait for password page after handling unusual login
                            await self.page.wait_for_timeout(5000)
                            break
                    except:
                        continue
                
                # If we handled unusual flow, try to find password input again
                if unusual_handled:
                    for selector in password_selectors:
                        try:
                            password_input = self.page.locator(selector)
                            await password_input.wait_for(timeout=10000)
                            if await password_input.is_visible():
                                break
                        except:
                            continue
            
            # Final check for password input
            if not password_input:
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_debug_password.png")
                    print("已保存调试截图: login_debug_password.png")
                except Exception as screenshot_error:
                    print(f"调试截图失败: {screenshot_error}")
                raise Exception("找不到密码输入框")
            
            # Check if password input is visible, if not, wait a bit more
            try:
                if not await password_input.is_visible():
                    print("密码输入框不可见，等待页面加载...")
                    await self.page.wait_for_timeout(3000)
                    # Check again
                    if not await password_input.is_visible():
                        print("密码输入框仍然不可见")
                        # Take screenshot for debugging
                        try:
                            await self.page.screenshot(path="login_debug_password_invisible.png")
                            print("已保存调试截图: login_debug_password_invisible.png")
                        except Exception as screenshot_error:
                            print(f"调试截图失败: {screenshot_error}")
                        raise Exception("密码输入框不可见")
            except Exception as visibility_error:
                print(f"检查密码输入框可见性失败: {visibility_error}")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_debug_password_error.png")
                    print("已保存调试截图: login_debug_password_error.png")
                except Exception as screenshot_error:
                    print(f"调试截图失败: {screenshot_error}")
                raise Exception("无法检查密码输入框状态")
            
            print("输入密码...")
            await password_input.fill(self.password)
            print("密码已输入")

            # 5. Find and click Login button (same as original)
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
                    print(f"Trying login button selector: {selector}")
                    login_button = self.page.locator(selector)
                    await login_button.wait_for(timeout=10000)
                    if await login_button.is_visible() and await login_button.is_enabled():
                        print(f"Found login button with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Login button selector {selector} failed: {e}")
                    continue
            
            if not login_button or not await login_button.is_visible():
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_debug_login.png")
                    print("已保存调试截图: login_debug_login.png")
                except Exception as screenshot_error:
                    print(f"调试截图失败: {screenshot_error}")
                raise Exception("找不到登录按钮")
            
            await login_button.click()
            print("已点击登录")

            # 6. Wait for successful login and save session (same as original)
            print("等待登录成功...")
            try:
                # Wait for home timeline or user menu to appear
                await self.page.wait_for_selector('[data-testid="primaryColumn"], [data-testid="SideNav_AccountSwitcher_Button"]', timeout=30000)
                print("✅ 登录成功！")

                # Save authentication state
                await self.context.storage_state(path=AUTH_STATE_PATH)
                print(f"认证状态已保存到: {AUTH_STATE_PATH}")
                
            except Exception as e:
                print(f"❌ 登录验证失败: {e}")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="login_error.png")
                    print("已保存错误截图: login_error.png")
                except Exception as screenshot_error:
                    print(f"错误截图失败: {screenshot_error}")
                raise Exception("登录验证超时，请检查账号和网络连接") from e

        except Exception as e:
            print(f"Login process failed: {e}")
            # Print traceback for better debugging
            import traceback
            traceback.print_exc()
            raise

    async def scan_page_links(self):
        """
        Scan current page for all links
        """
        if not self.page:
            raise Exception("Browser not initialized. Call login() first.")
            
        print("Scanning page for links...")
        urls = set()
        
        try:
            # Find all anchor tags with href attributes
            link_elements = await self.page.query_selector_all('a[href]')
            
            for element in link_elements:
                href = await element.get_attribute('href')
                if href:
                    # Convert to absolute URL if needed
                    from urllib.parse import urljoin
                    absolute_url = urljoin(self.page.url, href)
                    urls.add(absolute_url)
            
            print(f"Found {len(urls)} links on page")
            return list(urls)
            
        except Exception as e:
            print(f"Error scanning links: {e}")
            return []

    async def get_page_content(self):
        """
        Get content from current page
        """
        if not self.page:
            raise Exception("Browser not initialized. Call login() first.")
            
        try:
            title = await self.page.title()
            content = await self.page.content()
            
            return {
                'title': title,
                'url': self.page.url,
                'content_length': len(content)
            }
        except Exception as e:
            print(f"Error getting page content: {e}")
            return {}

    async def navigate_and_crawl(self, url):
        """
        Navigate to a URL and crawl its content
        """
        if not self.page:
            raise Exception("Browser not initialized. Call login() first.")
            
        try:
            print(f"Navigating to: {url}")
            await self.page.goto(url, wait_until="networkidle")
            print("Page loaded successfully")
            
            # Get page content
            content = await self.get_page_content()
            print(f"Page title: {content.get('title', 'N/A')}")
            
            # Scan for links
            links = await self.scan_page_links()
            
            return {
                'content': content,
                'links': links
            }
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return {}

    async def close(self):
        """
        Close browser and cleanup resources
        """
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Browser closed and resources cleaned up.")


# Production entry point
async def main():
    """
    Production entry point for X.com crawler
    """
    print("🚀 Starting Production X.com Crawler")
    
    crawler = ProductionXCrawler()
    
    try:
        # Perform login using the proven logic
        await crawler.login()
        print("✅ Login completed successfully!")
        
        # Keep browser session open for continuous operations
        print("⏳ Browser session maintained for continuous crawling")
        print("💡 You can now use the crawler for link scanning and content extraction")
        print("💡 Press Ctrl+C to exit")
        
        # Example of continuous operation
        while True:
            # This is where you would implement your continuous crawling logic
            # For now, we'll just keep the session alive
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down crawler...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup resources
        await crawler.close()
        print("✅ Crawler shutdown complete")


if __name__ == "__main__":
    # Run the production crawler
    # To run: python -m crawl4ai.crawlers.x_com.production_crawler
    asyncio.run(main())
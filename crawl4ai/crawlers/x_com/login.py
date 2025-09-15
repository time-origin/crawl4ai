# crawl4ai/crawlers/x_com/login.py
"""
X.com Login Module
Handles automated login to X.com with persistent session management
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Define a path for storing the authentication state
AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


class XComLogin:
    """Handles X.com login automation"""
    
    def __init__(self):
        """Initialize the login manager"""
        load_dotenv()
        self.username = os.getenv("X_USERNAME")
        self.password = os.getenv("X_PASSWORD")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        if not self.username or not self.password:
            raise ValueError("X_USERNAME and X_PASSWORD must be set in .env file")
    
    async def login(self):
        """
        Performs fully automated login to X.com.
        This method handles the complete login flow including clicking Next buttons
        and entering credentials automatically.
        """
        print("Starting X.com login...")
        
        # Initialize playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        try:
            # Navigate to login page
            print("Navigating to login page...")
            await self.page.goto("https://x.com/login", wait_until="networkidle", timeout=30000)
            print("Reached login page")
            
            # Wait for page to stabilize
            await self.page.wait_for_timeout(2000)
            
            # Enter username
            print("Entering username...")
            username_input = self.page.locator('input[autocomplete="username"]')
            await username_input.wait_for(timeout=10000)
            await username_input.fill(self.username)
            print("Username entered")
            
            # Click Next button
            print("Clicking Next button...")
            next_button = self.page.locator('button:has-text("Next")')
            await next_button.wait_for(timeout=10000)
            await next_button.click()
            print("Next button clicked")
            
            # Wait for password page
            print("Waiting for password page...")
            await self.page.wait_for_timeout(3000)
            
            # Enter password
            print("Entering password...")
            password_input = self.page.locator('input[name="password"]')
            await password_input.wait_for(timeout=10000)
            await password_input.fill(self.password)
            print("Password entered")
            
            # Click Login button
            print("Clicking Login button...")
            login_button = self.page.locator('button:has-text("Log in")')
            await login_button.wait_for(timeout=10000)
            await login_button.click()
            print("Login button clicked")
            
            # Wait for successful login
            print("Waiting for successful login...")
            await self.page.wait_for_selector('[data-testid="AppTabBar_Home_Link"]', timeout=30000)
            print("✅ Login successful!")
            
            # Save authentication state
            await self.context.storage_state(path=AUTH_STATE_PATH)
            print(f"Authentication state saved to: {AUTH_STATE_PATH}")
            
            # Keep browser open for further operations
            print("Browser session maintained. Ready for crawling operations.")
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            # Take screenshot for debugging
            await self.page.screenshot(path="login_error.png")
            print("Error screenshot saved: login_error.png")
            raise
    
    def get_browser_components(self):
        """Return browser components for use in other modules"""
        return self.playwright, self.browser, self.context, self.page
    
    async def close(self):
        """Close browser and cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Browser closed and resources cleaned up.")


# Example usage
async def main():
    """Example usage of the login module"""
    try:
        login_manager = XComLogin()
        await login_manager.login()
        
        # Keep the session open
        print("Login session maintained. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # In a real application, you might not want to close immediately
        # login_manager.close()
        pass


if __name__ == "__main__":
    asyncio.run(main())
# crawl4ai/crawlers/x_com/main_crawler.py
"""
Main X.com Crawler Module
Orchestrates login, link scanning, and content extraction
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Import our modules
from .login import XComLogin, AUTH_STATE_PATH
from .link_scanner import XComLinkScanner
from .content_extractor import XComContentExtractor


class XComCrawler:
    """Main X.com crawler that orchestrates all components"""
    
    def __init__(self):
        """Initialize the crawler"""
        load_dotenv()
        self.login_manager = None
        self.link_scanner = None
        self.content_extractor = None
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        """Initialize the crawler with authentication"""
        print("Initializing X.com Crawler...")
        
        # Check if we have saved authentication
        if AUTH_STATE_PATH.exists():
            print("Using saved authentication state...")
            await self._init_with_auth()
        else:
            print("No saved authentication found. Performing login...")
            await self._perform_login()
    
    async def _perform_login(self):
        """Perform login and save authentication"""
        self.login_manager = XComLogin()
        await self.login_manager.login()
        
        # Get browser components
        self.playwright, self.browser, self.context, self.page = self.login_manager.get_browser_components()
        
        # Initialize scanners and extractors
        self.link_scanner = XComLinkScanner(self.page)
        self.content_extractor = XComContentExtractor(self.page)
        
        print("Login completed and crawler initialized")
    
    async def _init_with_auth(self):
        """Initialize with saved authentication"""
        # Initialize playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(storage_state=str(AUTH_STATE_PATH))
        self.page = await self.context.new_page()
        
        # Initialize scanners and extractors
        self.link_scanner = XComLinkScanner(self.page)
        self.content_extractor = XComContentExtractor(self.page)
        
        print("Initialized with saved authentication")
    
    async def crawl_profile(self, profile_url, max_tweets=10):
        """
        Crawl a user profile and extract tweets
        
        Args:
            profile_url (str): URL of the profile to crawl
            max_tweets (int): Maximum number of tweets to extract
            
        Returns:
            dict: Crawled data including profile info and tweets
        """
        if not self.page:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        print(f"Crawling profile: {profile_url}")
        
        try:
            # Navigate to profile
            await self.page.goto(profile_url, wait_until="networkidle")
            print(f"Navigated to {profile_url}")
            
            # Extract profile information
            print("Extracting profile information...")
            profile_info = await self.content_extractor.extract_profile_info()
            
            # Extract tweets
            print("Extracting tweets...")
            tweets = await self.content_extractor.extract_tweets(max_tweets)
            
            result = {
                'profile': profile_info,
                'tweets': tweets,
                'url': profile_url
            }
            
            return result
            
        except Exception as e:
            print(f"Error crawling profile: {e}")
            return {}
    
    async def crawl_timeline(self, max_tweets=20):
        """
        Crawl the home timeline
        
        Args:
            max_tweets (int): Maximum number of tweets to extract
            
        Returns:
            list: List of tweets from timeline
        """
        if not self.page:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        print("Crawling home timeline...")
        
        try:
            # Navigate to home
            await self.page.goto("https://x.com/home", wait_until="networkidle")
            print("Navigated to home timeline")
            
            # Extract tweets
            print("Extracting tweets from timeline...")
            tweets = await self.content_extractor.extract_tweets(max_tweets)
            
            return tweets
            
        except Exception as e:
            print(f"Error crawling timeline: {e}")
            return []
    
    async def scan_page_links(self):
        """
        Scan current page for all links
        
        Returns:
            list: List of URLs found on the page
        """
        if not self.link_scanner:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        return await self.link_scanner.scan_links()
    
    async def scan_tweet_links(self):
        """
        Scan current page for tweet links
        
        Returns:
            list: List of tweet URLs found on the page
        """
        if not self.link_scanner:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        return await self.link_scanner.scan_tweet_links()
    
    async def follow_links_and_crawl(self, max_pages=5):
        """
        Follow links found on pages and crawl content
        
        Args:
            max_pages (int): Maximum number of pages to crawl
            
        Returns:
            list: List of crawled page data
        """
        if not self.page or not self.link_scanner or not self.content_extractor:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        print(f"Following links and crawling up to {max_pages} pages...")
        crawled_pages = []
        visited_urls = set()
        
        try:
            # Start with current page
            current_url = self.page.url
            visited_urls.add(current_url)
            
            # Scan for links
            links = await self.scan_tweet_links()
            print(f"Found {len(links)} links to follow")
            
            # Follow links and crawl content
            for i, url in enumerate(links):
                if i >= max_pages:
                    break
                
                if url in visited_urls:
                    continue
                
                print(f"Crawling page {i+1}/{min(max_pages, len(links))}: {url}")
                visited_urls.add(url)
                
                try:
                    # Navigate to the URL
                    await self.page.goto(url, wait_until="networkidle")
                    
                    # Extract content
                    content = await self.content_extractor.extract_page_content()
                    metadata = await self.link_scanner.get_page_metadata()
                    
                    page_data = {
                        'url': url,
                        'content': content,
                        'metadata': metadata
                    }
                    
                    crawled_pages.append(page_data)
                    
                    # Scan for more links on this page
                    new_links = await self.scan_tweet_links()
                    print(f"Found {len(new_links)} additional links on this page")
                    
                except Exception as e:
                    print(f"Error crawling page {url}: {e}")
                    continue
            
            print(f"Completed crawling {len(crawled_pages)} pages")
            return crawled_pages
            
        except Exception as e:
            print(f"Error in follow_links_and_crawl: {e}")
            return []
    
    async def close(self):
        """Close browser and cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("Browser closed and resources cleaned up.")
    
    async def crawl_home_and_format(self, max_tweets=20):
        """
        Crawl home timeline and format content as markdown
        
        Args:
            max_tweets (int): Maximum number of tweets to extract
            
        Returns:
            dict: Formatted content including raw data and markdown
        """
        if not self.page:
            raise Exception("Crawler not initialized. Call initialize() first.")
        
        print("Crawling home timeline and formatting content...")
        
        try:
            # Navigate to home
            await self.page.goto("https://x.com/home", wait_until="networkidle")
            print("Navigated to home timeline")
            
            # Extract tweets
            print("Extracting tweets from timeline...")
            tweets = await self.content_extractor.extract_tweets(max_tweets)
            
            # Format content as markdown
            markdown_content = self._format_tweets_as_markdown(tweets)
            
            result = {
                'tweets': tweets,
                'formatted_content': markdown_content,
                'url': "https://x.com/home"
            }
            
            return result
            
        except Exception as e:
            print(f"Error crawling and formatting timeline: {e}")
            return {}

    def _format_tweets_as_markdown(self, tweets):
        """
        Format tweets as markdown content
        
        Args:
            tweets (list): List of tweet dictionaries
            
        Returns:
            str: Formatted markdown content
        """
        markdown_lines = ["# X.com Home Timeline", ""]
        
        for i, tweet in enumerate(tweets, 1):
            markdown_lines.append(f"## Tweet {i}")
            markdown_lines.append(f"**Author**: {tweet.get('author_name', 'Unknown')} ({tweet.get('author_username', 'N/A')})")
            markdown_lines.append(f"**Timestamp**: {tweet.get('timestamp', 'N/A')}")
            markdown_lines.append("")
            markdown_lines.append(tweet.get('text', ''))
            markdown_lines.append("")
            
            # Add metrics
            metrics = tweet.get('metrics', {})
            if metrics:
                markdown_lines.append("**Engagement Metrics**:")
                if 'replies' in metrics:
                    markdown_lines.append(f"- Replies: {metrics['replies']}")
                if 'retweets' in metrics:
                    markdown_lines.append(f"- Retweets: {metrics['retweets']}")
                if 'likes' in metrics:
                    markdown_lines.append(f"- Likes: {metrics['likes']}")
                markdown_lines.append("")
            
            markdown_lines.append("---")
            markdown_lines.append("")
        
        return "\n".join(markdown_lines)

# Example usage
async def main():
    """Example usage of the main crawler"""
    crawler = XComCrawler()
    
    try:
        # Initialize crawler
        await crawler.initialize()
        
        # Example 1: Crawl a profile
        print("\n--- Crawling Profile ---")
        profile_data = await crawler.crawl_profile("https://x.com/Twitter", max_tweets=5)
        print(f"Extracted {len(profile_data.get('tweets', []))} tweets from profile")
        
        # Example 2: Crawl timeline
        print("\n--- Crawling Timeline ---")
        timeline_tweets = await crawler.crawl_timeline(max_tweets=5)
        print(f"Extracted {len(timeline_tweets)} tweets from timeline")
        
        # Example 3: Scan links
        print("\n--- Scanning Links ---")
        links = await crawler.scan_page_links()
        print(f"Found {len(links)} links on current page")
        
        # Example 4: Follow links and crawl
        print("\n--- Following Links ---")
        crawled_pages = await crawler.follow_links_and_crawl(max_pages=3)
        print(f"Crawled {len(crawled_pages)} additional pages")
        
        # Keep browser open for further use
        print("\nBrowser session maintained. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Uncomment to close browser when done
        # await crawler.close()
        pass


if __name__ == "__main__":
    asyncio.run(main())
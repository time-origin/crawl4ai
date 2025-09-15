# crawl4ai/crawlers/x_com/usage_example.py
"""
Usage example for the ProductionXCrawler
"""

import asyncio
from crawl4ai.crawlers.x_com.production_crawler import ProductionXCrawler


async def example_usage():
    """
    Example of how to use the ProductionXCrawler
    """
    print("=== Production X.com Crawler Usage Example ===")
    
    # Initialize crawler
    crawler = ProductionXCrawler()
    
    try:
        # Perform login (this will keep the browser open)
        print("1. Performing login...")
        await crawler.login()
        print("   ✅ Login successful!")
        
        # Example 1: Scan links on home page
        print("\n2. Scanning links on home page...")
        links = await crawler.scan_page_links()
        print(f"   Found {len(links)} links")
        
        # Example 2: Get page content
        print("\n3. Getting page content...")
        content = await crawler.get_page_content()
        print(f"   Page title: {content.get('title', 'N/A')}")
        print(f"   Current URL: {content.get('url', 'N/A')}")
        print(f"   Content length: {content.get('content_length', 0)} characters")
        
        # Example 3: Navigate to a specific page and crawl
        print("\n4. Navigating to Twitter profile...")
        result = await crawler.navigate_and_crawl("https://x.com/Twitter")
        print(f"   Crawled profile page with {len(result.get('links', []))} links")
        
        # Keep browser open for further operations
        print("\n✅ Example completed!")
        print("💡 Browser session is still active")
        print("💡 You can continue using the crawler for more operations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close browser when done
        await crawler.close()
        print("✅ Resources cleaned up")


# Simple continuous crawler example
async def continuous_crawling_example():
    """
    Example of continuous crawling operations
    """
    print("=== Continuous Crawling Example ===")
    
    crawler = ProductionXCrawler()
    
    try:
        # Login and keep session
        await crawler.login()
        print("✅ Logged in and session maintained")
        
        # Start crawling loop
        urls_to_crawl = [
            "https://x.com/Twitter",
            "https://x.com/explore"
        ]
        
        for url in urls_to_crawl:
            print(f"\n🔍 Crawling: {url}")
            result = await crawler.navigate_and_crawl(url)
            print(f"   Found {len(result.get('links', []))} links")
            
            # Brief pause between requests
            await asyncio.sleep(2)
        
        print("\n✅ Continuous crawling completed!")
        
    except Exception as e:
        print(f"❌ Error during continuous crawling: {e}")
    finally:
        await crawler.close()


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
    
    # Uncomment the next line to run continuous crawling example
    # asyncio.run(continuous_crawling_example())
# crawl4ai/crawlers/x_com/crawl_home_example.py
"""
Example of crawling X.com home timeline and formatting content
"""

import asyncio
import json
from crawl4ai.crawlers.x_com.main_crawler import XComCrawler


async def crawl_home_and_format_example():
    """
    Example of crawling home timeline and formatting content as markdown
    """
    print("=== X.com Home Timeline Crawler and Formatter ===")
    
    # Initialize crawler
    crawler = XComCrawler()
    
    try:
        # Perform login and initialization
        print("1. Initializing crawler with authentication...")
        await crawler.initialize()
        print("   ✅ Authentication successful!")
        
        # Crawl home timeline and format content
        print("\n2. Crawling home timeline and formatting content...")
        result = await crawler.crawl_home_and_format(max_tweets=10)
        
        # Display results
        print(f"   Extracted {len(result.get('tweets', []))} tweets")
        print(f"   Formatted content length: {len(result.get('formatted_content', ''))} characters")
        
        # Save formatted content to file
        formatted_content = result.get('formatted_content', '')
        if formatted_content:
            with open('x_com_home_content.md', 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            print("   ✅ Formatted content saved to 'x_com_home_content.md'")
        
        # Save raw data to JSON file
        tweets_data = result.get('tweets', [])
        if tweets_data:
            with open('x_com_home_raw_data.json', 'w', encoding='utf-8') as f:
                json.dump(tweets_data, f, indent=2, ensure_ascii=False)
            print("   ✅ Raw data saved to 'x_com_home_raw_data.json'")
        
        print("\n✅ Home timeline crawling and formatting completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close browser when done
        await crawler.close()
        print("✅ Resources cleaned up")


if __name__ == "__main__":
    # Run the example
    asyncio.run(crawl_home_and_format_example())
# crawl4ai/crawlers/x_com/run.py
"""
Production entry point for X.com crawler
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai.crawlers.x_com.main_crawler import XComCrawler


async def main():
    """Production entry point for X.com crawler"""
    print("🚀 Starting X.com Crawler")
    
    crawler = XComCrawler()
    
    try:
        # Initialize crawler with authentication
        await crawler.initialize()
        print("✅ Authentication successful")
        
        # Keep the crawler running
        print("⏳ Crawler is running. Press Ctrl+C to stop.")
        print("💡 Browser session is maintained for continuous operations.")
        
        # Keep running indefinitely until interrupted
        while True:
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
    asyncio.run(main())
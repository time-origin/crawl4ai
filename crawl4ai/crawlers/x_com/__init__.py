"""
X.com Crawler Package
=====================

This package provides tools for crawling and extracting content from X.com (formerly Twitter).

Features:
- Automated login to X.com
- Profile scraping
- Timeline crawling
- Link scanning
- Content extraction and formatting

Main Components:
- XCrawler: Core crawler with login functionality
- XComCrawler: Main orchestrator for all crawling operations
- XComContentExtractor: Handles content extraction from pages
- XComLinkScanner: Scans pages for links

Usage:
1. Set up your credentials in a .env file:
   X_USERNAME=your_username
   X_PASSWORD=your_password

2. Run the crawler:
   python -m crawl4ai.crawlers.x_com.run

3. For custom crawling:
   from crawl4ai.crawlers.x_com.main_crawler import XComCrawler
   
   crawler = XComCrawler()
   await crawler.initialize()
   result = await crawler.crawl_home_and_format(max_tweets=20)
"""

__version__ = "0.1.0"
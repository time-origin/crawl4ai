# crawl4ai/crawlers/x_com/link_scanner.py
"""
X.com Link Scanner Module
Handles scanning and extraction of links from X.com pages
"""

import asyncio
from urllib.parse import urljoin, urlparse


class XComLinkScanner:
    """Handles scanning and extraction of links from X.com pages"""
    
    def __init__(self, page):
        """Initialize with a page object"""
        self.page = page
    
    async def scan_links(self):
        """
        Scan current page for all links
        
        Returns:
            list: List of unique URLs found on the page
        """
        print("Scanning page for links...")
        urls = set()
        
        try:
            # Find all anchor tags with href attributes
            link_elements = await self.page.query_selector_all('a[href]')
            
            for element in link_elements:
                href = await element.get_attribute('href')
                if href:
                    # Convert relative URLs to absolute URLs
                    absolute_url = urljoin(self.page.url, href)
                    
                    # Filter for X.com URLs only
                    if self._is_valid_xcom_url(absolute_url):
                        urls.add(absolute_url)
            
            print(f"Found {len(urls)} unique links")
            return list(urls)
            
        except Exception as e:
            print(f"Error scanning links: {e}")
            return []
    
    async def scan_tweet_links(self):
        """
        Scan current page specifically for tweet links
        
        Returns:
            list: List of tweet URLs found on the page
        """
        print("Scanning page for tweet links...")
        tweet_urls = set()
        
        try:
            # Find all tweet articles
            tweet_elements = await self.page.query_selector_all('article[data-testid="tweet"]')
            
            for tweet_element in tweet_elements:
                # Find links within each tweet
                link_elements = await tweet_element.query_selector_all('a[href]')
                
                for element in link_elements:
                    href = await element.get_attribute('href')
                    if href:
                        # Convert relative URLs to absolute URLs
                        absolute_url = urljoin(self.page.url, href)
                        
                        # Check if it's a tweet URL
                        if self._is_tweet_url(absolute_url):
                            tweet_urls.add(absolute_url)
            
            print(f"Found {len(tweet_urls)} tweet links")
            return list(tweet_urls)
            
        except Exception as e:
            print(f"Error scanning tweet links: {e}")
            return []
    
    def _is_valid_xcom_url(self, url):
        """Check if URL is a valid X.com URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.endswith('x.com') and not url.startswith('mailto:')
        except:
            return False
    
    def _is_tweet_url(self, url):
        """Check if URL is a tweet URL"""
        try:
            parsed = urlparse(url)
            if not parsed.netloc.endswith('x.com'):
                return False
            
            # Tweet URLs typically have the pattern: /username/status/tweet_id
            path_parts = parsed.path.strip('/').split('/')
            return len(path_parts) >= 3 and path_parts[1] == 'status'
        except:
            return False
    
    async def get_page_metadata(self):
        """
        Extract metadata from the current page
        
        Returns:
            dict: Page metadata including title, description, etc.
        """
        try:
            title = await self.page.title()
            url = self.page.url
            
            metadata = {
                'title': title,
                'url': url,
                'links_count': 0,
                'tweet_links_count': 0
            }
            
            # Get all links
            all_links = await self.scan_links()
            metadata['links_count'] = len(all_links)
            
            # Get tweet links
            tweet_links = await self.scan_tweet_links()
            metadata['tweet_links_count'] = len(tweet_links)
            
            return metadata
            
        except Exception as e:
            print(f"Error getting page metadata: {e}")
            return {}


# Example usage
async def main():
    """Example usage - would require an active page object"""
    print("Link Scanner module ready for use")


if __name__ == "__main__":
    asyncio.run(main())
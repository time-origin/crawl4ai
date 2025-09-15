# crawl4ai/crawlers/x_com/content_extractor.py
"""
X.com Content Extractor Module
Handles extraction of content from X.com pages
"""

import asyncio
import json


class XComContentExtractor:
    """Handles extraction of content from X.com pages"""
    
    def __init__(self, page):
        """Initialize with a page object"""
        self.page = page
    
    async def extract_tweets(self, max_tweets=20):
        """
        Extract tweets from the current page
        
        Args:
            max_tweets (int): Maximum number of tweets to extract
            
        Returns:
            list: List of tweet dictionaries
        """
        print(f"Extracting up to {max_tweets} tweets...")
        tweets = []
        
        try:
            # Wait for tweets to load
            await self.page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
            
            # Get all tweet articles
            tweet_elements = await self.page.query_selector_all('article[data-testid="tweet"]')
            
            for i, tweet_element in enumerate(tweet_elements):
                if i >= max_tweets:
                    break
                
                try:
                    tweet_data = await self._extract_tweet_data(tweet_element)
                    if tweet_data:
                        tweets.append(tweet_data)
                        print(f"Extracted tweet {i+1}/{max_tweets}")
                except Exception as e:
                    print(f"Error extracting tweet {i+1}: {e}")
                    continue
            
            print(f"Successfully extracted {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            print(f"Error extracting tweets: {e}")
            return []
    
    async def _extract_tweet_data(self, tweet_element):
        """
        Extract data from a single tweet element
        
        Args:
            tweet_element: Playwright element handle for a tweet
            
        Returns:
            dict: Tweet data or None if extraction failed
        """
        try:
            tweet_data = {}
            
            # Extract tweet text
            text_element = await tweet_element.query_selector('[data-testid="tweetText"]')
            if text_element:
                tweet_data["text"] = await text_element.inner_text()
            else:
                tweet_data["text"] = ""
            
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
            
            return tweet_data
            
        except Exception as e:
            print(f"Error extracting tweet data: {e}")
            return None
    
    async def extract_profile_info(self):
        """
        Extract profile information from a user profile page
        
        Returns:
            dict: Profile information
        """
        try:
            profile_data = {}
            
            # Extract display name
            name_element = await self.page.query_selector('div[data-testid="UserName"] div[dir="ltr"] > span')
            if name_element:
                profile_data["display_name"] = await name_element.inner_text()
            
            # Extract username
            username_element = await self.page.query_selector('div[data-testid="UserDescription"]')
            if username_element:
                # This is a bit tricky, we need to find the username in the URL or header
                url = self.page.url
                if '/status/' in url:
                    # Extract username from URL
                    parts = url.split('/')
                    for i, part in enumerate(parts):
                        if part == 'x.com' and i+1 < len(parts):
                            profile_data["username"] = parts[i+1]
                            break
            
            # Extract bio
            bio_element = await self.page.query_selector('div[data-testid="UserDescription"]')
            if bio_element:
                profile_data["bio"] = await bio_element.inner_text()
            
            # Extract follower counts
            follower_elements = await self.page.query_selector_all('a[href*="followers"]')
            for element in follower_elements:
                text = await element.inner_text()
                if 'Followers' in text:
                    profile_data["followers"] = text.strip()
            
            following_elements = await self.page.query_selector_all('a[href*="following"]')
            for element in following_elements:
                text = await element.inner_text()
                if 'Following' in text:
                    profile_data["following"] = text.strip()
            
            return profile_data
            
        except Exception as e:
            print(f"Error extracting profile info: {e}")
            return {}
    
    async def extract_page_content(self):
        """
        Extract general page content
        
        Returns:
            dict: Page content including title, text, etc.
        """
        try:
            title = await self.page.title()
            content = await self.page.inner_text('body')
            
            page_data = {
                'title': title,
                'url': self.page.url,
                'content': content[:1000] + '...' if len(content) > 1000 else content,
                'word_count': len(content.split())
            }
            
            return page_data
            
        except Exception as e:
            print(f"Error extracting page content: {e}")
            return {}


# Example usage
async def main():
    """Example usage - would require an active page object"""
    print("Content Extractor module ready for use")


if __name__ == "__main__":
    asyncio.run(main())
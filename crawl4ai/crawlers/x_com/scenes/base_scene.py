# crawl4ai/crawlers/x_com/scenes/base_scene.py

from abc import ABC, abstractmethod
from playwright.async_api import Page


class BaseScene(ABC):
    """
    An abstract base class for a scraping scene on X.com.

    Each scene represents a specific page or view (e.g., home timeline, 
    search results, explore page) and contains the logic to navigate to
    and extract data from that page.
    """

    @abstractmethod
    async def scrape(self, page: Page, **kwargs) -> list:
        """
        The main method to perform the scraping for the specific scene.

        This method will be called by the main crawler and will be passed an
        authenticated Playwright Page object.

        Args:
            page (Page): An authenticated Playwright Page object.
            **kwargs: A dictionary for any extra parameters the scene might need,
                      such as a 'query' for a search scene.

        Returns:
            list: A list of dictionaries, where each dictionary represents
                  a scraped item (e.g., a tweet).
        """
        pass

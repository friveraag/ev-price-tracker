import asyncio
import random
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from playwright.async_api import async_playwright, Page, Browser


class ListingData:
    """Data class for a scraped listing."""
    def __init__(
        self,
        external_id: str,
        price: int,
        year: int = None,
        mileage: int = None,
        location: str = None,
        url: str = None
    ):
        self.external_id = external_id
        self.price = price
        self.year = year
        self.mileage = mileage
        self.location = location
        self.url = url

    def __repr__(self):
        return f"ListingData(id={self.external_id}, price=${self.price}, year={self.year})"


class BaseScraper(ABC):
    """Base class for all scrapers."""

    SOURCE_NAME = "base"
    BASE_URL = ""

    def __init__(self, zip_code: str = "90210", radius: int = 100):
        self.zip_code = zip_code
        self.radius = radius
        self.browser: Browser = None
        self.page: Page = None

    async def __aenter__(self):
        """Set up browser context."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch(
            headless=True
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser context."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to avoid detection."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @abstractmethod
    def build_search_url(self, make: str, model: str) -> str:
        """Build the search URL for a specific make/model."""
        pass

    @abstractmethod
    async def scrape_listings(self, make: str, model: str) -> AsyncGenerator[ListingData, None]:
        """Scrape listings for a specific make/model."""
        pass

    async def scroll_page(self, scroll_count: int = 3):
        """Scroll down the page to load lazy content."""
        for _ in range(scroll_count):
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await self.random_delay(0.5, 1.0)

    def parse_price(self, price_text: str) -> int:
        """Parse price string to integer."""
        if not price_text:
            return 0
        # Remove currency symbols, commas, and whitespace
        cleaned = "".join(c for c in price_text if c.isdigit())
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def parse_mileage(self, mileage_text: str) -> int:
        """Parse mileage string to integer."""
        if not mileage_text:
            return None
        cleaned = "".join(c for c in mileage_text if c.isdigit())
        try:
            return int(cleaned)
        except ValueError:
            return None

    def parse_year(self, year_text: str) -> int:
        """Parse year from text."""
        if not year_text:
            return None
        # Look for 4-digit year
        import re
        match = re.search(r"20[0-2]\d", year_text)
        if match:
            return int(match.group())
        return None

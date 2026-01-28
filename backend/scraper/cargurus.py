import re
from typing import AsyncGenerator
from urllib.parse import quote
from .base import BaseScraper, ListingData


class CarGurusScraper(BaseScraper):
    """Scraper for CarGurus.com"""

    SOURCE_NAME = "cargurus"
    BASE_URL = "https://www.cargurus.com"

    def build_search_url(self, make: str, model: str) -> str:
        """Build CarGurus search URL using text search."""
        # Use the Cars search page with make/model in the URL path
        make_slug = make.lower()
        model_slug = model.lower().replace(" ", "-").replace(".", "")

        return (
            f"{self.BASE_URL}/Cars/l-Used-{make}-{model_slug.replace('-', '_')}-"
            f"d210?zip={self.zip_code}&distance={self.radius}"
            f"&searchId=&sort=BEST_MATCH&type=USED"
        )

    async def scrape_listings(self, make: str, model: str) -> AsyncGenerator[ListingData, None]:
        """Scrape listings from CarGurus."""
        url = self.build_search_url(make, model)
        print(f"[CarGurus] Scraping {make} {model}: {url}")

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=45000)
            await self.random_delay(2, 3)

            # Scroll to load more listings
            await self.scroll_page(2)
            await self.random_delay(1, 2)

            # Get page content to analyze
            content = await self.page.content()

            # Find all listing links with prices using regex on page content
            # Pattern for listing URLs and prices
            listing_pattern = r'href="(/Cars/[^"]*VIN[^"]*)"[^>]*>.*?(\$[\d,]+)'

            # Try multiple selectors for listing cards
            selectors = [
                'article[data-cg-ft="car-blade"]',
                '[data-testid="srp-tile-wrapper"]',
                '.cg-dealFinder-result-wrap',
                'article',
                'div[class*="listing"]',
                'a[href*="/Cars/"][href*="VIN"]'
            ]

            listings = []
            for selector in selectors:
                listings = await self.page.query_selector_all(selector)
                if listings:
                    print(f"[CarGurus] Found {len(listings)} elements with selector: {selector}")
                    break

            if not listings:
                print(f"[CarGurus] No listings found for {make} {model}")
                return

            count = 0
            for listing in listings[:30]:  # Limit to 30 per scrape
                try:
                    listing_data = await self._parse_listing(listing, make, model)
                    if listing_data and listing_data.price > 5000:
                        count += 1
                        yield listing_data
                except Exception as e:
                    continue

            print(f"[CarGurus] Scraped {count} valid listings for {make} {model}")

        except Exception as e:
            print(f"[CarGurus] Error scraping {make} {model}: {e}")

    async def _parse_listing(self, listing, make: str, model: str) -> ListingData:
        """Parse a single listing element."""
        try:
            text_content = await listing.inner_text()
        except:
            return None

        # Skip if doesn't look like a car listing
        if len(text_content) < 20:
            return None

        # Try to get listing ID
        external_id = await listing.get_attribute("data-listing-id")
        if not external_id:
            external_id = await listing.get_attribute("id")
        if not external_id:
            external_id = f"cg-{abs(hash(text_content)) % 100000}"

        # Extract price from text
        price_match = re.search(r'\$[\d,]+', text_content)
        price = self.parse_price(price_match.group()) if price_match else 0

        if price == 0 or price > 500000:  # Sanity check
            return None

        # Extract year
        year = self.parse_year(text_content)

        # Verify this listing is for the right make/model
        text_lower = text_content.lower()
        if make.lower() not in text_lower or model.lower().split()[0] not in text_lower:
            return None

        # Extract mileage
        mileage_match = re.search(r'([\d,]+)\s*mi', text_content, re.IGNORECASE)
        mileage = self.parse_mileage(mileage_match.group(1)) if mileage_match else None

        # Get URL
        link_el = await listing.query_selector('a[href*="/Cars/"]')
        if not link_el:
            link_el = listing if await listing.get_attribute("href") else None

        href = await link_el.get_attribute("href") if link_el else ""
        url = f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href

        # Extract location if present
        location_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})', text_content)
        location = location_match.group(1) if location_match else None

        return ListingData(
            external_id=external_id,
            price=price,
            year=year,
            mileage=mileage,
            location=location,
            url=url
        )

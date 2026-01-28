import re
from typing import AsyncGenerator
from .base import BaseScraper, ListingData


class AutotraderScraper(BaseScraper):
    """Scraper for Autotrader.com"""

    SOURCE_NAME = "autotrader"
    BASE_URL = "https://www.autotrader.com"

    # Model name mappings for Autotrader URLs
    MAKE_SLUGS = {
        "Tesla": "TESLA",
        "Ford": "FORD",
        "Chevrolet": "CHEV",
        "Rivian": "RIVIAN",
        "Hyundai": "HYUND",
        "Kia": "KIA",
        "BMW": "BMW",
        "Mercedes": "MB",
        "Volkswagen": "VOLKS",
    }

    MODEL_SLUGS = {
        "Model 3": "MODEL3",
        "Model Y": "MODELY",
        "Model S": "MODELS",
        "Model X": "MODELX",
        "Mustang Mach-E": "MUSTANGMACHE",
        "F-150 Lightning": "F150LIGHTNING",
        "Bolt EV": "BOLTEV",
        "Bolt EUV": "BOLTEUV",
        "Equinox EV": "EQUINOXEV",
        "R1T": "R1T",
        "R1S": "R1S",
        "Ioniq 5": "IONIQ5",
        "Ioniq 6": "IONIQ6",
        "EV6": "EV6",
        "EV9": "EV9",
        "i4": "I4",
        "iX": "IX",
        "EQS": "EQSCLASS",
        "EQE": "EQECLASS",
        "ID.4": "ID4",
    }

    def build_search_url(self, make: str, model: str) -> str:
        """Build Autotrader search URL."""
        make_slug = self.MAKE_SLUGS.get(make, make.upper())
        model_slug = self.MODEL_SLUGS.get(model, model.upper().replace(" ", "").replace("-", "").replace(".", ""))

        return (
            f"{self.BASE_URL}/cars-for-sale/all-cars/{make.lower()}/{model.lower().replace(' ', '-')}"
            f"?zip={self.zip_code}&searchRadius={self.radius}&isNewSearch=true&marketExtension=include"
            f"&sortBy=relevance&numRecords=25"
        )

    async def scrape_listings(self, make: str, model: str) -> AsyncGenerator[ListingData, None]:
        """Scrape listings from Autotrader."""
        url = self.build_search_url(make, model)
        print(f"[Autotrader] Scraping {make} {model}: {url}")

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self.random_delay(2, 4)

            # Wait for listings to load
            await self.page.wait_for_selector('[data-testid="listing-card"], .inventory-listing, [class*="ListingCard"]', timeout=15000)

            # Scroll to load more listings
            await self.scroll_page(3)

            # Try multiple selectors for listing cards
            listings = await self.page.query_selector_all('[data-testid="listing-card"]')
            if not listings:
                listings = await self.page.query_selector_all('.inventory-listing')
            if not listings:
                listings = await self.page.query_selector_all('[class*="ListingCard"]')

            print(f"[Autotrader] Found {len(listings)} listings for {make} {model}")

            for listing in listings[:30]:  # Limit to 30 per scrape
                try:
                    listing_data = await self._parse_listing(listing)
                    if listing_data and listing_data.price > 5000:
                        yield listing_data
                except Exception as e:
                    print(f"[Autotrader] Error parsing listing: {e}")
                    continue

        except Exception as e:
            print(f"[Autotrader] Error scraping {make} {model}: {e}")

    async def _parse_listing(self, listing) -> ListingData:
        """Parse a single listing element."""
        # Try to get listing ID from data attribute or link
        external_id = await listing.get_attribute("data-listing-id")
        if not external_id:
            external_id = await listing.get_attribute("id")

        # Get price
        price_el = await listing.query_selector('[data-testid="listing-price"], .first-price, [class*="Price"]')
        price_text = await price_el.inner_text() if price_el else ""
        price = self.parse_price(price_text)

        if price == 0:
            return None

        # Get title
        title_el = await listing.query_selector('[data-testid="listing-title"], .text-bold, h2, h3')
        title_text = await title_el.inner_text() if title_el else ""
        year = self.parse_year(title_text)

        # Get mileage
        mileage_el = await listing.query_selector('[data-testid="listing-mileage"], .text-muted, [class*="mileage"]')
        mileage_text = await mileage_el.inner_text() if mileage_el else ""
        mileage = self.parse_mileage(mileage_text)

        # Get location
        location_el = await listing.query_selector('[data-testid="listing-location"], .dealer-name, [class*="Location"]')
        location = await location_el.inner_text() if location_el else None

        # Get URL
        link_el = await listing.query_selector('a[href*="/cars-for-sale/"]')
        href = await link_el.get_attribute("href") if link_el else ""
        url = f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href

        if not external_id and url:
            # Extract ID from URL
            match = re.search(r"/(\d+)(?:\?|$)", url)
            if match:
                external_id = match.group(1)

        if not external_id:
            external_id = f"at-{hash(title_text + str(price)) % 100000}"

        return ListingData(
            external_id=external_id,
            price=price,
            year=year,
            mileage=mileage,
            location=location,
            url=url
        )

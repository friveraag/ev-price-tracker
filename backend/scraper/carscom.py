import re
from typing import AsyncGenerator
from .base import BaseScraper, ListingData


class CarsComScraper(BaseScraper):
    """Scraper for Cars.com"""

    SOURCE_NAME = "cars.com"
    BASE_URL = "https://www.cars.com"

    # Make/model slugs for Cars.com
    MAKE_SLUGS = {
        "Tesla": "tesla",
        "Ford": "ford",
        "Chevrolet": "chevrolet",
        "Rivian": "rivian",
        "Hyundai": "hyundai",
        "Kia": "kia",
        "BMW": "bmw",
        "Mercedes": "mercedes_benz",
        "Volkswagen": "volkswagen",
    }

    MODEL_SLUGS = {
        ("Tesla", "Model 3"): "tesla-model_3",
        ("Tesla", "Model Y"): "tesla-model_y",
        ("Tesla", "Model S"): "tesla-model_s",
        ("Tesla", "Model X"): "tesla-model_x",
        ("Ford", "Mustang Mach-E"): "ford-mustang_mach_e",
        ("Ford", "F-150 Lightning"): "ford-f_150_lightning",
        ("Chevrolet", "Bolt EV"): "chevrolet-bolt_ev",
        ("Chevrolet", "Bolt EUV"): "chevrolet-bolt_euv",
        ("Chevrolet", "Equinox EV"): "chevrolet-equinox_ev",
        ("Rivian", "R1T"): "rivian-r1t",
        ("Rivian", "R1S"): "rivian-r1s",
        ("Hyundai", "Ioniq 5"): "hyundai-ioniq_5",
        ("Hyundai", "Ioniq 6"): "hyundai-ioniq_6",
        ("Kia", "EV6"): "kia-ev6",
        ("Kia", "EV9"): "kia-ev9",
        ("BMW", "i4"): "bmw-i4",
        ("BMW", "iX"): "bmw-ix",
        ("Mercedes", "EQS"): "mercedes_benz-eqs",
        ("Mercedes", "EQE"): "mercedes_benz-eqe",
        ("Volkswagen", "ID.4"): "volkswagen-id_4",
    }

    def build_search_url(self, make: str, model: str) -> str:
        """Build Cars.com search URL."""
        make_slug = self.MAKE_SLUGS.get(make, make.lower())
        model_slug = self.MODEL_SLUGS.get((make, model))

        if not model_slug:
            model_slug = f"{make_slug}-{model.lower().replace(' ', '_').replace('-', '_').replace('.', '_')}"

        return (
            f"{self.BASE_URL}/shopping/results/"
            f"?stock_type=used&makes[]={make_slug}&models[]={model_slug}"
            f"&zip={self.zip_code}&maximum_distance={self.radius}"
        )

    async def scrape_listings(self, make: str, model: str) -> AsyncGenerator[ListingData, None]:
        """Scrape listings from Cars.com."""
        url = self.build_search_url(make, model)
        print(f"[Cars.com] Scraping {make} {model}: {url}")

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self.random_delay(2, 4)

            # Scroll to load more listings
            await self.scroll_page(2)

            # Find vehicle cards
            listings = await self.page.query_selector_all(".vehicle-card")
            print(f"[Cars.com] Found {len(listings)} listings for {make} {model}")

            count = 0
            for listing in listings[:30]:  # Limit to 30 per scrape
                try:
                    listing_data = await self._parse_listing(listing, make, model)
                    if listing_data and listing_data.price > 5000:
                        count += 1
                        yield listing_data
                except Exception as e:
                    print(f"[Cars.com] Error parsing listing: {e}")
                    continue

            print(f"[Cars.com] Scraped {count} valid listings for {make} {model}")

        except Exception as e:
            print(f"[Cars.com] Error scraping {make} {model}: {e}")

    async def _parse_listing(self, listing, make: str, model: str) -> ListingData:
        """Parse a single listing element."""
        try:
            text_content = await listing.inner_text()
        except:
            return None

        if len(text_content) < 20:
            return None

        # Get listing ID
        external_id = await listing.get_attribute("data-listing-id")
        if not external_id:
            external_id = await listing.get_attribute("id")
        if not external_id:
            external_id = f"cc-{abs(hash(text_content)) % 100000}"

        # Extract price
        price_match = re.search(r'\$[\d,]+', text_content)
        price = self.parse_price(price_match.group()) if price_match else 0

        if price == 0 or price > 500000:
            return None

        # Extract year
        year = self.parse_year(text_content)

        # Verify it's the right make/model
        text_lower = text_content.lower()
        if make.lower() not in text_lower:
            return None

        # Extract mileage
        mileage_match = re.search(r'([\d,]+)\s*mi', text_content, re.IGNORECASE)
        mileage = self.parse_mileage(mileage_match.group(1)) if mileage_match else None

        # Get URL
        link_el = await listing.query_selector('a[href*="/vehicledetail/"]')
        href = await link_el.get_attribute("href") if link_el else ""
        url = f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href

        # Extract location
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

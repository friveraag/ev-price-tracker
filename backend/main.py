import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db,
    get_all_models,
    get_model_by_id,
    get_price_history,
    get_listings,
    get_stats,
    get_settings,
    update_setting,
    save_listing,
    update_price_history,
)
from scraper import CarGurusScraper, AutotraderScraper, CarsComScraper


# Track scraping state
scrape_status = {
    "is_running": False,
    "current_model": None,
    "progress": 0,
    "total": 0,
    "errors": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="EV Price Tracker API",
    description="Track used EV prices across multiple listing sites",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SettingsUpdate(BaseModel):
    zip_code: Optional[str] = None
    search_radius: Optional[int] = None


@app.get("/api/models")
async def list_models():
    """Get all tracked EV models."""
    models = await get_all_models()
    return {"models": models}


@app.get("/api/models/{model_id}")
async def get_model(model_id: int):
    """Get a specific model."""
    model = await get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.get("/api/models/{model_id}/prices")
async def get_model_prices(model_id: int, days: int = 90):
    """Get price history for a model."""
    model = await get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    history = await get_price_history(model_id, days)
    return {
        "model": model,
        "history": history
    }


@app.get("/api/models/{model_id}/listings")
async def get_model_listings(
    model_id: int,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "price",
    sort_order: str = "asc"
):
    """Get current listings for a model."""
    model = await get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    listings = await get_listings(model_id, limit, offset, sort_by, sort_order)
    return {
        "model": model,
        "listings": listings,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/stats")
async def get_dashboard_stats():
    """Get dashboard summary statistics."""
    stats = await get_stats()
    return stats


@app.get("/api/settings")
async def get_app_settings():
    """Get application settings."""
    settings = await get_settings()
    return settings


@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update application settings."""
    if settings.zip_code:
        await update_setting("zip_code", settings.zip_code)
    if settings.search_radius:
        await update_setting("search_radius", str(settings.search_radius))
    return await get_settings()


@app.get("/api/scrape/status")
async def get_scrape_status():
    """Get current scrape status."""
    return scrape_status


async def run_scrape(model_ids: list[int] = None):
    """Run scraping for specified models or all models."""
    global scrape_status

    if scrape_status["is_running"]:
        return

    scrape_status["is_running"] = True
    scrape_status["errors"] = []

    try:
        settings = await get_settings()
        zip_code = settings.get("zip_code", "90210")
        radius = int(settings.get("search_radius", "100"))

        models = await get_all_models()
        if model_ids:
            models = [m for m in models if m["id"] in model_ids]

        # Only using Cars.com for now (most reliable)
        scrapers = [
            (CarsComScraper, "cars.com"),
        ]

        scrape_status["total"] = len(models) * len(scrapers)
        scrape_status["progress"] = 0

        for model in models:
            model_id = model["id"]
            make = model["make"]
            model_name = model["model"]
            scrape_status["current_model"] = f"{make} {model_name}"

            for ScraperClass, source_name in scrapers:
                try:
                    async with ScraperClass(zip_code=zip_code, radius=radius) as scraper:
                        async for listing in scraper.scrape_listings(make, model_name):
                            await save_listing(
                                model_id=model_id,
                                source=source_name,
                                external_id=listing.external_id,
                                year=listing.year,
                                price=listing.price,
                                mileage=listing.mileage,
                                location=listing.location,
                                url=listing.url
                            )
                except Exception as e:
                    error_msg = f"Error scraping {make} {model_name} from {source_name}: {str(e)}"
                    print(error_msg)
                    scrape_status["errors"].append(error_msg)

                scrape_status["progress"] += 1
                await asyncio.sleep(0.1)  # Small delay between sources

            # Update price history after scraping all sources for this model
            await update_price_history(model_id)

    finally:
        scrape_status["is_running"] = False
        scrape_status["current_model"] = None
        scrape_status["progress"] = scrape_status["total"]


@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, model_id: Optional[int] = None):
    """Trigger a manual scrape."""
    if scrape_status["is_running"]:
        raise HTTPException(status_code=409, detail="Scrape already in progress")

    model_ids = [model_id] if model_id else None
    background_tasks.add_task(run_scrape, model_ids)

    return {"message": "Scrape started", "status": scrape_status}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

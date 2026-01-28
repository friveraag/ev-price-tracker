import aiosqlite
import os
from datetime import date, datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "prices.db")

# EV models to track
EV_MODELS = [
    ("Tesla", "Model 3"),
    ("Tesla", "Model Y"),
    ("Tesla", "Model S"),
    ("Tesla", "Model X"),
    ("Ford", "Mustang Mach-E"),
    ("Ford", "F-150 Lightning"),
    ("Chevrolet", "Bolt EV"),
    ("Chevrolet", "Bolt EUV"),
    ("Chevrolet", "Equinox EV"),
    ("Rivian", "R1T"),
    ("Rivian", "R1S"),
    ("Hyundai", "Ioniq 5"),
    ("Hyundai", "Ioniq 6"),
    ("Kia", "EV6"),
    ("Kia", "EV9"),
    ("BMW", "i4"),
    ("BMW", "iX"),
    ("Mercedes", "EQS"),
    ("Mercedes", "EQE"),
    ("Volkswagen", "ID.4"),
]


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database schema and seed data."""
    db = await get_db()
    try:
        # Create tables
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                UNIQUE(make, model)
            );

            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY,
                model_id INTEGER REFERENCES models(id),
                source TEXT NOT NULL,
                external_id TEXT,
                year INTEGER,
                price INTEGER,
                mileage INTEGER,
                location TEXT,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, external_id)
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY,
                model_id INTEGER REFERENCES models(id),
                date DATE NOT NULL,
                avg_price INTEGER,
                min_price INTEGER,
                max_price INTEGER,
                listing_count INTEGER,
                avg_mileage INTEGER,
                UNIQUE(model_id, date)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_listings_model_id ON listings(model_id);
            CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at);
            CREATE INDEX IF NOT EXISTS idx_price_history_model_date ON price_history(model_id, date);
        """)

        # Seed EV models
        for make, model in EV_MODELS:
            await db.execute(
                "INSERT OR IGNORE INTO models (make, model) VALUES (?, ?)",
                (make, model)
            )

        # Set default settings (Houston, TX area with 200 mile radius)
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("zip_code", "77001")
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("search_radius", "200")
        )

        await db.commit()
    finally:
        await db.close()


async def get_all_models():
    """Get all tracked EV models."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, make, model FROM models ORDER BY make, model"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_model_by_id(model_id: int):
    """Get a specific model by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, make, model FROM models WHERE id = ?",
            (model_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_price_history(model_id: int, days: int = 90):
    """Get price history for a model."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT date, avg_price, min_price, max_price, listing_count, avg_mileage
            FROM price_history
            WHERE model_id = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (model_id, days)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
    finally:
        await db.close()


async def get_listings(
    model_id: int,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "price",
    sort_order: str = "asc"
):
    """Get current listings for a model."""
    db = await get_db()
    try:
        valid_sort_columns = {"price", "mileage", "year", "scraped_at"}
        if sort_by not in valid_sort_columns:
            sort_by = "price"
        order = "ASC" if sort_order.lower() == "asc" else "DESC"

        cursor = await db.execute(
            f"""
            SELECT id, source, external_id, year, price, mileage, location, url, scraped_at
            FROM listings
            WHERE model_id = ?
            ORDER BY {sort_by} {order}
            LIMIT ? OFFSET ?
            """,
            (model_id, limit, offset)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_stats():
    """Get dashboard summary statistics."""
    db = await get_db()
    try:
        # Total listings
        cursor = await db.execute("SELECT COUNT(*) as count FROM listings")
        row = await cursor.fetchone()
        total_listings = row["count"]

        # Models with data
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT model_id) as count FROM listings"
        )
        row = await cursor.fetchone()
        models_with_data = row["count"]

        # Average price across all listings
        cursor = await db.execute(
            "SELECT AVG(price) as avg_price FROM listings WHERE price > 0"
        )
        row = await cursor.fetchone()
        avg_price = int(row["avg_price"]) if row["avg_price"] else 0

        # Last scrape time
        cursor = await db.execute(
            "SELECT MAX(scraped_at) as last_scrape FROM listings"
        )
        row = await cursor.fetchone()
        last_scrape = row["last_scrape"]

        # Top 5 cheapest models (by average price)
        cursor = await db.execute(
            """
            SELECT m.make, m.model, AVG(l.price) as avg_price, COUNT(*) as count
            FROM listings l
            JOIN models m ON l.model_id = m.id
            WHERE l.price > 0
            GROUP BY l.model_id
            ORDER BY avg_price ASC
            LIMIT 5
            """
        )
        rows = await cursor.fetchall()
        cheapest_models = [
            {
                "make": row["make"],
                "model": row["model"],
                "avg_price": int(row["avg_price"]),
                "count": row["count"]
            }
            for row in rows
        ]

        return {
            "total_listings": total_listings,
            "models_with_data": models_with_data,
            "avg_price": avg_price,
            "last_scrape": last_scrape,
            "cheapest_models": cheapest_models
        }
    finally:
        await db.close()


async def save_listing(
    model_id: int,
    source: str,
    external_id: str,
    year: Optional[int],
    price: int,
    mileage: Optional[int],
    location: Optional[str],
    url: str
):
    """Save a scraped listing."""
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT OR REPLACE INTO listings
            (model_id, source, external_id, year, price, mileage, location, url, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (model_id, source, external_id, year, price, mileage, location, url, datetime.utcnow())
        )
        await db.commit()
    finally:
        await db.close()


async def update_price_history(model_id: int):
    """Update price history aggregates for a model."""
    db = await get_db()
    try:
        today = date.today().isoformat()
        await db.execute(
            """
            INSERT OR REPLACE INTO price_history
            (model_id, date, avg_price, min_price, max_price, listing_count, avg_mileage)
            SELECT
                model_id,
                ?,
                AVG(price),
                MIN(price),
                MAX(price),
                COUNT(*),
                AVG(mileage)
            FROM listings
            WHERE model_id = ? AND price > 0
            GROUP BY model_id
            """,
            (today, model_id)
        )
        await db.commit()
    finally:
        await db.close()


async def get_settings():
    """Get all settings."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        await db.close()


async def update_setting(key: str, value: str):
    """Update a setting."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()
    finally:
        await db.close()

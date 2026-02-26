# Scrapers - Data Collection System

## Overview

Scrapers are background workers that collect product data from various sources and store them in the database. They run on a schedule inside the Docker container.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   eBay API      │     │   TCGdex API    │     │  Mock Scraper   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                         ┌───────▼───────┐
                         │    Worker     │
                         │  (worker.py)  │
                         └───────┬───────┘
                                 │
                         ┌───────▼───────┐
                         │  PostgreSQL   │
                         │   (products)  │
                         └───────────────┘
```

---

## Project Structure

```
scrapers/
├── worker.py           # Main entry point, scheduler
├── base.py             # BaseScraper class (all scrapers inherit from this)
├── mock_scraper.py     # Fake data for development
├── ebay.py             # eBay Browse API integration
├── tcgdex.py           # TCGdex API for Pokémon cards
├── reverb.py           # [Stub] Reverb API for instruments
├── discogs.py          # [Stub] Discogs API for vinyl/CDs
├── DATA_SOURCES.md     # Reference of all data sources
└── requirements.txt
```

---

## How It Works

### 1. Worker Startup (worker.py)

```python
def main():
    # 1. Wait for database to be ready
    time.sleep(10)
    
    # 2. Seed database on first run
    if os.getenv("SEED_DATABASE") == "true":
        seed_database()
    
    # 3. Schedule scrape job
    schedule.every(SCRAPE_INTERVAL).seconds.do(run_scrape_job)
    
    # 4. Run immediately, then loop
    run_scrape_job()
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### 2. Scrape Job Flow

```python
def run_scrape_job():
    all_products = []
    
    # Try eBay (if configured)
    if EBAY_CLIENT_ID:
        products = ebay_scraper.scrape_category("elettronica")
        all_products.extend(products)
    
    # Try TCGdex (free, no config needed)
    products = tcgdex_scraper.scrape_category("pokemon")
    all_products.extend(products)
    
    # Fallback to mock if no real data
    if not all_products:
        products = mock_scraper.scrape_category("auto")
        all_products.extend(products)
    
    # Save to database
    save_products(all_products)
```

---

## Base Scraper Class

All scrapers inherit from `BaseScraper`:

```python
class BaseScraper:
    SOURCE_NAME = "base"          # Override this
    BASE_URL = ""                 # Override this
    RATE_LIMIT_SECONDS = 1.0      # Time between requests
    
    def scrape_category(self, category: str, max_pages: int = 5) -> List[ScrapedProduct]:
        """Override this method."""
        raise NotImplementedError
    
    def scrape_search(self, query: str, max_results: int = 50) -> List[ScrapedProduct]:
        """Override this method."""
        raise NotImplementedError
    
    def _rate_limit(self):
        """Call this before each request."""
        time.sleep(self.RATE_LIMIT_SECONDS)
    
    def validate_product(self, product: ScrapedProduct) -> bool:
        """Check if product is valid."""
        return product.title and product.price_eur > 0
```

### ScrapedProduct Data Model

```python
@dataclass
class ScrapedProduct:
    source_url: str      # Original listing URL
    source_name: str     # "ebay", "tcgdex", etc.
    title: str
    description: str
    price_eur: float     # Always in EUR
    region: str          # "Lombardia", "Europa", etc.
    city: str            # Optional
    condition: str       # "nuovo", "buono", "discreto", "usato"
    year: Optional[int]
    brand: Optional[str]
    category: str        # "auto", "moto", "elettronica", etc.
```

---

## Adding a New Scraper

### Step 1: Create the File

```python
# scrapers/mysite.py
from base import BaseScraper, ScrapedProduct
import httpx

class MySiteScraper(BaseScraper):
    SOURCE_NAME = "mysite"
    BASE_URL = "https://api.mysite.com"
    RATE_LIMIT_SECONDS = 0.5
    
    def __init__(self):
        super().__init__()
        self.client = httpx.Client(timeout=30.0)
    
    def scrape_category(self, category: str, max_pages: int = 5) -> List[ScrapedProduct]:
        products = []
        
        for page in range(max_pages):
            self._rate_limit()
            
            response = self.client.get(
                f"{self.BASE_URL}/products",
                params={"category": category, "page": page}
            )
            
            for item in response.json()["items"]:
                product = self._parse_item(item, category)
                if product and self.validate_product(product):
                    products.append(product)
        
        return products
    
    def _parse_item(self, item: dict, category: str) -> ScrapedProduct:
        return ScrapedProduct(
            source_url=item["url"],
            source_name=self.SOURCE_NAME,
            title=item["title"],
            description=item.get("description", ""),
            price_eur=float(item["price"]),
            region="Italia",
            city=item.get("location", ""),
            condition=self._map_condition(item.get("condition")),
            year=None,
            brand=item.get("brand"),
            category=category,
        )
    
    def close(self):
        super().close()
        self.client.close()
```

### Step 2: Add to Worker

```python
# worker.py
from mysite import MySiteScraper

def run_scrape_job():
    # ... existing scrapers ...
    
    # Add your scraper
    try:
        scraper = MySiteScraper()
        products = scraper.scrape_category("elettronica", max_pages=3)
        all_products.extend(products)
        logger.info(f"MySite: Scraped {len(products)} products")
        scraper.close()
    except Exception as e:
        logger.warning(f"MySite scraper failed: {e}")
```

### Step 3: Add Requirements (if needed)

```
# scrapers/requirements.txt
httpx
```

### Step 4: Rebuild

```bash
sudo docker-compose up -d --build scraper
sudo docker logs piranha2-scraper-1 -f
```

---

## Implemented Scrapers

### 1. Mock Scraper (mock_scraper.py)
- **Purpose**: Development/testing
- **Auth**: None required
- **Data**: Generates fake Italian products
- **Categories**: All

### 2. eBay Scraper (ebay.py)
- **Purpose**: Real eBay listings
- **Auth**: eBay Developer API credentials
- **API**: eBay Browse API (OAuth 2.0)
- **Categories**: auto, moto, elettronica, casa, abiti

```bash
# Setup
EBAY_CLIENT_ID=your-app-id
EBAY_CLIENT_SECRET=your-cert-id
EBAY_ENVIRONMENT=sandbox  # or production
```

### 3. TCGdex Scraper (tcgdex.py)
- **Purpose**: Pokémon card prices
- **Auth**: None required (free API)
- **API**: tcgdex.net
- **Categories**: carte/pokemon

---

## Environment Variables

```bash
# Scraper timing
SCRAPE_INTERVAL=21600     # 6 hours (in seconds)
SEED_DATABASE=true        # Seed on first run

# Database
DATABASE_URL=postgresql://piranha:pass@db:5432/piranha

# API credentials
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_ENVIRONMENT=sandbox
```

---

## Database Upsert Logic

The `save_products` function uses PostgreSQL's `ON CONFLICT` to update existing products:

```python
def save_products(products):
    for product in products:
        stmt = insert(Product).values(**product.to_dict())
        stmt = stmt.on_conflict_do_update(
            constraint="unique_source",  # source_url + source_name
            set_={
                "title": stmt.excluded.title,
                "price_eur": stmt.excluded.price_eur,
                "scraped_at": datetime.utcnow(),
            }
        )
        session.execute(stmt)
    session.commit()
```

This means:
- **New products** → Insert
- **Existing products** (same URL + source) → Update price & timestamp

---

## Commands

```bash
# View scraper logs
sudo docker logs piranha2-scraper-1 -f

# Restart scraper
sudo docker-compose restart scraper

# Rebuild after code changes
sudo docker-compose up -d --build scraper

# Run scraper manually (one-shot)
sudo docker exec -it piranha2-scraper-1 python -c "from worker import run_scrape_job; run_scrape_job()"
```

---

## Legal Considerations

### ✅ Safe to Use
- **Official APIs** with your credentials (eBay, Discogs, Reverb)
- **Public data feeds** (Cardmarket CSV)
- **Open APIs** (TCGdex)

### ⚠️ Requires Care
- **Rate limiting**: Always use `_rate_limit()` between requests
- **ToS compliance**: Display attribution, don't cache too long

### ❌ Avoid
- **Web scraping** without permission
- **Bypassing anti-bot measures**
- **Storing data in violation of ToS**

---

## Troubleshooting

### Scraper Not Running
```bash
sudo docker ps | grep scraper
sudo docker logs piranha2-scraper-1 --tail 50
```

### API Authentication Errors
- Check environment variables are set
- Verify API credentials are correct
- Check if sandbox vs production

### No Products Saved
- Check `validate_product()` isn't rejecting everything
- Verify price is > 0
- Check logs for parsing errors

# EV Price Tracker

A web application that tracks used electric vehicle prices across major listing sites (CarGurus, Autotrader, Cars.com).

## Features

- Track 20 popular EV models from Tesla, Ford, Chevrolet, Rivian, Hyundai, Kia, BMW, Mercedes, and Volkswagen
- Scrape listings from CarGurus, Autotrader, and Cars.com
- View price trends over time with interactive charts
- Browse current listings with sorting and filtering
- Dashboard with summary statistics

## Tech Stack

- **Frontend**: React + Vite + Recharts
- **Backend**: Python FastAPI
- **Database**: SQLite
- **Scraping**: Playwright

## Setup

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the server
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The UI will be available at http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | List all tracked EV models |
| GET | `/api/models/{id}/prices` | Get price history for a model |
| GET | `/api/models/{id}/listings` | Get current listings for a model |
| GET | `/api/stats` | Dashboard summary stats |
| POST | `/api/scrape` | Trigger a manual scrape |
| GET | `/api/scrape/status` | Get current scrape status |
| GET | `/api/settings` | Get app settings |
| PUT | `/api/settings` | Update settings (zip_code, search_radius) |

## Usage

1. Start both the backend and frontend servers
2. Open http://localhost:5173 in your browser
3. Click "Scrape Prices" to fetch listings from all sources
4. Select an EV model from the sidebar to view its price history and listings

## Configuration

Settings can be configured via the API:
- **zip_code**: Location for searches (default: 90210)
- **search_radius**: Search radius in miles (default: 100)

## EV Models Tracked

- **Tesla**: Model 3, Model Y, Model S, Model X
- **Ford**: Mustang Mach-E, F-150 Lightning
- **Chevrolet**: Bolt EV, Bolt EUV, Equinox EV
- **Rivian**: R1T, R1S
- **Hyundai**: Ioniq 5, Ioniq 6
- **Kia**: EV6, EV9
- **BMW**: i4, iX
- **Mercedes**: EQS, EQE
- **Volkswagen**: ID.4

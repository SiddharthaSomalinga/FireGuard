# FireGuard 🔥

**Real-time wildfire risk assessment system combining environmental data, fire behavior modeling, and Prolog-based reasoning.**

🌐 **Live Demo**: [https://prolog-api.onrender.com](https://prolog-api.onrender.com)

## Inspiration

Wildfires continue to pose significant threats globally. FireGuard was developed to provide real-time wildfire risk assessment by combining environmental data, fire behavior modeling, and a Prolog-based reasoning system. The goal is to empower first responders, emergency planners, and the public with actionable insights for evacuation, resource allocation, and fire management.

## How It Works

FireGuard integrates multiple layers to assess wildfire risk:

### 1. Dynamic Environmental Data

- **Weather Data**: Temperature, humidity, wind speed, and precipitation are fetched in real-time from the Open-Meteo API.
- **Rain History**: Historical rainfall is analyzed to estimate days since last rain and its effect on fuel moisture.
- **Topography**: Elevation and slope are estimated using the Open-Elevation API to classify terrain.
- **Population & Infrastructure**: Population density and critical infrastructure are inferred from OpenStreetMap APIs.

### 2. Fire Behavior Modeling

FireGuard uses classical fire science models:

- **Rothermel Equation**: Predicts fire spread rate.
- **Byram Equation**: Calculates fireline intensity.
- **Flame Length & Height**: Derived from fire intensity.
- **Safety Zones, Burn Area, Escape Time**: Calculated using fire behavior metrics.

### 3. Risk Scoring System

Risk is evaluated across multiple parameters:

| Factor | Scoring | Notes |
|--------|---------|-------|
| Fuel Moisture | 0–30 | Very critical |
| Temperature | 0–20 | Higher temp = higher risk |
| Humidity | 0–20 | Lower humidity = higher risk |
| Wind Speed | 0–20 | Stronger wind = higher risk |
| Topography | 0–15 | Steeper slopes = faster spread |
| Population Density | 0–10 | More people at risk |
| Infrastructure | 0–15 | Critical infrastructure increases consequence |

Total score is mapped to risk levels: Very Low, Low, Medium, High, Very High, Extreme.

Evacuation and resource recommendations are provided based on risk level.

### 4. Machine Learning & Fire Danger Index (FDI)

- FDI is computed dynamically using temperature, humidity, wind, and rainfall history.
- FDI numeric value is mapped to categories: Blue, Green, Yellow, Orange, Red.

### 5. Prolog-Based Reasoning

- **Dynamic Prolog Facts**: Each area is dynamically added/updated in the Prolog knowledge base.
- **Classification**: Prolog evaluates all parameters to assign fire risk, evacuation recommendations, and required resources.
- **JSON Output**: Results can be easily integrated with Python for further processing or visualization.

### 6. Interactive Chatbot

Users can query fireline intensity, flame length, safety zones, burn area, escape time, and risk level via a Prolog chatbot interface.

## How We Built It

- Python scripts fetch real-time environmental data.
- Fire science equations are implemented in Prolog for deterministic reasoning.
- Random Forest machine learning model (legacy) complements the system with historical predictions.
- Python-Prolog integration allows dynamic area creation and real-time classification.
- Flask web application provides an intuitive web interface for easy access.
- Results include risk levels, evacuation recommendations, and resource allocation.

## Challenges

- Fetching and integrating multiple external APIs reliably.
- Converting continuous environmental data into categorical scores for Prolog classification.
- Maintaining real-time performance while running complex calculations and external queries.
- Handling dynamic Prolog facts for multiple areas without conflicts.

## Accomplishments

- Fully dynamic, real-time fire risk system combining Python, Prolog, and machine learning.
- Provides actionable outputs for firefighters and emergency responders.
- Interactive web interface with clean, modern UI for easy access.
- Prolog chatbot interface for advanced queries.
- Programmatic JSON outputs for integration with other systems.
- Supports multi-area comparisons with priority ordering.

## Future Plans

- Integrate live satellite and drone feeds to improve fire detection.
- Expand to more granular local sensor data for vegetation and soil moisture.
- Improve predictive accuracy with additional datasets.
- Add real-time map visualization for multiple locations.
- Implement user authentication and saved location history.

## Deployment

FireGuard is deployed as a unified Flask application on Render with Docker:

- **Production URL**: [https://prolog-api.onrender.com](https://prolog-api.onrender.com)
- **API Endpoints**:
  - `GET /` - Web interface
  - `GET /api/health` - Health check
  - `POST /api/analyze` - Fire risk analysis
  - `POST /api/prolog/classify` - Prolog classification
  - `GET /api/prolog/health` - Prolog service health

### Architecture

- **Frontend**: Served from `templates/` and `static/` by Flask
- **Backend**: Merged Flask app combining fire analysis and Prolog reasoning
- **Container**: Docker image with Python 3.13 + SWI-Prolog
- **WSGI Server**: Gunicorn (production-ready)

### Environment Variables

- `PORT` - Server port (default: 5000)
- `MOCK_WEATHER` - Set to `1` to use mock weather data (for testing/rate limit avoidance)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- SWI-Prolog installed and accessible via `swipl` command
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd <repository_directory>
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install required Python libraries:
```bash
pip install -r requirements.txt
```

4. Ensure SWI-Prolog is installed:
```bash
swipl --version
```

If not installed:
- **macOS**: `brew install swi-prolog`
- **Linux**: `sudo apt-get install swi-prolog`
- **Windows**: Download from [SWI-Prolog website](https://www.swi-prolog.org/download/stable)

### Running the Web Application

1. Activate the virtual environment (if not already active):
```bash
source .venv/bin/activate
```

2. Start the Flask server:
```bash
python app.py
```

Or use the convenience script:
```bash
./run.sh
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

4. Enter coordinates (latitude and longitude) and click "Analyze Fire Risk"

The web interface provides a user-friendly way to analyze fire risk with real-time data visualization.

### Running Command-Line Script

For programmatic access, you can run the Python analysis directly:

```bash
python fdi.py
```

This will analyze predefined locations and print results to the console.

### Running Prolog Chatbot

1. Open SWI-Prolog or an s(CASP) interpreter.

2. Load `prolog.pl` and run:
```prolog
chatbot.
priority_list(OrderedResults).
```

3. Query fireline intensity, flame length, safety zones, burn area, escape time, or risk level interactively.

## Example Usage

### Web Interface

1. Start the Flask server: `python app.py`
2. Open `http://localhost:5000` in your browser
3. Enter coordinates:
   - **Frisco, TX**: Latitude: 33.1507, Longitude: -96.8236
   - **Los Angeles, CA**: Latitude: 34.0522, Longitude: -118.2437
   - **San Francisco, CA**: Latitude: 37.7749, Longitude: -122.4194
4. Click "Analyze Fire Risk" to view results

### Programmatic Usage

Python script dynamically analyzes multiple locations:
```python
from fdi import analyze_location_dynamic

locations = [
    (33.1507, -96.8236, "frisco_tx"),
    (34.0522, -118.2437, "los_angeles_ca"),
    (37.7749, -122.4194, "san_francisco_ca"),
]

for lat, lon, name in locations:
    result = analyze_location_dynamic(lat, lon, area_name=name)
    print(f"{name}: {result['prolog_classification'].get('RiskLevel', 'Unknown')} risk")
```

Each location outputs risk classification, evacuation status, resources needed, and FDI category.

### API Usage

**Production API** (deployed on Render):

```bash
# Health check
curl https://prolog-api.onrender.com/api/health

# Analyze fire risk for coordinates
curl -X POST https://prolog-api.onrender.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude": 33.1507, "longitude": -96.8236, "area_name": "frisco_tx"}'

# Direct Prolog classification
curl -X POST https://prolog-api.onrender.com/api/prolog/classify \
  -H "Content-Type: application/json" \
  -d '{
    "area_name": "test_area",
    "fuel": "moderate",
    "temp": "moderate",
    "hum": "moderate",
    "wind": "moderate",
    "topo": "flat",
    "pop": "low",
    "infra": "no_critical"
  }'
```

**Local API**:

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"latitude": 33.1507, "longitude": -96.8236, "area_name": "frisco_tx"}'
```

### Testing with Mock Weather

To avoid Open-Meteo API rate limits during development:

```bash
# Local testing
MOCK_WEATHER=1 python app.py

# Or test analysis directly
MOCK_WEATHER=1 python -c "
from fdi import analyze_location_dynamic
import json
result = analyze_location_dynamic(33.1507, -96.8236, 'test')
print(json.dumps(result, indent=2))
"
```

## Project Structure

```
FireGuard/
├── app.py                     # Merged Flask application (web + API)
├── fdi.py                     # Fire risk analysis logic with MOCK_WEATHER support
├── prolog.pl                  # Prolog knowledge base (dynamic facts enabled)
├── Dockerfile                 # Docker build for Render deployment
├── requirements.txt           # Python dependencies (includes gunicorn)
├── build.sh                   # Build script (no-op when using Docker)
├── templates/
│   └── index.html             # Web interface template
├── static/
│   ├── css/
│   │   └── style.css          # Styling with red fire theme
│   └── js/
│       └── main.js            # Frontend JavaScript
├── api/
│   └── prolog/                # Vercel serverless functions (optional)
│       ├── classify.js
│       └── health.js
├── apitests.py                # API testing utilities
└── README.md                  # This file
```

## Features

- ✅ **Web Interface**: Modern, responsive web UI with red fire-themed design
- ✅ **Real-time Analysis**: Fetches live weather and environmental data
- ✅ **Multiple Interfaces**: Web UI, REST API, command-line script, and Prolog chatbot
- ✅ **Production Deployment**: Dockerized on Render with Gunicorn
- ✅ **Mock Weather Mode**: Test without API rate limits
- ✅ **Dynamic Prolog Facts**: Runtime assertion of area data
- ✅ **Comprehensive Results**: Weather, topography, FDI, risk classification, and recommendations

## Tech Stack

- **Backend**: Python 3.13, Flask, Gunicorn
- **Logic Engine**: SWI-Prolog
- **APIs**: Open-Meteo (weather), Open-Elevation (topography), OpenStreetMap (population/infrastructure)
- **Deployment**: Docker, Render
- **Frontend**: HTML, CSS, JavaScript

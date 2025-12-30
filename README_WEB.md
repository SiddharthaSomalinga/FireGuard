# FireGuard Web Application

A modern web interface for the FireGuard wildfire risk assessment system, featuring a clean red-themed UI.

## Features

- **Real-time Risk Assessment**: Enter coordinates to get instant fire risk analysis
- **Comprehensive Data Display**: View weather conditions, rain history, topography, and more
- **Clean Red Theme**: Modern, responsive design with a fire-themed color scheme
- **Interactive UI**: Smooth animations and intuitive user experience

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- SWI-Prolog installed and accessible via `swipl` command
- All dependencies from `requirements.txt`

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure SWI-Prolog is installed:
```bash
swipl --version
```

If not installed, download from: https://www.swi-prolog.org/download/stable

### Running the Web Application

1. Activate the virtual environment (if using one):
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

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Enter coordinates (latitude and longitude) and click "Analyze Fire Risk"

### Example Coordinates

- Frisco, TX: Latitude: 33.1507, Longitude: -96.8236
- Los Angeles, CA: Latitude: 34.0522, Longitude: -118.2437
- San Francisco, CA: Latitude: 37.7749, Longitude: -122.4194

## API Endpoints

### POST /api/analyze
Analyze fire risk for a given location.

**Request Body:**
```json
{
    "latitude": 33.1507,
    "longitude": -96.8236,
    "area_name": "frisco_tx"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "location": {...},
        "weather_data": {...},
        "rain_data": {...},
        "environmental": {...},
        "classifications": {...},
        "fdi": {...},
        "prolog_classification": {...}
    }
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
    "status": "ok"
}
```

## Project Structure

```
FireGuard/
├── app.py                 # Flask web application
├── fdi.py                 # Fire risk analysis logic
├── prolog.pl              # Prolog knowledge base
├── templates/
│   └── index.html         # Main web page
├── static/
│   ├── css/
│   │   └── style.css      # Styling with red theme
│   └── js/
│       └── main.js        # Frontend JavaScript
└── requirements.txt       # Python dependencies
```

## Troubleshooting

### Prolog Not Found
If you get an error about `swipl` not being found:
- Ensure SWI-Prolog is installed and in your PATH
- On macOS: `brew install swi-prolog`
- On Linux: `sudo apt-get install swi-prolog`
- On Windows: Download installer from SWI-Prolog website

### API Errors
If external APIs fail:
- Check your internet connection
- Some APIs may have rate limits
- Check the console for detailed error messages

### Port Already in Use
If port 5000 is already in use, modify `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port number
```

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## License

See main project README for license information.


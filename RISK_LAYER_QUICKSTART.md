# Quick Start: Geospatial Risk Layer

## What Was Added

FireGuard now generates a **pre-rendered, deterministic geospatial wildfire risk layer** for direct map integration.

## Key Components

### 1. **risk_layer.py** (New Module)
Core module for generating risk layers:
- `compute_grid_cell_risk()` - Calculate risk for a single grid cell
- `generate_geojson_risk_layer()` - Generate complete GeoJSON layer
- `get_risk_layer_summary()` - Get lightweight summary statistics
- `get_layer_configuration()` - Get configuration for clients

### 2. **API Endpoints** (New in app.py)
Three new endpoints for accessing risk layer data:
- `GET /api/risk-layer/config` - Configuration and metadata
- `GET /api/risk-layer/geojson` - Complete GeoJSON layer (supports grid_resolution parameter)
- `GET /api/risk-layer/summary` - Summary statistics for dashboards

### 3. **Interactive Map UI**
- New "Geospatial Wildfire Risk Layer" section on main page
- Color-coded grid cells representing risk levels
- Interactive popups with detailed risk metrics
- Legend showing risk categories

## How It Works

**Risk Score Calculation** (0-100):
```
Risk Score = (FDI Risk × 0.6) + (Fire Proximity Risk × 0.4)
```

**Risk Categories**:
- Critical (≥80): Dark Red
- High (60-79): Red
- Moderate (40-59): Orange
- Low (20-39): Yellow
- Minimal (<20): Light Green

## Integration Points

### Backend
```python
from risk_layer import generate_geojson_risk_layer

geojson = generate_geojson_risk_layer(grid_resolution=1.0)
```

### Frontend (JavaScript)
```javascript
fetch('/api/risk-layer/geojson?grid_resolution=1.0')
  .then(r => r.json())
  .then(data => renderLayer(data.data));
```

### Database/Cache
- No database required
- Uses cached weather data from open-meteo
- Caches active fire data from NASA FIRMS
- Deterministic computation for reproducibility

## Configuration

**Grid Resolutions** (supported):
- 0.25° - Very detailed (~7000 cells)
- 0.5° - Standard (~1700 cells) - **default**
- 1.0° - Balanced (~450 cells)
- 2.0° - Fast (~100 cells)

**Risk Thresholds** (in risk_layer.py):
```python
RISK_LAYER_CONFIG['risk_thresholds'] = {
    'critical': 80,
    'high': 60,
    'moderate': 40,
    'low': 20,
    'minimal': 0
}
```

## Performance

- **Generation time**: ~1-5 seconds depending on grid resolution
- **Data transfer**: ~500KB-5MB depending on resolution
- **Browser rendering**: Real-time with Leaflet
- **Update frequency**: Real-time (pulls latest FIRMS data)

## Testing the Feature

### Test Endpoint
```bash
# Get risk layer configuration
curl http://localhost:5000/api/risk-layer/config

# Get risk layer as GeoJSON (1.0° resolution for quick test)
curl 'http://localhost:5000/api/risk-layer/geojson?grid_resolution=1.0'

# Get summary statistics
curl http://localhost:5000/api/risk-layer/summary
```

### Browser Testing
1. Go to main page (http://localhost:5000)
2. Scroll to top - see "Geospatial Wildfire Risk Layer" map
3. Hover over grid cells to see risk details
4. Click cells for popup with full metrics

## Data Sources

1. **FDI Risk Component**:
   - Temperature, humidity, wind from Open-Meteo API
   - Rainfall history (90-day lookback)
   - Local elevation data

2. **Fire Proximity Component**:
   - Active fires from NASA FIRMS API
   - Confidence levels (low/nominal/high)
   - Distance-based decay function

## Files Modified

| File | Changes |
|------|---------|
| `risk_layer.py` | NEW - Core module |
| `app.py` | Added 3 API endpoints + imports |
| `templates/index.html` | Added risk layer map section |
| `static/js/main.js` | Added risk layer rendering logic |
| `static/css/style.css` | Added risk layer & popup styles |
| `requirements.txt` | Updated with feature notes |

## Next Steps

### For Users
1. Navigate to main page to see risk layer
2. Use grid_resolution parameter for different detail levels
3. Integrate into existing dashboards via API

### For Developers
1. Customize risk component weights in `compute_grid_cell_risk()`
2. Add additional data sources to risk calculation
3. Implement tile rendering for larger-scale deployments
4. Add historical tracking for risk evolution

## Documentation

- Full feature documentation: [RISK_LAYER_FEATURE.md](RISK_LAYER_FEATURE.md)
- API details in docstrings: [risk_layer.py](risk_layer.py)
- Integration examples in frontend: [static/js/main.js](static/js/main.js)

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: January 5, 2025

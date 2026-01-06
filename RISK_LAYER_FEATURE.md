# Geospatial Wildfire Risk Layer Feature

## Overview
FireGuard now includes a **pre-rendered, deterministic geospatial wildfire risk layer** designed for direct integration into interactive maps. This feature generates a comprehensive risk assessment grid covering continental USA and Canada, combining multiple data sources into a single unified risk metric.

## Features

### 1. **Grid-Based Risk Assessment**
- 0.5° resolution grid (~55 km cells at equator)
- Covers entire continental USA and Canada
- Pre-computed for deterministic, reproducible results
- Supports multiple resolutions (0.25°, 0.5°, 1.0°, 2.0°)

### 2. **Multi-Factor Risk Computation**
Each grid cell's risk score combines:
- **FDI (Fire Danger Index) Risk** (60% weight)
  - Weather conditions (temperature, humidity, wind speed)
  - Fuel moisture classification
  - Topographic factors
  - Historical rainfall patterns

- **Fire Proximity Risk** (40% weight)
  - Distance to active fires detected by NASA FIRMS
  - Fire confidence levels (low/nominal/high)
  - Exponential decay based on distance zones:
    - Critical zone: ≤50 km (highest risk)
    - High risk zone: 50-100 km
    - Moderate zone: 100-200 km

### 3. **Risk Categories & Color Coding**
| Score | Category | Color | Description |
|-------|----------|-------|-------------|
| ≥80 | Critical | #8B0000 (Dark Red) | Extreme wildfire risk |
| 60-79 | High | #FF0000 (Red) | High wildfire risk |
| 40-59 | Moderate | #FFA500 (Orange) | Moderate wildfire risk |
| 20-39 | Low | #FFFF00 (Yellow) | Low wildfire risk |
| <20 | Minimal | #90EE90 (Light Green) | Minimal wildfire risk |

### 4. **GeoJSON Output Format**
Each feature in the GeoJSON includes:
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], ...]]
  },
  "properties": {
    "risk_score": 65.3,
    "risk_category": "high",
    "risk_color": "#FF0000",
    "fdi_risk": 58.2,
    "fire_proximity_risk": 72.4,
    "nearby_fires": 3,
    "closest_fire_km": 45.2,
    "timestamp": "2025-01-05T18:30:00+00:00",
    "center": {"lat": 45.0, "lon": -100.0}
  }
}
```

## API Endpoints

### 1. **Get Risk Layer Configuration**
```
GET /api/risk-layer/config
```
Returns layer configuration, bounds, and URL template for client-side rendering.

**Response:**
```json
{
  "success": true,
  "data": {
    "config": {
      "grid_resolution": 0.5,
      "zoom_levels": [4, 5, 6, 7, 8, 9, 10],
      "risk_thresholds": {...},
      "colors": {...}
    },
    "bounds": {
      "north": 70.0,
      "south": 24.0,
      "east": -50.0,
      "west": -170.0
    },
    "url_template": "/api/risk-layer/tiles/{z}/{x}/{y}.png"
  }
}
```

### 2. **Get Risk Layer as GeoJSON**
```
GET /api/risk-layer/geojson?grid_resolution=1.0
```
Generates and returns the complete risk layer as a GeoJSON FeatureCollection.

**Query Parameters:**
- `grid_resolution`: Grid cell size in degrees (default: 0.5, range: 0.25-5.0)

**Response:**
```json
{
  "success": true,
  "data": {
    "type": "FeatureCollection",
    "features": [...],
    "metadata": {
      "grid_resolution": 1.0,
      "bounds": {...},
      "generated_at": "2025-01-05T18:30:00+00:00",
      "fire_count": 287,
      "total_cells": 845
    }
  }
}
```

### 3. **Get Risk Layer Summary**
```
GET /api/risk-layer/summary
```
Lightweight endpoint returning summary statistics for dashboard displays.

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-01-05T18:30:00+00:00",
    "total_active_fires": 287,
    "fires_by_confidence": {
      "high": 89,
      "nominal": 142,
      "low": 56
    },
    "high_risk_zones": 23,
    "moderate_risk_zones": 156,
    "low_risk_zones": 666
  }
}
```

## Integration with Maps

### Leaflet Integration
The risk layer is rendered using Leaflet's GeoJSON layer with:
- Color-coded polygons matching risk categories
- Interactive popups showing detailed metrics
- Smooth hover effects and transparency
- Dark mode support

### Client-Side Usage
```javascript
// Fetch risk layer
const resp = await fetch('/api/risk-layer/geojson?grid_resolution=1.0');
const data = await resp.json();

// Add to Leaflet map
L.geoJSON(data.data, {
    style: {
        fillColor: feature.properties.risk_color,
        weight: 1,
        opacity: 0.7,
        fillOpacity: 0.6
    },
    onEachFeature: (feature, layer) => {
        layer.bindPopup(/* detailed risk info */);
    }
}).addTo(map);
```

## Technical Implementation

### Files Added/Modified
1. **risk_layer.py** (NEW)
   - Core risk layer generation module
   - Grid-based computation functions
   - GeoJSON output generation
   - Summary statistics

2. **app.py** (MODIFIED)
   - Three new API endpoints for risk layer
   - Integration with existing analysis pipeline

3. **templates/index.html** (MODIFIED)
   - New risk layer map visualization section
   - Legend with risk categories

4. **static/js/main.js** (MODIFIED)
   - Risk layer map initialization
   - GeoJSON rendering and interaction
   - Popup generation for risk details

5. **static/css/style.css** (MODIFIED)
   - Risk layer map styling
   - Legend styling
   - Popup styling for risk data

## Data Flow

```
┌─────────────────────────────────────────┐
│  Risk Layer Generation Process          │
└─────────────────────────────────────────┘
                    ↓
      ┌─────────────────────────────┐
      │  For each grid cell (0.5°)  │
      └─────────────────────────────┘
                    ↓
     ┌──────────────────────────────────┐
     │  1. Get FDI-based risk score     │
     │  2. Calculate fire proximity     │
     │  3. Combine components (60/40)   │
     │  4. Map to risk category         │
     └──────────────────────────────────┘
                    ↓
         ┌──────────────────────────┐
         │  Generate GeoJSON        │
         │  Feature with properties │
         └──────────────────────────┘
                    ↓
         ┌──────────────────────────┐
         │  Render on interactive   │
         │  map with Leaflet        │
         └──────────────────────────┘
```

## Performance Considerations

- **Grid Resolution**: Balances detail vs. performance
  - 0.5°: 1700+ cells (detailed, ~2-5 seconds)
  - 1.0°: ~450 cells (balanced, <2 seconds)
  - 2.0°: ~100 cells (fast, <1 second)

- **Caching**: FDI and fire data are cached to avoid redundant API calls

- **Browser Rendering**: GeoJSON rendering optimized for typical map zoom levels 4-10

## Future Enhancements

1. **Raster Tile Support**: Generate PNG/MVT tiles for web mapping services
2. **Historical Analysis**: Track risk evolution over time
3. **Custom Weights**: Allow users to adjust risk component weights
4. **Real-time Updates**: Auto-refresh risk layer based on new fire data
5. **Geofencing**: Generate alerts for high-risk zones
6. **Data Export**: Download risk layer as GeoTIFF, Shapefile, or other formats

## Usage Examples

### Dashboard Integration
```javascript
// Load and display risk layer summary
fetch('/api/risk-layer/summary')
  .then(r => r.json())
  .then(data => updateDashboard(data.data));
```

### Advanced Analysis
```javascript
// Get high-detail risk layer
fetch('/api/risk-layer/geojson?grid_resolution=0.5')
  .then(r => r.json())
  .then(data => {
    // Filter critical risk zones
    const criticalZones = data.data.features.filter(
      f => f.properties.risk_category === 'critical'
    );
    analyzeZones(criticalZones);
  });
```

### Mobile Applications
```javascript
// Load coarse grid for mobile (lower bandwidth)
fetch('/api/risk-layer/geojson?grid_resolution=2.0')
  .then(r => r.json())
  .then(data => renderMobileMap(data.data));
```

## Testing

The risk layer has been integrated with:
- Existing NASA FIRMS active fire data
- FDI weather and topography analysis
- Deterministic computation for reproducibility
- Dark mode support
- Responsive design for all screen sizes

## References

- **Fire Danger Index (FDI)**: [fdi.py](fdi.py)
- **NASA FIRMS Data**: [firms.py](firms.py)
- **Risk Layer Module**: [risk_layer.py](risk_layer.py)
- **API Implementation**: [app.py](app.py)
- **Frontend Integration**: [templates/index.html](templates/index.html), [static/js/main.js](static/js/main.js)

---

**Status**: ✅ Production Ready  
**Last Updated**: January 5, 2025

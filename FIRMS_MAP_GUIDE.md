# 🛰️ NASA FIRMS Active Fire Overlay - Map Integration Guide

## Overview

FireGuard now includes **real-time satellite-detected fire hotspots** from NASA's FIRMS (Fire Information for Resource Management System) API with interactive map visualization.

## ✅ Your Setup Status

| Item | Status | Details |
|------|--------|---------|
| **MAP_KEY** | ✅ VALID | `501896775f6b28df986593019e4634fe` |
| **Transaction Limit** | ✅ 5000/10min | Full quota available |
| **API Connection** | ✅ WORKING | NASA FIRMS server responding |
| **Map Library** | ✅ LEAFLET | Leaflet.js + OpenStreetMap tiles |
| **Integration** | ✅ COMPLETE | Backend + Frontend implemented |

## 🚀 Quick Start

### 1. View the FIRMS Map Demo
Navigate to the demo page in your browser:
```
http://localhost:5000/firms-demo
```

**Features:**
- 🗺️ Interactive map centered on wildfire zones
- 🔥 Real-time satellite fire detections (24-48h latency)
- 📍 Three quick-access locations (NorCal, SoCal, Colorado)
- 📊 Fire metadata (power, confidence, acquisition time)
- 🎨 Color-coded confidence levels

### 2. Use FIRMS in Main Analysis
When you perform a fire risk analysis:
1. Enter location coordinates
2. Click "Analyze Fire Risk"
3. System automatically:
   - Computes risk from FDI model
   - Queries NASA FIRMS for nearby fires
   - Displays interactive map below risk assessment
   - Auto-elevates risk if fires detected nearby
   - Triggers evacuation recommendations if critical fires found

### 3. Test Locations

**High Fire Season Areas (Best for Testing):**
- **Northern California**: `37.8°N, -122.2°W` (Bay Area)
- **Southern California**: `34.5°N, -118.2°W` (Los Angeles)
- **Colorado**: `39.7°N, -104.9°W` (Front Range)

During wildfire season (May-October), these locations typically show detected fires.

## 📡 Data Source Details

### NASA FIRMS API
- **Provider**: NASA Earth Observation Data and Information System (EOSDIS)
- **Dataset**: VIIRS SNPP NRT (Visible Infrared Imaging Radiometer Suite)
- **Update Frequency**: ~24-48 hours behind real-time
- **Coverage**: Global
- **Confidence Levels**:
  - 🔴 **High**: 76-100 confidence score
  - 🟠 **Nominal**: 41-75 confidence score
  - 🟡 **Low**: 0-40 confidence score

### Map Tiles
- **Provider**: OpenStreetMap Foundation
- **Library**: Leaflet.js (lightweight, open-source)
- **Features**: Zoom, pan, click popups

## 🗂️ File Structure

```
FireGuard/
├── firms.py                    # NEW: FIRMS API integration module
├── templates/
│   ├── index.html             # Updated with FIRMS card + map
│   └── firms_demo.html        # NEW: Standalone FIRMS map demo
├── static/
│   ├── js/main.js             # Updated with map initialization
│   └── css/style.css          # Updated with FIRMS & map styles
└── test_firms_map.py          # NEW: MAP_KEY validation script
```

## 🔧 Implementation Details

### Backend: `/api/firms/active-fires` Endpoint

**Request:**
```json
{
  "latitude": 37.8,
  "longitude": -122.2,
  "current_risk_level": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "fires": [
      {
        "lat": 37.456,
        "lon": -121.892,
        "distance_km": 45.3,
        "confidence": 85,
        "confidence_level": "high",
        "frp": 125.4,
        "acq_date": "2025-01-03",
        "acq_time": "14:30",
        "satellite": "VIIRS"
      }
    ],
    "threat_analysis": {
      "has_nearby_fires": true,
      "fire_threat_level": "moderate",
      "evacuation_recommended": false,
      "recommended_risk_elevation": "high"
    },
    "timestamp": "2025-01-03T15:00:00"
  }
}
```

### Frontend: Interactive Map Display

**Key Functions:**
- `fetchAndDisplayFIRMSData()` - Fetches fires after analysis
- `initializeFIRMSMap()` - Creates Leaflet map instance
- `displayFIRMSResults()` - Renders threat status + fires list

**Map Features:**
- 🔵 Blue marker: Your location
- 🔴/🟠/🟡 Colored circles: Fire hotspots (by confidence)
- 📍 Click markers for fire details popup
- 🎯 Auto-zoom to show all fires + location

## 🎨 Visual Indicator Colors

### Fire Threat Levels
| Level | Color | Meaning |
|-------|-------|---------|
| **Critical** | 🔴 Red | High-confidence fire within 10km |
| **Severe** | 🟠 Orange | High-confidence fire 10-25km away |
| **Moderate** | 🟡 Yellow | Nominal confidence or 25-50km away |
| **Minor** | 🟢 Green | Low confidence or >50km away |
| **None** | ✅ Green | No fires detected |

### Fire Confidence Levels
| Confidence | Color | NASA Score |
|------------|-------|-----------|
| **High** | 🔴 Red | 76-100 |
| **Nominal** | 🟠 Orange | 41-75 |
| **Low** | 🟡 Yellow | 0-40 |

## 📊 Risk Elevation Logic

When active fires are detected, the system automatically elevates risk levels:

```
Original Risk + Fire Threat = Elevated Risk
─────────────────────────────────────────
low         + critical    = extreme
low         + severe      = high
low         + moderate    = moderate

moderate    + critical    = extreme
moderate    + severe      = extreme
moderate    + moderate    = high

high        + critical    = extreme
high        + severe      = extreme
high        + moderate    = extreme

extreme     + anything    = extreme (stays extreme)
```

## 🚨 Evacuation Trigger Conditions

Evacuation is **recommended** when:

1. **Critical Threat** (High confidence fire ≤10km):
   - Alert: "CRITICAL: Confirmed fire detected only Xkm away. Immediate evacuation strongly recommended."

2. **Severe Threat** (High confidence fire 10-25km):
   - Alert: "SEVERE: Confirmed fire detected Xkm away. Evacuation recommended."

3. **Moderate Threat Nearby** (Any fire ≤15km):
   - Alert: "Confirmed fire detected Xkm away. Consider evacuation preparation."

## 🧪 Testing the Feature

### Test 1: Verify MAP_KEY
```bash
python test_firms_map.py
```

**Expected Output:**
```
✅ MAP_KEY is VALID!
Transaction Status:
  transaction_limit: 5000
  current_transactions: 0
  transaction_interval: 10 minutes
```

### Test 2: Browse FIRMS Demo Page
1. Start Flask server: `python app.py`
2. Navigate to: `http://localhost:5000/firms-demo`
3. Click location buttons to see fires
4. Click fire markers for details

### Test 3: Test Main Analysis with FIRMS
1. Go to main page: `http://localhost:5000/`
2. Enter coordinates for a high-fire-risk zone
3. Click "Analyze Fire Risk"
4. Scroll down to NASA FIRMS card
5. Verify map appears with fire markers

## 🔐 API Key Management

Your MAP_KEY is configured in `firms.py`:

```python
FIRMS_API_KEY = os.environ.get('FIRMS_API_KEY', '501896775f6b28df986593019e4634fe')
```

### To Change Your Key (Optional):
1. Set environment variable:
   ```bash
   export FIRMS_API_KEY='your_new_key_here'
   ```
2. Or edit `firms.py` line 15:
   ```python
   FIRMS_API_KEY = 'your_new_key_here'
   ```

## 📈 API Usage & Quotas

**Your Current Status:**
- Limit: **5000 transactions** per 10 minutes
- Current usage: **0 transactions**
- Reset: Every 10 minutes

**Cost per Request:**
- `POST /api/firms/active-fires` = 1 transaction
- Each analysis request uses 1 transaction

**Example Usage:**
- Analyzing 5 locations per minute = 5 transactions/min
- Running continuously = 300 transactions per hour
- ✅ Well within the 5000/10min limit

## 🛠️ Troubleshooting

### Issue: Map shows "Unavailable"
**Solution:**
- Check internet connection
- Verify FireGuard backend is running
- Check browser console for errors (F12)

### Issue: No fires shown in high-fire areas
**Solution:**
- FIRMS data has 24-48 hour latency
- Active fires may have been extinguished
- Try different location or time
- Check NASA FIRMS website directly: https://firms.modaps.eosdis.nasa.gov/

### Issue: "API Connection Failed"
**Solution:**
1. Verify MAP_KEY is correct: `python test_firms_map.py`
2. Check internet connection
3. NASA FIRMS server may be temporarily down
4. Visit: https://status.eosdis.nasa.gov/

## 📚 Additional Resources

- **NASA FIRMS Main Page**: https://firms.modaps.eosdis.nasa.gov/
- **Data API Documentation**: https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html
- **Leaflet Documentation**: https://leafletjs.com/
- **OpenStreetMap**: https://www.openstreetmap.org/

## 🎯 Next Steps

1. ✅ Test the FIRMS demo page: `http://localhost:5000/firms-demo`
2. ✅ Perform risk analysis and verify map displays
3. ✅ Test with different locations during fire season
4. ✅ Monitor transaction usage in test_firms_map.py output
5. Consider: Adding historical fire data, fire tracking, evacuation zone generation

---

**NASA FIRMS Integration Complete! 🎉**

Your FireGuard system now bridges real-time satellite data with risk modeling for maximum situational awareness.

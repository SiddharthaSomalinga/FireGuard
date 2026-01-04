"""
NASA FIRMS (Fire Information for Resource Management System) Integration
Provides real-time satellite-detected active fire hotspots with confidence levels.

API: https://firms.modaps.eosdis.nasa.gov/api/area/csv/
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import os

# NASA FIRMS API Configuration
FIRMS_API_KEY = os.environ.get('FIRMS_API_KEY', '501896775f6b28df986593019e4634fe')
# Alternative endpoint that works without OAuth
FIRMS_API_BASE = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{{key}}/VIIRS_SNPP_NRT/{{date}}"

# Fire confidence levels mapping (NASA MODIS/VIIRS terminology)
CONFIDENCE_LEVELS = {
    'low': {'value': 30, 'label': 'Low Confidence', 'color': '#FFFF00', 'risk_boost': 0.1},
    'nominal': {'value': 60, 'label': 'Nominal Confidence', 'color': '#FFA500', 'risk_boost': 0.25},
    'high': {'value': 90, 'label': 'High Confidence', 'color': '#FF0000', 'risk_boost': 0.4}
}

# Default radius to check for nearby active fires (in km)
DEFAULT_FIRE_CHECK_RADIUS_KM = 50


def parse_confidence_level(confidence_score) -> str:
    """
    Parse NASA VIIRS confidence score to risk level.
    Can be numeric (0-100) or character ('h'=high, 'n'=nominal, 'l'=low).
    
    Numeric mapping:
    - 0-40: low
    - 41-75: nominal
    - 76-100: high
    
    Character mapping:
    - 'h': high
    - 'n': nominal
    - 'l': low
    """
    # Handle string values (character confidence)
    if isinstance(confidence_score, str):
        conf_str = str(confidence_score).lower().strip()
        if conf_str in ('h', 'high'):
            return 'high'
        elif conf_str in ('n', 'nominal'):
            return 'nominal'
        elif conf_str in ('l', 'low'):
            return 'low'
        # Try to convert string number
        try:
            confidence_score = float(conf_str)
        except ValueError:
            return 'nominal'  # Default to nominal if parsing fails
    
    # Handle numeric values
    try:
        score = float(confidence_score)
        if score >= 76:
            return 'high'
        elif score >= 41:
            return 'nominal'
        else:
            return 'low'
    except (ValueError, TypeError):
        return 'nominal'  # Default to nominal


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate approximate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def fetch_firms_fires(latitude: float, longitude: float, days_back: int = 7) -> List[Dict]:
    """
    Fetch active fires from NASA FIRMS API for a given location.
    Returns list of fire objects with coordinates, confidence, and timestamp.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        days_back: Number of days back to fetch (default 7)
    
    Returns:
        List of fire dictionaries with keys:
        - lat, lon: Fire coordinates
        - confidence: Confidence score (0-100)
        - confidence_level: 'low', 'nominal', or 'high'
        - frp: Fire Radiative Power (MW)
        - acq_date: Acquisition date
        - acq_time: Acquisition time
        - distance_km: Distance from query point
    """
    try:
        # Build request parameters
        # Dataset options: MODIS_NRT, VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT
        # We use VIIRS for newer, more accurate data
        
        params = {
            'key': FIRMS_API_KEY,
            'source_file': 'VIIRS_SNPP_NRT',
            'date': 'LAST7',  # Last 7 days
            'format': 'json'
        }
        
        # Make API request
        response = requests.get(FIRMS_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        fires = response.json()
        if not isinstance(fires, list):
            return []
        
        # Filter and enrich fires based on proximity
        nearby_fires = []
        
        for fire in fires:
            try:
                fire_lat = float(fire.get('latitude', 0))
                fire_lon = float(fire.get('longitude', 0))
                confidence = float(fire.get('confidence', 0))
                
                # Calculate distance
                distance = calculate_distance_km(latitude, longitude, fire_lat, fire_lon)
                
                # Filter to fires within ~100km radius (can be adjusted)
                if distance <= 100:
                    confidence_level = parse_confidence_level(confidence)
                    
                    nearby_fires.append({
                        'lat': fire_lat,
                        'lon': fire_lon,
                        'confidence': confidence,
                        'confidence_level': confidence_level,
                        'frp': float(fire.get('frp', 0)),  # Fire Radiative Power
                        'acq_date': fire.get('acq_date', ''),
                        'acq_time': fire.get('acq_time', ''),
                        'distance_km': round(distance, 2),
                        'satellite': fire.get('satellite', 'VIIRS'),
                        'daynight': fire.get('daynight', 'N')
                    })
            except (ValueError, TypeError):
                # Skip malformed entries
                continue
        
        # Sort by distance
        nearby_fires.sort(key=lambda x: x['distance_km'])
        
        return nearby_fires
        
    except requests.RequestException as e:
        print(f"⚠️  Error fetching FIRMS data: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Unexpected error in FIRMS fetch: {e}")
        return []


def analyze_active_fire_threat(latitude: float, longitude: float, 
                               current_risk_level: str) -> Dict:
    """
    Analyze active fire threat for a location and determine if risk should be elevated.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        current_risk_level: Current computed risk level (low/moderate/high/extreme)
    
    Returns:
        Dictionary with:
        - has_nearby_fires: Boolean
        - nearby_fire_count: Number of fires within radius
        - closest_fire_distance_km: Distance to closest fire
        - fire_threat_level: Threat assessment (none/minor/moderate/severe/critical)
        - recommended_risk_elevation: Risk level to elevate to
        - fires: List of detailed fire objects
        - evacuation_recommended: Boolean
        - evacuation_reason: String describing why evacuation is recommended
    """
    
    fires = fetch_firms_fires(latitude, longitude)
    
    result = {
        'has_nearby_fires': len(fires) > 0,
        'nearby_fire_count': len(fires),
        'closest_fire_distance_km': fires[0]['distance_km'] if fires else None,
        'closest_fire_confidence': fires[0]['confidence_level'] if fires else None,
        'fires': fires,
        'fire_threat_level': 'none',
        'recommended_risk_elevation': None,
        'evacuation_recommended': False,
        'evacuation_reason': ''
    }
    
    if not fires:
        return result
    
    # Determine threat level based on closest fire characteristics
    closest_fire = fires[0]
    distance = closest_fire['distance_km']
    confidence = closest_fire['confidence_level']
    
    # Threat matrix: distance + confidence
    threat_scores = {
        'high': {'within_10km': 'critical', 'within_25km': 'severe', 'within_50km': 'moderate', 'beyond': 'minor'},
        'nominal': {'within_10km': 'severe', 'within_25km': 'moderate', 'within_50km': 'minor', 'beyond': 'none'},
        'low': {'within_10km': 'moderate', 'within_25km': 'minor', 'within_50km': 'none', 'beyond': 'none'}
    }
    
    # Determine distance category
    if distance <= 10:
        distance_cat = 'within_10km'
    elif distance <= 25:
        distance_cat = 'within_25km'
    elif distance <= 50:
        distance_cat = 'within_50km'
    else:
        distance_cat = 'beyond'
    
    fire_threat_level = threat_scores[confidence][distance_cat]
    result['fire_threat_level'] = fire_threat_level
    
    # Risk elevation logic
    risk_elevation_map = {
        'low': {'critical': 'extreme', 'severe': 'high', 'moderate': 'moderate', 'minor': 'low', 'none': 'low'},
        'moderate': {'critical': 'extreme', 'severe': 'extreme', 'moderate': 'high', 'minor': 'moderate', 'none': 'moderate'},
        'high': {'critical': 'extreme', 'severe': 'extreme', 'moderate': 'extreme', 'minor': 'high', 'none': 'high'},
        'extreme': {'critical': 'extreme', 'severe': 'extreme', 'moderate': 'extreme', 'minor': 'extreme', 'none': 'extreme'}
    }
    
    if current_risk_level in risk_elevation_map:
        elevated_level = risk_elevation_map[current_risk_level][fire_threat_level]
        result['recommended_risk_elevation'] = elevated_level
    
    # Evacuation recommendation
    if fire_threat_level in ['critical', 'severe'] and distance <= 25:
        result['evacuation_recommended'] = True
        if fire_threat_level == 'critical':
            result['evacuation_reason'] = f"CRITICAL: Confirmed fire detected only {distance:.1f}km away (High confidence). Immediate evacuation strongly recommended."
        else:  # severe
            result['evacuation_reason'] = f"SEVERE: Confirmed fire detected {distance:.1f}km away ({confidence} confidence). Evacuation recommended."
    elif fire_threat_level == 'moderate' and distance <= 15:
        result['evacuation_recommended'] = True
        result['evacuation_reason'] = f"Confirmed fire detected {distance:.1f}km away. Consider evacuation preparation."
    
    return result


def get_fires_geojson(fires: List[Dict]) -> Dict:
    """
    Convert fire list to GeoJSON format for map visualization.
    
    Returns GeoJSON FeatureCollection with fire hotspots as point features.
    """
    features = []
    
    for fire in fires:
        # Handle both global fires (no distance_km) and location-specific fires (with distance_km)
        distance_text = f" | Distance: {fire.get('distance_km', 'N/A'):.1f}km" if 'distance_km' in fire else ""
        popup_text = f"Satellite Fire Detection\nConfidence: {fire['confidence_level']}{distance_text}\nPower: {fire['frp']:.0f}MW\nDate: {fire['acq_date']} {fire['acq_time']}"
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [fire['lon'], fire['lat']]
            },
            'properties': {
                'confidence': fire['confidence'],
                'confidence_level': fire['confidence_level'],
                'frp': fire['frp'],
                'distance_km': fire.get('distance_km', None),
                'acq_date': fire['acq_date'],
                'acq_time': fire['acq_time'],
                'satellite': fire['satellite'],
                'color': CONFIDENCE_LEVELS[fire['confidence_level']]['color'],
                'popup': popup_text
            }
        }
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }


def get_confidence_level_info(level: str) -> Dict:
    """Get styling and metadata for a confidence level."""
    return CONFIDENCE_LEVELS.get(level, CONFIDENCE_LEVELS['low'])


def is_fire_in_usa_canada(latitude: float, longitude: float) -> bool:
    """
    Check if fire coordinates fall within approximate USA/Canada bounds.
    
    Bounds:
    - Latitude: 15°N to 85°N (southern Mexico to Arctic)
    - Longitude: -170°W to -50°W (Pacific to Atlantic)
    """
    return 15 <= latitude <= 85 and -170 <= longitude <= -50


def fetch_recent_fires_global(days_back: int = 7, max_results: Optional[int] = 2000, 
                              region: str = 'usa_canada') -> List[Dict]:
    """
    Fetch recent FIRMS fires globally or filtered by region.
    
    Args:
        days_back: Number of days back to fetch (default 7, max 10)
        max_results: Maximum number of fire records to return (safety limit)
        region: 'usa_canada' (default) or 'global'
    
    Returns:
        List of fire dictionaries
    """
    try:
        # NASA FIRMS API requires area bounds [west,south,east,north] and day range [1-10]
        # For USA/Canada, use bounds: -180,-70,180,85 (covers entire region)
        days_back = min(max(days_back, 1), 10)  # Clamp to 1-10 range
        
        # Build proper API URL with area bounds and day count
        # Format: /api/area/csv/{key}/{dataset}/{bounds}/{day_range}
        area_bounds = "-180,-70,180,85"  # Global bounds for simplicity
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_API_KEY}/VIIRS_SNPP_NRT/{area_bounds}/{days_back}"
        
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        parsed = []
        
        # Parse CSV response
        import csv
        import io
        text = response.text
        # Skip empty lines and use io.StringIO for CSV reading
        lines = [line for line in text.splitlines() if line.strip()]
        if lines:
            try:
                reader = csv.DictReader(io.StringIO('\n'.join(lines)))
                fires_list = list(reader) if reader else []
            except:
                fires_list = []
        else:
            fires_list = []

        for fire in fires_list:
            try:
                lat_val = fire.get('latitude')
                lon_val = fire.get('longitude')
                conf_val = fire.get('confidence')
                frp_val = fire.get('frp')
                date_val = fire.get('acq_date', '')
                time_val = fire.get('acq_time', '')
                sat_val = fire.get('satellite', 'VIIRS')
                day_val = fire.get('daynight', 'N')
                
                if not lat_val or not lon_val:
                    continue
                    
                fire_lat = float(lat_val)
                fire_lon = float(lon_val)
                
                # Skip if coordinates are all zeros or missing
                if fire_lat == 0.0 and fire_lon == 0.0:
                    continue
                
                # Filter by region if specified
                if region == 'usa_canada' and not is_fire_in_usa_canada(fire_lat, fire_lon):
                    continue
                
                # Parse confidence level - NASA returns character code (h/n/l) or numeric string
                confidence_level = parse_confidence_level(conf_val)
                
                # For confidence numeric value, try to parse or use default
                try:
                    confidence_numeric = float(conf_val) if conf_val and conf_val not in ('h', 'n', 'l') else 0.0
                except (ValueError, TypeError):
                    confidence_numeric = 0.0

                parsed.append({
                    'lat': fire_lat,
                    'lon': fire_lon,
                    'confidence': confidence_numeric,
                    'confidence_level': confidence_level,
                    'frp': float(frp_val) if frp_val else 0.0,
                    'acq_date': str(date_val) if date_val else '',
                    'acq_time': str(time_val) if time_val else '',
                    'satellite': str(sat_val) if sat_val else 'VIIRS',
                    'daynight': str(day_val) if day_val else 'N'
                })
            except (ValueError, TypeError, AttributeError) as e:
                continue

        # Limit results to avoid overloading frontend
        if max_results and len(parsed) > max_results:
            parsed = parsed[:max_results]

        return parsed
    except requests.RequestException as e:
        print(f"⚠️  Error fetching global FIRMS data: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Unexpected error in FIRMS global fetch: {e}")
        return []

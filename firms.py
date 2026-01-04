"""
NASA FIRMS (Fire Information for Resource Management System) Integration
Provides real-time satellite-detected active fire hotspots with confidence levels.

API docs: https://firms.modaps.eosdis.nasa.gov/api/area/csv/
"""
import requests
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from math import radians, cos, sin, asin, sqrt
import os

# NASA FIRMS API Configuration
FIRMS_API_KEY = os.environ.get('FIRMS_API_KEY', '501896775f6b28df986593019e4634fe')

# Fire confidence levels mapping (NASA MODIS/VIIRS terminology)
CONFIDENCE_LEVELS = {
    'low': {'value': 30, 'label': 'Low Confidence', 'color': '#FFFF00', 'risk_boost': 0.1},
    'nominal': {'value': 60, 'label': 'Nominal Confidence', 'color': '#FFA500', 'risk_boost': 0.25},
    'high': {'value': 90, 'label': 'High Confidence', 'color': '#FF0000', 'risk_boost': 0.4}
}

DEFAULT_FIRE_CHECK_RADIUS_KM = 50  # Default radius to check for nearby fires


# ------------------ Utilities ------------------

def parse_confidence_level(confidence_score) -> str:
    """
    Convert NASA VIIRS confidence score to 'low', 'nominal', or 'high'.
    Accepts numeric (0-100) or character ('h', 'n', 'l').
    """
    if isinstance(confidence_score, str):
        c = confidence_score.lower().strip()
        if c in ('h', 'high'):
            return 'high'
        elif c in ('n', 'nominal'):
            return 'nominal'
        elif c in ('l', 'low'):
            return 'low'
        try:
            confidence_score = float(c)
        except ValueError:
            return 'nominal'
    try:
        score = float(confidence_score)
        if score >= 76:
            return 'high'
        elif score >= 41:
            return 'nominal'
        else:
            return 'low'
    except (ValueError, TypeError):
        return 'nominal'


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two coordinates in kilometers."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth radius in km


# ------------------ FIRMS Fetch ------------------

def fetch_firms_fires(latitude: float = None, longitude: float = None, days_back: int = 7) -> List[Dict]:
    """
    Fetch FIRMS fires for all USA + Canada.
    If latitude/longitude provided, calculates distance for threat analysis.
    """
    try:
        days_back = min(max(days_back, 1), 10)
        # USA + Canada bounding box
        west, south, east, north = -170, 15, -50, 85
        bounds = f"{west},{south},{east},{north}"

        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{FIRMS_API_KEY}/VIIRS_SNPP_NRT/{bounds}/{days_back}"
        )

        response = requests.get(url, timeout=20)
        response.raise_for_status()

        lines = [l for l in response.text.splitlines() if l.strip()]
        if not lines:
            return []

        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        fires: List[Dict] = []

        for row in reader:
            try:
                fire_lat = float(row.get("latitude", 0))
                fire_lon = float(row.get("longitude", 0))
                if fire_lat == 0.0 and fire_lon == 0.0:
                    continue

                confidence_raw = row.get("confidence")
                confidence_level = parse_confidence_level(confidence_raw)

                distance = None
                if latitude is not None and longitude is not None:
                    distance = calculate_distance_km(latitude, longitude, fire_lat, fire_lon)

                fires.append({
                    "lat": fire_lat,
                    "lon": fire_lon,
                    "confidence": float(confidence_raw) if confidence_raw not in ("h", "n", "l", None) else 0.0,
                    "confidence_level": confidence_level,
                    "frp": float(row.get("frp") or 0.0),
                    "acq_date": row.get("acq_date", ""),
                    "acq_time": row.get("acq_time", ""),
                    "distance_km": round(distance, 2) if distance is not None else None,
                    "satellite": row.get("satellite", "VIIRS"),
                    "daynight": row.get("daynight", "N"),
                })

            except (ValueError, TypeError):
                continue

        if latitude is not None and longitude is not None:
            fires.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 9999)

        return fires

    except requests.RequestException as e:
        print(f"⚠️ FIRMS request error: {e}")
        return []
    except Exception as e:
        print(f"⚠️ FIRMS processing error: {e}")
        return []


def fetch_recent_fires_global(days_back: int = 7, max_results: Optional[int] = 2000) -> List[Dict]:
    """
    Fetch recent FIRMS fires globally (USA + Canada) safely.
    """
    try:
        fires = fetch_firms_fires(days_back=days_back)
        return fires[:max_results] if max_results else fires
    except Exception as e:
        print(f"⚠️ FIRMS recent fetch error: {e}")
        return []


# ------------------ Threat Analysis ------------------

def analyze_active_fire_threat(latitude: float, longitude: float, current_risk_level: str) -> Dict:
    """
    Analyze active fire threat for a location and determine risk elevation.
    """
    fires = fetch_firms_fires(latitude, longitude)

    result = {
        "has_nearby_fires": len(fires) > 0,
        "nearby_fire_count": len(fires),
        "closest_fire_distance_km": fires[0]["distance_km"] if fires else None,
        "closest_fire_confidence": fires[0]["confidence_level"] if fires else None,
        "fires": fires,
        "fire_threat_level": "none",
        "recommended_risk_elevation": None,
        "evacuation_recommended": False,
        "evacuation_reason": ""
    }

    if not fires:
        return result

    closest_fire = fires[0]
    distance = closest_fire["distance_km"]
    confidence = closest_fire["confidence_level"]

    # Threat matrix
    threat_scores = {
        "high": {"within_10km": "critical", "within_25km": "severe", "within_50km": "moderate", "beyond": "minor"},
        "nominal": {"within_10km": "severe", "within_25km": "moderate", "within_50km": "minor", "beyond": "none"},
        "low": {"within_10km": "moderate", "within_25km": "minor", "within_50km": "none", "beyond": "none"}
    }

    if distance <= 10:
        distance_cat = "within_10km"
    elif distance <= 25:
        distance_cat = "within_25km"
    elif distance <= 50:
        distance_cat = "within_50km"
    else:
        distance_cat = "beyond"

    fire_threat_level = threat_scores[confidence][distance_cat]
    result["fire_threat_level"] = fire_threat_level

    # Risk elevation mapping
    risk_elevation_map = {
        "low": {"critical": "extreme", "severe": "high", "moderate": "moderate", "minor": "low", "none": "low"},
        "moderate": {"critical": "extreme", "severe": "extreme", "moderate": "high", "minor": "moderate", "none": "moderate"},
        "high": {"critical": "extreme", "severe": "extreme", "moderate": "extreme", "minor": "high", "none": "high"},
        "extreme": {"critical": "extreme", "severe": "extreme", "moderate": "extreme", "minor": "extreme", "none": "extreme"}
    }

    if current_risk_level in risk_elevation_map:
        result["recommended_risk_elevation"] = risk_elevation_map[current_risk_level][fire_threat_level]

    # Evacuation recommendation
    if fire_threat_level in ["critical", "severe"] and distance <= 25:
        result["evacuation_recommended"] = True
        if fire_threat_level == "critical":
            result["evacuation_reason"] = f"CRITICAL: Fire detected {distance:.1f}km away (High confidence). Immediate evacuation recommended."
        else:
            result["evacuation_reason"] = f"SEVERE: Fire detected {distance:.1f}km away ({confidence} confidence). Evacuation recommended."
    elif fire_threat_level == "moderate" and distance <= 15:
        result["evacuation_recommended"] = True
        result["evacuation_reason"] = f"Fire detected {distance:.1f}km away. Consider evacuation preparation."

    return result


# ------------------ GeoJSON Conversion ------------------

def get_fires_geojson(fires: List[Dict]) -> Dict:
    """
    Convert fire list to GeoJSON FeatureCollection for mapping.
    """
    features = []

    for fire in fires:
        distance_text = f" | Distance: {fire.get('distance_km', 'N/A'):.1f}km" if 'distance_km' in fire and fire['distance_km'] else ""
        popup_text = (
            f"Satellite Fire Detection\nConfidence: {fire['confidence_level']}{distance_text}\n"
            f"Power: {fire['frp']:.0f}MW\nDate: {fire['acq_date']} {fire['acq_time']}"
        )

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [fire["lon"], fire["lat"]]},
            "properties": {
                "confidence": fire["confidence"],
                "confidence_level": fire["confidence_level"],
                "frp": fire["frp"],
                "distance_km": fire.get("distance_km"),
                "acq_date": fire["acq_date"],
                "acq_time": fire["acq_time"],
                "satellite": fire["satellite"],
                "color": CONFIDENCE_LEVELS[fire["confidence_level"]]["color"],
                "popup": popup_text
            }
        })

    return {"type": "FeatureCollection", "features": features}


def get_confidence_level_info(level: str) -> Dict:
    """Return styling/metadata for a confidence level."""
    return CONFIDENCE_LEVELS.get(level, CONFIDENCE_LEVELS['low'])

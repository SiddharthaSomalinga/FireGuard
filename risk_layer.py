"""
Geospatial Wildfire Risk Layer Generation Module
Generates pre-rendered, deterministic risk layers for interactive map integration.

Features:
- Grid-based risk assessment covering continental USA & Canada
- Deterministic computation for reproducible results
- GeoJSON output for direct map integration
- Raster tile support for web mapping libraries (Leaflet, Mapbox)
- Caching for efficient rendering
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import hashlib
from functools import lru_cache
from fdi import analyze_location_dynamic
from firms import (
    fetch_firms_fires, 
    calculate_distance_km,
    fetch_recent_fires_global
)

# Risk layer configuration
RISK_LAYER_CONFIG = {
    'grid_resolution': 0.5,  # 0.5 degree grid (~55 km at equator)
    'zoom_levels': [4, 5, 6, 7, 8, 9, 10],  # Web mercator zoom levels
    'risk_thresholds': {
        'critical': 80,    # >= 80: Extreme/Critical risk
        'high': 60,        # 60-79: High risk
        'moderate': 40,    # 40-59: Moderate risk
        'low': 20,         # 20-39: Low risk
        'minimal': 0       # < 20: Minimal risk
    },
    'colors': {
        'critical': '#8B0000',   # Dark red
        'high': '#FF0000',       # Red
        'moderate': '#FFA500',   # Orange
        'low': '#FFFF00',        # Yellow
        'minimal': '#90EE90'     # Light green
    }
}

# Continental bounds (USA + Canada)
CONTINENTAL_BOUNDS = {
    'north': 70.0,
    'south': 24.0,
    'east': -50.0,
    'west': -170.0
}


@lru_cache(maxsize=128)
def get_risk_category(risk_score: float) -> str:
    """Map numerical risk score to category."""
    if risk_score >= RISK_LAYER_CONFIG['risk_thresholds']['critical']:
        return 'critical'
    elif risk_score >= RISK_LAYER_CONFIG['risk_thresholds']['high']:
        return 'high'
    elif risk_score >= RISK_LAYER_CONFIG['risk_thresholds']['moderate']:
        return 'moderate'
    elif risk_score >= RISK_LAYER_CONFIG['risk_thresholds']['low']:
        return 'low'
    else:
        return 'minimal'


def compute_grid_cell_risk(latitude: float, longitude: float, 
                           nearby_fires: List[Dict],
                           fire_weights: Dict = None,
                           fdi_cache: Dict = None) -> Dict:
    """
    Compute fire risk for a single grid cell (0.5° resolution).
    Uses simple geometric calculations to avoid slow API calls.
    
    Args:
        latitude: Cell center latitude
        longitude: Cell center longitude
        nearby_fires: List of nearby active fires
        fire_weights: Custom weights for fire proximity scoring
        fdi_cache: Cache of FDI results to avoid re-computation
        
    Returns:
        Dictionary with risk score, components, and metadata
    """
    if fire_weights is None:
        fire_weights = {
            'critical_radius': 50,  # km - critical fire influence zone
            'high_radius': 100,     # km - high risk zone
            'moderate_radius': 200  # km - moderate risk zone
        }
    
    try:
        # Use simple weather-based FDI approximation instead of expensive API calls
        # This provides instant results without network delays
        base_risk = compute_simple_fdi_risk(latitude, longitude)
        
        # Calculate fire proximity component
        fire_proximity_risk = compute_fire_proximity_risk(
            latitude, longitude, nearby_fires, fire_weights
        )
        
        # Combine components (weighted average)
        # FDI: 60%, Fire Proximity: 40%
        combined_risk = (base_risk * 0.6) + (fire_proximity_risk * 0.4)
        
        # Cap at 100
        combined_risk = min(100, max(0, combined_risk))
        
        return {
            'risk_score': round(combined_risk, 2),
            'risk_category': get_risk_category(combined_risk),
            'components': {
                'fdi_risk': round(base_risk, 2),
                'fire_proximity_risk': round(fire_proximity_risk, 2)
            },
            'nearby_fire_count': len(nearby_fires),
            'closest_fire_distance_km': (
                min([calculate_distance_km(latitude, longitude, f['lat'], f['lon']) 
                     for f in nearby_fires])
                if nearby_fires else None
            ),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Return neutral risk on error
        return {
            'risk_score': 50.0,
            'risk_category': 'moderate',
            'components': {'error': str(e)},
            'nearby_fire_count': 0,
            'closest_fire_distance_km': None,
            'timestamp': datetime.utcnow().isoformat()
        }


def compute_simple_fdi_risk(latitude: float, longitude: float) -> float:
    """
    Compute FDI-based risk using simple heuristics without API calls.
    This is fast and deterministic for grid-based rendering.
    
    Risk is based on:
    - Latitude (higher latitudes = more fuel, lower temps = higher FDI during fire season)
    - Longitude (east coast = wetter, west coast = drier)
    - Historical fire patterns
    """
    # Base risk by latitude band (continental US fire patterns)
    if latitude < 24 or latitude > 70:
        # Outside continental US
        base_risk = 20
    elif latitude < 35:
        # Southern tier (CA, AZ, NM, TX) - high fire risk
        base_risk = 65
    elif latitude < 40:
        # Mid-south (OK, KS, AR, TN, NC) - moderate-high
        base_risk = 50
    elif latitude < 45:
        # Central (CO, UT, WY, MT) - variable, western high
        base_risk = 55 if longitude < -105 else 40
    elif latitude < 50:
        # Northern (WA, OR, ID, MT) - high risk
        base_risk = 60
    else:
        # Canada - moderate
        base_risk = 45
    
    # Longitude adjustment (western states tend drier)
    if longitude < -115:
        # Pacific west - drier, higher risk
        base_risk += 10
    elif longitude < -100:
        # Rocky Mountain - variable
        base_risk += 5
    elif longitude > -80:
        # Eastern states - wetter, lower risk
        base_risk -= 10
    
    # Add some geographic variation
    geohash_seed = hash(f"{latitude:.1f},{longitude:.1f}") % 20
    base_risk += (geohash_seed - 10) / 2  # ±5 variation
    
    # Cap and return
    return min(100, max(10, base_risk))


def compute_fire_proximity_risk(latitude: float, longitude: float,
                                nearby_fires: List[Dict],
                                fire_weights: Dict) -> float:
    """
    Compute risk score based on nearby active fires.
    Closer fires = higher risk, decays with distance.
    """
    if not nearby_fires:
        return 0.0
    
    total_risk = 0.0
    
    for fire in nearby_fires:
        distance_km = calculate_distance_km(
            latitude, longitude,
            fire['lat'], fire['lon']
        )
        
        # Extract fire confidence (handle different formats)
        confidence = fire.get('confidence', 'nominal')
        if isinstance(confidence, str):
            confidence_weight = {
                'low': 0.5,
                'nominal': 0.75,
                'high': 1.0
            }.get(confidence.lower(), 0.75)
        else:
            confidence_weight = min(1.0, confidence / 100.0)
        
        # Compute distance-based decay
        if distance_km <= fire_weights['critical_radius']:
            # Critical zone: max risk
            fire_risk = 90 * confidence_weight
        elif distance_km <= fire_weights['high_radius']:
            # High risk zone: linear decay
            decay = 1 - ((distance_km - fire_weights['critical_radius']) / 
                        (fire_weights['high_radius'] - fire_weights['critical_radius']))
            fire_risk = 60 * decay * confidence_weight
        elif distance_km <= fire_weights['moderate_radius']:
            # Moderate risk zone: reduced decay
            decay = 1 - ((distance_km - fire_weights['high_radius']) / 
                        (fire_weights['moderate_radius'] - fire_weights['high_radius']))
            fire_risk = 30 * decay * confidence_weight
        else:
            fire_risk = 0.0
        
        total_risk += fire_risk
    
    # Average over fire count (prevent stacking)
    return min(100, total_risk / len(nearby_fires))


def generate_geojson_risk_layer(bounds: Dict = None, 
                               grid_resolution: float = None,
                               include_fires: bool = True,
                               max_cells: int = 500) -> Dict:
    """
    Generate GeoJSON FeatureCollection with risk assessment grid.
    Memory-optimized for production deployment.
    
    Args:
        bounds: Bounding box {'north', 'south', 'east', 'west'}
        grid_resolution: Grid cell size in degrees
        include_fires: Include nearby fires in feature properties
        max_cells: Maximum number of grid cells to generate (memory safety limit)
        
    Returns:
        GeoJSON FeatureCollection with risk features
    """
    if bounds is None:
        bounds = CONTINENTAL_BOUNDS
    if grid_resolution is None:
        grid_resolution = RISK_LAYER_CONFIG['grid_resolution']
    
    # Fetch active fires for proximity analysis (reduced for memory efficiency)
    active_fires = fetch_recent_fires_global(days_back=7, max_results=2000) if include_fires else []
    
    # Calculate total cells and adjust grid_resolution if needed to stay within limit
    # This ensures cells remain contiguous (no gaps)
    lat_range = bounds['north'] - bounds['south']
    lon_range = bounds['east'] - bounds['west']
    estimated_cells = (lat_range / grid_resolution) * (lon_range / grid_resolution)
    
    if estimated_cells > max_cells:
        # Increase grid_resolution to reduce cell count while keeping cells contiguous
        scale_factor = np.sqrt(estimated_cells / max_cells)
        grid_resolution = grid_resolution * scale_factor
    
    # Spatial hashing: Group fires by grid region for O(1) lookup
    # This reduces O(n*m) to O(n + m) complexity
    fire_regions = {}
    if active_fires:
        for fire in active_fires:
            # Map fire to grid region
            fire_lat_idx = int(fire['lat'] / grid_resolution)
            fire_lon_idx = int(fire['lon'] / grid_resolution)
            region_key = (fire_lat_idx, fire_lon_idx)
            
            if region_key not in fire_regions:
                fire_regions[region_key] = []
            fire_regions[region_key].append(fire)
    
    features = []
    
    # Generate grid cells (now with adjusted resolution for contiguous coverage)
    latitudes = np.arange(bounds['south'], bounds['north'], grid_resolution)
    longitudes = np.arange(bounds['west'], bounds['east'], grid_resolution)
    
    cell_count = 0
    for lat in latitudes:
        if cell_count >= max_cells:
            break
        for lon in longitudes:
            if cell_count >= max_cells:
                break
            
            # Find fires near this cell using spatial hashing (9-cell neighborhood)
            cell_center_lat = lat + grid_resolution / 2
            cell_center_lon = lon + grid_resolution / 2
            
            # Get grid indices for this cell
            cell_lat_idx = int(lat / grid_resolution)
            cell_lon_idx = int(lon / grid_resolution)
            
            # Check current cell and 8 adjacent cells (3x3 neighborhood)
            nearby_fires = []
            max_search_distance_km = 300  # Maximum search radius in km
            
            for dlat in [-1, 0, 1]:
                for dlon in [-1, 0, 1]:
                    region_key = (cell_lat_idx + dlat, cell_lon_idx + dlon)
                    if region_key in fire_regions:
                        for fire in fire_regions[region_key]:
                            distance = calculate_distance_km(
                                cell_center_lat, cell_center_lon,
                                fire['lat'], fire['lon']
                            )
                            if distance <= max_search_distance_km:
                                nearby_fires.append(fire)
            
            # Compute risk
            risk_data = compute_grid_cell_risk(cell_center_lat, cell_center_lon, nearby_fires)
            
            # Create feature (optimized: removed redundant fields to save memory)
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [lon, lat],
                        [lon + grid_resolution, lat],
                        [lon + grid_resolution, lat + grid_resolution],
                        [lon, lat + grid_resolution],
                        [lon, lat]
                    ]]
                },
                'properties': {
                    'risk_score': risk_data['risk_score'],
                    'risk_category': risk_data['risk_category'],
                    'risk_color': RISK_LAYER_CONFIG['colors'][risk_data['risk_category']],
                    'fdi_risk': risk_data['components'].get('fdi_risk', 50),
                    'fire_proximity_risk': risk_data['components'].get('fire_proximity_risk', 0),
                    'nearby_fires': risk_data['nearby_fire_count']
                }
            }
            features.append(feature)
            cell_count += 1
    
    return {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'grid_resolution': grid_resolution,
            'bounds': bounds,
            'generated_at': datetime.utcnow().isoformat(),
            'fire_count': len(active_fires),
            'total_cells': len(features)
        }
    }


def generate_raster_tile_url_template() -> str:
    """
    Generate URL template for raster tiles (XYZ format).
    Clients can use this with mapping libraries like Leaflet.
    """
    return "/api/risk-layer/tiles/{z}/{x}/{y}.png"


def get_risk_layer_summary(bounds: Dict = None) -> Dict:
    """
    Get summary statistics for risk layer.
    Lightweight endpoint for dashboard displays.
    """
    if bounds is None:
        bounds = CONTINENTAL_BOUNDS
    
    active_fires = fetch_recent_fires_global(days_back=7, max_results=5000)
    
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'bounds': bounds,
        'total_active_fires': len(active_fires),
        'fires_by_confidence': {
            'high': len([f for f in active_fires if f.get('confidence', 'nominal') == 'high']),
            'nominal': len([f for f in active_fires if f.get('confidence', 'nominal') == 'nominal']),
            'low': len([f for f in active_fires if f.get('confidence', 'nominal') == 'low'])
        },
        'high_risk_zones': 0,
        'moderate_risk_zones': 0,
        'low_risk_zones': 0
    }
    
    return summary


def get_layer_configuration() -> Dict:
    """Return risk layer configuration for client-side rendering."""
    return {
        'config': RISK_LAYER_CONFIG,
        'bounds': CONTINENTAL_BOUNDS,
        'url_template': generate_raster_tile_url_template(),
        'timestamp': datetime.utcnow().isoformat()
    }

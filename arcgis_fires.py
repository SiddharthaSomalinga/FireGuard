"""
ArcGIS Wildfire Data Integration
Uses public ArcGIS REST services for active fire perimeters and wildfire data.
No API key required for public services.

Data Sources:
1. NIFC/WFIGS Active Fire Perimeters
2. USGS Fire Detection (MODIS)
3. ArcGIS Living Atlas Wildfire Layers
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from math import radians, cos, sin, asin, sqrt


def _normalize_arcgis_timestamp(value: Optional[object]) -> str:
    """Convert ArcGIS millisecond timestamps to ISO string; return original if unknown."""
    if value is None:
        return ''
    # Already ISO-like
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit() and len(stripped) >= 12:
            try:
                ms = int(stripped)
                return datetime.utcfromtimestamp(ms / 1000).isoformat() + 'Z'
            except Exception:
                return value
        return value
    # Numeric epoch millis
    try:
        if isinstance(value, (int, float)) and value > 1e11:
            return datetime.utcfromtimestamp(float(value) / 1000).isoformat() + 'Z'
    except Exception:
        pass
    return str(value)


# Public ArcGIS wildfire service endpoints (no API key required)
ARCGIS_SERVICES = {
    'nifc_perimeters': {
        'url': 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Public_Wildfire_Perimeters_View/FeatureServer/0/query',
        'description': 'NIFC Active Fire Perimeters'
    },
    'wfigs_current': {
        'url': 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query',
        'description': 'Current Wildland Fire Perimeters'
    },
    'modis_thermal': {
        'url': 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/MODIS_Thermal_v1/FeatureServer/0/query',
        'description': 'MODIS Thermal Hotspots'
    },
    'usa_wildfires': {
        'url': 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/USA_Wildfires_v1/FeatureServer/0/query',
        'description': 'USA Active Wildfires'
    }
}


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two coordinates in kilometers."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def fetch_arcgis_fire_perimeters(days_back: int = 7) -> List[Dict]:
    """
    Fetch current wildfire perimeters from ArcGIS/NIFC with a resilient fallback.
    Switch to JSON (not GeoJSON) to avoid 400s and retry the alternate layer if needed.
    """
    def request_perimeters(url: str, start_date: datetime) -> List[Dict]:
        params = {
            'where': f"CreateDate >= timestamp '{start_date.strftime('%Y-%m-%d 00:00:00')}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': 4326,
            'f': 'json',  # GeoJSON intermittently 400s; json is stable
            'resultRecordCount': 2000,
            'resultOffset': 0
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        features = data.get('features', [])
        perims: List[Dict] = []

        for feature in features:
            attrs = feature.get('attributes', {})
            geometry = feature.get('geometry', {}) or {}

            fire_info = {
                'fire_name': attrs.get('IncidentName', attrs.get('FIRE_NAME', 'Unknown Fire')),
                'acres': attrs.get('GISAcres', attrs.get('ACRES', 0)),
                'containment': attrs.get('PercentContained', attrs.get('CONTAINMENT', 0)),
                'discovery_date': _normalize_arcgis_timestamp(attrs.get('FireDiscoveryDateTime', attrs.get('DISCOVERY_DATE', ''))),
                'fire_type': attrs.get('IncidentTypeCategory', 'Wildfire'),
                'status': attrs.get('FireCause', 'Active'),
                'state': attrs.get('POOState', ''),
                'county': attrs.get('POOCounty', ''),
                'residences_destroyed': attrs.get('ResidencesDestroyed', attrs.get('Residences', 0)),
                'structures_destroyed': attrs.get('OtherStructuresDestroyed', attrs.get('StructuresDestroyed', 0)),
                'update_time': _normalize_arcgis_timestamp(attrs.get('ModifiedOn', '')),
                'geometry': geometry,
                'source': 'ArcGIS NIFC'
            }

            # Calculate centroid from rings if present
            rings = geometry.get('rings')
            if rings and len(rings) > 0:
                coords = rings[0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    fire_info['lat'] = sum(lats) / len(lats)
                    fire_info['lon'] = sum(lons) / len(lons)

            perims.append(fire_info)

        return perims

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Primary attempt: NIFC perimeters
        try:
            return request_perimeters(ARCGIS_SERVICES['nifc_perimeters']['url'], start_date)
        except Exception as primary_err:
            print(f"Primary NIFC perimeter fetch failed, retrying fallback: {primary_err}")
            # Fallback to the alternate perimeters layer
            try:
                fallback = request_perimeters(ARCGIS_SERVICES['wfigs_current']['url'], start_date)
                if fallback:
                    return fallback
            except Exception as secondary_err:
                print(f"Fallback WFIGS perimeter fetch failed: {secondary_err}")
            # If both fail, bubble the first error for visibility
            raise primary_err

    except Exception as e:
        print(f"Error fetching ArcGIS fire perimeters: {e}")
        return []


def fetch_arcgis_thermal_hotspots(days_back: int = 1, max_results: int = 5000) -> List[Dict]:
    """
    Fetch MODIS thermal hotspots from ArcGIS.
    Similar to NASA FIRMS but through ArcGIS infrastructure.
    Limited to max_results for performance.
    """
    try:
        # Query for recent thermal detections
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'where': f"ACQ_DATE >= timestamp '{start_date.strftime('%Y-%m-%d 00:00:00')}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'json',
            'resultRecordCount': 5000
        }
        
        response = requests.get(
            ARCGIS_SERVICES['modis_thermal']['url'],
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        hotspots = []
        
        if 'features' in data:
            for feature in data['features']:
                attrs = feature.get('attributes', {})
                geometry = feature.get('geometry', {})
                
                hotspot = {
                    'lat': geometry.get('y', 0) if geometry else 0,
                    'lon': geometry.get('x', 0) if geometry else 0,
                    'brightness': attrs.get('BRIGHTNESS', 0),
                    'confidence': attrs.get('CONFIDENCE', 0),
                    'frp': attrs.get('FRP', 0),  # Fire Radiative Power
                    'acq_date': attrs.get('ACQ_DATE', ''),
                    'acq_time': attrs.get('ACQ_TIME', ''),
                    'satellite': attrs.get('SATELLITE', 'MODIS'),
                    'source': 'ArcGIS MODIS'
                }
                
                # Map confidence to categories
                conf_value = hotspot['confidence']
                if conf_value >= 80:
                    hotspot['confidence_level'] = 'high'
                elif conf_value >= 50:
                    hotspot['confidence_level'] = 'nominal'
                else:
                    hotspot['confidence_level'] = 'low'
                
                hotspots.append(hotspot)
        
        return hotspots
        
    except Exception as e:
        print(f"Error fetching ArcGIS thermal hotspots: {e}")
        return []


def fetch_arcgis_active_wildfires(days_back: int = 7) -> List[Dict]:
    """
    Fetch active wildfires from ArcGIS USA Wildfires layer.
    Combines multiple data sources into one comprehensive dataset.
    """
    try:
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'json',
            'resultRecordCount': 2000,
            'orderByFields': 'ModifiedOnDateTime DESC'
        }
        
        response = requests.get(
            ARCGIS_SERVICES['usa_wildfires']['url'],
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        wildfires = []
        seen_keys = set()
        
        if 'features' in data:
            for feature in data['features']:
                attrs = feature.get('attributes', {})
                geometry = feature.get('geometry', {})
                
                unique_key = attrs.get('UniqueFireIdentifier') or attrs.get('IrwinID') or attrs.get('IncidentName', '')
                if unique_key in seen_keys:
                    continue
                seen_keys.add(unique_key)

                wildfire = {
                    'fire_name': attrs.get('IncidentName', attrs.get('FIRE_NAME', 'Unknown')),
                    'lat': geometry.get('y', 0) if geometry else attrs.get('Y', 0),
                    'lon': geometry.get('x', 0) if geometry else attrs.get('X', 0),
                    'acres': attrs.get('DailyAcres', attrs.get('ACRES', 0)) or 0,
                    'containment': attrs.get('PercentContained', 0) or 0,
                    'personnel': attrs.get('PersonnelInvolved', 0) or 0,
                    'status': attrs.get('FireDiscoveryDateTime', 'Active'),
                    'fire_cause': attrs.get('FireCause', 'Unknown'),
                    'state': attrs.get('POOState', ''),
                    'county': attrs.get('POOCounty', ''),
                    'discovery_date': _normalize_arcgis_timestamp(attrs.get('FireDiscoveryDateTime', '')),
                    'update_time': _normalize_arcgis_timestamp(attrs.get('ModifiedOn', '')),
                    'residences_destroyed': attrs.get('ResidencesDestroyed') or 0,
                    'structures_destroyed': attrs.get('OtherStructuresDestroyed') or 0,
                    'fatalities': attrs.get('Fatalities') or 0,
                    'injuries': attrs.get('Injuries') or 0,
                    'source': 'ArcGIS USA Wildfires'
                }
                
                # Add confidence based on data completeness
                acres = wildfire.get('acres', 0) or 0
                if wildfire['fire_name'] != 'Unknown' and acres > 0:
                    wildfire['confidence_level'] = 'high'
                    wildfire['confidence'] = 90
                    wildfire['frp'] = wildfire['acres'] * 10  # Rough estimate
                else:
                    wildfire['confidence_level'] = 'nominal'
                    wildfire['confidence'] = 60
                    wildfire['frp'] = 50
                
                wildfires.append(wildfire)

        # Second pass: explicitly fetch incidents with destroyed structures to ensure we include them even if not in the primary page
        try:
            params_impacts = {
                'where': '(ResidencesDestroyed > 0) OR (OtherStructuresDestroyed > 0)',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'json',
                'resultRecordCount': 500,
                'orderByFields': 'ResidencesDestroyed DESC, OtherStructuresDestroyed DESC, ModifiedOnDateTime DESC'
            }
            resp_impacts = requests.get(
                ARCGIS_SERVICES['usa_wildfires']['url'],
                params=params_impacts,
                timeout=30
            )
            resp_impacts.raise_for_status()
            data_impacts = resp_impacts.json()
            for feature in data_impacts.get('features', []):
                attrs = feature.get('attributes', {})
                geometry = feature.get('geometry', {})
                unique_key = attrs.get('UniqueFireIdentifier') or attrs.get('IrwinID') or attrs.get('IncidentName', '')
                if unique_key in seen_keys:
                    continue
                seen_keys.add(unique_key)

                wildfire = {
                    'fire_name': attrs.get('IncidentName', attrs.get('FIRE_NAME', 'Unknown')),
                    'lat': geometry.get('y', 0) if geometry else attrs.get('Y', 0),
                    'lon': geometry.get('x', 0) if geometry else attrs.get('X', 0),
                    'acres': attrs.get('DailyAcres', attrs.get('ACRES', 0)) or 0,
                    'containment': attrs.get('PercentContained', 0) or 0,
                    'personnel': attrs.get('PersonnelInvolved', 0) or 0,
                    'status': attrs.get('FireDiscoveryDateTime', 'Active'),
                    'fire_cause': attrs.get('FireCause', 'Unknown'),
                    'state': attrs.get('POOState', ''),
                    'county': attrs.get('POOCounty', ''),
                    'discovery_date': attrs.get('FireDiscoveryDateTime', ''),
                    'update_time': attrs.get('ModifiedOn', ''),
                    'residences_destroyed': attrs.get('ResidencesDestroyed') or 0,
                    'structures_destroyed': attrs.get('OtherStructuresDestroyed') or 0,
                    'fatalities': attrs.get('Fatalities') or 0,
                    'injuries': attrs.get('Injuries') or 0,
                    'source': 'ArcGIS USA Wildfires'
                }

                acres = wildfire.get('acres', 0) or 0
                if wildfire['fire_name'] != 'Unknown' and acres > 0:
                    wildfire['confidence_level'] = 'high'
                    wildfire['confidence'] = 90
                    wildfire['frp'] = wildfire['acres'] * 10
                else:
                    wildfire['confidence_level'] = 'nominal'
                    wildfire['confidence'] = 60
                    wildfire['frp'] = 50

                wildfires.append(wildfire)
        except Exception as e:
            print(f"Error fetching impact-focused wildfires: {e}")
        
        return wildfires
        
    except Exception as e:
        print(f"Error fetching ArcGIS active wildfires: {e}")
        return []


def fetch_all_arcgis_fires(days_back: int = 7, include_hotspots: bool = True) -> Dict:
    """
    Fetch all available fire data from ArcGIS services.
    Combines perimeters, active fires, and thermal hotspots.
    
    Returns:
        Dict with 'perimeters', 'active_fires', 'thermal_hotspots', and 'combined' lists
    """
    result = {
        'perimeters': [],
        'active_fires': [],
        'thermal_hotspots': [],
        'combined': [],
        'total_count': 0,
        'sources': []
    }
    
    # Fetch fire perimeters
    try:
        perimeters = fetch_arcgis_fire_perimeters(days_back)
        result['perimeters'] = perimeters
        result['sources'].append('NIFC Perimeters')
        print(f"Fetched {len(perimeters)} fire perimeters from ArcGIS")
    except Exception as e:
        print(f"Failed to fetch perimeters: {e}")
    
    # Fetch active wildfires
    try:
        active = fetch_arcgis_active_wildfires(days_back)
        result['active_fires'] = active
        result['sources'].append('USA Wildfires')
        print(f"Fetched {len(active)} active wildfires from ArcGIS")
    except Exception as e:
        print(f"Failed to fetch active fires: {e}")
    
    # Fetch thermal hotspots (only recent ones)
    if include_hotspots:
        try:
            hotspots = fetch_arcgis_thermal_hotspots(min(days_back, 2))
            result['thermal_hotspots'] = hotspots
            result['sources'].append('MODIS Thermal')
            print(f"Fetched {len(hotspots)} thermal hotspots from ArcGIS")
        except Exception as e:
            print(f"Failed to fetch thermal hotspots: {e}")
    
    # Combine all into unified format
    combined = []
    
    # Add perimeters to combined
    for fire in result['perimeters']:
        if 'lat' in fire and 'lon' in fire:
            combined.append({
                'lat': fire['lat'],
                'lon': fire['lon'],
                'fire_name': fire['fire_name'],
                'acres': fire['acres'],
                'containment': fire['containment'],
                'confidence_level': 'high',
                'confidence': 95,
                'frp': fire['acres'] * 10,
                'type': 'perimeter',
                'source': fire['source'],
                'brightness': 350,
                'acq_date': datetime.now().strftime('%Y-%m-%d'),
                'acq_time': datetime.now().strftime('%H:%M'),
                'satellite': 'ArcGIS',
                'county': fire.get('county', ''),
                'state': fire.get('state', ''),
                'fire_type': fire.get('fire_type', 'Wildfire'),
                'status': fire.get('status', ''),
                'discovery_date': fire.get('discovery_date', ''),
                'update_time': fire.get('update_time', ''),
                'residences_destroyed': fire.get('residences_destroyed', 0),
                'structures_destroyed': fire.get('structures_destroyed', 0)
            })
    
    # Add active fires to combined
    for fire in result['active_fires']:
        combined.append({
            'lat': fire['lat'],
            'lon': fire['lon'],
            'fire_name': fire.get('fire_name', 'Wildfire'),
            'acres': fire.get('acres', 0),
            'containment': fire.get('containment', 0),
            'confidence_level': fire['confidence_level'],
            'confidence': fire['confidence'],
            'frp': fire['frp'],
            'type': 'active_fire',
            'source': fire['source'],
            'brightness': 350,
            'acq_date': datetime.now().strftime('%Y-%m-%d'),
            'acq_time': datetime.now().strftime('%H:%M'),
            'satellite': fire['source'],
            'county': fire.get('county', ''),
            'state': fire.get('state', ''),
            'fire_type': fire.get('fire_type', 'Wildfire'),
            'status': fire.get('status', ''),
            'discovery_date': fire.get('discovery_date', ''),
            'update_time': fire.get('update_time', ''),
            'fire_cause': fire.get('fire_cause', ''),
            'personnel': fire.get('personnel', 0),
            'residences_destroyed': fire.get('residences_destroyed', 0),
            'structures_destroyed': fire.get('structures_destroyed', 0),
            'fatalities': fire.get('fatalities', 0),
            'injuries': fire.get('injuries', 0)
        })
    
    # Add thermal hotspots to combined
    for hotspot in result['thermal_hotspots']:
        combined.append({
            'lat': hotspot['lat'],
            'lon': hotspot['lon'],
            'fire_name': 'Thermal Detection',
            'acres': 0,
            'containment': 0,
            'confidence_level': hotspot['confidence_level'],
            'confidence': hotspot['confidence'],
            'frp': hotspot['frp'],
            'type': 'thermal',
            'source': hotspot['source'],
            'brightness': hotspot['brightness'],
            'acq_date': hotspot['acq_date'],
            'acq_time': hotspot['acq_time'],
            'satellite': hotspot['satellite']
        })
    
    result['combined'] = combined
    result['total_count'] = len(combined)
    
    return result


def get_arcgis_fires_geojson(days_back: int = 7) -> Dict:
    """
    Get all ArcGIS fire data as GeoJSON for map display.
    """
    fire_data = fetch_all_arcgis_fires(days_back, include_hotspots=True)
    
    features = []
    for fire in fire_data['combined']:
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [fire['lon'], fire['lat']]
            },
            'properties': fire
        }
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'total_fires': fire_data['total_count'],
            'sources': fire_data['sources'],
            'generated_at': datetime.now().isoformat(),
            'days_back': days_back
        }
    }
    
    return geojson


if __name__ == '__main__':
    print("Testing ArcGIS Fire Data Integration...")
    print("=" * 60)
    
    result = fetch_all_arcgis_fires(days_back=7, include_hotspots=True)
    
    print(f"\n📊 Results Summary:")
    print(f"  Fire Perimeters: {len(result['perimeters'])}")
    print(f"  Active Wildfires: {len(result['active_fires'])}")
    print(f"  Thermal Hotspots: {len(result['thermal_hotspots'])}")
    print(f"  Total Combined: {result['total_count']}")
    print(f"  Data Sources: {', '.join(result['sources'])}")
    
    if result['combined']:
        print(f"\n🔥 Sample Fire Data:")
        for i, fire in enumerate(result['combined'][:5], 1):
            print(f"  {i}. {fire.get('fire_name', 'Unknown')} - "
                  f"{fire['type']} ({fire['confidence_level']} confidence)")

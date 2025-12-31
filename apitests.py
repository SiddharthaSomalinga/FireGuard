import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

_CACHE_SESSION = None
_RETRY_SESSION = None

def _get_session():
    """Get or create global cached session for connection pooling."""
    global _CACHE_SESSION, _RETRY_SESSION
    if _CACHE_SESSION is None:
        _CACHE_SESSION = requests_cache.CachedSession('.cache', expire_after=3600)
        _RETRY_SESSION = retry(_CACHE_SESSION, retries=5, backoff_factor=0.2)
    return _RETRY_SESSION

def test_separator(title):
    """Print a nice separator for test sections."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_open_meteo_archive():
    """Test Open-Meteo Archive API for historical rainfall data."""
    test_separator("TEST 1: Open-Meteo Archive API (Historical Rainfall)")
    
    try:
        retry_session = _get_session()
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # Test coordinates: Frisco, TX
        latitude = 33.1507
        longitude = -96.8236
        
        end_date = datetime.now().date()
        start_date = (end_date - timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": "rain"
        }
        
        print(f"📍 Testing location: {latitude}, {longitude}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print("🔄 Fetching data...\n")
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        hourly = response.Hourly()
        rain = hourly.Variables(0).ValuesAsNumpy()
        
        print(f"✅ SUCCESS!")
        print(f"   - Location: {response.Latitude()}°N, {response.Longitude()}°E")
        print(f"   - Elevation: {response.Elevation()} m")
        print(f"   - Data points received: {len(rain)}")
        print(f"   - Total rainfall: {sum(rain):.2f} mm")
        print(f"   - Max hourly rain: {max(rain):.2f} mm")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_open_meteo_forecast():
    """Test Open-Meteo Forecast API for current weather."""
    test_separator("TEST 2: Open-Meteo Forecast API (Current Weather)")
    
    try:
        retry_session = _get_session()
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        latitude = 33.1507
        longitude = -96.8236
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"]
        }
        
        print(f"📍 Testing location: {latitude}, {longitude}")
        print("🔄 Fetching current weather...\n")
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        current = response.Current()
        
        temp = current.Variables(0).Value()
        humidity = current.Variables(1).Value()
        wind = current.Variables(2).Value()
        precip = current.Variables(3).Value()
        
        print(f"✅ SUCCESS!")
        print(f"   - Temperature: {temp:.1f}°C")
        print(f"   - Humidity: {humidity:.1f}%")
        print(f"   - Wind Speed: {wind:.1f} km/h")
        print(f"   - Precipitation: {precip:.2f} mm")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_open_elevation():
    """Test Open-Elevation API for terrain data."""
    test_separator("TEST 3: Open-Elevation API (Terrain/Elevation)")
    
    try:
        latitude = 33.1507
        longitude = -96.8236
        
        # Sample 5 points for slope calculation
        offset = 0.001
        points = [
            {"latitude": latitude, "longitude": longitude},
            {"latitude": latitude + offset, "longitude": longitude},
            {"latitude": latitude - offset, "longitude": longitude},
            {"latitude": latitude, "longitude": longitude + offset},
            {"latitude": latitude, "longitude": longitude - offset},
        ]
        
        print(f"📍 Testing location: {latitude}, {longitude}")
        print(f"🔄 Fetching elevation for 5 sample points...\n")
        
        response = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": points},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            elevations = [loc["elevation"] for loc in data["results"]]
            center_elev = elevations[0]
            
            elev_changes = [abs(center_elev - e) for e in elevations[1:]]
            avg_change = sum(elev_changes) / len(elev_changes)
            
            import numpy as np
            distance = 100  # meters
            slope_degrees = np.arctan(avg_change / distance) * (180 / np.pi)
            
            print(f"✅ SUCCESS!")
            print(f"   - Center elevation: {center_elev:.1f} m")
            print(f"   - Elevation range: {min(elevations):.1f} - {max(elevations):.1f} m")
            print(f"   - Average elevation change: {avg_change:.2f} m")
            print(f"   - Estimated slope: {slope_degrees:.2f}°")
            print(f"   - All elevations: {[f'{e:.1f}' for e in elevations]}")
            
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_nominatim():
    """Test OpenStreetMap Nominatim API for reverse geocoding."""
    test_separator("TEST 4: OSM Nominatim API (Reverse Geocoding)")
    
    try:
        latitude = 33.1507
        longitude = -96.8236
        
        print(f"📍 Testing location: {latitude}, {longitude}")
        print("🔄 Reverse geocoding...\n")
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json"
            },
            headers={"User-Agent": "FireGuard-API-Tester/1.0"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            
            print(f"✅ SUCCESS!")
            print(f"   - Display Name: {data.get('display_name', 'N/A')}")
            print(f"   - Place Type: {data.get('type', 'N/A')}")
            print(f"   - Address Components:")
            
            # Show relevant address components
            for key in ["city", "town", "village", "suburb", "county", "state", "country"]:
                if key in address:
                    print(f"     • {key.capitalize()}: {address[key]}")
            
            # Determine population density
            if any(k in address for k in ["city", "town"]):
                pop_class = "high"
            elif any(k in address for k in ["village", "suburb", "neighbourhood"]):
                pop_class = "medium"
            else:
                pop_class = "low"
            
            print(f"   - Estimated Population Density: {pop_class}")
            
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_overpass():
    """Test OpenStreetMap Overpass API for infrastructure data."""
    test_separator("TEST 5: OSM Overpass API (Infrastructure)")
    
    try:
        latitude = 33.1507
        longitude = -96.8236
        radius = 1000  # meters
        
        print(f"📍 Testing location: {latitude}, {longitude}")
        print(f"🔍 Searching for critical infrastructure within {radius}m...\n")
        
        overpass_query = f"""
        [out:json][timeout:15];
        (
          node["amenity"~"hospital|fire_station|police"](around:{radius},{latitude},{longitude});
          node["power"~"plant|substation"](around:{radius},{latitude},{longitude});
          way["amenity"~"hospital|fire_station|police"](around:{radius},{latitude},{longitude});
          way["power"~"plant|substation"](around:{radius},{latitude},{longitude});
        );
        out body;
        """
        
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            print(f"✅ SUCCESS!")
            print(f"   - Critical facilities found: {len(elements)}")
            
            # Categorize findings
            categories = {}
            for element in elements:
                tags = element.get("tags", {})
                amenity = tags.get("amenity", "")
                power = tags.get("power", "")
                
                facility_type = amenity or power
                if facility_type:
                    categories[facility_type] = categories.get(facility_type, 0) + 1
            
            if categories:
                print(f"   - Breakdown:")
                for facility, count in categories.items():
                    print(f"     • {facility}: {count}")
            else:
                print(f"   - No critical infrastructure found in search radius")
            
            # Classify infrastructure level
            count = len(elements)
            if count >= 5:
                infra_class = "critical"
            elif count >= 2:
                infra_class = "slightly_critical"
            elif count >= 1:
                infra_class = "no_critical"
            else:
                infra_class = "no"
            
            print(f"   - Infrastructure Classification: {infra_class}")
            
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def run_all_tests():
    """Run all API tests in parallel and provide summary."""
    print("\n" + "="*70)
    print("  FIRE RISK API TESTING SUITE")
    print("  Testing all external APIs used in the system (Parallel Execution)")
    print("="*70)
    
    test_functions = [
        ("Open-Meteo Archive (Rain History)", test_open_meteo_archive),
        ("Open-Meteo Forecast (Current Weather)", test_open_meteo_forecast),
        ("Open-Elevation (Terrain)", test_open_elevation),
        ("OSM Nominatim (Population)", test_nominatim),
        ("OSM Overpass (Infrastructure)", test_overpass),
    ]
    
    results = {}
    
    # Run tests in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        futures = {executor.submit(test_func): test_name for test_name, test_func in test_functions}
        
        # Collect results as they complete
        for future in as_completed(futures):
            test_name = futures[future]
            try:
                result = future.result()
                results[test_name] = result
            except Exception as e:
                print(f"❌ Exception in {test_name}: {e}")
                results[test_name] = False
    
    # Summary
    test_separator("TEST SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"  🎉 All APIs are working correctly!")
    else:
        print(f"  ⚠️  Some APIs failed - check errors above")
    
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    run_all_tests()
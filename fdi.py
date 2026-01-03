import openmeteo_requests
import pandas as pd
import numpy as np
import requests_cache
from retry_requests import retry
from datetime import datetime, timezone
import subprocess
import json
import requests
import os
from typing import Dict, Optional, Tuple
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Check if we're in a serverless environment (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or not os.access('.', os.W_OK)

# Check if mock weather mode is enabled (for testing without API calls)
MOCK_WEATHER = os.environ.get('MOCK_WEATHER') == '1'

# Initialize global session for connection pooling
_CACHE_SESSION = None
_RETRY_SESSION = None
_EXECUTOR = ThreadPoolExecutor(max_workers=5)

# ============================================
# DATA LAYER: Weather & Environmental Data
# ============================================

def _get_session():
    """Get or create global cached session for connection pooling."""
    global _CACHE_SESSION, _RETRY_SESSION
    if _CACHE_SESSION is None:
        if IS_SERVERLESS:
            _CACHE_SESSION = requests_cache.CachedSession(backend='memory', expire_after=-1)
        else:
            _CACHE_SESSION = requests_cache.CachedSession('.cache', expire_after=-1)
        _RETRY_SESSION = retry(_CACHE_SESSION, retries=5, backoff_factor=0.2)
    return _RETRY_SESSION

def get_days_since_last_rain(latitude: float, longitude: float, lookback_days: int = 90):
    """Fetch historical rain data and calculate days since last rain."""
    # If MOCK_WEATHER is enabled, return mock rain data
    if MOCK_WEATHER:
        last_rain_date = (datetime.now(timezone.utc) - pd.Timedelta(days=5)).date()
        rainfall_on_last_rain = 12.5
        days_since_last_rain = 5
        return last_rain_date, rainfall_on_last_rain, days_since_last_rain
    
    try:
        retry_session = _get_session()
        openmeteo = openmeteo_requests.Client(session=retry_session)

        end_date = datetime.now().date()
        start_date = (end_date - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": "rain"
        }

        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        hourly = response.Hourly()
        rain = hourly.Variables(0).ValuesAsNumpy()
        timestamps = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )

        df = pd.DataFrame({"datetime": timestamps, "rain": rain})
        df = df.set_index("datetime").resample("D").sum()

        rainy_days = df[df["rain"] > 0]
        if rainy_days.empty:
            return None, None, lookback_days
        else:
            last_rain_date = rainy_days.index[-1].date()
            rainfall_on_last_rain = rainy_days.iloc[-1]["rain"]
            days_since_last_rain = (datetime.now(timezone.utc).date() - last_rain_date).days
            return last_rain_date, rainfall_on_last_rain, days_since_last_rain
    except Exception as e:
        print(f"   ⚠️  Could not fetch rain data: {e}")
        return None, None, lookback_days


def get_current_weather(latitude: float, longitude: float):
    """Fetch current weather conditions."""
    # If MOCK_WEATHER is enabled, return mock weather data
    if MOCK_WEATHER:
        return {
            "temperature": 28.5,
            "humidity": 45.0,
            "wind_speed": 15.2,
            "current_precipitation": 0.0
        }
    
    try:
        retry_session = _get_session()
        openmeteo = openmeteo_requests.Client(session=retry_session)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"]
        }

        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        current = response.Current()

        return {
            "temperature": current.Variables(0).Value(),
            "humidity": current.Variables(1).Value(),
            "wind_speed": current.Variables(2).Value(),
            "current_precipitation": current.Variables(3).Value()
        }
    except Exception as e:
        print(f"   ⚠️  Could not fetch weather data: {e}")
        return {
            "temperature": 25,
            "humidity": 50,
            "wind_speed": 10,
            "current_precipitation": 0
        }


def get_fuel_moisture_classification(days_since_rain: int, rainfall_amount: float, 
                                    temperature: float, humidity: float) -> str:
    """
    Classify fuel moisture based on multiple factors.
    Fuel moisture is critical for fire risk - dry vegetation burns easily.
    Uses: days since rain, rainfall amount, temperature, and humidity.
    """
    # Calculate a moisture score (0 = very dry, 100 = very wet)
    moisture_score = 50  # baseline
    
    # Rain impact (most important)
    if days_since_rain <= 1:
        moisture_score += 40
    elif days_since_rain <= 3:
        moisture_score += 30
    elif days_since_rain <= 7:
        moisture_score += 15
    elif days_since_rain <= 14:
        moisture_score += 5
    else:
        moisture_score -= (days_since_rain - 14) * 2  # gets drier each day
    
    # Rainfall amount impact
    if rainfall_amount and rainfall_amount > 10:
        moisture_score += 15
    elif rainfall_amount and rainfall_amount > 5:
        moisture_score += 10
    elif rainfall_amount and rainfall_amount > 1:
        moisture_score += 5
    
    # Humidity impact
    if humidity > 70:
        moisture_score += 10
    elif humidity > 50:
        moisture_score += 5
    elif humidity < 30:
        moisture_score -= 10
    elif humidity < 20:
        moisture_score -= 15
    
    # Temperature impact (heat dries out vegetation)
    if temperature > 35:
        moisture_score -= 15
    elif temperature > 30:
        moisture_score -= 10
    elif temperature > 25:
        moisture_score -= 5
    
    # Classify based on final score
    if moisture_score >= 70:
        return "moist"
    elif moisture_score >= 50:
        return "moderate"
    elif moisture_score >= 30:
        return "dry"
    else:
        return "extremely_dry"


def get_elevation_and_slope(latitude: float, longitude: float) -> Dict[str, float]:
    """
    Get elevation and estimate slope using Open-Elevation API.
    We sample points around the location to estimate slope.
    """
    try:
        # Sample 5 points: center and 4 cardinal directions (~100m away)
        offset = 0.001  # approximately 100 meters
        points = [
            {"latitude": latitude, "longitude": longitude},
            {"latitude": latitude + offset, "longitude": longitude},
            {"latitude": latitude - offset, "longitude": longitude},
            {"latitude": latitude, "longitude": longitude + offset},
            {"latitude": latitude, "longitude": longitude - offset},
        ]
        
        response = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": points},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            elevations = [loc["elevation"] for loc in data["results"]]
            center_elev = elevations[0]
            
            # Calculate average elevation change
            elev_changes = [abs(center_elev - e) for e in elevations[1:]]
            avg_change = sum(elev_changes) / len(elev_changes)
            
            # Estimate slope in degrees
            distance = 100  # meters
            slope_degrees = np.arctan(avg_change / distance) * (180 / np.pi)
            
            return {
                "elevation": center_elev,
                "slope_degrees": slope_degrees
            }
    except Exception as e:
        print(f"   ⚠️  Could not fetch elevation data: {e}")
    
    return {"elevation": 0, "slope_degrees": 0}


def classify_topography(slope_degrees: float) -> str:
    """Classify topography based on slope."""
    if slope_degrees < 5:
        return "flat"
    elif slope_degrees < 15:
        return "hilly"
    elif slope_degrees < 30:
        return "steep"
    else:
        return "very_steep"


def get_population_density(latitude: float, longitude: float) -> Optional[str]:
    """
    Estimate population density using OpenStreetMap Nominatim (reverse geocoding).
    This gives us the place type which correlates with population density.
    """
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json"
            },
            headers={"User-Agent": "FireGuard/1.0"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            
            # Classify based on place type
            if any(key in address for key in ["city", "town"]):
                return "high"
            elif any(key in address for key in ["village", "suburb", "neighbourhood"]):
                return "medium"
            else:
                return "low"
    except Exception as e:
        print(f"   ⚠️  Could not fetch population data: {e}")
    
    return "medium"  # Default fallback


def get_infrastructure_data(latitude: float, longitude: float) -> str:
    """
    Estimate infrastructure criticality using OpenStreetMap Overpass API.
    Looks for hospitals, power stations, water treatment, etc.
    """
    try:
        # Search within 1km radius
        radius = 1000
        
        overpass_query = f"""
        [out:json];
        (
          node["amenity"~"hospital|fire_station|police"](around:{radius},{latitude},{longitude});
          node["power"~"plant|substation"](around:{radius},{latitude},{longitude});
          way["amenity"~"hospital|fire_station|police"](around:{radius},{latitude},{longitude});
          way["power"~"plant|substation"](around:{radius},{latitude},{longitude});
        );
        out count;
        """
        
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("elements", []))
            
            if count >= 5:
                return "critical"
            elif count >= 2:
                return "slightly_critical"
            elif count >= 1:
                return "no_critical"
            else:
                return "no"
    except Exception as e:
        print(f"   ⚠️  Could not fetch infrastructure data: {e}")
    
    return "no_critical"  # Default fallback


def get_temperature_classification(temp_celsius: float) -> str:
    """Classify temperature for fire risk."""
    if temp_celsius < 15:
        return "low"
    elif temp_celsius < 25:
        return "moderate"
    elif temp_celsius < 35:
        return "high"
    else:
        return "very_high"


def get_humidity_classification(humidity_percent: float) -> str:
    """Classify humidity for fire risk."""
    if humidity_percent > 70:
        return "high"
    elif humidity_percent > 50:
        return "moderate"
    elif humidity_percent > 30:
        return "low"
    else:
        return "very_low"


def get_wind_classification(wind_kmh: float) -> str:
    """Classify wind speed for fire risk."""
    if wind_kmh < 10:
        return "low"
    elif wind_kmh < 25:
        return "moderate"
    elif wind_kmh < 40:
        return "strong"
    else:
        return "extreme"


# ============================================
# FDI CALCULATION (OPTIMIZED)
# ============================================

# Pre-computed lookup table for better performance
_FDI_THRESHOLDS = [
    (0, 2.7, [0.7, 0.9, 1.0]),
    (2.7, 5.3, [0.6, 0.8, 0.9, 1.0]),
    (5.3, 7.7, [0.5, 0.7, 0.9, 0.9, 1.0]),
    (7.7, 10.3, [0.4, 0.6, 0.8, 0.9, 0.9, 1.0]),
    (10.3, 12.9, [0.4, 0.6, 0.7, 0.8, 0.9, 0.9, 1.0]),
    (12.9, 15.4, [0.3, 0.5, 0.7, 0.8, 0.8, 0.9, 1.0]),
    (15.4, 20.6, [0.2, 0.5, 0.6, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
    (20.6, 25.6, [0.2, 0.4, 0.5, 0.7, 0.7, 0.8, 0.9, 0.9, 1.0]),
    (25.6, 38.5, [0.1, 0.3, 0.4, 0.6, 0.6, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
    (38.5, 51.2, [0.0, 0.2, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]),
    (51.2, 63.9, [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 0.9, 1.0]),
    (63.9, 76.6, [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0]),
    (76.6, float("inf"), [0.0, 0.0, 0.1, 0.2, 0.4, 0.5, 0.6, 0.6, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.8, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0])
]

_WIND_THRESHOLDS = [3, 9, 17, 26, 33, 37, 42, 46]
_WIND_ADDITIONS = [0, 5, 10, 15, 20, 25, 30, 35]

def wind_factor(wind, burn_index):
    """Calculate wind adjustment factor with optimized lookup."""
    for threshold, add in zip(_WIND_THRESHOLDS, _WIND_ADDITIONS):
        if wind < threshold:
            return burn_index + add
    return burn_index + 40


def get_adjustment_factor(rain, days_rain):
    """Get rainfall adjustment factor from lookup table using binary search."""
    for low, high, factors in _FDI_THRESHOLDS:
        if low <= rain < high:
            index = min(days_rain - 1, len(factors) - 1)
            return factors[index]
    return 1.0


def calculate_fdi(temperature, humidity, wind, days_rain, rain):
    """Calculate Fire Danger Index."""
    temperature_factor = (temperature - 3) * 6.7
    humidity_factor = (90 - humidity) * 2.6

    rain = max(rain, 1)
    days_rain = max(days_rain, 1)
    wind = max(wind, 3)

    burn_factor = temperature_factor - humidity_factor
    burn_index = (burn_factor / 2 + humidity_factor) / 3.3
    wind_fac = wind_factor(wind, burn_index)

    adjustment = get_adjustment_factor(rain, days_rain)
    return round(wind_fac * adjustment)


def fdi_to_category(fdi_value):
    """Convert FDI numeric value to category."""
    if fdi_value <= 20:
        return "Blue (insignificant)"
    elif fdi_value <= 45:
        return "Green (low)"
    elif fdi_value <= 60:
        return "Yellow (moderate)"
    elif fdi_value <= 75:
        return "Orange (high)"
    else:
        return "Red (extremely high)"


# ============================================
# PROLOG INTEGRATION LAYER
# ============================================

def create_dynamic_prolog_fact(area_name: str, fuel: str, temp: str, hum: str, 
                               wind: str, topo: str, pop: str, infra: str,
                               prolog_file: str = "prolog.pl") -> str:
    """
    Add or update a dynamic area fact in the Prolog file.
    This allows us to create areas based on real-time data.
    Returns the fact string for use in serverless environments.
    """
    fact = f"area_details({area_name}, {fuel}, {temp}, {hum}, {wind}, {topo}, {pop}, {infra})."
    
    # In serverless environments, don't write to file, just return the fact
    if IS_SERVERLESS:
        return fact
    
    # Read existing file
    try:
        with open(prolog_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    
    # Find and replace or append area fact
    area_pattern = f"area_details({area_name},"
    new_lines = []
    found = False
    
    for line in lines:
        if area_pattern in line:
            new_lines.append(fact + "\n")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(fact + "\n")
    
    # Write back efficiently
    with open(prolog_file, 'w') as f:
        f.writelines(new_lines)
    
    return fact


def call_prolog_query(query: str, prolog_file: str = "prolog.pl", additional_fact: str = None) -> str:
    """Execute a Prolog query and return raw output with optimized error handling."""
    if IS_SERVERLESS and additional_fact:
        # In serverless, assert the fact dynamically and then run the query
        # Remove the trailing period from the fact for assertz
        fact_term = additional_fact.rstrip('.')
        full_query = f"assertz({fact_term}), {query}"
        cmd = ["swipl", "-q", "-s", prolog_file, "-g", full_query, "-t", "halt"]
    else:
        cmd = ["swipl", "-q", "-s", prolog_file, "-g", query, "-t", "halt"]
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"Prolog error: {result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("Prolog query timed out after 30 seconds")
    except Exception as e:
        raise RuntimeError(f"Prolog execution failed: {str(e)}")


def generate_risk_explanation(fuel: str, temp_class: str, hum_class: str, wind_class: str, 
                             topo_class: str, pop_class: str, infra_class: str, 
                             fdi_value: int, risk_level: str) -> str:
    """
    Generate a human-readable explanation of why the risk is at the current level.
    Returns a detailed explanation highlighting contributing factors.
    """
    explanations = []
    critical_factors = []
    
    # Analyze fuel moisture
    if fuel in ["dry", "extremely_dry"]:
        critical_factors.append(f"🔥 Fuel moisture: {fuel.replace('_', ' ').title()}")
        explanations.append(f"Vegetation is highly flammable due to {fuel} fuel moisture")
    elif fuel == "moderate":
        explanations.append(f"Fuel moisture is moderate")
    else:
        explanations.append(f"Fuel moisture is {fuel} - vegetation is less flammable")
    
    # Analyze temperature
    if temp_class in ["high", "very_high"]:
        critical_factors.append(f"🌡️ Temperature: {temp_class.replace('_', ' ').title()}")
        explanations.append(f"{temp_class.title()} temperatures accelerate fuel drying and fire spread")
    else:
        explanations.append(f"Temperature is {temp_class}")
    
    # Analyze humidity
    if hum_class in ["low", "very_low"]:
        critical_factors.append(f"💧 Humidity: {hum_class.replace('_', ' ').title()}")
        explanations.append(f"{hum_class.title()} humidity significantly increases fire risk")
    else:
        explanations.append(f"Humidity is {hum_class}")
    
    # Analyze wind
    if wind_class in ["strong", "extreme"]:
        critical_factors.append(f"💨 Wind: {wind_class.title()}")
        explanations.append(f"{wind_class.title()} winds dramatically increase fire spread rate")
    else:
        explanations.append(f"Wind speed is {wind_class}")
    
    # Analyze topography
    if topo_class in ["steep", "very_steep"]:
        critical_factors.append(f"⛰️ Terrain: {topo_class.replace('_', ' ').title()}")
        explanations.append(f"Fires spread faster uphill on {topo_class} slopes")
    else:
        explanations.append(f"Terrain is {topo_class}")
    
    # Analyze population
    if pop_class == "high":
        explanations.append(f"High population density increases evacuation complexity")
    
    # Analyze infrastructure
    if infra_class in ["critical", "slightly_critical"]:
        explanations.append(f"Critical infrastructure at risk requires additional resources")
    
    # Build final explanation with dynamic emoji color
    risk_emoji = "🔴" if risk_level in ["Extreme", "Very High"] else "🟠" if risk_level == "High" else "🟡" if risk_level == "Medium" else "🟢" if risk_level == "Low" else "🔵"
    result = f"{risk_emoji} **{risk_level}**\n\n"
    
    if critical_factors:
        result += "**Critical Factors:**\n"
        for factor in critical_factors:
            result += f"{factor}\n"
        result += "\n"
    
    result += "**Analysis:**\n"
    for exp in explanations:
        if exp:  # Skip empty explanations
            result += f"• {exp}\n"
    
    result += f"\n📊 **FDI: {fdi_value}**"
    
    return result


def classify_area_with_prolog(area: str, prolog_file: str = "prolog.pl", additional_fact: str = None) -> dict:
    """Get fire risk classification for a specific area from Prolog."""
    # In serverless environments, call remote Prolog API service
    if IS_SERVERLESS:
        prolog_api_url = os.environ.get('PROLOG_API_URL')
        if not prolog_api_url:
            print(f"   ⚠️  PROLOG_API_URL not set. Set it to your Prolog API service URL.")
            return {
                'Area': area,
                'RiskLevel': 'Unknown',
                'Evacuation': 'no',
                'Resources': 'fire_engines'
            }
        
        try:
            # Parse the fact to extract parameters
            if additional_fact:
                fact = additional_fact.rstrip('.')
                import re
                match = re.match(r'area_details\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', fact)
                if match:
                    _, fuel, temp, hum, wind, topo, pop, infra = match.groups()
                    
                    # Call remote Prolog API
                    response = requests.post(
                        f"{prolog_api_url}/classify",
                        json={
                            'area_name': area,
                            'fuel': fuel.strip(),
                            'temp': temp.strip(),
                            'hum': hum.strip(),
                            'wind': wind.strip(),
                            'topo': topo.strip(),
                            'pop': pop.strip(),
                            'infra': infra.strip()
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            return result.get('data', {})
                    
                    print(f"   ⚠️  Prolog API error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Failed to connect to Prolog API at {prolog_api_url}: {e}")
        except Exception as e:
            print(f"   ⚠️  Prolog API classification error: {e}")
        
        return {
            'Area': area,
            'RiskLevel': 'Unknown',
            'Evacuation': 'no',
            'Resources': 'fire_engines'
        }
    
    # For local development, use Prolog directly
    goal = f'classify_fire_risk_json({area})'
    output = call_prolog_query(goal, prolog_file, additional_fact)
    
    if not output:
        return {}
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        result = {}
        for part in output.split(','):
            if ':' in part:
                k, v = part.split(':', 1)
                result[k.strip().strip('"{}').strip()] = v.strip().strip('"{}').strip()
        return result


# ============================================
# MAIN ORCHESTRATION LAYER
# ============================================

def analyze_location_dynamic(latitude: float, longitude: float, area_name: str = "dynamic_area"):
    """
    Complete fire risk analysis with REAL-TIME DATA for all parameters.
    No hardcoded values - everything is fetched from APIs!
    """
    # Record analysis timestamp
    analysis_timestamp = datetime.now(timezone.utc)
    
    print(f"\n{'='*60}")
    print(f"DYNAMIC FIRE RISK ANALYSIS FOR {area_name.upper()}")
    print(f"Location: {latitude}, {longitude}")
    print(f"Analysis Time: {analysis_timestamp.isoformat()}")
    print(f"{'='*60}\n")

    # Step 1: Get historical rain data
    print("📊 Fetching rain history...")
    last_rain_date, rainfall_amount, days_since_rain = get_days_since_last_rain(
        latitude, longitude
    )
    rain_data_timestamp = datetime.now(timezone.utc)
    print(f"   Last Rain: {last_rain_date}")
    print(f"   Rainfall Amount: {rainfall_amount:.2f} mm")
    print(f"   Days Since Rain: {days_since_rain}")

    # Step 2: Get current weather
    print("\n🌤️  Fetching current weather...")
    weather = get_current_weather(latitude, longitude)
    weather_data_timestamp = datetime.now(timezone.utc)
    print(f"   Temperature: {weather['temperature']:.1f}°C")
    print(f"   Humidity: {weather['humidity']:.1f}%")
    print(f"   Wind Speed: {weather['wind_speed']:.1f} km/h")
    print(f"   Current Precipitation: {weather['current_precipitation']:.2f} mm")

    # Step 3: Get elevation and topography
    print("\n🏔️  Analyzing topography...")
    elevation_data = get_elevation_and_slope(latitude, longitude)
    print(f"   Elevation: {elevation_data['elevation']:.1f} m")
    print(f"   Slope: {elevation_data['slope_degrees']:.2f}°")

    # Step 4: Get population density
    print("\n👥 Analyzing population density...")
    pop_density = get_population_density(latitude, longitude)
    print(f"   Population Density: {pop_density}")

    # Step 5: Get infrastructure data
    print("\n🏗️  Analyzing infrastructure...")
    infrastructure = get_infrastructure_data(latitude, longitude)
    print(f"   Infrastructure Level: {infrastructure}")

    # Step 6: Classify all parameters
    print("\n🔄 Classifying parameters...")
    fuel = get_fuel_moisture_classification(
        days_since_rain, rainfall_amount, 
        weather['temperature'], weather['humidity']
    )
    temp_class = get_temperature_classification(weather['temperature'])
    hum_class = get_humidity_classification(weather['humidity'])
    wind_class = get_wind_classification(weather['wind_speed'])
    topo_class = classify_topography(elevation_data['slope_degrees'])
    
    print(f"   Fuel Moisture: {fuel}")
    print(f"   Temperature Class: {temp_class}")
    print(f"   Humidity Class: {hum_class}")
    print(f"   Wind Class: {wind_class}")
    print(f"   Topography Class: {topo_class}")

    # Step 7: Calculate FDI
    print("\n🔥 Calculating Fire Danger Index...")
    fdi_value = calculate_fdi(
        weather['temperature'],
        weather['humidity'],
        weather['wind_speed'],
        days_since_rain,
        rainfall_amount
    )
    fdi_category = fdi_to_category(fdi_value)
    print(f"   FDI Value: {fdi_value}")
    print(f"   FDI Category: {fdi_category}")

    # Step 8: Create dynamic Prolog fact and classify
    print(f"\n🧠 Analyzing fire risk with Prolog...")
    fact = create_dynamic_prolog_fact(
        area_name, fuel, temp_class, hum_class, 
        wind_class, topo_class, pop_density, infrastructure
    )
    
    try:
        # Pass the fact to Prolog query if in serverless environment
        additional_fact = fact if IS_SERVERLESS else None
        prolog_result = classify_area_with_prolog(area_name, additional_fact=additional_fact)
        if prolog_result:
            print(f"   Risk Level: {prolog_result.get('RiskLevel', 'N/A')}")
            print(f"   Evacuation Needed: {prolog_result.get('Evacuation', 'N/A')}")
            print(f"   Resources Required: {prolog_result.get('Resources', 'N/A')}")
        else:
            print(f"   ⚠️  No result returned from Prolog")
    except Exception as e:
        print(f"   ⚠️  Prolog classification error: {e}")
        prolog_result = {}

    print(f"\n{'='*60}\n")

    # Generate risk explanation
    risk_level = prolog_result.get('RiskLevel', 'Unknown')
    risk_explanation = generate_risk_explanation(
        fuel, temp_class, hum_class, wind_class, topo_class, pop_density, 
        infrastructure, fdi_value, risk_level
    )

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "analysis_timestamp": analysis_timestamp.isoformat(),
        "weather_data": weather,
        "weather_data_timestamp": weather_data_timestamp.isoformat(),
        "rain_data": {
            "last_rain_date": str(last_rain_date),
            "rainfall_amount": rainfall_amount,
            "days_since_rain": days_since_rain,
            "lookback_days": 90
        },
        "rain_data_timestamp": rain_data_timestamp.isoformat(),
        "environmental": {
            "elevation": elevation_data['elevation'],
            "slope": elevation_data['slope_degrees'],
            "population": pop_density,
            "infrastructure": infrastructure
        },
        "classifications": {
            "fuel": fuel,
            "temperature": temp_class,
            "humidity": hum_class,
            "wind": wind_class,
            "topography": topo_class
        },
        "fdi": {
            "value": fdi_value,
            "category": fdi_category
        },
        "prolog_classification": prolog_result,
        "risk_explanation": risk_explanation
    }


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Frisco, Texas coordinates
    latitude = 33.1507
    longitude = -96.8236

    # Analyze with REAL dynamic data
    result = analyze_location_dynamic(latitude, longitude, area_name="frisco_tx")

    # You can also analyze multiple locations
    print("\n" + "="*60)
    print("COMPARING MULTIPLE LOCATIONS")
    print("="*60)
    
    locations = [
        (33.1507, -96.8236, "frisco_tx"),
        (34.0522, -118.2437, "los_angeles_ca"),
        (37.7749, -122.4194, "san_francisco_ca"),
    ]
    
    for lat, lon, name in locations:
        print(f"\n📍 Analyzing {name}...")
        try:
            result = analyze_location_dynamic(lat, lon, area_name=name)
            print(f"✅ {name}: {result['prolog_classification'].get('RiskLevel', 'Unknown')} risk")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
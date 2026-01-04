"""
Merged Flask backend serving both fire risk analysis and Prolog classification.
Serves the main website, /api/analyze endpoint, and /api/prolog/classify endpoint.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import sys
import numpy as np
from datetime import datetime
from functools import lru_cache

# Import the fire risk analysis functions
from fdi import analyze_location_dynamic
from firms import (
    analyze_active_fire_threat,
    fetch_firms_fires,
    get_fires_geojson,
    fetch_recent_fires_global,
)


# ============= Enhanced Recommendations Logic =============

def map_fire_proximity(distance_km, has_fires):
    """Convert fire distance to proximity category for Prolog."""
    if not has_fires:
        return "none"
    if distance_km is None:
        return "unknown"
    if distance_km <= 2:
        return "critical"
    elif distance_km <= 5:
        return "close"
    elif distance_km <= 15:
        return "moderate"
    elif distance_km <= 25:
        return "distant"
    else:
        return "far"


def generate_enhanced_recommendations(prolog_result, threat_analysis, area_metadata):
    """
    Generate enhanced evacuation and resource recommendations based on:
    1. Prolog risk classification
    2. Active fire threat analysis
    3. Area characteristics (population, infrastructure)
    """
    risk_level = prolog_result.get('RiskLevel', 'Low')
    population = area_metadata.get('population', 'low')
    infrastructure = area_metadata.get('infrastructure', 'no')
    
    # Determine fire proximity
    fire_proximity = "none"
    if threat_analysis.get('has_nearby_fires'):
        closest_distance = threat_analysis.get('closest_fire_distance_km')
        fire_proximity = map_fire_proximity(closest_distance, True)
    
    # Build recommendations object
    recommendations = {
        "evacuation": {
            "type": "prepare",  # no_evac, prepare, evacuate
            "urgency": "none",  # none, low, high, immediate, mandatory
            "population_at_risk": population,
            "rationale": ""
        },
        "resources": {
            "fire_trucks": 0,
            "water_tankers": 0,
            "helicopters": 0,
            "command_centers": 0,
            "ground_crews": 0,
            "ambulances": 0,
            "special_equipment": []
        },
        "actions": [],
        "timeline": {}
    }
    
    # Evacuation logic based on multiple factors
    score = calculate_evacuation_score(risk_level, population, infrastructure, fire_proximity)
    
    if score < 2:
        recommendations["evacuation"]["type"] = "no_evac"
        recommendations["evacuation"]["urgency"] = "none"
    elif score < 4:
        recommendations["evacuation"]["type"] = "prepare"
        recommendations["evacuation"]["urgency"] = "low"
    elif score < 6:
        recommendations["evacuation"]["type"] = "prepare"
        recommendations["evacuation"]["urgency"] = "high"
    elif score < 8:
        recommendations["evacuation"]["type"] = "evacuate"
        recommendations["evacuation"]["urgency"] = "immediate"
    else:
        recommendations["evacuation"]["type"] = "evacuate"
        recommendations["evacuation"]["urgency"] = "mandatory"
    
    # Resource allocation based on risk and proximity
    allocate_resources_enhanced(recommendations, risk_level, population, infrastructure, fire_proximity)
    
    # Generate action items
    generate_action_items(recommendations, risk_level, fire_proximity, threat_analysis)
    
    # Generate timeline
    generate_timeline(recommendations, risk_level, fire_proximity)
    
    # Add rationale
    recommendations["evacuation"]["rationale"] = generate_evac_rationale(
        risk_level, population, infrastructure, fire_proximity, threat_analysis
    )
    
    return recommendations


def calculate_evacuation_score(risk_level, population, infrastructure, fire_proximity):
    """Calculate evacuation urgency score (0-10+ scale)."""
    risk_scores = {
        'Very Low': 0, 'Low': 1, 'Medium': 3,
        'High': 6, 'Very High': 8, 'Extreme': 10
    }
    
    pop_scores = {'low': 0, 'medium': 2, 'high': 4}
    infra_scores = {'no': 0, 'no_critical': 0, 'slightly_critical': 1, 'critical': 3}
    fire_scores = {
        'none': 0, 'far': 0.5, 'distant': 1,
        'moderate': 3, 'close': 5, 'critical': 8
    }
    
    base = risk_scores.get(risk_level, 0)
    pop = pop_scores.get(population, 0)
    infra = infra_scores.get(infrastructure, 0)
    fire = fire_scores.get(fire_proximity, 0)
    
    return base + pop + infra + fire


def allocate_resources_enhanced(recommendations, risk_level, population, infrastructure, fire_proximity):
    """Allocate resources based on all factors."""
    base_allocation = {
        'Very Low': {'fire_trucks': 1, 'water_tankers': 0, 'helicopters': 0, 'command_centers': 0},
        'Low': {'fire_trucks': 2, 'water_tankers': 1, 'helicopters': 0, 'command_centers': 0},
        'Medium': {'fire_trucks': 3, 'water_tankers': 2, 'helicopters': 0, 'command_centers': 0},
        'High': {'fire_trucks': 4, 'water_tankers': 3, 'helicopters': 1, 'command_centers': 0},
        'Very High': {'fire_trucks': 6, 'water_tankers': 4, 'helicopters': 2, 'command_centers': 1},
        'Extreme': {'fire_trucks': 8, 'water_tankers': 6, 'helicopters': 3, 'command_centers': 1}
    }
    
    allocation = base_allocation.get(risk_level, base_allocation['Low']).copy()
    
    # Scale by population
    if population == 'medium':
        allocation = {k: int(v * 1.5) for k, v in allocation.items()}
    elif population == 'high':
        allocation = {k: v * 2 for k, v in allocation.items()}
        allocation['ground_crews'] = 100 if risk_level in ['High', 'Very High', 'Extreme'] else 0
    
    # Enhance for infrastructure
    if infrastructure == 'critical':
        allocation['command_centers'] = max(1, allocation.get('command_centers', 0))
        allocation['ground_crews'] = allocation.get('ground_crews', 0) + 50
    
    # Enhance for fire proximity
    if fire_proximity in ['close', 'critical']:
        allocation['helicopters'] = max(2, allocation.get('helicopters', 0))
        allocation['water_tankers'] = allocation.get('water_tankers', 0) + 2
        allocation['ground_crews'] = allocation.get('ground_crews', 0) + (200 if fire_proximity == 'critical' else 100)
        allocation['ambulances'] = 5 if fire_proximity == 'critical' else 2
    elif fire_proximity == 'moderate':
        allocation['water_tankers'] = allocation.get('water_tankers', 0) + 1
        allocation['ambulances'] = 2
    
    # Update recommendations
    for resource, quantity in allocation.items():
        if resource in recommendations["resources"]:
            recommendations["resources"][resource] = quantity


def generate_action_items(recommendations, risk_level, fire_proximity, threat_analysis):
    """Generate specific action items."""
    actions = []
    
    if risk_level in ['High', 'Very High', 'Extreme']:
        actions.append("Activate incident command system")
        actions.append("Pre-position firefighting resources")
        actions.append("Alert residents of potential evacuation")
    
    if fire_proximity in ['close', 'critical']:
        actions.append("Establish evacuation centers and assembly points")
        actions.append("Activate emergency shelters")
        actions.append("Deploy aerial reconnaissance")
        
        if threat_analysis.get('has_nearby_fires'):
            closest = threat_analysis.get('closest_fire_distance_km', 'Unknown')
            actions.append(f"Active fire detected {closest}km away - increase alert status")
    
    if fire_proximity == 'moderate':
        actions.append("Pre-position water tankers and equipment")
        actions.append("Establish communication with mutual aid agencies")
    
    if recommendations["evacuation"]["type"] == "evacuate":
        actions.append("Execute evacuation plan immediately")
        actions.append("Establish traffic control at evacuation routes")
        actions.append("Set up reception and care facilities")
    elif recommendations["evacuation"]["type"] == "prepare":
        actions.append("Brief residents on evacuation procedures")
        actions.append("Identify evacuation routes and shelters")
        actions.append("Review mutual aid agreements")
    
    recommendations["actions"] = actions


def generate_timeline(recommendations, risk_level, fire_proximity):
    """Generate action timeline."""
    timeline = {}
    
    if recommendations["evacuation"]["type"] == "evacuate":
        if recommendations["evacuation"]["urgency"] == "mandatory":
            timeline["immediate"] = "Begin evacuation - lives at imminent risk"
            timeline["5_minutes"] = "All resources deployed"
            timeline["15_minutes"] = "Evacuation routes secured"
        else:
            timeline["15_minutes"] = "Prepare evacuation"
            timeline["30_minutes"] = "Begin evacuation if conditions worsen"
    elif recommendations["evacuation"]["type"] == "prepare":
        timeline["now"] = "Alert residents and activate emergency operations"
        timeline["30_minutes"] = "Position resources at strategic locations"
        timeline["2_hours"] = "Review evacuation readiness"
    
    recommendations["timeline"] = timeline


def generate_evac_rationale(risk_level, population, infrastructure, fire_proximity, threat_analysis):
    """Generate human-readable evacuation rationale."""
    factors = []
    
    if risk_level in ['High', 'Very High', 'Extreme']:
        factors.append(f"High fire risk classification ({risk_level})")
    
    if population == 'high':
        factors.append("High population density requires priority protection")
    
    if infrastructure == 'critical':
        factors.append("Critical infrastructure at risk")
    
    if fire_proximity in ['close', 'critical']:
        factors.append(f"Active fire threat detected nearby ({fire_proximity})")
        if threat_analysis.get('evacuation_reason'):
            factors.append(threat_analysis['evacuation_reason'])
    
    if not factors:
        return "Risk level indicates normal precautions"
    
    return " | ".join(factors)

app = Flask(__name__)
CORS(app)

PROLOG_FILE = "prolog.pl"
PROLOG_TIMEOUT = 30

def convert_to_native_types(obj):
    """Convert NumPy/pandas types to native Python types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_types(item) for item in obj]
    elif hasattr(obj, 'item'):  # NumPy scalar
        return obj.item()
    else:
        return obj


def call_prolog_query(query: str) -> str:
    """Execute a Prolog query with timeout protection."""
    cmd = ["swipl", "-q", "-s", PROLOG_FILE, "-g", query, "-t", "halt"]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=PROLOG_TIMEOUT)
        if result.returncode != 0:
            raise RuntimeError(f"Prolog error: {result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Prolog query timed out after {PROLOG_TIMEOUT}s")
    except Exception as e:
        raise RuntimeError(f"Prolog execution failed: {str(e)}")

# ============= Website & Analysis Routes =============

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/firms-demo')
def firms_demo():
    """Serve the NASA FIRMS map demo page."""
    return render_template('firms_demo.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze fire risk for a given location with enhanced recommendations."""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        area_name = data.get('area_name', 'user_location')
        
        # Perform the analysis
        result = analyze_location_dynamic(latitude, longitude, area_name)
        
        # Convert NumPy/pandas types to native Python types for JSON serialization
        result = convert_to_native_types(result)
        
        # Get current risk level from analysis
        current_risk_level = result.get('prolog_classification', {}).get('RiskLevel', 'moderate')
        
        # Analyze active fires from NASA FIRMS and get threat assessment
        threat_analysis = analyze_active_fire_threat(latitude, longitude, current_risk_level.lower())
        
        # Extract area characteristics from prolog classification
        area_metadata = {
            'population': map_population_density(result.get('prolog_classification', {}).get('Population', 'low')),
            'infrastructure': result.get('prolog_classification', {}).get('Infrastructure', 'no')
        }
        
        # Generate enhanced recommendations
        enhanced_recommendations = generate_enhanced_recommendations(
            result.get('prolog_classification', {}),
            threat_analysis,
            area_metadata
        )
        
        # Add recommendations to result
        result['enhanced_recommendations'] = enhanced_recommendations
        
        # If there's an active fire threat, include detailed analysis
        if threat_analysis.get('has_nearby_fires'):
            result['active_fire_threat'] = threat_analysis
            # Update evacuation if fire threat is severe
            if threat_analysis.get('evacuation_recommended'):
                enhanced_recommendations['evacuation']['type'] = 'evacuate'
                if enhanced_recommendations['evacuation']['urgency'] != 'mandatory':
                    enhanced_recommendations['evacuation']['urgency'] = 'immediate'
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def map_population_density(pop_value):
    """Map Prolog population value to simple category."""
    if isinstance(pop_value, str):
        return pop_value.lower()
    return 'low'

# ============= NASA FIRMS Active Fire Overlay Routes =============

@app.route('/api/firms/active-fires', methods=['POST'])
def get_active_fires():
    """
    Get active satellite-detected fires near a location from NASA FIRMS API.
    Optionally analyzes threat and provides evacuation recommendations.
    """
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        current_risk_level = data.get('current_risk_level', 'moderate')
        
        # Fetch fires
        fires = fetch_firms_fires(latitude, longitude)
        
        # Analyze threat level
        threat_analysis = analyze_active_fire_threat(latitude, longitude, current_risk_level)
        
        # Convert to GeoJSON for mapping
        fires_geojson = get_fires_geojson(fires)
        
        return jsonify({
            'success': True,
            'data': {
                'fires': fires,
                'fires_geojson': fires_geojson,
                'threat_analysis': threat_analysis,
                'location': {'lat': latitude, 'lon': longitude},
                'timestamp': datetime.now().isoformat()
            }
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameters: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/firms/recent', methods=['GET'])
def get_recent_fires():
    """Return recent FIRMS fires globally (bounded by a safety limit)."""
    try:
        # Optional query params
        days = int(request.args.get('days', 7))
        max_results = int(request.args.get('max', 2000))

        fires = fetch_recent_fires_global(days_back=days, max_results=max_results)
        fires_geojson = get_fires_geojson(fires)

        return jsonify({
            'success': True,
            'data': {
                'fires': fires,
                'fires_geojson': fires_geojson,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/firms/threat-analysis', methods=['POST'])
def firms_threat_analysis():
    """
    Get threat level analysis for active fires and evacuation recommendations.
    """
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        current_risk_level = data.get('current_risk_level', 'moderate')
        
        threat_analysis = analyze_active_fire_threat(latitude, longitude, current_risk_level)
        
        return jsonify({
            'success': True,
            'data': threat_analysis
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameters: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============= Prolog API Routes =============

@app.route('/api/prolog/health', methods=['GET'])
def prolog_health():
    """Health check endpoint for Prolog service."""
    return jsonify({'status': 'ok', 'service': 'merged-api'})

@app.route('/api/prolog/classify', methods=['POST'])
def prolog_classify():
    """Classify fire risk for an area using Prolog with better validation."""
    try:
        data = request.get_json()
        
        # Required parameters
        required_params = ['area_name', 'fuel', 'temp', 'hum', 'wind', 'topo', 'pop', 'infra']
        missing = [p for p in required_params if not data.get(p)]
        
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required parameters: {", ".join(missing)}'
            }), 400
        
        area_name = data['area_name']
        fuel = data['fuel']
        temp = data['temp']
        hum = data['hum']
        wind = data['wind']
        topo = data['topo']
        pop = data['pop']
        infra = data['infra']
        
        # Create and assert the fact, then query
        fact = f"area_details({area_name}, {fuel}, {temp}, {hum}, {wind}, {topo}, {pop}, {infra})."
        fact_term = fact.rstrip('.')
        
        # Assert fact and run query
        goal = f'classify_fire_risk_json({area_name})'
        full_query = f"assertz({fact_term}), {goal}"
        
        output = call_prolog_query(full_query)
        
        if not output:
            return jsonify({
                'success': False,
                'error': 'No output from Prolog'
            }), 500
        
        try:
            result = json.loads(output)
            return jsonify({
                'success': True,
                'data': result
            })
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': f'Invalid JSON from Prolog'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============= Generic Health Check =============

@app.route('/api/health', methods=['GET'])
def health():
    """Generic health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'merged-api'})

# ============= Chatbot API Routes =============

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Process chatbot queries using Prolog."""
    try:
        data = request.get_json()
        query_type = data.get('query_type')
        params = data.get('params', {})
        
        if not query_type:
            return jsonify({
                'success': False,
                'error': 'Missing query_type parameter'
            }), 400
        
        result = process_chatbot_query(query_type, params)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def process_chatbot_query(query_type, params):
    """Process different types of chatbot queries."""
    
    if query_type == 'fireline_intensity':
        # Extract parameters
        I = params.get('I', 0)
        P = params.get('P', 0)
        W = params.get('W', 0)
        S = params.get('S', 0)
        B = params.get('B', 0)
        E = params.get('E', 0)
        H = params.get('H', 0)
        H_Yield = params.get('H_Yield', 0)
        A_Fuel = params.get('A_Fuel', 0)
        
        query = f"fireline_intensity({I}, {P}, {W}, {S}, {B}, {E}, {H}, {H_Yield}, {A_Fuel})"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'fireline_intensity'}
    
    elif query_type == 'flame_length':
        I = params.get('I', 0)
        query = f"flame_length({I})"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'flame_length'}
    
    elif query_type == 'safety_zone':
        C = params.get('C', 0)
        I = params.get('I', 0)
        N = params.get('N', 0)
        query = f"H is {C} * ({I} ** {N}), R is 4 * H, format('Safety Zone: ~2f m~n', [R])"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'safety_zone'}
    
    elif query_type == 'burn_area':
        R = params.get('R', 0)
        T = params.get('T', 0)
        query = f"calculate_burn_area({R}, {T})"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'burn_area'}
    
    elif query_type == 'escape_time':
        D = params.get('D', 0)
        R = params.get('R', 0)
        query = f"calculate_escape_time({D}, {R})"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'escape_time'}
    
    elif query_type == 'risk_level':
        fuel = params.get('fuel', 'moderate')
        temp = params.get('temp', 'moderate')
        hum = params.get('hum', 'moderate')
        wind = params.get('wind', 'moderate')
        topo = params.get('topo', 'flat')
        pop = params.get('pop', 'low')
        infra = params.get('infra', 'no')
        
        query = f"calculate_risk({fuel}, {temp}, {hum}, {wind}, {topo}, {pop}, {infra}, RiskLevel), format('Fire Risk Level: ~w~n', [RiskLevel])"
        output = call_prolog_query(query)
        return {'result': output, 'type': 'risk_level'}
    
    else:
        raise ValueError(f'Unknown query type: {query_type}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


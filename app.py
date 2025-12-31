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
from functools import lru_cache

# Import the fire risk analysis functions
from fdi import analyze_location_dynamic

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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze fire risk for a given location."""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        area_name = data.get('area_name', 'user_location')
        
        # Perform the analysis
        result = analyze_location_dynamic(latitude, longitude, area_name)
        
        # Convert NumPy/pandas types to native Python types for JSON serialization
        result = convert_to_native_types(result)
        
        return jsonify({
            'success': True,
            'data': result
        })
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


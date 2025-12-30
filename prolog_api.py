"""
Standalone Prolog API service.
Deploy this separately on Render/Fly.io/Railway, then call it from Vercel.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os

app = Flask(__name__)
CORS(app)

PROLOG_FILE = "prolog.pl"

def call_prolog_query(query: str) -> str:
    """Execute a Prolog query and return raw output."""
    cmd = ["swipl", "-q", "-s", PROLOG_FILE, "-g", query, "-t", "halt"]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"Prolog error: {result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("Prolog query timed out")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'prolog-api'})

@app.route('/classify', methods=['POST'])
def classify():
    """Classify fire risk for an area."""
    try:
        data = request.get_json()
        area_name = data.get('area_name')
        fuel = data.get('fuel')
        temp = data.get('temp')
        hum = data.get('hum')
        wind = data.get('wind')
        topo = data.get('topo')
        pop = data.get('pop')
        infra = data.get('infra')
        
        if not all([area_name, fuel, temp, hum, wind, topo, pop, infra]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
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
                'error': f'Invalid JSON from Prolog: {output}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

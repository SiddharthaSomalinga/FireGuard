from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import os
import numpy as np

# Import the fire risk analysis functions
from fdi import analyze_location_dynamic

app = Flask(__name__)
CORS(app)

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

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


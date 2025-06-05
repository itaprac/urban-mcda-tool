from flask import Flask, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import os
import numpy as np
from pymcdm.methods import SPOTIS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


app = Flask(__name__)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1 = np.radians([lat1, lon1])
    p2 = np.radians([lat2, lon2])
    dlat, dlon = p2 - p1
    a = np.sin(dlat/2)**2 + np.cos(p1[0])*np.cos(p2[0])*np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def rancom_weights(criteria, pairwise):
    counts = {c: 0.0 for c in criteria}
    for key, val in pairwise.items():
        c1, c2 = key.split('_')
        if val == c1:
            counts[c1] += 1
        elif val == c2:
            counts[c2] += 1
        else:  # equal
            counts[c1] += 0.5
            counts[c2] += 0.5
    total = sum(counts.values())
    if total == 0:
        return np.ones(len(criteria)) / len(criteria)
    return np.array([counts[c]/total for c in criteria])

@app.route('/')
def index():
    index_path = os.path.join(BASE_DIR, 'index.html')
    return send_file(index_path)

@app.route('/save', methods=['POST'])
def save_points():
    data = request.get_json()
    points = data.get('points', [])
    criteria = data.get('criteria', [])
    locations = data.get('locations', {})
    
    # Save points
    df_points = pd.DataFrame(points)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    points_filename = os.path.join(DATA_DIR, f"points_{timestamp}.csv")
    df_points.to_csv(points_filename, index=False)
    
    # Save criteria with locations if provided
    records = []
    for c in criteria:
        loc = locations.get(c, {})
        records.append({
            'criteria': c,
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude')
        })
    df_criteria = pd.DataFrame(records)
    criteria_filename = os.path.join(DATA_DIR, f"criteria_{timestamp}.csv")
    df_criteria.to_csv(criteria_filename, index=False)
    
    print(f"Saved {len(points)} points and {len(criteria)} criteria")

    return jsonify({
        'success': True,
        'filename': os.path.basename(points_filename),
        'criteria_file': os.path.basename(criteria_filename)
    })


@app.route('/rank', methods=['POST'])
def rank_points():
    data = request.get_json()
    points = data.get('points', [])
    criteria = data.get('criteria', [])
    pairwise = data.get('pairwise', {})
    locations = data.get('locations', {})

    if not points or not criteria:
        return jsonify({'success': False, 'error': 'No data'}), 400

    weights = rancom_weights(criteria, pairwise)

    matrix = []
    for p in points:
        lat = p['latitude']
        lon = p['longitude']
        row = []
        for c in criteria:
            loc = locations.get(c)
            if loc:
                row.append(haversine(lat, lon, loc['latitude'], loc['longitude']))
            else:
                row.append(0.0)
        matrix.append(row)
    matrix = np.array(matrix)
    types = np.array([-1]*len(criteria))
    bounds = SPOTIS.make_bounds(matrix)
    spotis = SPOTIS(bounds)
    prefs = spotis(matrix, weights, types)
    ranking = list(np.argsort(prefs) + 1)
    return jsonify({'success': True, 'weights': weights.tolist(), 'ranking': ranking})

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)

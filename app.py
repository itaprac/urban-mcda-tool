from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
    with open(index_path, 'r') as f:
        return f.read()

@app.route('/save', methods=['POST'])
def save_points():
    data = request.get_json()
    points = data.get('points', [])
    criteria = data.get('criteria', [])
    
    # Save points
    df_points = pd.DataFrame(points)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    points_filename = f"points_{timestamp}.csv"
    df_points.to_csv(points_filename, index=False)
    
    # Save criteria
    df_criteria = pd.DataFrame({'criteria': criteria})
    criteria_filename = f"criteria_{timestamp}.csv"
    df_criteria.to_csv(criteria_filename, index=False)
    
    print(f"Saved {len(points)} points and {len(criteria)} criteria")
    
    return jsonify({
        'success': True, 
        'filename': points_filename,
        'criteria_file': criteria_filename
    })

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)

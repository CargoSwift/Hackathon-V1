from flask import Flask, request, jsonify, send_file
from datetime import datetime
import csv

app = Flask(__name__)

# In-memory storage for items and containers
items = []
containers = []
logs = []

# Helper functions
def log_action(action_type, item_id=None, user_id=None, details=None):
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "actionType": action_type,
        "itemId": item_id,
        "userId": user_id,
        "details": details
    })

@app.route('/',methods=['GET'])
def home():
    return jsonify({'message':'hello'})

# Placement Recommendations API
@app.route('/api/placement', methods=['POST'])
def placement_recommendations():
    data = request.json
    items = data.get('items', [])
    containers = data.get('containers', [])

    # Dummy placement logic (replace with actual logic)
    placements = []
    for item in items:
        for container in containers:
            if item['preferredZone'] == container['zone']:
                placements.append({
                    "itemId": item['itemId'],
                    "containerId": container['containerId'],
                    "position": {
                        "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                        "endCoordinates": {"width": item['width'], "depth": item['depth'], "height": item['height']}
                    }
                })
                break

    log_action("placement", details=f"Placed {len(placements)} items")
    return jsonify({"success": True, "placements": placements, "rearrangements": []})

# Item Search and Retrieval API
@app.route('/api/search', methods=['GET'])
def search_item():
    item_id = request.args.get('itemId')
    item_name = request.args.get('itemName')
    user_id = request.args.get('userId')

    # Dummy search logic (replace with actual logic)
    found_item = None
    for item in items:
        if item['itemId'] == item_id or item['name'] == item_name:
            found_item = item
            break

    if found_item:
        log_action("retrieval", item_id=item_id, user_id=user_id, details="Item found")
        return jsonify({
            "success": True,
            "found": True,
            "item": found_item,
            "retrievalSteps": [{"step": 1, "action": "retrieve", "itemId": item_id, "itemName": found_item['name']}]
        })
    else:
        return jsonify({"success": True, "found": False})

@app.route('/api/retrieve', methods=['POST'])
def retrieve_item():
    data = request.json
    item_id = data['itemId']
    user_id = data['userId']
    timestamp = data['timestamp']

    # Dummy retrieval logic (replace with actual logic)
    log_action("retrieval", item_id=item_id, user_id=user_id, details="Item retrieved")
    return jsonify({"success": True})

@app.route('/api/place', methods=['POST'])
def place_item():
    data = request.json
    item_id = data['itemId']
    user_id = data['userId']
    timestamp = data['timestamp']
    container_id = data['containerId']
    position = data['position']

    # Dummy placement logic (replace with actual logic)
    log_action("placement", item_id=item_id, user_id=user_id, details="Item placed")
    return jsonify({"success": True})

# Waste Management API
@app.route('/api/waste/identify', methods=['GET'])
def identify_waste():
    # Dummy waste identification logic (replace with actual logic)
    waste_items = []
    for item in items:
        if item['expiryDate'] < datetime.now().isoformat() or item['usageLimit'] <= 0:
            waste_items.append(item)

    return jsonify({"success": True, "wasteItems": waste_items})

@app.route('/api/waste/return-plan', methods=['POST'])
def return_plan():
    data = request.json
    undocking_container_id = data['undockingContainerId']
    undocking_date = data['undockingDate']
    max_weight = data['maxWeight']

    # Dummy return plan logic (replace with actual logic)
    return jsonify({
        "success": True,
        "returnPlan": [],
        "retrievalSteps": [],
        "returnManifest": {
            "undockingContainerId": undocking_container_id,
            "undockingDate": undocking_date,
            "returnItems": [],
            "totalVolume": 0,
            "totalWeight": 0
        }
    })

@app.route('/api/waste/complete-undocking', methods=['POST'])
def complete_undocking():
    data = request.json
    undocking_container_id = data['undockingContainerId']
    timestamp = data['timestamp']

    # Dummy undocking logic (replace with actual logic)
    log_action("disposal", details=f"Undocked container {undocking_container_id}")
    return jsonify({"success": True, "itemsRemoved": 0})

# Time Simulation API
@app.route('/api/simulate/day', methods=['POST'])
def simulate_day():
    data = request.json
    num_of_days = data.get('numOfDays', 1)
    to_timestamp = data.get('toTimestamp')
    items_to_be_used_per_day = data.get('itemsToBeUsedPerDay', [])

    # Dummy simulation logic (replace with actual logic)
    new_date = datetime.now().isoformat()
    changes = {
        "itemsUsed": [],
        "itemsExpired": [],
        "itemsDepletedToday": []
    }

    return jsonify({"success": True, "newDate": new_date, "changes": changes})

# Import/Export API
@app.route('/api/import/items', methods=['POST'])
def import_items():
    file = request.files['file']
    items_imported = 0
    errors = []

    # Dummy import logic (replace with actual logic)
    csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in csv_reader:
        items.append(row)
        items_imported += 1

    return jsonify({"success": True, "itemsImported": items_imported, "errors": errors})

@app.route('/api/export/arrangement', methods=['GET'])
def export_arrangement():
    # Dummy export logic (replace with actual logic)
    with open('data/arrangement.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["Item ID", "Container ID", "Coordinates (W1,D1,H1)", "(W2,D2,H2)"])
        for item in items:
            writer.writerow([item['itemId'], item['containerId'], "(0,0,0)", "(10,10,10)"])

    return send_file('data/arrangement.csv', as_attachment=True)

# Logging API
@app.route('/api/logs', methods=['GET'])
def get_logs():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    item_id = request.args.get('itemId')
    user_id = request.args.get('userId')
    action_type = request.args.get('actionType')

    # Filter logs based on query parameters
    filtered_logs = logs
    if start_date:
        filtered_logs = [log for log in filtered_logs if log['timestamp'] >= start_date]
    if end_date:
        filtered_logs = [log for log in filtered_logs if log['timestamp'] <= end_date]
    if item_id:
        filtered_logs = [log for log in filtered_logs if log['itemId'] == item_id]
    if user_id:
        filtered_logs = [log for log in filtered_logs if log['userId'] == user_id]
    if action_type:
        filtered_logs = [log for log in filtered_logs if log['actionType'] == action_type]

    return jsonify({"success": True, "logs": filtered_logs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
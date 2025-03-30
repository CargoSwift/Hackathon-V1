# backend/app.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'))
    return conn

# Helper functions
def log_action(action_type, item_id=None, user_id=None, details=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (action_type, item_id, user_id, details) VALUES (%s, %s, %s, %s)",
        (action_type, item_id, user_id, details)
    )
    conn.commit()
    cur.close()
    conn.close()

def calculate_retrieval_steps(item_id, container_id):
    # This is a simplified version - in a real implementation, you'd need to:
    # 1. Find all items in front of the target item in the container
    # 2. Calculate how many need to be moved to retrieve the target
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get the target item's position
    cur.execute("""
        SELECT start_coordinates->>'depth' as depth 
        FROM placements 
        WHERE item_id = %s AND container_id = %s
    """, (item_id, container_id))
    target_depth = float(cur.fetchone()['depth'])
    
    # Count items in front (with lower depth)
    cur.execute("""
        SELECT COUNT(*) 
        FROM placements 
        WHERE container_id = %s 
        AND (start_coordinates->>'depth')::float < %s
    """, (container_id, target_depth))
    
    steps = cur.fetchone()['count']
    cur.close()
    conn.close()
    return steps

def check_expired_items():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Mark expired items as waste
    cur.execute("""
        UPDATE items 
        SET is_waste = TRUE 
        WHERE expiry_date < CURRENT_DATE AND is_waste = FALSE
        RETURNING item_id
    """)
    expired_items = cur.fetchall()
    
    # Log the expired items
    for item in expired_items:
        cur.execute("""
            INSERT INTO waste (item_id, reason) 
            VALUES (%s, 'Expired')
        """, (item['item_id'],))
    
    conn.commit()
    cur.close()
    conn.close()
    return len(expired_items)

@app.route('/')
def home():
    return jsonify({'message': 'Space Station Cargo Management System API'})

# Placement Recommendations API
@app.route('/api/placement', methods=['POST'])
def placement_recommendations():
    data = request.json
    new_items = data.get('items', [])
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    placements = []
    rearrangements = []
    
    for item in new_items:
        # Try preferred zone first
        cur.execute("""
            SELECT container_id, available_volume 
            FROM containers 
            WHERE zone = %s AND available_volume >= %s
            ORDER BY available_volume DESC
            LIMIT 1
        """, (item['preferredZone'], item['width'] * item['depth'] * item['height']))
        
        container = cur.fetchone()
        
        if container:
            # Place in preferred zone
            placement = {
                "itemId": item['itemId'],
                "containerId": container['container_id'],
                "position": {
                    "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                    "endCoordinates": {
                        "width": item['width'],
                        "depth": item['depth'],
                        "height": item['height']
                    }
                }
            }
            placements.append(placement)
            
            # Update container available volume
            cur.execute("""
                UPDATE containers 
                SET available_volume = available_volume - %s 
                WHERE container_id = %s
            """, (item['width'] * item['depth'] * item['height'], container['container_id']))
            
            # Update item current zone
            cur.execute("""
                UPDATE items 
                SET current_zone = %s 
                WHERE item_id = %s
            """, (item['preferredZone'], item['itemId']))
            
            # Log placement
            cur.execute("""
                INSERT INTO placements (item_id, container_id, start_coordinates, end_coordinates)
                VALUES (%s, %s, %s, %s)
            """, (
                item['itemId'],
                container['container_id'],
                '{"width": 0, "depth": 0, "height": 0}',
                f'{{"width": {item["width"]}, "depth": {item["depth"]}, "height": {item["height"]}}}'
            ))
        else:
            # Try any available container
            cur.execute("""
                SELECT container_id, zone, available_volume 
                FROM containers 
                WHERE available_volume >= %s
                ORDER BY available_volume DESC
                LIMIT 1
            """, (item['width'] * item['depth'] * item['height'],))
            
            container = cur.fetchone()
            
            if container:
                placement = {
                    "itemId": item['itemId'],
                    "containerId": container['container_id'],
                    "position": {
                        "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                        "endCoordinates": {
                            "width": item['width'],
                            "depth": item['depth'],
                            "height": item['height']
                        }
                    }
                }
                placements.append(placement)
                
                # Update container available volume
                cur.execute("""
                    UPDATE containers 
                    SET available_volume = available_volume - %s 
                    WHERE container_id = %s
                """, (item['width'] * item['depth'] * item['height'], container['container_id']))
                
                # Update item current zone
                cur.execute("""
                    UPDATE items 
                    SET current_zone = %s 
                    WHERE item_id = %s
                """, (container['zone'], item['itemId']))
                
                # Log placement
                cur.execute("""
                    INSERT INTO placements (item_id, container_id, start_coordinates, end_coordinates)
                    VALUES (%s, %s, %s, %s)
                """, (
                    item['itemId'],
                    container['container_id'],
                    '{"width": 0, "depth": 0, "height": 0}',
                    f'{{"width": {item["width"]}, "depth": {item["depth"]}, "height": {item["height"]}}}'
                ))
            else:
                # No space available - suggest rearrangement
                rearrangements.append({
                    "itemId": item['itemId'],
                    "message": "Insufficient space - rearrangement required"
                })
    
    conn.commit()
    cur.close()
    conn.close()
    
    log_action("placement", details=f"Placed {len(placements)} items")
    return jsonify({
        "success": True, 
        "placements": placements, 
        "rearrangements": rearrangements
    })

# Item Search and Retrieval API
@app.route('/api/search', methods=['GET'])
def search_item():
    item_id = request.args.get('itemId')
    item_name = request.args.get('itemName')
    user_id = request.args.get('userId')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM items WHERE "
    params = []
    
    if item_id:
        query += "item_id = %s"
        params.append(item_id)
    elif item_name:
        query += "name ILIKE %s"
        params.append(f"%{item_name}%")
    else:
        return jsonify({"success": False, "message": "Please provide itemId or itemName"})
    
    cur.execute(query, params)
    found_item = cur.fetchone()
    
    if found_item:
        # Get placement info
        cur.execute("""
            SELECT p.*, c.zone 
            FROM placements p
            JOIN containers c ON p.container_id = c.container_id
            WHERE p.item_id = %s
            ORDER BY p.placed_at DESC
            LIMIT 1
        """, (found_item['item_id'],))
        
        placement = cur.fetchone()
        
        if placement:
            steps = calculate_retrieval_steps(found_item['item_id'], placement['container_id'])
            
            log_action(
                "search", 
                item_id=found_item['item_id'], 
                user_id=user_id, 
                details=f"Searched for item {found_item['name']}"
            )
            
            return jsonify({
                "success": True,
                "found": True,
                "item": found_item,
                "placement": placement,
                "retrievalSteps": steps,
                "instructions": [
                    f"1. Locate container {placement['container_id']} in {placement['zone']} zone",
                    f"2. Remove {steps} items in front if necessary",
                    f"3. Retrieve {found_item['name']} (ID: {found_item['item_id']})"
                ]
            })
    
    return jsonify({"success": True, "found": False})

@app.route('/api/retrieve', methods=['POST'])
def retrieve_item():
    data = request.json
    item_id = data['itemId']
    user_id = data['userId']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get item and placement info
    cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
    item = cur.fetchone()
    
    if not item:
        return jsonify({"success": False, "message": "Item not found"})
    
    cur.execute("""
        SELECT p.*, c.zone 
        FROM placements p
        JOIN containers c ON p.container_id = c.container_id
        WHERE p.item_id = %s
        ORDER BY p.placed_at DESC
        LIMIT 1
    """, (item_id,))
    
    placement = cur.fetchone()
    
    if not placement:
        return jsonify({"success": False, "message": "Item not placed in any container"})
    
    # Calculate retrieval steps
    steps = calculate_retrieval_steps(item_id, placement['container_id'])
    
    # Log the retrieval
    cur.execute("""
        INSERT INTO retrievals (item_id, user_id, steps, from_container)
        VALUES (%s, %s, %s, %s)
    """, (item_id, user_id, steps, placement['container_id']))
    
    # Update usage limit if applicable
    if item['usage_limit'] is not None:
        new_usage_limit = item['usage_limit'] - 1
        if new_usage_limit <= 0:
            # Mark as waste if no uses left
            cur.execute("""
                UPDATE items SET is_waste = TRUE, usage_limit = 0 WHERE item_id = %s
            """, (item_id,))
            cur.execute("""
                INSERT INTO waste (item_id, reason) VALUES (%s, 'Out of Uses')
            """, (item_id,))
        else:
            cur.execute("""
                UPDATE items SET usage_limit = %s WHERE item_id = %s
            """, (new_usage_limit, item_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    log_action("retrieval", item_id=item_id, user_id=user_id, 
              details=f"Retrieved {item['name']} with {steps} steps")
    
    return jsonify({
        "success": True,
        "message": f"Item {item['name']} retrieved successfully",
        "steps": steps,
        "remainingUses": item['usage_limit'] - 1 if item['usage_limit'] else None
    })

@app.route('/api/place', methods=['POST'])
def place_item():
    data = request.json
    item_id = data['itemId']
    user_id = data['userId']
    container_id = data['containerId']
    position = data['position']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get item and container info
    cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
    item = cur.fetchone()
    
    cur.execute("SELECT * FROM containers WHERE container_id = %s", (container_id,))
    container = cur.fetchone()
    
    if not item or not container:
        return jsonify({"success": False, "message": "Item or container not found"})
    
    # Calculate item volume
    item_volume = item['width'] * item['depth'] * item['height']
    
    # Check if container has enough space
    if container['available_volume'] < item_volume:
        return jsonify({"success": False, "message": "Not enough space in container"})
    
    # Record the placement
    cur.execute("""
        INSERT INTO placements (item_id, container_id, start_coordinates, end_coordinates)
        VALUES (%s, %s, %s, %s)
    """, (
        item_id,
        container_id,
        position['startCoordinates'],
        position['endCoordinates']
    ))
    
    # Update container available volume
    cur.execute("""
        UPDATE containers 
        SET available_volume = available_volume - %s 
        WHERE container_id = %s
    """, (item_volume, container_id))
    
    # Update item current zone
    cur.execute("""
        UPDATE items 
        SET current_zone = %s 
        WHERE item_id = %s
    """, (container['zone'], item_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    log_action("placement", item_id=item_id, user_id=user_id, 
              details=f"Placed item in container {container_id}")
    
    return jsonify({"success": True, "message": "Item placed successfully"})

# Waste Management API
@app.route('/api/waste/identify', methods=['GET'])
def identify_waste():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get expired items
    cur.execute("""
        SELECT i.* 
        FROM items i
        LEFT JOIN waste w ON i.item_id = w.item_id
        WHERE (i.expiry_date < CURRENT_DATE OR i.usage_limit <= 0)
        AND i.is_waste = FALSE
        AND w.item_id IS NULL
    """)
    potential_waste = cur.fetchall()
    
    # Mark them as waste
    for item in potential_waste:
        reason = 'Expired' if item['expiry_date'] and item['expiry_date'] < datetime.now().date() else 'Out of Uses'
        cur.execute("""
            UPDATE items 
            SET is_waste = TRUE 
            WHERE item_id = %s
        """, (item['item_id'],))
        
        cur.execute("""
            INSERT INTO waste (item_id, reason) 
            VALUES (%s, %s)
        """, (item['item_id'], reason))
    
    conn.commit()
    
    # Get all waste items
    cur.execute("""
        SELECT i.*, w.reason, w.marked_at
        FROM items i
        JOIN waste w ON i.item_id = w.item_id
        WHERE i.is_waste = TRUE
    """)
    waste_items = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True, 
        "wasteItems": waste_items,
        "newlyIdentified": len(potential_waste)
    })

@app.route('/api/waste/return-plan', methods=['POST'])
def return_plan():
    data = request.json
    undocking_container_id = data['undockingContainerId']
    undocking_date = data['undockingDate']
    max_weight = data['maxWeight']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all waste items
    cur.execute("""
        SELECT i.*, w.reason
        FROM items i
        JOIN waste w ON i.item_id = w.item_id
        WHERE i.is_waste = TRUE
    """)
    waste_items = cur.fetchall()
    
    # Get undocking container info
    cur.execute("""
        SELECT * FROM containers 
        WHERE container_id = %s
    """, (undocking_container_id,))
    container = cur.fetchone()
    
    if not container:
        return jsonify({"success": False, "message": "Undocking container not found"})
    
    # Calculate total volume and weight
    total_volume = sum(item['width'] * item['depth'] * item['height'] for item in waste_items)
    total_weight = sum(item['mass'] for item in waste_items)
    
    # Check if everything fits
    if total_volume > container['available_volume'] or total_weight > max_weight:
        # Need to prioritize which waste to return
        # Simple strategy: prioritize by oldest waste first
        cur.execute("""
            SELECT i.*, w.reason, w.marked_at
            FROM items i
            JOIN waste w ON i.item_id = w.item_id
            WHERE i.is_waste = TRUE
            ORDER BY w.marked_at ASC
        """)
        prioritized_waste = cur.fetchall()
        
        selected_items = []
        current_volume = 0
        current_weight = 0
        
        for item in prioritized_waste:
            item_volume = item['width'] * item['depth'] * item['height']
            if (current_volume + item_volume <= container['available_volume'] and 
                current_weight + item['mass'] <= max_weight):
                selected_items.append(item)
                current_volume += item_volume
                current_weight += item['mass']
        
        waste_items = selected_items
        total_volume = current_volume
        total_weight = current_weight
    
    # Create return plan
    cur.execute("""
        INSERT INTO return_plans (
            undocking_container_id, 
            undocking_date, 
            max_weight, 
            total_volume, 
            total_weight
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING plan_id
    """, (undocking_container_id, undocking_date, max_weight, total_volume, total_weight))
    
    plan_id = cur.fetchone()['plan_id']
    
    # Generate manifest
    manifest = {
        "undockingContainerId": undocking_container_id,
        "undockingDate": undocking_date,
        "returnItems": waste_items,
        "totalVolume": total_volume,
        "totalWeight": total_weight
    }
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "returnPlan": {
            "planId": plan_id,
            "itemsToReturn": len(waste_items),
            "totalVolume": total_volume,
            "totalWeight": total_weight
        },
        "retrievalSteps": [],  # This would require more complex logic
        "returnManifest": manifest
    })

@app.route('/api/waste/complete-undocking', methods=['POST'])
def complete_undocking():
    data = request.json
    plan_id = data['planId']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get the return plan
    cur.execute("""
        SELECT * FROM return_plans 
        WHERE plan_id = %s
    """, (plan_id,))
    plan = cur.fetchone()
    
    if not plan:
        return jsonify({"success": False, "message": "Return plan not found"})
    
    # Get items in the plan (simplified - in reality you'd have a separate table for plan items)
    cur.execute("""
        SELECT i.*
        FROM items i
        JOIN waste w ON i.item_id = w.item_id
        WHERE i.is_waste = TRUE
        ORDER BY w.marked_at ASC
        LIMIT (
            SELECT COUNT(*) 
            FROM items i
            JOIN waste w ON i.item_id = w.item_id
            WHERE i.is_waste = TRUE
        )
    """)
    waste_items = cur.fetchall()
    
    # Remove the items (in a real system, you might archive them instead)
    items_removed = 0
    for item in waste_items:
        cur.execute("DELETE FROM placements WHERE item_id = %s", (item['item_id'],))
        cur.execute("DELETE FROM items WHERE item_id = %s", (item['item_id'],))
        items_removed += 1
    
    # Update container available volume
    cur.execute("""
        UPDATE containers 
        SET available_volume = width * depth * height 
        WHERE container_id = %s
    """, (plan['undocking_container_id'],))
    
    conn.commit()
    cur.close()
    conn.close()
    
    log_action("disposal", details=f"Undocked {items_removed} waste items")
    
    return jsonify({
        "success": True, 
        "itemsRemoved": items_removed,
        "message": f"Successfully undocked {items_removed} waste items"
    })

# Time Simulation API
@app.route('/api/simulate/day', methods=['POST'])
def simulate_day():
    data = request.json
    num_of_days = data.get('numOfDays', 1)
    items_to_be_used_per_day = data.get('itemsToBeUsedPerDay', [])
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    changes = {
        "itemsUsed": [],
        "itemsExpired": [],
        "itemsDepletedToday": []
    }
    
    # Simulate each day
    for day in range(num_of_days):
        # Mark expired items
        expired_count = check_expired_items()
        if expired_count > 0:
            changes["itemsExpired"].append({
                "day": day + 1,
                "count": expired_count
            })
        
        # Process items to be used
        for item_usage in items_to_be_used_per_day:
            item_id = item_usage['itemId']
            uses = item_usage.get('uses', 1)
            
            cur.execute("""
                SELECT * FROM items 
                WHERE item_id = %s AND is_waste = FALSE
            """, (item_id,))
            item = cur.fetchone()
            
            if item and item['usage_limit'] is not None:
                new_usage_limit = item['usage_limit'] - uses
                if new_usage_limit <= 0:
                    # Mark as waste
                    cur.execute("""
                        UPDATE items 
                        SET is_waste = TRUE, usage_limit = 0 
                        WHERE item_id = %s
                    """, (item_id,))
                    
                    cur.execute("""
                        INSERT INTO waste (item_id, reason) 
                        VALUES (%s, 'Out of Uses')
                    """, (item_id,))
                    
                    changes["itemsDepletedToday"].append({
                        "day": day + 1,
                        "itemId": item_id,
                        "name": item['name']
                    })
                else:
                    cur.execute("""
                        UPDATE items 
                        SET usage_limit = %s 
                        WHERE item_id = %s
                    """, (new_usage_limit, item_id))
                
                changes["itemsUsed"].append({
                    "day": day + 1,
                    "itemId": item_id,
                    "name": item['name'],
                    "remainingUses": max(0, new_usage_limit)
                })
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True, 
        "daysSimulated": num_of_days,
        "changes": changes
    })

# Data Export/Import APIs
@app.route('/api/import/items', methods=['POST'])
def import_items():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "message": "Only CSV files are supported"})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    items_imported = 0
    errors = []
    
    try:
        csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        for row in csv_reader:
            try:
                cur.execute("""
                    INSERT INTO items (
                        item_id, name, width, depth, height, mass, priority,
                        expiry_date, usage_limit, preferred_zone
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['Item ID'],
                    row['Name'],
                    float(row['Width (cm)']),
                    float(row['Depth (cm)']),
                    float(row['Height (cm)']),
                    float(row['Mass (kg)']),
                    int(row['Priority (1-100)']),
                    datetime.strptime(row['Expiry Date (ISO Format)'], '%Y-%m-%d').date() if row['Expiry Date (ISO Format)'] != 'N/A' else None,
                    int(row['Usage Limit']) if row['Usage Limit'] != 'N/A' else None,
                    row['Preferred Zone']
                ))
                items_imported += 1
            except Exception as e:
                errors.append({
                    "row": row,
                    "error": str(e)
                })
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": f"Import failed: {str(e)}",
            "itemsImported": items_imported,
            "errors": errors
        })
    finally:
        cur.close()
        conn.close()
    
    log_action("import", details=f"Imported {items_imported} items")
    return jsonify({
        "success": True,
        "itemsImported": items_imported,
        "errors": errors
    })

@app.route('/api/export/arrangement', methods=['GET'])
def export_arrangement():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get current placements
        cur.execute("""
            SELECT 
                i.item_id, i.name,
                p.container_id, 
                c.zone,
                p.start_coordinates,
                p.end_coordinates
            FROM placements p
            JOIN items i ON p.item_id = i.item_id
            JOIN containers c ON p.container_id = c.container_id
            ORDER BY p.placed_at DESC
        """)
        
        placements = cur.fetchall()
        
        # Write to CSV
        csv_file = 'arrangement_export.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Item ID', 'Item Name', 'Container ID', 'Zone',
                'Start Width', 'Start Depth', 'Start Height',
                'End Width', 'End Depth', 'End Height'
            ])
            
            for placement in placements:
                writer.writerow([
                    placement['item_id'],
                    placement['name'],
                    placement['container_id'],
                    placement['zone'],
                    placement['start_coordinates']['width'],
                    placement['start_coordinates']['depth'],
                    placement['start_coordinates']['height'],
                    placement['end_coordinates']['width'],
                    placement['end_coordinates']['depth'],
                    placement['end_coordinates']['height']
                ])
        
        log_action("export", details="Exported current arrangement")
        return send_file(csv_file, as_attachment=True)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Export failed: {str(e)}"
        })
    finally:
        cur.close()
        conn.close()

# Logging API
@app.route('/api/logs', methods=['GET'])
def get_logs():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    item_id = request.args.get('itemId')
    user_id = request.args.get('userId')
    action_type = request.args.get('actionType')
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM logs WHERE TRUE"
    params = []
    
    if start_date:
        query += " AND logged_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND logged_at <= %s"
        params.append(end_date)
    if item_id:
        query += " AND item_id = %s"
        params.append(item_id)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    if action_type:
        query += " AND action_type = %s"
        params.append(action_type)
    
    query += " ORDER BY logged_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cur.execute(query, params)
    logs = cur.fetchall()
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) FROM logs WHERE TRUE"
    count_params = []
    
    if start_date:
        count_query += " AND logged_at >= %s"
        count_params.append(start_date)
    if end_date:
        count_query += " AND logged_at <= %s"
        count_params.append(end_date)
    if item_id:
        count_query += " AND item_id = %s"
        count_params.append(item_id)
    if user_id:
        count_query += " AND user_id = %s"
        count_params.append(user_id)
    if action_type:
        count_query += " AND action_type = %s"
        count_params.append(action_type)
    
    cur.execute(count_query, count_params)
    total = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
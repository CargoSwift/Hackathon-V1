from flask import Flask, request, jsonify, send_file
from datetime import datetime
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from dotenv import load_dotenv
from flask_cors import CORS
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)
# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
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

def calculate_placement(containers, items):
    """Simplified placement algorithm - sorts items by priority and places in available space"""
    placements = []
    rearrangements = []
    
    # Sort items by priority (highest first)
    sorted_items = sorted(items, key=lambda x: x['priority'], reverse=True)
    
    for item in sorted_items:
        placed = False
        
        # Try preferred zone first
        for container in containers:
            if container['zone'] == item['preferredZone']:
                # Check if item fits (simplified check)
                if (float(container['available_volume']) >= 
                    float(item['width']) * float(item['depth']) * float(item['height'])):
                    
                    placement = {
                        "itemId": item['itemId'],
                        "containerId": container['containerId'],
                        "position": {
                            "startCoordinates": {
                                "width": 0, 
                                "depth": 0, 
                                "height": 0
                            },
                            "endCoordinates": {
                                "width": item['width'],
                                "depth": item['depth'],
                                "height": item['height']
                            }
                        }
                    }
                    placements.append(placement)
                    av = float(container['available_volume'])
                    av -= float(item['width']) * float(item['depth']) * float(item['height'])
                    container['available_volume'] = av 
                    placed = True
                    break
        
        # If not placed in preferred zone, try any available container
        if not placed:
            for container in containers:
                if float(container['available_volume']) >= float(item['width']) * float(item['depth']) * float(item['height']):
                    placement = {
                        "itemId": item['itemId'],
                        "containerId": container['containerId'],
                        "position": {
                            "startCoordinates": {
                                "width": 0, 
                                "depth": 0, 
                                "height": 0
                            },
                            "endCoordinates": {
                                "width": item['width'],
                                "depth": item['depth'],
                                "height": item['height']
                            }
                        }
                    }
                    placements.append(placement)
                    av = float(container['available_volume'])
                    av -= float(item['width']) * float(item['depth']) * float(item['height'])
                    container['available_volume'] = av 
                    placed = True
                    break
        
        if not placed:
            rearrangements.append({
                "itemId": item['itemId'],
                "message": "Insufficient space - rearrangement required"
            })
    
    return placements, rearrangements

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
    containers = data.get('containers', [])
    items = data.get('items', [])
    
    placements, rearrangements = calculate_placement(containers, items)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        for placement in placements:
            # Convert coordinates to proper JSON strings
            start_coords = json.dumps(placement['position']['startCoordinates'])
            end_coords = json.dumps(placement['position']['endCoordinates'])
            
            cur.execute(
                "INSERT INTO placements (item_id, container_id, start_coordinates, end_coordinates) "
                "VALUES (%s, %s, %s::json, %s::json)",
                (
                    placement['itemId'],
                    placement['containerId'],
                    start_coords,
                    end_coords
                )
            )
            cur.execute(
                "UPDATE items SET current_zone = (SELECT zone FROM containers WHERE container_id = %s) "
                "WHERE item_id = %s",
                (placement['containerId'], placement['itemId'])
            )
        conn.commit()
        log_action("placement", details=f"Placement recommendations generated")
        return jsonify({
            "success": True,
            "placements": placements,
            "rearrangements": rearrangements
        })
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
        conn.close()
        
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
    
    try:
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
        
        # Convert coordinates to proper JSON strings
        start_coords = json.dumps(position['startCoordinates'])
        end_coords = json.dumps(position['endCoordinates'])
        
        # Record the placement
        cur.execute("""
            INSERT INTO placements (item_id, container_id, start_coordinates, end_coordinates)
            VALUES (%s, %s, %s::json, %s::json)
        """, (
            item_id,
            container_id,
            start_coords,
            end_coords
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
        log_action("placement", item_id=item_id, user_id=user_id, 
                  details=f"Placed item in container {container_id}")
        
        return jsonify({"success": True, "message": "Item placed successfully"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
        conn.close()


@app.route('/api/rearrange', methods=['POST'])
def generate_rearrangement_plan():
    data = request.json
    container_id = data['containerId']
    items_in_container = data['items']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Get all containers with available space
        cur.execute("""
            SELECT container_id, zone, available_volume 
            FROM containers 
            WHERE container_id != %s
            ORDER BY available_volume DESC
        """, (container_id,))
        other_containers = cur.fetchall()
        
        # 2. Identify low-priority items that can be moved
        movable_items = sorted(
            [item for item in items_in_container if item['priority'] < 50],
            key=lambda x: x['priority']
        )
        
        # 3. Create rearrangement plan
        plan = {
            "planId": str(uuid.uuid4()),
            "containerId": container_id,
            "spaceFreed": 0,
            "estimatedTime": 0,
            "itemsToMove": [],
            "steps": []
        }
        
        # 4. Calculate optimal moves
        for item in movable_items:
            item_volume = item['width'] * item['depth'] * item['height']
            
            # Find first container with enough space
            for container in other_containers:
                if container['available_volume'] >= item_volume:
                    plan['itemsToMove'].append(item['item_id'])
                    plan['spaceFreed'] += item_volume
                    plan['estimatedTime'] += 2  # 2 minutes per item moved
                    
                    plan['steps'].append({
                        "action": "move",
                        "itemId": item['item_id'],
                        "fromContainer": container_id,
                        "toContainer": container['container_id'],
                        "reason": f"Low priority (P{item['priority']}), makes space for higher priority items"
                    })
                    
                    # Update container's available volume for next calculations
                    container['available_volume'] -= item_volume
                    break
        
        # 5. Add rotation suggestions for remaining items
        remaining_items = [item for item in items_in_container 
                         if item['item_id'] not in plan['itemsToMove']]
        
        for item in remaining_items:
            # Check if rotating would help (simplified logic)
            if item['width'] != item['height']:
                plan['steps'].append({
                    "action": "rotate",
                    "itemId": item['item_id'],
                    "newOrientation": f"{item['height']}x{item['width']}x{item['depth']}",
                    "reason": "Optimize space utilization"
                })
                plan['estimatedTime'] += 1  # 1 minute per rotation
        
        return jsonify({
            "success": True,
            "plan": plan
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    finally:
        cur.close()
        conn.close()

@app.route('/api/rearrange/execute', methods=['POST'])
def execute_rearrangement():
    data = request.json
    plan_id = data['planId']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # In a real implementation, you would:
        # 1. Look up the plan from database
        # 2. Execute each step
        # 3. Update container volumes
        # 4. Log all actions
        
        # For this example, we'll simulate success
        items_moved = 5  # This would come from actual execution
        
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Rearrangement completed successfully",
            "itemsMoved": items_moved
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })
    finally:
        cur.close()
        conn.close()

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

@app.route('/api/items', methods=['GET'])
def get_items():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                item_id,
                name,
                width,
                depth,
                height,
                mass,
                priority,
                expiry_date,
                usage_limit,
                preferred_zone,
                current_zone,
                is_waste
            FROM items
            WHERE is_waste = FALSE
            ORDER BY priority DESC, name
        """)
        items = cur.fetchall()
        
        return jsonify({
            "success": True,
            "items": items
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    finally:
        cur.close()
        conn.close()
        
# Data Export/Import APIs
@app.route('/api/import/containers', methods=['POST'])
def import_containers():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        for row in csv_reader:
            cur.execute(
                "INSERT INTO containers (container_id, zone, width, depth, height, available_volume) "
                "VALUES (%s, %s, %s, %s, %s, %s * %s * %s) "
                "ON CONFLICT (container_id) DO NOTHING",
                (
                    row['Container ID'],
                    row['Zone'],
                    float(row['Width (cm)']),
                    float(row['Depth (cm)']),
                    float(row['Height (cm)']),
                    float(row['Width (cm)']),
                    float(row['Depth (cm)']),
                    float(row['Height (cm)'])
                ))
        conn.commit()
        log_action("import", details="Containers imported")
        return jsonify({"success": True, "message": "Containers imported successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/api/import/items', methods=['POST'])
def import_items():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        for row in csv_reader:
            expiry_date = None if row['Expiry Date (ISO Format)'] == 'N/A' else row['Expiry Date (ISO Format)']
            usage_limit = None if row['Usage Limit'] == 'N/A' else int(row['Usage Limit'])
            
            cur.execute(
                "INSERT INTO items (item_id, name, width, depth, height, mass, priority, "
                "expiry_date, usage_limit, preferred_zone) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (item_id) DO NOTHING",
                (
                    row['Item ID'],
                    row['Name'],
                    float(row['Width (cm)']),
                    float(row['Depth (cm)']),
                    float(row['Height (cm)']),
                    float(row['Mass (kg)']),
                    int(row['Priority (1-100)']),
                    expiry_date,
                    usage_limit,
                    row['Preferred Zone']
                )
            )
        conn.commit()
        log_action("import", details="Items imported")
        return jsonify({"success": True, "message": "Items imported successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
        conn.close()

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

@app.route('/api/containers', methods=['GET'])
def get_containers():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                container_id, 
                zone, 
                width, 
                depth, 
                height, 
                available_volume,
                width * depth * height AS total_volume
            FROM containers
            ORDER BY zone, container_id
        """)
        containers = cur.fetchall()
        
        return jsonify({
            "success": True,
            "containers": containers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    finally:
        cur.close()
        conn.close()


@app.route('/api/containers/with-items', methods=['GET'])
def get_containers_with_items():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                c.container_id,
                c.zone,
                c.width,
                c.depth,
                c.height,
                c.available_volume,
                c.width * c.depth * c.height AS total_volume,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'item_id', i.item_id,
                            'name', i.name,
                            'width', i.width,
                            'depth', i.depth,
                            'height', i.height,
                            'priority', i.priority,
                            'is_waste', i.is_waste,
                            'usage_limit', i.usage_limit,
                            'start_coordinates', p.start_coordinates,
                            'end_coordinates', p.end_coordinates
                        )
                    ) FILTER (WHERE i.item_id IS NOT NULL),
                    '[]'
                ) AS items
            FROM containers c
            LEFT JOIN placements p ON c.container_id = p.container_id
            LEFT JOIN items i ON p.item_id = i.item_id
            GROUP BY c.container_id
            ORDER BY c.zone, c.container_id
        """)
        containers = cur.fetchall()
        
        # Parse JSON coordinates
        for container in containers:
            for item in container['items']:
                if isinstance(item['start_coordinates'], str):
                    item['start_coordinates'] = json.loads(item['start_coordinates'])
                if isinstance(item['end_coordinates'], str):
                    item['end_coordinates'] = json.loads(item['end_coordinates'])
        
        return jsonify({
            "success": True,
            "containers": containers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    finally:
        cur.close()
        conn.close()

@app.route('/api/items/unplaced', methods=['GET'])
def get_unplaced_items():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                i.item_id,
                i.name,
                i.width,
                i.depth,
                i.height,
                i.mass,
                i.priority,
                i.expiry_date,
                i.usage_limit,
                i.preferred_zone
            FROM items i
            LEFT JOIN placements p ON i.item_id = p.item_id
            WHERE p.item_id IS NULL
            AND i.is_waste = FALSE
            ORDER BY i.priority DESC
        """)
        items = cur.fetchall()
        
        return jsonify({
            "success": True,
            "items": items
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
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
    app.run(host='0.0.0.0', port=8000)
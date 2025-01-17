from flask import Flask, jsonify, request, send_file
import psycopg2
import os
import json
from flask_cors import CORS
import pandas as pd
from datetime import datetime
from urllib.parse import unquote


app = Flask(__name__)
CORS(app)

SCHEDULE_FILE = 'schedule.json'
BREAKOUTS_FILE = 'breakouts.json'
MENU_FILE = 'food.json'
BREAKOUT_FILES = ['ebreakouts.csv', 'ibreakouts.csv']



# Connect to PostgreSQL function
def connect_db():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')
        return conn
    except Exception as e:
        return str(e)  # Return the error message if connection fails

# Default route to avoid 404 on root
@app.route('/')
def home():
    return 'Welcome to the Seva Bot API!'


@app.route('/report', methods=['GET'])
def get_pdf():
    try:
        return send_file('BKY Annual Report 2024.pdf', as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Utility function to load the menu
def load_menu():
    try:
        with open(MENU_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"menu": {}}

# Endpoint: Get the full menu
@app.route('/menu', methods=['GET'])
def get_full_menu():
    menu = load_menu()
    return jsonify(menu)

@app.route('/menu/<path:date>', methods=['GET'])
def get_menu_by_date(date):
    # Load menu from the JSON file
    menu = load_menu().get('menu', {})
    
    # Decode the URL-encoded date and normalize it
    decoded_date = unquote(date).strip()
    
    # Add debug logging
    print(f"Received date (decoded): {decoded_date}")
    print(f"Available dates in menu: {list(menu.keys())}")
    
    # Try exact match first
    if decoded_date in menu:
        return jsonify({decoded_date: menu[decoded_date]})
        
    # Try normalized comparison (case-insensitive, trimmed)
    normalized_menu = {key.strip().lower(): (key, value) 
                      for key, value in menu.items()}
    normalized_date = decoded_date.lower()
    
    if normalized_date in normalized_menu:
        original_key, value = normalized_menu[normalized_date]
        return jsonify({original_key: value})
    
    return jsonify({"error": "Menu for this date not found"}), 404
    
# Route to return the schedule image
@app.route('/schedule_image', methods=['GET'])
def get_schedule_image():
    try:
        # Path to the uploaded image file
        image_path = 'schedule.jpg'
        return send_file(image_path, mimetype='image/jpeg')
    except Exception as e:
        return {"error": str(e)}, 500

# Load the breakout schedule JSON
def load_breakout_schedule():
    with open(BREAKOUTS_FILE, 'r') as file:
        return json.load(file)
    
# Endpoint: Get all Mandals
@app.route('/mandals', methods=['GET'])
def get_mandals():
    data = load_breakout_schedule()
    return jsonify({"mandals": list(data["mandals"].keys())})

# Endpoint: Get all Tracks for a Mandal
@app.route('/mandals/<mandal_name>/tracks', methods=['GET'])
def get_tracks(mandal_name):
    data = load_breakout_schedule()
    mandals = data.get("mandals", {})
    if mandal_name not in mandals:
        return jsonify({"error": "Mandal not found"}), 404
    return jsonify({"tracks": list(mandals[mandal_name].keys())})

# Endpoint: Get all Sessions for a Track
@app.route('/mandals/<mandal_name>/tracks/<track_name>/sessions', methods=['GET'])
def get_sessions(mandal_name, track_name):
    data = load_breakout_schedule()
    mandals = data.get("mandals", {})
    if mandal_name not in mandals:
        return jsonify({"error": "Mandal not found"}), 404
    tracks = mandals[mandal_name]
    if track_name not in tracks:
        return jsonify({"error": "Track not found"}), 404
    return jsonify({"sessions": tracks[track_name]})

# Endpoint: Search for a Session by Name
@app.route('/sessions/<session_name>', methods=['GET'])
def search_session(session_name):
    data = load_breakout_schedule()
    for mandal_name, tracks in data.get("mandals", {}).items():
        for track_name, sessions in tracks.items():
            for session in sessions:
                if session["name"].lower() == session_name.lower():
                    return jsonify({
                        "mandal": mandal_name,
                        "track": track_name,
                        "session": session
                    })
    return jsonify({"error": "Session not found"}), 404

# Utility function to load the schedule
def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist

# Utility function to save the schedule
def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w') as file:
        json.dump(schedule, file, indent=2)

# Route to get the full schedule
@app.route('/schedule', methods=['GET'])
def get_schedule():
    schedule = load_schedule()
    return jsonify(schedule)

# Route to update the schedule
@app.route('/schedule', methods=['POST'])
def update_schedule():
    new_schedule = request.json  # Expect the entire schedule to be sent in the request body
    if not isinstance(new_schedule, list):
        return jsonify({'error': 'Invalid schedule format. Expected a list of days with sessions.'}), 400

    save_schedule(new_schedule)
    return jsonify({'message': 'Schedule updated successfully!'})


# Utility function to load breakout data
def load_combined_breakouts():
    dataframes = [pd.read_csv(file) for file in BREAKOUT_FILES]
    return pd.concat(dataframes, ignore_index=True)

# Load breakouts into memory
combined_breakouts = load_combined_breakouts()

@app.route('/search_breakouts', methods=['POST'])
def search_breakouts():
    user_first_name = request.json.get('first_name', '').strip().title()
    
    if not user_first_name:
        return jsonify({"message": "Please provide your first name."}), 400

    matches = combined_breakouts[combined_breakouts['First Name'] == user_first_name]
    if matches.empty:
        return jsonify({
            "message": "No match found for your name. Please provide your full name (First and Last).",
            "prompt": "Enter your First Name and Last Name to search."
        })
    
    options = matches[['First Name', 'Last Name', 'Center', 'Primary Seva']].to_dict(orient='records')
    return jsonify({
        "message": "Please confirm your identity from the options below.",
        "options": options
    })

@app.route('/confirm_breakout', methods=['POST'])
def confirm_breakout():
    try:
        user_data = request.json
        first_name = user_data.get('First Name', '').strip().title()
        last_name = user_data.get('Last Name', '').strip().title()
        center = user_data.get('Center', '').strip()
        seva = user_data.get('Primary Seva', '').strip()

        if not all([first_name, last_name, center, seva]):
            return jsonify({"message": "Please provide complete details to confirm your identity."}), 400

        # Use the pre-loaded combined_breakouts
        matches = combined_breakouts[
            (combined_breakouts['First Name'] == first_name) &
            (combined_breakouts['Last Name'] == last_name) &
            (combined_breakouts['Center'] == center) &
            (combined_breakouts['Primary Seva'] == seva)
        ]
            
        eSideBreakouts = pd.read_csv("ebreakouts.csv")
        eSideBreakouts = pd.concat(eSideBreakouts, ignore_index=True)
        iSideBreakouts = pd.read_csv("ibreakouts.csv")
        iSideBreakouts = pd.concat(iSideBreakouts, ignore_index=True)

        eSideMatches = eSideBreakouts[
            (eSideBreakouts['First Name'] == first_name) &
            (eSideBreakouts['Last Name'] == last_name) &
            (eSideBreakouts['Center'] == center) &
            (eSideBreakouts['Primary Seva'] == seva)
        ]

        iSideMatches = iSideBreakouts[
            (iSideBreakouts['First Name'] == first_name) &
            (iSideBreakouts['Last Name'] == last_name) &
            (iSideBreakouts['Center'] == center) &
            (iSideBreakouts['Primary Seva'] == seva)
        ]

        if matches.empty:
            return jsonify({"message": "Confirmation failed. Please try again or contact support."}), 400

        # Extract data from the row
        person = matches.iloc[0]
        # Replace the current is_ibreakout detection with:
        columns = set(person.index)
        is_ibreakout = 'Room Number' not in columns
        
        # Helper function to format room numbers
        def format_room(room):
            if pd.isna(room):
                return "N/A"
            try:
                # Convert to float first to handle both string and numeric inputs
                num = float(room)
                # Check if it's a whole number
                if num.is_integer():
                    return str(int(num))  # Remove decimal for whole numbers
                return str(num)  # Keep decimal if it's not a whole number
            except (ValueError, TypeError):
                return str(room)
        
        # Helper function to handle nan values
        def format_session(session):
            if pd.isna(session):
                return "N/A"
            return str(session)

        breakout_details = {}
        
        # Check if person is from ibreakouts.csv (looking for indicators like Wing or specific columns)
        is_ibreakout = False
        eSidePerson = eSideMatches.iloc[0]
        iSidePerson = iSideMatches.iloc[0]
        for col in iSidePerson.index if eSideMatches.empty else eSidePerson.index:
            if col in ['Wing', 'Goshthi']:  # Add any other columns unique to ibreakouts.csv
                is_ibreakout = True
                break

        if 'Breakout #1 (10:30 - 12:00)' in person.index:
            # Handle original format with separate room columns
            breakout1_session = format_session(person.get('Breakout #1 (10:30 - 12:00)', 'N/A'))
            breakout1_room = format_room(person.get('Room Number', 'N/A'))
            if breakout1_session != "N/A":
                breakout_details['Breakout #1'] = {
                    "Time": "10:30 - 12:00",
                    "Session": breakout1_session,
                    "Room": breakout1_room,
                    "Display": f"{breakout1_session} (Room {breakout1_room})" if breakout1_session != 'N/A' else 'N/A'
                }

            breakout2_session = format_session(person.get('Breakout #2 (6:00 - 7:30)', 'N/A'))
            breakout2_room = format_room(person.get('Room Number.1', 'N/A'))
            if breakout2_session != "N/A":
                breakout_details['Breakout #2'] = {
                    "Time": "6:00 - 7:30",
                    "Session": breakout2_session,
                    "Room": breakout2_room,
                    "Display": f"{breakout2_session} (Room {breakout2_room})" if breakout2_session != 'N/A' else 'N/A'
                }

            breakout3_session = format_session(person.get('Breakout #3 (8:45 - 9:45)', 'N/A'))
            breakout3_room = format_room(person.get('Room Number.2', 'N/A'))
            if breakout3_session != "N/A":
                breakout_details['Breakout #3'] = {
                    "Time": "8:45 - 9:45",
                    "Session": breakout3_session,
                    "Room": breakout3_room,
                    "Display": f"{breakout3_session} (Room {breakout3_room})" if breakout3_session != 'N/A' else 'N/A'
                }

            center_planning_session = format_session(person.get('Center Planning (4:30 - 6:00)', 'N/A'))
            center_planning_room = format_room(person.get('Room Number.3', 'N/A'))
            center_planning = {
                "Time": "4:30 - 6:00",
                "Session": center_planning_session,
                "Room": center_planning_room,
                "Display": f"{center_planning_session} (Room {center_planning_room})" if center_planning_session != 'N/A' else 'N/A'
            }

            ghoshti_session = format_session(person.get('Ghosthi Group (3:15 - 4:00)', 'N/A'))
            ghoshti_room = format_room(person.get('Room Number.4', 'N/A'))
            ghoshti = {
                "Time": "3:15 - 4:00",
                "Session": ghoshti_session,
                "Room": ghoshti_room,
                "Display": f"{ghoshti_session} (Room {ghoshti_room})" if ghoshti_session != 'N/A' else 'N/A'
            }
        else:
            # Handle new format
            breakout1_session = format_session(person.get('Breakout #1', 'N/A'))
            if breakout1_session != "N/A":
                breakout_details['Breakout #1'] = {
                    "Time": "10:30 - 12:00",
                    "Session": breakout1_session,
                    "Room": "N/A",
                    "Display": breakout1_session
                }

            breakout2_session = format_session(person.get('Breakout #2', 'N/A'))
            if breakout2_session != "N/A":
                breakout_details['Breakout #2'] = {
                    "Time": "2:00 - 3:30",
                    "Session": breakout2_session,
                    "Room": "N/A",
                    "Display": breakout2_session
                }

            # Parse room from Goshthi field (e.g., "4 - Room 5" -> "Room 5")
            goshthi = format_session(person.get('Goshthi', 'N/A'))
            if ' - ' in str(goshthi):
                room_info = str(goshthi).split(' - ')[1]
                session_info = str(goshthi).split(' - ')[0]
            else:
                room_info = 'N/A'
                session_info = str(goshthi) if goshthi != 'N/A' else 'N/A'

            ghoshti = {
                "Time": "3:45 - 4:45",
                "Session": session_info,
                "Room": room_info,
                "Display": goshthi if goshthi != 'N/A' else 'N/A'
            }
            
            center_planning = {
                "Time": "N/A",
                "Session": "N/A",
                "Room": "N/A",
                "Display": "N/A"
            }

        # Build the response
        response_details = {
            "First Name": person['First Name'],
            "Last Name": person['Last Name'],
            "Center": person['Center'],
            "Primary Seva": person['Primary Seva'],
            "Breakout Sessions": breakout_details,
            "Center Planning": center_planning,
            "Ghoshti": ghoshti,
            "Source": "ibreakouts" if is_ibreakout else "ebreakouts"
        }

        return jsonify({
            "message": "Breakout details confirmed!",
            "details": response_details
        })
    
    except Exception as e:
        print(f"Error in confirm_breakout: {str(e)}")  # Add this for debugging
        return jsonify({"message": "Error confirming breakout details.", "error": str(e)}), 500


@app.route('/search_by_full_name', methods=['POST'])
def search_by_full_name():
    user_data = request.json
    first_name = user_data.get('First Name', '').strip().title()
    last_name = user_data.get('Last Name', '').strip().title()

    if not first_name or not last_name:
        return jsonify({"message": "Please provide both First Name and Last Name."}), 400

    matches = combined_breakouts[
        (combined_breakouts['First Name'] == first_name) &
        (combined_breakouts['Last Name'] == last_name)
    ]

    if matches.empty:
        return jsonify({"message": "No match found for the provided name. Please check your details or contact support."})
    
    options = matches[['First Name', 'Last Name', 'Center', 'Primary Seva']].to_dict(orient='records')
    return jsonify({
        "message": "Please confirm your identity from the options below.",
        "options": options
    })

@app.route('/ebreakouts_map', methods=['GET'])
def get_ebreakouts_map():
    try:
        return send_file('eBreakoutsMap.jpg', mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ibreakouts_map', methods=['GET'])
def get_ibreakouts_map():
    try:
        return send_file('iBreakoutsMap.jpg', mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


### Stuff from seva

# Route to get all seva slots with volunteers
@app.route('/sevas', methods=['GET'])
def get_sevas():
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB

    cursor = conn.cursor()
    # Get all sevas
    cursor.execute("""
        SELECT s.id, s.seva_name, s.time_slot, s.date_slot, s.description, 
        COALESCE(array_agg(v.name) FILTER (WHERE v.name IS NOT NULL), '{}') AS volunteers
        FROM seva_slots s
        LEFT JOIN volunteers v ON s.id = v.seva_id
        GROUP BY s.id;
    """)
    sevas = cursor.fetchall()
    conn.close()

    # Map the result to include column names
    sevas_list = []
    for seva in sevas:
        sevas_list.append({
            'id': seva[0],
            'seva_name': seva[1],
            'time_slot': seva[2],
            'date_slot': seva[3],
            'description': seva[4],
            'volunteers': seva[5]  # List of volunteers
        })

    return jsonify(sevas_list)


# Route to add a new seva
@app.route('/add_seva', methods=['POST'])
def add_seva():
    seva_name = request.json['seva_name']
    time_slot = request.json['time_slot']
    date_slot = request.json['date_slot']  # Get date_slot from the request
    description = request.json['description']
    
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB
    
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO seva_slots (seva_name, time_slot, date_slot, description) VALUES (%s, %s, %s, %s)", 
        (seva_name, time_slot, date_slot, description)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Seva added successfully!'})

# Route to join a seva
@app.route('/join_seva', methods=['POST'])
def join_seva():
    name = request.json['name']
    seva_id = request.json['seva_id']
    
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB
    
    cursor = conn.cursor()
    cursor.execute("SELECT seva_name FROM seva_slots WHERE id = %s", (seva_id,))
    seva = cursor.fetchone()
    
    if seva:
        cursor.execute("INSERT INTO volunteers (name, seva_id) VALUES (%s, %s)", (name, seva_id))
        conn.commit()
        conn.close()
        return jsonify({'message': f'{name} has joined the seva: {seva[0]}'})
    else:
        conn.close()
        return jsonify({'message': 'Invalid seva ID.'})

# Route to delete a seva
@app.route('/delete_seva/<int:id>', methods=['DELETE'])
def delete_seva(id):
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB
    
    cursor = conn.cursor()
    
    # Delete volunteers associated with this seva first
    cursor.execute("DELETE FROM volunteers WHERE seva_id = %s", (id,))
    
    # Delete the seva from seva_slots
    cursor.execute("DELETE FROM seva_slots WHERE id = %s", (id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Seva deleted successfully!'})

if __name__ == '__main__':
    app.run(debug=True)


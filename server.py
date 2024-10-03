from flask import Flask, jsonify, request
import psycopg2
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

# Route to get all seva slots
@app.route('/sevas', methods=['GET'])
def get_sevas():
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seva_slots")
    sevas = cursor.fetchall()
    conn.close()
    
    # Map the result to include column names
    sevas_list = []
    for seva in sevas:
        sevas_list.append({
            'id': seva[0],
            'seva_name': seva[1],
            'time_slot': seva[2],
            'date_slot': seva[3],  # Include the date slot
            'description': seva[4]
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


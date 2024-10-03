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
    
    return jsonify(sevas)

# Route to add a new seva
@app.route('/add_seva', methods=['POST'])
def add_seva():
    seva_name = request.json['seva_name']
    time_slot = request.json['time_slot']
    description = request.json['description']
    
    conn = connect_db()
    if isinstance(conn, str):
        return jsonify({'error': conn}), 500  # If there was an error connecting to the DB
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO seva_slots (seva_name, time_slot, description) VALUES (%s, %s, %s)", (seva_name, time_slot, description))
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

if __name__ == '__main__':
    app.run(debug=True)


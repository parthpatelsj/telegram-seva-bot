from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

# Connect to database function
def connect_db():
    conn = sqlite3.connect('seva.db')
    return conn

# Route to get all seva slots
@app.route('/sevas', methods=['GET'])
def get_sevas():
    conn = connect_db()
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
    cursor = conn.cursor()
    cursor.execute("INSERT INTO seva_slots (seva_name, time_slot, description) VALUES (?, ?, ?)", (seva_name, time_slot, description))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Seva added successfully!'})

# Route to join a seva
@app.route('/join_seva', methods=['POST'])
def join_seva():
    name = request.json['name']
    seva_id = request.json['seva_id']
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT seva_name FROM seva_slots WHERE id = ?", (seva_id,))
    seva = cursor.fetchone()
    
    if seva:
        cursor.execute("INSERT INTO volunteers (name, seva_id) VALUES (?, ?)", (name, seva_id))
        conn.commit()
        conn.close()
        return jsonify({'message': f'{name} has joined the seva: {seva[0]}'})
    else:
        conn.close()
        return jsonify({'message': 'Invalid seva ID.'})

if __name__ == '__main__':
    app.run(debug=True)


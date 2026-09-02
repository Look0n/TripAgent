import os
import sys
import sqlite3
import requests
from flask import Flask, jsonify, request, send_from_directory

# Path configuration for database and frontend modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_FOLDER = os.path.join(BASE_DIR, 'frontend')

# Add backend directory to system path
sys.path.append(BASE_DIR)

from database.init_db import DB_PATH, init_db, get_db_connection

app = Flask(__name__, static_folder=FRONTEND_FOLDER)

# Initialize database on startup
init_db()

# ==========================================
# FRONTEND STATIC ROUTES
# ==========

@app.route('/')
def serve_index():
    """Serves the main index.html file."""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serves static files (styles.css, images, JS) or fallbacks to index.html."""
    file_path = os.path.join(FRONTEND_FOLDER, path)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_FOLDER, path)
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

# =========
# ATTRACTIONS API ENDPOINTS (CRUD)
# ==========================================

@app.route('/api/attractions', methods=['GET'])
def get_attractions():
    """Fetch all attractions or search by query."""
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        query = """
            SELECT * FROM attractions 
            WHERE name LIKE ? OR city LIKE ? OR description LIKE ? OR category LIKE ?
        """
        param = f"%{search_query}%"
        cursor.execute(query, (param, param, param, param))
    else:
        cursor.execute("SELECT * FROM attractions")

    rows = cursor.fetchall()
    conn.close()

    attractions = [dict(row) for row in rows]
    return jsonify(attractions)

@app.route('/api/attractions/<int:attraction_id>', methods=['GET'])
def get_attraction_details(attraction_id):
    """Fetch single attraction details with reviews."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attractions WHERE attraction_id = ?", (attraction_id,))
    attraction = cursor.fetchone()

    if not attraction:
        conn.close()
        return jsonify({"error": "Attraction not found"}), 404

    cursor.execute("SELECT * FROM reviews WHERE attraction_id = ?", (attraction_id,))
    reviews = cursor.fetchall()
    conn.close()

    result = dict(attraction)
    result['reviews'] = [dict(r) for r in reviews]
    return jsonify(result)

@app.route('/api/attractions', methods=['POST'])
def create_attraction():
    """Create a new attraction."""
    data = request.json or {}
    name = data.get('name')
    category = data.get('category')
    city = data.get('city')
    price = data.get('price', 0.0)
    image_url = data.get('image_url', '')
    description = data.get('description', '')

    if not name or not category or not city:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
        VALUES (?, ?, ?, ?, ?, ?, 0.0)
        """,
        (name, category, city, price, image_url, description)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Attraction created"}), 201

@app.route('/api/attractions/<int:attraction_id>', methods=['DELETE'])
def delete_attraction(attraction_id):
    """Delete an attraction by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attractions WHERE attraction_id = ?", (attraction_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Attraction deleted"})

# ==========================================
# AI INTEGRATION ENDPOINT
# ======================

@app.route('/api/attractions/recommend', methods=['POST'])
def get_ai_recommendations():
    """Generate dynamic AI recommendations based on optional user prompt using local Ollama."""
    data = request.json or {}
    custom_prompt = data.get('prompt', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, city, category FROM attractions LIMIT 5")
    rows = cursor.fetchall()
    conn.close()

    items = ", ".join([f"{r['name']} in {r['city']}" for r in rows]) if rows else "local attractions"

    if custom_prompt:
        full_prompt = f"Context: Available spots are {items}. User question: {custom_prompt}. Provide a clear and helpful response in 2-3 short sentences."
    else:
        full_prompt = f"Given these attractions: {items}. Provide a 1-day travel tip in 2 concise sentences."

    try:
        ollama_url = os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434/api/generate")
        res = requests.post(
            ollama_url,
            json={
                "model": "qwen2.5:0.5b",
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            },
            timeout=12
        )
        if res.status_code == 200:
            ai_response = res.json().get('response', '')
            if ai_response:
                return jsonify({"recommendation": ai_response})
    except Exception as e:
        print(f"Ollama connection error: {e}")

    # Fallback response if Ollama is not responding
    return jsonify({
        "recommendation": f"For '{custom_prompt or 'your trip'}', we recommend visiting the highlights in the morning to beat the crowds and booking skip-the-line tickets!"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import sqlite3
import os
import sys

# Подключение init_db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.init_db import DB_PATH, init_db, get_db_connection

app = Flask(__name__)
CORS(app)

# Авто-инициализация базы при старте
init_db()

# ==========================================
# SECTION 1: CORE CRUD OPERATIONS
# ==========================================

@app.route('/api/attractions', methods=['GET'])
def get_all_attractions():
    """READ ALL & SEARCH"""
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    query = "SELECT * FROM attractions WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE ? OR description LIKE ? OR city LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
    if category:
        query += " AND category = ?"
        params.append(category)

    attractions = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in attractions]), 200


@app.route('/api/attractions/<int:attraction_id>', methods=['GET'])
def get_attraction_by_id(attraction_id):
    """READ SINGLE ATTRACTION + REVIEWS"""
    conn = get_db_connection()
    attraction = conn.execute("SELECT * FROM attractions WHERE attraction_id = ?", (attraction_id,)).fetchone()
    
    if not attraction:
        conn.close()
        return jsonify({"error": "Attraction not found"}), 404

    reviews = conn.execute("SELECT * FROM reviews WHERE attraction_id = ?", (attraction_id,)).fetchall()
    conn.close()

    result = dict(attraction)
    result['reviews'] = [dict(r) for r in reviews]
    return jsonify(result), 200


@app.route('/api/attractions', methods=['POST'])
def create_new_attraction():
    """CREATE ATTRACTION"""
    data = request.json or {}
    name = data.get('name')
    category = data.get('category')
    city = data.get('city')
    description = data.get('description', '')
    price = data.get('price', 0.0)

    if not name or not category or not city:
        return jsonify({"error": "Fields 'name', 'category', and 'city' are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO attractions (name, category, city, description, price)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, category, city, description, price))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "Attraction created successfully", "attraction_id": new_id}), 201


@app.route('/api/attractions/<int:attraction_id>', methods=['PUT'])
def update_attraction(attraction_id):
    """UPDATE ATTRACTION"""
    data = request.json or {}
    conn = get_db_connection()
    
    conn.execute('''
        UPDATE attractions 
        SET name = COALESCE(?, name),
            category = COALESCE(?, category),
            city = COALESCE(?, city),
            description = COALESCE(?, description),
            price = COALESCE(?, price)
        WHERE attraction_id = ?
    ''', (data.get('name'), data.get('category'), data.get('city'), data.get('description'), data.get('price'), attraction_id))
    
    conn.commit()
    conn.close()
    return jsonify({"message": f"Attraction {attraction_id} updated successfully"}), 200


@app.route('/api/attractions/<int:attraction_id>', methods=['DELETE'])
def delete_attraction_by_id(attraction_id):
    """DELETE ATTRACTION"""
    conn = get_db_connection()
    conn.execute("DELETE FROM attractions WHERE attraction_id = ?", (attraction_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Attraction {attraction_id} deleted successfully"}), 200


# ==========================================
# SECTION 2: CROSS-FEATURE INTEGRATION API
# (Заготовки для межсервисного взаимодействия с другими студентами)
# ==========================================

@app.route('/api/cross-feature/attractions-by-city/<string:city>', methods=['GET'])
def get_attractions_for_other_services(city):
    """
    Эндпоинт для Студента 1 (Itinerary Planner).
    Позволяет запросить аттракционы по городу для включения в маршрут.
    """
    conn = get_db_connection()
    attractions = conn.execute("SELECT attraction_id, name, category, price FROM attractions WHERE city LIKE ?", (f'%{city}%',)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in attractions]), 200


def call_accommodation_service(city):
    """
    Планы на будущее: Вызов сервиса Студента 3 (Accommodations API)
    Прямой запрос запрещен ТЗ, только через HTTP.
    """
    try:
        response = requests.get(f'http://student-3-backend:5003/api/accommodations?city={city}', timeout=2)
        return response.json()
    except Exception as e:
        return {"note": "Accommodation service not reachable yet"}


# ==========================================
# SECTION 3: AI INTEGRATION & AGENTIC LOOP (STUBS)
# (Заготовки под вызовы Ollama/Gemini)
# ==========================================

@app.route('/api/attractions/recommend', methods=['POST'])
def recommend_attractions_ai():
    """
    Заглушка AI Recomendation System.
    На следующем шаге сюда подключается Ollama/Gemini.
    """
    conn = get_db_connection()
    top_items = conn.execute("SELECT * FROM attractions ORDER BY average_rating DESC LIMIT 3").fetchall()
    conn.close()
    
    return jsonify({
        "status": "AI_Disabled_Stub",
        "recommendations": [dict(r) for r in top_items],
        "note": "AI Integration will be connected here using Gemini/Ollama."
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'attractions.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create table with image_url column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attractions (
            attraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT,
            description TEXT,
            average_rating REAL DEFAULT 0.0
        )
    ''')

    # Insert initial mock data if table is empty
    cursor.execute("SELECT COUNT(*) FROM attractions")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            (
                'Eiffel Tower Summit Tour', 
                'Sightseeing', 
                'Paris', 
                45.0, 
                'https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?auto=format&fit=crop&w=600&q=80',
                'Experience breathtaking views of Paris from the iconic Eiffel Tower.', 
                4.8
            ),
            (
                'Louvre Museum Guided Walk', 
                'Culture', 
                'Paris', 
                65.0, 
                'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=600&q=80',
                'Explore world-famous masterpieces with an expert art historian.', 
                4.9
            ),
            (
                'Disneyland Adventure Pass', 
                'Entertainment', 
                'Paris', 
                95.0, 
                'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80',
                'Enjoy a magical day filled with rides and entertainment.', 
                4.7
            )
        ])
        conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
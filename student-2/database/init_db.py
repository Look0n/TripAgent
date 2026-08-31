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

    # Схема 1: Attractions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attractions (
            attraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            average_rating REAL DEFAULT 0.0
        )
    ''')

    # Схема 2: Reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            attraction_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating_score INTEGER NOT NULL,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attraction_id) REFERENCES attractions (attraction_id)
        )
    ''')

    # Наполнение базы 10+ начальными записями
    cursor.execute("SELECT COUNT(*) FROM attractions")
    if cursor.fetchone()[0] == 0:
        sample_attractions = [
            ("Sydney Opera House", "Landmark", "Sydney", "Iconic performing arts venue.", 150.0, 4.8),
            ("Sydney Harbour Bridge Climb", "Adventure", "Sydney", "Guided climb to the top of the bridge.", 300.0, 4.9),
            ("Taronga Zoo", "Wildlife", "Sydney", "City zoo with harbour views.", 50.0, 4.6),
            ("Bondi Beach Surf Lesson", "Sports", "Sydney", "2-hour beginner surfing lesson.", 80.0, 4.5),
            ("Royal Botanic Garden", "Nature", "Sydney", "Heritage-listed botanical garden.", 0.0, 4.7),
            ("Art Gallery of NSW", "Culture", "Sydney", "Museum with Australian and international art.", 0.0, 4.6),
            ("Manly Ferry Cruise", "Tour", "Sydney", "Scenic ferry ride across Sydney Harbour.", 10.0, 4.8),
            ("Blue Mountains Day Tour", "Nature", "Katoomba", "Day trip to Three Sisters and waterfalls.", 120.0, 4.7),
            ("SEA LIFE Sydney Aquarium", "Family", "Sydney", "Large aquarium with sharks and dugongs.", 45.0, 4.3),
            ("Darling Harbour Food Tour", "Food", "Sydney", "Guided tasting tour of local cuisine.", 95.0, 4.6)
        ]
        cursor.executemany('''
            INSERT INTO attractions (name, category, city, description, price, average_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_attractions)

        sample_reviews = [
            (1, 101, 5, "Unbelievable experience! Great views."),
            (1, 102, 4, "A bit crowded, but worth visiting."),
            (2, 103, 5, "Exhilarating climb! Highly recommend.")
        ]
        cursor.executemany('''
            INSERT INTO reviews (attraction_id, user_id, rating_score, comment)
            VALUES (?, ?, ?, ?)
        ''', sample_reviews)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
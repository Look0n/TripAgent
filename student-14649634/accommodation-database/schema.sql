CREATE TABLE IF NOT EXISTS accommodations (
    accommodation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accommodation_name TEXT NOT NULL,
    type TEXT NOT NULL,
    city TEXT NOT NULL,
    address TEXT,
    price_per_night REAL NOT NULL,
    guest_capacity INTEGER NOT NULL,
    rating REAL,
    description TEXT,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accommodation_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (accommodation_id)
        REFERENCES accommodations(accommodation_id)
);
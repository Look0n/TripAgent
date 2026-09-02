PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    price REAL NOT NULL,
    duration INTEGER NOT NULL,
    image TEXT,
    seat_availability INTEGER NOT NULL DEFAULT 0,

    UNIQUE (airline, origin, destination, departure_time)
);



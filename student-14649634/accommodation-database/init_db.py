import sqlite3
import os

DATABASE_NAME = os.path.join(os.path.dirname(__file__),"accommodation.db")

accommodations = [
    (
        "Crown Melbourne",
        "Hotel",
        "Melbourne",
        "8 Whiteman Street, Southbank VIC",
        320.0,
        4,
        4.5,
        "Luxury accommodation in Melbourne's Southbank precinct, close to restaurants, entertainment and the Melbourne CBD.",
        "static/images/crown_melbourne.png"
    ),

    (
        "Hilton Surfers Paradise",
        "Hotel",
        "Gold Coast",
        "6 Orchid Avenue, Surfers Paradise QLD",
        280.0,
        4,
        4.4,
        "Modern accommodation in the centre of Surfers Paradise, close to the beach, shopping, restaurants and nightlife.",
        "static/images/hilton_surfers.png"
    ),

    (
        "ibis Sydney Darling Harbour",
        "Hotel",
        "Sydney",
        "70 Murray Street, Pyrmont NSW",
        190.0,
        2,
        4.1,
        "Affordable accommodation in Darling Harbour with convenient access to the Sydney CBD, light rail, ICC Sydney and major waterfront attractions.",
        "static/images/ibis_harbour.png"
    ),

    (
        "Littlebourne Guest House",
        "Guesthouse",
        "Bathurst",
        "4031 O'Connell Road, Kelso NSW",
        550.0,
        14,
        4.7,
        "A historic boutique guest house in the Bathurst region offering luxury suites, landscaped gardens and whole-house group accommodation for larger stays.",
        "static/images/littlebourne.png"
    ),

    (
        "Oaks Sydney Goldsbrough Suites",
        "Apartment",
        "Sydney",
        "243 Pyrmont Street, Darling Harbour NSW",
        230.0,
        4,
        4.1,
        "Apartment-style accommodation near Darling Harbour, suitable for travellers wanting additional space and convenient access to central Sydney.",
        "static/images/oaks_goldsbrough.png"
    ),

    (
        "Oaks Port Douglas Resort",
        "Resort",
        "Port Douglas",
        "87-109 Port Douglas Road, Port Douglas QLD",
        210.0,
        6,
        4.2,
        "A tropical resort in Port Douglas offering a relaxed setting near beaches and attractions around Far North Queensland.",
        "static/images/oaks_portdouglas.png"
    ),

    (
        "Pacific Hotel Cairns",
        "Hotel",
        "Cairns",
        "43 The Esplanade, Cairns City QLD",
        190.0,
        3,
        4.3,
        "Waterfront accommodation in central Cairns, convenient for travellers visiting the Esplanade, marina and Great Barrier Reef departure points.",
        "static/images/pacific_cairns.png"
    ),

    (
        "Park Hyatt Sydney",
        "Hotel",
        "Sydney",
        "7 Hickson Road, The Rocks NSW",
        650.0,
        3,
        4.8,
        "Luxury waterfront accommodation in The Rocks with convenient access to Circular Quay, Sydney Harbour and major city attractions.",
        "static/images/park_hyatt_sydney.png"
    ),

    (
        "Pier One Sydney Harbour",
        "Hotel",
        "Sydney",
        "11 Hickson Road, Walsh Bay NSW",
        360.0,
        4,
        4.5,
        "Waterfront hotel at Walsh Bay offering harbour surroundings and convenient access to The Rocks and central Sydney.",
        "static/images/pier_one.png"
    ),

    (
        "Rydges Sydney Airport Hotel",
        "Hotel",
        "Sydney",
        "8 Arrival Court, Mascot NSW",
        220.0,
        2,
        4.2,
        "Airport accommodation suitable for international travellers, early departures, late arrivals and short Sydney stopovers.",
        "static/images/rydges_airport.png"
    ),

    (
        "Shangri-La The Marina Cairns",
        "Hotel",
        "Cairns",
        "Pierpoint Road, Cairns City QLD",
        270.0,
        4,
        4.5,
        "Premium waterfront accommodation beside the Cairns marina, suitable for travellers seeking convenient access to reef tours and the Esplanade.",
        "static/images/shangrila_cairns.png"
    ),

    (
        "Sheraton Grand Sydney Hyde Park",
        "Hotel",
        "Sydney",
        "161 Elizabeth Street, Sydney NSW",
        350.0,
        3,
        4.6,
        "Premium accommodation overlooking Hyde Park with walking access to shopping, restaurants and major Sydney CBD attractions.",
        "static/images/sheraton_sydney.png"
    ),

    (
        "Stamford Plaza Sydney Airport",
        "Hotel",
        "Sydney",
        "241 O'Riordan Street, Mascot NSW",
        195.0,
        4,
        4.2,
        "Comfortable accommodation near Sydney Airport suitable for business travellers, families and short stays.",
        "static/images/stamford.png"
    ),

    (
        "W Brisbane",
        "Hotel",
        "Brisbane",
        "81 North Quay, Brisbane City QLD",
        340.0,
        4,
        4.6,
        "Contemporary luxury accommodation overlooking the Brisbane River, close to the CBD, South Bank and major entertainment areas.",
        "static/images/w_brisbane.png"
    ),

    (
        "W Sydney",
        "Hotel",
        "Sydney",
        "31 Wheat Road, Sydney NSW",
        420.0,
        4,
        4.6,
        "Modern luxury accommodation at Darling Harbour with convenient access to restaurants, entertainment, shopping and the Sydney CBD.",
        "static/images/w_sydney.png"
    )
    
]

availability = [
    (1, "2026-09-01", 1),
    (1, "2026-09-02", 1),
    (1, "2026-09-03", 0),
    (1, "2026-09-04", 1),
    (1, "2026-09-05", 1),
    (1, "2026-09-06", 0),
    (1, "2026-09-07", 1),
    (1, "2026-09-08", 1),
    (1, "2026-09-09", 1),
    (1, "2026-09-10", 0)
]

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

cursor.execute("""
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
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accommodation_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (accommodation_id)
        REFERENCES accommodations(accommodation_id)
)
""")

cursor.execute("DELETE FROM availability")
cursor.execute("DELETE FROM accommodations")

cursor.execute("DELETE FROM sqlite_sequence WHERE name='availability'")
cursor.execute("DELETE FROM sqlite_sequence WHERE name='accommodations'")

cursor.executemany(
    """INSERT INTO accommodations 
        (accommodation_name, type, city, address, price_per_night, guest_capacity, rating, description, image_url) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    accommodations
)

cursor.executemany(
    """
    INSERT INTO availability (
        accommodation_id,
        date,
        is_available
    )
    VALUES (?, ?, ?)
    """,
    availability
)

conn.commit()
conn.close()

print("Database initialized with accommodations.")
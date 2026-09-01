DELETE FROM availability;
DELETE FROM accommodations;


INSERT INTO accommodations (
    accommodation_name,
    type,
    city,
    address,
    price_per_night,
    guest_capacity,
    rating,
    description,
    image_url
)
VALUES
(
    'Crown Melbourne',
    'Hotel',
    'Melbourne',
    '8 Whiteman Street, Southbank VIC',
    320,
    4,
    4.5,
    'Luxury accommodation in Melbourne Southbank precinct, close to restaurants, entertainment and the Melbourne CBD.',
    'static/images/crown_melbourne.jpg.webp'
),
(
    'Hilton Surfers Paradise',
    'Hotel',
    'Gold Coast',
    '6 Orchid Ave, Surfers Paradise QLD',
    280,
    4,
    4.4,
    'Modern accommodation in the centre of Surfers Paradise, close to the beach, shopping, restaurants and nightlife.',
    'static/images/hilton_surfers.jpg'
),
(
    'ibis Sydney Darling Harbour',
    'Hotel',
    'Sydney',
    '70 Murray Street, Pyrmont NSW',
    190,
    2,
    4.1,
    'Affordable accommodation in Darling Harbour with convenient access to the Sydney CBD, light rail, ICC Sydney and major waterfront attractions.',
    'static/images/ibis_darlingharbour.jpg.webp'
),
(
    'Littlebourne Guest House',
    'Guesthouse',
    'Bathurst',
    '4031 O''Connell Road, Kelso NSW',
    550,
    14,
    4.7,
    'A historic boutique guest house in the Bathurst region offering luxury suites, landscaped gardens and whole-house group accommodation for larger stays.',
    'static/images/littlebourne.jpg.webp'
),
(
    'Oaks Sydney Goldsbrough Suites',
    'Apartment',
    'Sydney',
    '243 Pyrmont Street, Sydney NSW',
    230,
    4,
    4.1,
    'AApartment-style accommodation near Darling Harbour, suitable for travellers wanting additional space and convenient access to central Sydney.',
    'static/images/oaks_goldsbrough.jpg'
),
(
    'Oaks Port Douglas Resort',
    'Resort',
    'Port Douglas',
    '87-109 Port Douglas Road',
    210,
    6,
    4.2,
    'A tropical resort in Port Douglas offering a relaxed setting near beaches and attractions around Far North Queensland.',
    'static/images/oaks_portdouglas.jpeg'
),
(
    'Pacific Hotel Cairns',
    'Hotel',
    'Cairns',
    '43 Esplanade, Cairns QLD',
    190,
    3,
    4.3,
    'Waterfront accommodation in central Cairns, convenient for travellers visiting the Esplanade, marina and Great Barrier Reef departure points.',
    'static/images/pacific_cairns.jpeg'
),
(
    'Park Hyatt Sydney',
    'Hotel',
    'Sydney',
    '7 Hickson Road, The Rocks NSW',
    650,
    3,
    4.8,
    'Luxury waterfront accommodation in The Rocks with convenient access to Circular Quay, Sydney Harbour and major city attractions.',
    'static/images/parkhyatt.jpeg'
),
(
    'Pier One Sydney Harbour',
    'Hotel',
    'Sydney',
    '11 Hickson Road, Walsh Bay NSW',
    360,
    4,
    4.5,
    'Waterfront hotel at Walsh Bay offering harbour surroundings and convenient access to The Rocks and central Sydney.',
    'static/images/pierone.jpeg'
),
(
    'Rydges Sydney Airport Hotel',
    'Hotel',
    'Sydney',
    '8 Arrival Court, Mascot NSW',
    220,
    2,
    4.2,
    'Airport accommodation suitable for international travellers, early departures, late arrivals and short Sydney stopovers.',
    'static/images/rydges_airport.jpeg'
),
(
    'Shangri-La The Marina Cairns',
    'Hotel',
    'Cairns',
    'Pierpoint Road, Cairns City QLD',
    270.0,
    4,
    4.5,
    'Premium waterfront accommodation beside the Cairns marina, suitable for travellers seeking convenient access to reef tours and the Esplanade.',
    'static/images/shangri-la.jpeg'
),
(
    'Stamford Plaza Sydney Airport',
    'Hotel',
    'Sydney',
    'Riordan Street, Mascot NSW',
    195.0,
    4,
    4.2,
    'Comfortable accommodation near Sydney Airport suitable for business travellers, families and short stays.',
    'static/images/stamford.jpg'
),
(
    'W Brisbane',
    'Hotel',
    'Brisbane',
    '81 North Quay, Brisbane QLD',
    340,
    4,
    4.6,
    'Contemporary luxury accommodation overlooking the Brisbane River, close to the CBD, South Bank and major entertainment areas.',
    'static/images/w_brisbane.jpg'
),
(
    'W Sydney',
    'Hotel',
    'Sydney',
    '31 Wheat Road, Sydney NSW',
    420,
    2,
    4.6,
    'Modern luxury accommodation at Darling Harbour with convenient access to restaurants, entertainment, shopping and the Sydney CBD.',
    'static/images/w_sydney.jpeg'
);

INSERT INTO availability (
    accommodation_id,
    date,
    is_available
)
VALUES
(1, '2026-09-05', 1),
(1, '2026-09-06', 0),
(1, '2026-09-07', 1),
(1, '2026-09-08', 1),
(1, '2026-09-09', 1),
(1, '2026-09-10', 0),
(2, '2026-09-05', 1),
(3, '2026-09-05', 1),
(4, '2026-09-07', 1),
(5, '2026-09-07', 1),
(6, '2026-09-08', 1),
(7, '2026-09-09', 1),
(8, '2026-09-09', 1),
(9, '2026-09-09', 1),
(10, '2026-09-09', 1);
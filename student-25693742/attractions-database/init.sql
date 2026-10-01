INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Eiffel Tower Summit Tour', 'Sightseeing', 'Paris', 45.0,
       'https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?auto=format&fit=crop&w=600&q=80',
       'Experience breathtaking views of Paris from the iconic Eiffel Tower.', 4.8
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Eiffel Tower Summit Tour');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Louvre Museum Guided Walk', 'Culture', 'Paris', 65.0,
       'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=600&q=80',
       'Explore world-famous masterpieces with an expert art historian.', 4.9
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Louvre Museum Guided Walk');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Disneyland Paris Adventure Pass', 'Entertainment', 'Paris', 95.0,
       'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80',
       'Enjoy a magical day filled with rides and entertainment.', 4.7
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Disneyland Paris Adventure Pass');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Sydney Opera House Backstage Tour', 'Culture', 'Sydney', 42.0,
       'https://images.unsplash.com/photo-1524293581917-878a6d017c71?auto=format&fit=crop&w=600&q=80',
       'Go behind the scenes of one of the world''s most iconic performance venues.', 4.8
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Sydney Opera House Backstage Tour');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Sydney Harbour Bridge Climb', 'Adventure', 'Sydney', 178.0,
       'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?auto=format&fit=crop&w=600&q=80',
       'Climb to the summit of the Harbour Bridge for panoramic views of the city.', 4.9
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Sydney Harbour Bridge Climb');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Bondi to Coogee Coastal Walk', 'Sightseeing', 'Sydney', 0.0,
       'https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?auto=format&fit=crop&w=600&q=80',
       'A scenic self-guided coastal walk past some of Sydney''s best beaches.', 4.6
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Bondi to Coogee Coastal Walk');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Tokyo Tsukiji Food Walking Tour', 'Food & Drink', 'Tokyo', 58.0,
       'https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?auto=format&fit=crop&w=600&q=80',
       'Sample fresh sushi and local delicacies around the historic Tsukiji outer market.', 4.7
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Tokyo Tsukiji Food Walking Tour');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Senso-ji Temple & Asakusa Tour', 'Culture', 'Tokyo', 30.0,
       'https://images.unsplash.com/photo-1545569341-9eb8b30979d9?auto=format&fit=crop&w=600&q=80',
       'Discover Tokyo''s oldest temple and the historic streets of Asakusa.', 4.8
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Senso-ji Temple & Asakusa Tour');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'teamLab Planets Digital Art Museum', 'Entertainment', 'Tokyo', 35.0,
       'https://images.unsplash.com/photo-1554797589-7241bb691973?auto=format&fit=crop&w=600&q=80',
       'An immersive, borderless digital art experience across water and light installations.', 4.9
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'teamLab Planets Digital Art Museum');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Statue of Liberty & Ellis Island Cruise', 'Sightseeing', 'New York', 30.0,
       'https://images.unsplash.com/photo-1485738422979-f5c462d49f74?auto=format&fit=crop&w=600&q=80',
       'Cruise past the Statue of Liberty and explore the Ellis Island immigration museum.', 4.7
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Statue of Liberty & Ellis Island Cruise');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Central Park Bike Tour', 'Adventure', 'New York', 40.0,
       'https://images.unsplash.com/photo-1534430480872-3498386e7856?auto=format&fit=crop&w=600&q=80',
       'Cycle through Central Park''s most iconic landmarks with a local guide.', 4.6
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Central Park Bike Tour');

INSERT INTO attractions (name, category, city, price, image_url, description, average_rating)
SELECT 'Metropolitan Museum of Art Highlights Tour', 'Culture', 'New York', 55.0,
       'https://images.unsplash.com/photo-1553913861-c0fddf2619ee?auto=format&fit=crop&w=600&q=80',
       'A guided highlights tour of one of the world''s largest and finest art museums.', 4.8
WHERE NOT EXISTS (SELECT 1 FROM attractions WHERE name = 'Metropolitan Museum of Art Highlights Tour');

INSERT INTO reviews (attraction_id, user_id, rating, comment)
SELECT attraction_id, 1, 5, 'Absolutely stunning views, worth every dollar.'
FROM attractions WHERE name = 'Eiffel Tower Summit Tour'
AND NOT EXISTS (SELECT 1 FROM reviews WHERE comment = 'Absolutely stunning views, worth every dollar.');

INSERT INTO reviews (attraction_id, user_id, rating, comment)
SELECT attraction_id, 2, 5, 'Our guide was incredibly knowledgeable, highly recommend.'
FROM attractions WHERE name = 'Louvre Museum Guided Walk'
AND NOT EXISTS (SELECT 1 FROM reviews WHERE comment = 'Our guide was incredibly knowledgeable, highly recommend.');

INSERT INTO reviews (attraction_id, user_id, rating, comment)
SELECT attraction_id, 3, 5, 'The climb was thrilling and the views over the harbour were unbeatable.'
FROM attractions WHERE name = 'Sydney Harbour Bridge Climb'
AND NOT EXISTS (SELECT 1 FROM reviews WHERE comment = 'The climb was thrilling and the views over the harbour were unbeatable.');

INSERT INTO reviews (attraction_id, user_id, rating, comment)
SELECT attraction_id, 4, 4, 'Great food and a fun way to see a local market.'
FROM attractions WHERE name = 'Tokyo Tsukiji Food Walking Tour'
AND NOT EXISTS (SELECT 1 FROM reviews WHERE comment = 'Great food and a fun way to see a local market.');

INSERT INTO reviews (attraction_id, user_id, rating, comment)
SELECT attraction_id, 5, 5, 'One of the most unique art experiences I have ever had.'
FROM attractions WHERE name = 'teamLab Planets Digital Art Museum'
AND NOT EXISTS (SELECT 1 FROM reviews WHERE comment = 'One of the most unique art experiences I have ever had.');

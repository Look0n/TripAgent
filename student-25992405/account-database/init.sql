PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO customer
(first_name, last_name, email, password, phone, country)
VALUES

(
    'Alice',
    'Brown',
    'alice@example.com',
    'pbkdf2:sha256:600000$GZnFd7MMiXLJtRFY$7f52360ac558265374a71fc3dfa4c7ebb5ac86304a5634868d02763f567a808d',
    '0400000001',
    'Australia'
),

(
    'Ben',
    'Smith',
    'ben@example.com',
    'pbkdf2:sha256:600000$6podccqtGAOTRHz5$fe996f517e962874c31accf4eca449c96c705c775a43a904cd0d0630deb096e0',
    '0400000002',
    'Australia'
),

(
    'Chloe',
    'Lee',
    'chloe@example.com',
    'pbkdf2:sha256:600000$goGWX2at0LdtsyNX$c121679509dced5c48e37e7cd522eaed28c4bcadc4066a6f79b5f6de65ba3966',
    '0400000003',
    'Singapore'
),

(
    'Daniel',
    'Wong',
    'daniel@example.com',
    'pbkdf2:sha256:600000$BcG4GHo5lIYkps4b$913074f6d2e861d2b7c9df23124d95449543d6eda04ed2dcdc010edc9e607067',
    '0400000004',
    'Malaysia'
),

(
    'Emma',
    'Taylor',
    'emma@example.com',
    'pbkdf2:sha256:600000$cMpfeTJ9cDGZcXfz$84a67b99916dc9b97f74053beb5fd69618b64eafc8c19313aecf6f6da32ea5fb',
    '0400000005',
    'United Kingdom'
),

(
    'Felix',
    'Chen',
    'felix@example.com',
    'pbkdf2:sha256:600000$FZRBTUWzp0caaWd3$6b8db8fe3089925adaac333b965fa7a26a2dbab69dc89a45327bc03ef31e807e',
    '0400000006',
    'China'
),

(
    'Grace',
    'Wilson',
    'grace@example.com',
    'pbkdf2:sha256:600000$1v7y4Aat0JWpJxuV$6e24e88f46f869b977238d6cad6a81babb132050e09db95a2512606f4669c2ca',
    '0400000007',
    'New Zealand'
),

(
    'Henry',
    'Martin',
    'henry@example.com',
    'pbkdf2:sha256:600000$253PfzJMpjBbDnOo$972e0622109637033223fa00b7d217d13789c60bc9c145c0caf0c61e4efed862',
    '0400000008',
    'Canada'
),

(
    'Isla',
    'Moore',
    'isla@example.com',
    'pbkdf2:sha256:600000$j2cJ4I3OPwS18LnJ$085a4fe27e91aac8899aec45bf5811f9d0e5bf3eda57f8677c33391721e4cad6',
    '0400000009',
    'Australia'
),

(
    'Jack',
    'Davis',
    'jack@example.com',
    'pbkdf2:sha256:600000$vn0Thj1jFcYwfnv2$06d1d29f2bfb6cab7f8b504256498d22ea7d17c37ea1bd8f82fbf9fed4f5cf80',
    '0400000010',
    'United States'
);


INSERT OR IGNORE INTO preference
(
    customer_id,
    budget_level,
    travel_style,
    accommodation_type,
    transport_preference,
    food_preference,
    pace_preference
)
VALUES

(
    1,
    'budget',
    'adventure',
    'hostel',
    'public transport',
    'local cuisine',
    'fast-paced'
),

(
    2,
    'moderate',
    'relaxation',
    'hotel',
    'train',
    'seafood',
    'relaxed'
),

(
    3,
    'luxury',
    'culture',
    'resort',
    'private car',
    'fine dining',
    'balanced'
),

(
    4,
    'moderate',
    'nature',
    'hotel',
    'rental car',
    'local cuisine',
    'balanced'
),

(
    5,
    'luxury',
    'relaxation',
    'resort',
    'private transfer',
    'vegetarian',
    'relaxed'
),

(
    6,
    'budget',
    'culture',
    'hostel',
    'public transport',
    'street food',
    'fast-paced'
),

(
    7,
    'moderate',
    'adventure',
    'apartment',
    'rental car',
    'local cuisine',
    'balanced'
),

(
    8,
    'luxury',
    'nature',
    'lodge',
    'private car',
    'fine dining',
    'relaxed'
),

(
    9,
    'budget',
    'backpacking',
    'hostel',
    'bus',
    'street food',
    'fast-paced'
),

(
    10,
    'moderate',
    'family',
    'hotel',
    'rental car',
    'family-friendly',
    'balanced'
);
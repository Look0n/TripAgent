PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO flights
(airline, origin, destination, departure_time, arrival_time, price, duration, image, seat_availability)
VALUES

('Qantas', 'SYD', 'MEL', '2026-09-15T06:00:00', '2026-09-15T07:35:00', 249.00, 95, 'qantas-a330.jpg', 38),

('Jetstar', 'SYD', 'MEL', '2026-09-15T11:20:00', '2026-09-15T13:00:00', 109.00, 100, 'jetstar-a320.jpg', 64),

('Virgin Australia', 'SYD', 'MEL', '2026-09-15T18:45:00', '2026-09-15T20:20:00', 178.00, 95, 'virgin-737.jpg', 3),

('Qantas', 'SYD', 'BNE', '2026-09-16T07:10:00', '2026-09-16T08:40:00', 215.00, 90, 'qantas-737.jpg', 51),

('Jetstar', 'SYD', 'BNE', '2026-09-16T14:30:00', '2026-09-16T16:05:00', 98.00, 95, 'jetstar-787.jpg', 72),

('Qantas', 'SYD', 'PER', '2026-09-17T09:00:00', '2026-09-17T14:15:00', 445.00, 315, 'qantas-a330.jpg', 27),

('Virgin Australia', 'SYD', 'PER', '2026-09-17T21:30:00', '2026-09-18T03:05:00', 312.00, 335, 'virgin-737.jpg', 44),

('Singapore Airlines', 'SYD', 'SIN', '2026-09-18T10:15:00', '2026-09-18T16:30:00', 1120.00, 375, 'singapore-a350.jpg', 19),

('Scoot', 'SYD', 'SIN', '2026-09-18T23:45:00', '2026-09-19T06:20:00', 528.00, 395, 'scoot-787.jpg', 88),

('Air New Zealand', 'SYD', 'AKL', '2026-09-19T08:30:00', '2026-09-19T13:35:00', 389.00, 185, 'airnz-787.jpg', 6),

('Qantas', 'MEL', 'SYD', '2026-09-20T16:00:00', '2026-09-20T17:30:00', 232.00, 90, 'qantas-737.jpg', 41),

('Japan Airlines', 'SYD', 'HND', '2026-09-21T20:50:00', '2026-09-22T05:25:00', 1385.00, 575, 'jal-787.jpg', 15);
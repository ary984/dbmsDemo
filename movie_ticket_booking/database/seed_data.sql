-- =====================================================================
-- SEED DATA: MOVIES, CINEMAS, SCREENS, SEATS, SHOWS & DEFAULT USERS
-- =====================================================================

USE `movie_booking_db`;

-- 1. Insert Default Users (Admin & Customer)
-- Admin: admin@cinema.com / Admin@123
-- Customer: john@example.com / User@123
INSERT INTO `users` (`user_id`, `full_name`, `email`, `password_hash`, `phone`, `role`) VALUES
(1, 'System Administrator', 'admin@cinema.com', 'scrypt:32768:8:1$5qgqh4EGP3s83uL1$e1f85edade5bcb11aaf0ca1c3027f055e471cdf823a93bc88ebcf622f4ae31726570a9b244b0ee4049353dc385aabec336ccf206ec48d3e6b61141a4afde876d', '9876543210', 'admin'),
(2, 'John Doe', 'john@example.com', 'scrypt:32768:8:1$ORw8kjn0JbBl7zUj$7d8d92b0939a680089a9b764f96f1bfd0a927605abd4455e9773b8c7b9a656a3ea7cae2f3562248dc718a573a2319ba8f610ac799eccfe6723816d7fcc5641ce', '9123456780', 'customer')
ON DUPLICATE KEY UPDATE `full_name` = VALUES(`full_name`);

-- 2. Insert Cinemas
INSERT INTO `cinemas` (`cinema_id`, `name`, `city`, `address`) VALUES
(1, 'PVR Heritage Square', 'Mumbai', 'Plot 44, Linking Road, Bandra West'),
(2, 'INOX Megaplex & IMAX', 'Mumbai', 'Level 4, Phoenix Marketcity, Kurla')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- 3. Insert Screens
INSERT INTO `screens` (`screen_id`, `cinema_id`, `screen_name`, `total_seats`, `sound_system`) VALUES
(1, 1, 'Audi 1 (Dolby Atmos)', 40, 'Dolby Atmos 7.1 Surround'),
(2, 1, 'Audi 2 (Standard)', 30, 'Dolby Digital 5.1'),
(3, 2, 'IMAX Screen 1', 40, 'IMAX 12-Channel Laser Sound')
ON DUPLICATE KEY UPDATE `screen_name` = VALUES(`screen_name`);

-- 4. Insert Movies
INSERT INTO `movies` (`movie_id`, `title`, `description`, `genre`, `duration_mins`, `language`, `release_date`, `rating`, `poster_url`, `trailer_url`) VALUES
(1, 'Interstellar', 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity survival.', 'Sci-Fi / Adventure', 169, 'English', '2014-11-07', 8.7, 'https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&q=80', 'https://www.youtube.com/watch?v=zSWdZVtXT7E'),
(2, 'The Dark Knight', 'When the menace known as the Joker wreaks havoc on Gotham, Batman must accept one of the greatest psychological tests.', 'Action / Crime', 152, 'English', '2008-07-18', 9.0, 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80', 'https://www.youtube.com/watch?v=EXeTwQWrcwY'),
(3, 'Inception', 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.', 'Sci-Fi / Action', 148, 'English', '2010-07-16', 8.8, 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80', 'https://www.youtube.com/watch?v=YoHD9XEInc0'),
(4, 'Dune: Part Two', 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.', 'Sci-Fi / Drama', 166, 'English', '2024-03-01', 8.6, 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80', 'https://www.youtube.com/watch?v=Way9Dexny3w'),
(5, 'Gladiator II', 'Years after witnessing the death of Maximus, Lucius must enter the Colosseum after his home is conquered.', 'Action / Drama', 148, 'English', '2024-11-22', 8.2, 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80', 'https://www.youtube.com/watch?v=4rgYUipGJNo')
ON DUPLICATE KEY UPDATE `title` = VALUES(`title`);

-- 5. Helper Script to populate 40 seats for Screen 1 and Screen 3, and 30 seats for Screen 2
-- Row A & B: SILVER ($150)
-- Row C & D: GOLD ($250)
-- Row E: RECLINER ($400)
DELETE FROM `seats` WHERE `screen_id` IN (1, 2, 3);

-- Screen 1 Seats (40 seats: 5 rows x 8 cols)
INSERT INTO `seats` (`screen_id`, `seat_number`, `seat_row`, `seat_col`, `seat_tier`, `base_price`) VALUES
(1, 'A1', 'A', 1, 'SILVER', 150.00), (1, 'A2', 'A', 2, 'SILVER', 150.00), (1, 'A3', 'A', 3, 'SILVER', 150.00), (1, 'A4', 'A', 4, 'SILVER', 150.00), (1, 'A5', 'A', 5, 'SILVER', 150.00), (1, 'A6', 'A', 6, 'SILVER', 150.00), (1, 'A7', 'A', 7, 'SILVER', 150.00), (1, 'A8', 'A', 8, 'SILVER', 150.00),
(1, 'B1', 'B', 1, 'SILVER', 150.00), (1, 'B2', 'B', 2, 'SILVER', 150.00), (1, 'B3', 'B', 3, 'SILVER', 150.00), (1, 'B4', 'B', 4, 'SILVER', 150.00), (1, 'B5', 'B', 5, 'SILVER', 150.00), (1, 'B6', 'B', 6, 'SILVER', 150.00), (1, 'B7', 'B', 7, 'SILVER', 150.00), (1, 'B8', 'B', 8, 'SILVER', 150.00),
(1, 'C1', 'C', 1, 'GOLD', 250.00),   (1, 'C2', 'C', 2, 'GOLD', 250.00),   (1, 'C3', 'C', 3, 'GOLD', 250.00),   (1, 'C4', 'C', 4, 'GOLD', 250.00),   (1, 'C5', 'C', 5, 'GOLD', 250.00),   (1, 'C6', 'C', 6, 'GOLD', 250.00),   (1, 'C7', 'C', 7, 'GOLD', 250.00),   (1, 'C8', 'C', 8, 'GOLD', 250.00),
(1, 'D1', 'D', 1, 'GOLD', 250.00),   (1, 'D2', 'D', 2, 'GOLD', 250.00),   (1, 'D3', 'D', 3, 'GOLD', 250.00),   (1, 'D4', 'D', 4, 'GOLD', 250.00),   (1, 'D5', 'D', 5, 'GOLD', 250.00),   (1, 'D6', 'D', 6, 'GOLD', 250.00),   (1, 'D7', 'D', 7, 'GOLD', 250.00),   (1, 'D8', 'D', 8, 'GOLD', 250.00),
(1, 'E1', 'E', 1, 'RECLINER', 400.00), (1, 'E2', 'E', 2, 'RECLINER', 400.00), (1, 'E3', 'E', 3, 'RECLINER', 400.00), (1, 'E4', 'E', 4, 'RECLINER', 400.00), (1, 'E5', 'E', 5, 'RECLINER', 400.00), (1, 'E6', 'E', 6, 'RECLINER', 400.00), (1, 'E7', 'E', 7, 'RECLINER', 400.00), (1, 'E8', 'E', 8, 'RECLINER', 400.00);

-- Screen 3 Seats (IMAX - 40 seats)
INSERT INTO `seats` (`screen_id`, `seat_number`, `seat_row`, `seat_col`, `seat_tier`, `base_price`) VALUES
(3, 'A1', 'A', 1, 'SILVER', 200.00), (3, 'A2', 'A', 2, 'SILVER', 200.00), (3, 'A3', 'A', 3, 'SILVER', 200.00), (3, 'A4', 'A', 4, 'SILVER', 200.00), (3, 'A5', 'A', 5, 'SILVER', 200.00), (3, 'A6', 'A', 6, 'SILVER', 200.00), (3, 'A7', 'A', 7, 'SILVER', 200.00), (3, 'A8', 'A', 8, 'SILVER', 200.00),
(3, 'B1', 'B', 1, 'SILVER', 200.00), (3, 'B2', 'B', 2, 'SILVER', 200.00), (3, 'B3', 'B', 3, 'SILVER', 200.00), (3, 'B4', 'B', 4, 'SILVER', 200.00), (3, 'B5', 'B', 5, 'SILVER', 200.00), (3, 'B6', 'B', 6, 'SILVER', 200.00), (3, 'B7', 'B', 7, 'SILVER', 200.00), (3, 'B8', 'B', 8, 'SILVER', 200.00),
(3, 'C1', 'C', 1, 'GOLD', 320.00),   (3, 'C2', 'C', 2, 'GOLD', 320.00),   (3, 'C3', 'C', 3, 'GOLD', 320.00),   (3, 'C4', 'C', 4, 'GOLD', 320.00),   (3, 'C5', 'C', 5, 'GOLD', 320.00),   (3, 'C6', 'C', 6, 'GOLD', 320.00),   (3, 'C7', 'C', 7, 'GOLD', 320.00),   (3, 'C8', 'C', 8, 'GOLD', 320.00),
(3, 'D1', 'D', 1, 'GOLD', 320.00),   (3, 'D2', 'D', 2, 'GOLD', 320.00),   (3, 'D3', 'D', 3, 'GOLD', 320.00),   (3, 'D4', 'D', 4, 'GOLD', 320.00),   (3, 'D5', 'D', 5, 'GOLD', 320.00),   (3, 'D6', 'D', 6, 'GOLD', 320.00),   (3, 'D7', 'D', 7, 'GOLD', 320.00),   (3, 'D8', 'D', 8, 'GOLD', 320.00),
(3, 'E1', 'E', 1, 'RECLINER', 550.00), (3, 'E2', 'E', 2, 'RECLINER', 550.00), (3, 'E3', 'E', 3, 'RECLINER', 550.00), (3, 'E4', 'E', 4, 'RECLINER', 550.00), (3, 'E5', 'E', 5, 'RECLINER', 550.00), (3, 'E6', 'E', 6, 'RECLINER', 550.00), (3, 'E7', 'E', 7, 'RECLINER', 550.00), (3, 'E8', 'E', 8, 'RECLINER', 550.00);

-- 6. Insert Shows (Dynamic dates relative to NOW so shows are always active for demo)
DELETE FROM `shows` WHERE `show_id` IN (1, 2, 3, 4, 5);

INSERT INTO `shows` (`show_id`, `movie_id`, `screen_id`, `start_time`, `end_time`, `price_multiplier`, `status`) VALUES
(1, 1, 1, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 2 HOUR), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 5 HOUR), 1.00, 'SCHEDULED'),
(2, 2, 1, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 6 HOUR), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 9 HOUR), 1.15, 'SCHEDULED'),
(3, 3, 3, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 HOUR), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 4 HOUR), 1.20, 'SCHEDULED'),
(4, 4, 3, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 5 HOUR), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 8 HOUR), 1.25, 'SCHEDULED'),
(5, 5, 1, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY) + INTERVAL 18 HOUR, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY) + INTERVAL 21 HOUR, 1.10, 'SCHEDULED');

-- =====================================================================
-- MOVIE TICKET BOOKING SYSTEM - DATABASE SCHEMA (3NF NORMALIZED)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `movie_booking_db`
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `movie_booking_db`;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `phone` VARCHAR(20),
    `role` ENUM('customer', 'admin') DEFAULT 'customer',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB;

-- 2. MOVIES TABLE
CREATE TABLE IF NOT EXISTS `movies` (
    `movie_id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT,
    `genre` VARCHAR(60) NOT NULL,
    `duration_mins` INT NOT NULL,
    `language` VARCHAR(50) NOT NULL,
    `release_date` DATE,
    `rating` DECIMAL(3, 1) DEFAULT 8.0,
    `poster_url` VARCHAR(500),
    `trailer_url` VARCHAR(500),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_movies_title` (`title`)
) ENGINE=InnoDB;

-- 3. CINEMAS TABLE
CREATE TABLE IF NOT EXISTS `cinemas` (
    `cinema_id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `city` VARCHAR(100) NOT NULL,
    `address` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_cinemas_city` (`city`)
) ENGINE=InnoDB;

-- 4. SCREENS TABLE
CREATE TABLE IF NOT EXISTS `screens` (
    `screen_id` INT AUTO_INCREMENT PRIMARY KEY,
    `cinema_id` INT NOT NULL,
    `screen_name` VARCHAR(60) NOT NULL,
    `total_seats` INT NOT NULL DEFAULT 40,
    `sound_system` VARCHAR(60) DEFAULT 'Dolby Atmos 7.1',
    FOREIGN KEY (`cinema_id`) REFERENCES `cinemas`(`cinema_id`) ON DELETE CASCADE,
    INDEX `idx_screens_cinema` (`cinema_id`)
) ENGINE=InnoDB;

-- 5. SEATS TABLE
CREATE TABLE IF NOT EXISTS `seats` (
    `seat_id` INT AUTO_INCREMENT PRIMARY KEY,
    `screen_id` INT NOT NULL,
    `seat_number` VARCHAR(10) NOT NULL,
    `seat_row` VARCHAR(5) NOT NULL,
    `seat_col` INT NOT NULL,
    `seat_tier` ENUM('SILVER', 'GOLD', 'RECLINER') NOT NULL DEFAULT 'SILVER',
    `base_price` DECIMAL(8, 2) NOT NULL DEFAULT 150.00,
    FOREIGN KEY (`screen_id`) REFERENCES `screens`(`screen_id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_screen_seat` (`screen_id`, `seat_number`),
    INDEX `idx_seats_screen` (`screen_id`)
) ENGINE=InnoDB;

-- 6. SHOWS TABLE
CREATE TABLE IF NOT EXISTS `shows` (
    `show_id` INT AUTO_INCREMENT PRIMARY KEY,
    `movie_id` INT NOT NULL,
    `screen_id` INT NOT NULL,
    `start_time` DATETIME NOT NULL,
    `end_time` DATETIME NOT NULL,
    `price_multiplier` DECIMAL(4, 2) NOT NULL DEFAULT 1.00,
    `status` ENUM('SCHEDULED', 'RUNNING', 'COMPLETED', 'CANCELLED') DEFAULT 'SCHEDULED',
    FOREIGN KEY (`movie_id`) REFERENCES `movies`(`movie_id`) ON DELETE CASCADE,
    FOREIGN KEY (`screen_id`) REFERENCES `screens`(`screen_id`) ON DELETE CASCADE,
    INDEX `idx_shows_start_time` (`start_time`),
    INDEX `idx_shows_movie` (`movie_id`),
    INDEX `idx_shows_screen` (`screen_id`)
) ENGINE=InnoDB;

-- 7. BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS `bookings` (
    `booking_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_reference` VARCHAR(16) NOT NULL UNIQUE,
    `user_id` INT NOT NULL,
    `show_id` INT NOT NULL,
    `booking_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `total_amount` DECIMAL(10, 2) NOT NULL,
    `status` ENUM('CONFIRMED', 'CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`show_id`) REFERENCES `shows`(`show_id`) ON DELETE CASCADE,
    INDEX `idx_bookings_user` (`user_id`),
    INDEX `idx_bookings_show` (`show_id`),
    INDEX `idx_bookings_ref` (`booking_reference`)
) ENGINE=InnoDB;

-- 8. BOOKING_SEATS TABLE (M:N Relationship between Bookings and Seats)
CREATE TABLE IF NOT EXISTS `booking_seats` (
    `booking_seat_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL,
    `seat_id` INT NOT NULL,
    `price` DECIMAL(8, 2) NOT NULL,
    FOREIGN KEY (`booking_id`) REFERENCES `bookings`(`booking_id`) ON DELETE CASCADE,
    FOREIGN KEY (`seat_id`) REFERENCES `seats`(`seat_id`) ON DELETE CASCADE,
    UNIQUE KEY `uk_booking_seat` (`booking_id`, `seat_id`),
    INDEX `idx_bs_seat` (`seat_id`)
) ENGINE=InnoDB;

-- 9. PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS `payments` (
    `payment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL,
    `transaction_id` VARCHAR(60) NOT NULL UNIQUE,
    `amount` DECIMAL(10, 2) NOT NULL,
    `payment_method` ENUM('CARD', 'UPI', 'NETBANKING', 'WALLET') NOT NULL DEFAULT 'UPI',
    `status` ENUM('SUCCESS', 'FAILED', 'REFUNDED') NOT NULL DEFAULT 'SUCCESS',
    `payment_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`booking_id`) REFERENCES `bookings`(`booking_id`) ON DELETE CASCADE,
    INDEX `idx_payments_booking` (`booking_id`),
    INDEX `idx_payments_tx` (`transaction_id`)
) ENGINE=InnoDB;

-- 10. AUDIT_LOGS TABLE (Tracks critical DBMS actions & triggers)
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `log_id` INT AUTO_INCREMENT PRIMARY KEY,
    `action_type` VARCHAR(50) NOT NULL,
    `table_name` VARCHAR(50) NOT NULL,
    `record_id` INT NOT NULL,
    `details` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

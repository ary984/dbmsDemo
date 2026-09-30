-- =====================================================================
-- ADVANCED DBMS FEATURES: VIEWS, STORED PROCEDURES, TRIGGERS
-- =====================================================================

USE `movie_booking_db`;

-- Drop existing views/procedures/triggers if any
DROP VIEW IF EXISTS `vw_active_shows`;
DROP VIEW IF EXISTS `vw_booking_details`;
DROP VIEW IF EXISTS `vw_cinema_revenue`;
DROP PROCEDURE IF EXISTS `sp_get_show_seats`;
DROP PROCEDURE IF EXISTS `sp_cancel_booking`;
DROP TRIGGER IF EXISTS `trg_after_booking_update`;
DROP TRIGGER IF EXISTS `trg_after_booking_insert`;

-- ---------------------------------------------------------------------
-- 1. VIEWS (Joins, aggregations, data abstraction)
-- ---------------------------------------------------------------------

-- View: Active shows with cinema, screen, and real-time available seats
CREATE VIEW `vw_active_shows` AS
SELECT 
    s.show_id,
    s.start_time,
    s.end_time,
    s.price_multiplier,
    s.status AS show_status,
    m.movie_id,
    m.title AS movie_title,
    m.genre,
    m.duration_mins,
    m.language,
    m.rating,
    m.poster_url,
    c.cinema_id,
    c.name AS cinema_name,
    c.city,
    sc.screen_id,
    sc.screen_name,
    sc.total_seats,
    COUNT(DISTINCT bs.seat_id) AS booked_seats,
    (sc.total_seats - COUNT(DISTINCT bs.seat_id)) AS available_seats
FROM `shows` s
JOIN `movies` m ON s.movie_id = m.movie_id
JOIN `screens` sc ON s.screen_id = sc.screen_id
JOIN `cinemas` c ON sc.cinema_id = c.cinema_id
LEFT JOIN `bookings` b ON s.show_id = b.show_id AND b.status = 'CONFIRMED'
LEFT JOIN `booking_seats` bs ON b.booking_id = bs.booking_id
GROUP BY s.show_id, m.movie_id, c.cinema_id, sc.screen_id;

-- View: Complete booking receipts with user, movie, cinema, payment details
CREATE VIEW `vw_booking_details` AS
SELECT 
    b.booking_id,
    b.booking_reference,
    b.booking_time,
    b.total_amount,
    b.status AS booking_status,
    u.user_id,
    u.full_name AS customer_name,
    u.email AS customer_email,
    u.phone AS customer_phone,
    m.title AS movie_title,
    m.poster_url,
    m.duration_mins,
    m.language,
    c.name AS cinema_name,
    c.city AS cinema_city,
    sc.screen_name,
    s.show_id,
    s.start_time AS show_time,
    p.transaction_id,
    p.payment_method,
    p.status AS payment_status,
    p.payment_time,
    GROUP_CONCAT(st.seat_number ORDER BY st.seat_number ASC SEPARATOR ', ') AS booked_seat_numbers,
    COUNT(bs.seat_id) AS total_tickets
FROM `bookings` b
JOIN `users` u ON b.user_id = u.user_id
JOIN `shows` s ON b.show_id = s.show_id
JOIN `movies` m ON s.movie_id = m.movie_id
JOIN `screens` sc ON s.screen_id = sc.screen_id
JOIN `cinemas` c ON sc.cinema_id = c.cinema_id
LEFT JOIN `booking_seats` bs ON b.booking_id = bs.booking_id
LEFT JOIN `seats` st ON bs.seat_id = st.seat_id
LEFT JOIN `payments` p ON b.booking_id = p.booking_id
GROUP BY b.booking_id, p.payment_id;

-- View: Admin Analytics - Cinema Revenue & Performance
CREATE VIEW `vw_cinema_revenue` AS
SELECT 
    c.cinema_id,
    c.name AS cinema_name,
    c.city,
    m.movie_id,
    m.title AS movie_title,
    COUNT(DISTINCT b.booking_id) AS total_bookings,
    COUNT(bs.seat_id) AS total_tickets_sold,
    COALESCE(SUM(CASE WHEN b.status = 'CONFIRMED' THEN b.total_amount ELSE 0 END), 0.00) AS gross_revenue
FROM `cinemas` c
JOIN `screens` sc ON c.cinema_id = sc.cinema_id
JOIN `shows` s ON sc.screen_id = s.screen_id
JOIN `movies` m ON s.movie_id = m.movie_id
LEFT JOIN `bookings` b ON s.show_id = b.show_id
LEFT JOIN `booking_seats` bs ON b.booking_id = bs.booking_id AND b.status = 'CONFIRMED'
GROUP BY c.cinema_id, m.movie_id;

-- ---------------------------------------------------------------------
-- 2. STORED PROCEDURES (Encapsulated Business Logic & Transactions)
-- ---------------------------------------------------------------------

DELIMITER $$

-- Procedure to retrieve seat layout with real-time reservation status
CREATE PROCEDURE `sp_get_show_seats`(IN p_show_id INT)
BEGIN
    SELECT 
        st.seat_id,
        st.seat_number,
        st.seat_row,
        st.seat_col,
        st.seat_tier,
        ROUND(st.base_price * s.price_multiplier, 2) AS calculated_price,
        CASE 
            WHEN bs.booking_seat_id IS NOT NULL AND b.status = 'CONFIRMED' THEN 1 
            ELSE 0 
        END AS is_booked
    FROM `shows` s
    JOIN `screens` sc ON s.screen_id = sc.screen_id
    JOIN `seats` st ON sc.screen_id = st.screen_id
    LEFT JOIN `bookings` b ON b.show_id = s.show_id AND b.status = 'CONFIRMED'
    LEFT JOIN `booking_seats` bs ON bs.booking_id = b.booking_id AND bs.seat_id = st.seat_id
    WHERE s.show_id = p_show_id
    ORDER BY st.seat_row ASC, st.seat_col ASC;
END$$

-- Procedure to cancel booking safely with user authorization check
CREATE PROCEDURE `sp_cancel_booking`(
    IN p_booking_id INT,
    IN p_user_id INT,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_current_status VARCHAR(20);
    DECLARE v_owner_id INT;

    SELECT `status`, `user_id` INTO v_current_status, v_owner_id
    FROM `bookings`
    WHERE `booking_id` = p_booking_id;

    IF v_owner_id IS NULL THEN
        SET p_success = FALSE;
        SET p_message = 'Booking not found.';
    ELSEIF v_owner_id != p_user_id THEN
        SET p_success = FALSE;
        SET p_message = 'Unauthorized: You can only cancel your own bookings.';
    ELSEIF v_current_status = 'CANCELLED' THEN
        SET p_success = FALSE;
        SET p_message = 'Booking is already cancelled.';
    ELSE
        -- Update booking status (Trigger will handle payment refund & audit log)
        UPDATE `bookings`
        SET `status` = 'CANCELLED'
        WHERE `booking_id` = p_booking_id;

        SET p_success = TRUE;
        SET p_message = 'Booking cancelled successfully. Refund initiated.';
    END IF;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 3. TRIGGERS (Automated DBMS integrity & audit logging)
-- ---------------------------------------------------------------------

DELIMITER $$

-- Trigger: When a booking is inserted, log to audit_logs
CREATE TRIGGER `trg_after_booking_insert`
AFTER INSERT ON `bookings`
FOR EACH ROW
BEGIN
    INSERT INTO `audit_logs` (`action_type`, `table_name`, `record_id`, `details`)
    VALUES (
        'BOOKING_CREATED',
        'bookings',
        NEW.booking_id,
        CONCAT('Ref: ', NEW.booking_reference, ' | User: ', NEW.user_id, ' | Total: $', NEW.total_amount)
    );
END$$

-- Trigger: When booking is CANCELLED, auto-refund payment and log to audit_logs
CREATE TRIGGER `trg_after_booking_update`
AFTER UPDATE ON `bookings`
FOR EACH ROW
BEGIN
    IF OLD.status != 'CANCELLED' AND NEW.status = 'CANCELLED' THEN
        -- Auto update payment status to REFUNDED
        UPDATE `payments`
        SET `status` = 'REFUNDED'
        WHERE `booking_id` = NEW.booking_id;

        -- Record into audit log
        INSERT INTO `audit_logs` (`action_type`, `table_name`, `record_id`, `details`)
        VALUES (
            'BOOKING_CANCELLED',
            'bookings',
            NEW.booking_id,
            CONCAT('Booking Ref: ', NEW.booking_reference, ' was cancelled. Payment refunded.')
        );
    END IF;
END$$

DELIMITER ;

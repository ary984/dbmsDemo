import threading
import time
from flask import Blueprint, render_template, request, jsonify
from app.db import query_all, query_one, get_db_connection

dbms_bp = Blueprint("dbms", __name__)

@dbms_bp.route("/")
def index():
    # Fetch live DBMS metadata
    views = query_all("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
    procedures = query_all("SHOW PROCEDURE STATUS WHERE Db = 'movie_booking_db'")
    triggers = query_all("SHOW TRIGGERS FROM movie_booking_db")
    tables_counts = query_all("""
        SELECT 'users' as tbl, count(*) as count FROM users UNION ALL
        SELECT 'movies', count(*) FROM movies UNION ALL
        SELECT 'cinemas', count(*) FROM cinemas UNION ALL
        SELECT 'screens', count(*) FROM screens UNION ALL
        SELECT 'seats', count(*) FROM seats UNION ALL
        SELECT 'shows', count(*) FROM shows UNION ALL
        SELECT 'bookings', count(*) FROM bookings UNION ALL
        SELECT 'booking_seats', count(*) FROM booking_seats UNION ALL
        SELECT 'payments', count(*) FROM payments UNION ALL
        SELECT 'audit_logs', count(*) FROM audit_logs
    """)

    revenue_view_data = query_all("SELECT * FROM vw_cinema_revenue")
    active_shows_view = query_all("SELECT * FROM vw_active_shows LIMIT 5")

    return render_template("dbms_demo.html", 
                           views=views, 
                           procedures=procedures, 
                           triggers=triggers, 
                           tables_counts=tables_counts,
                           revenue_view_data=revenue_view_data,
                           active_shows_view=active_shows_view)

@dbms_bp.route("/simulate-concurrency", methods=["POST"])
def simulate_concurrency():
    """
    Demonstrates Concurrency Control & Row-Level Locking (SELECT ... FOR UPDATE)
    Simulates User A and User B attempting to book the EXACT SAME SEAT at the same millisecond.
    Result: One succeeds, the other is blocked and safely rolled back!
    """
    data = request.get_json() or {}
    show_id = data.get("show_id", 1)
    seat_id = data.get("seat_id", 1)

    results = []

    def attempt_booking(user_name, user_id, delay):
        time.sleep(delay)
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Lock row
                cur.execute("""
                    SELECT bs.seat_id 
                    FROM booking_seats bs
                    JOIN bookings b ON bs.booking_id = b.booking_id
                    WHERE b.show_id = %s AND bs.seat_id = %s AND b.status = 'CONFIRMED'
                    FOR UPDATE
                """, (show_id, seat_id))
                already_booked = cur.fetchone()

                if already_booked:
                    conn.rollback()
                    results.append({
                        "user": user_name,
                        "status": "FAILED",
                        "reason": "Seat already locked/booked by another concurrent transaction (ROLLBACK)."
                    })
                    return

                # Insert booking
                ref = f"SIM-{int(time.time()*1000)%100000}"
                cur.execute("INSERT INTO bookings (booking_reference, user_id, show_id, total_amount, status) VALUES (%s, %s, %s, 150.00, 'CONFIRMED')", (ref, user_id, show_id))
                bid = cur.lastrowid
                cur.execute("INSERT INTO booking_seats (booking_id, seat_id, price) VALUES (%s, %s, 150.00)", (bid, seat_id))
                cur.execute("INSERT INTO payments (booking_id, transaction_id, amount, payment_method, status) VALUES (%s, %s, 150.00, 'UPI', 'SUCCESS')", (bid, f"SIM_TX_{bid}"))
                conn.commit()
                results.append({
                    "user": user_name,
                    "status": "SUCCESS",
                    "reason": f"Seat secured! Booking Ref: {ref} (COMMITTED)."
                })
        except Exception as e:
            conn.rollback()
            results.append({
                "user": user_name,
                "status": "ERROR",
                "reason": str(e)
            })
        finally:
            conn.close()

    # Launch two concurrent threads for Seat 1
    t1 = threading.Thread(target=attempt_booking, args=("Customer Alpha", 1, 0.0))
    t2 = threading.Thread(target=attempt_booking, args=("Customer Beta", 2, 0.01))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return jsonify({"concurrency_test_results": results})

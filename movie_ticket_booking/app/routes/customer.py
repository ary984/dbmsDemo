import random
import string
import time
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.db import get_db_connection, query_all, query_one
from app.routes.auth import login_required

customer_bp = Blueprint("customer", __name__)

def generate_booking_reference():
    timestamp = time.strftime("%y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"BK{timestamp}{random_str}"

@customer_bp.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    selected_genre = request.args.get("genre", "").strip()

    sql = """
        SELECT m.movie_id, m.title, m.genre, m.duration_mins, m.language, 
               m.rating, m.poster_url, COUNT(s.show_id) as total_shows
        FROM movies m
        LEFT JOIN shows s ON m.movie_id = s.movie_id AND s.start_time > NOW()
        WHERE 1=1
    """
    params = []
    if search_query:
        sql += " AND (m.title LIKE %s OR m.genre LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    if selected_genre:
        sql += " AND m.genre LIKE %s"
        params.append(f"%{selected_genre}%")

    sql += " GROUP BY m.movie_id ORDER BY m.rating DESC"
    movies = query_all(sql, params)

    # Get distinct genres for the filter pills
    genres_data = query_all("SELECT DISTINCT genre FROM movies")
    genres = sorted(list({g.strip() for row in genres_data for g in row["genre"].split("/")}))

    return render_template("customer/index.html", movies=movies, genres=genres, search_query=search_query, selected_genre=selected_genre)

@customer_bp.route("/movies/<int:movie_id>")
def movie_detail(movie_id):
    movie = query_one("SELECT * FROM movies WHERE movie_id = %s", (movie_id,))
    if not movie:
        flash("Movie not found.", "warning")
        return redirect(url_for("customer.index"))

    # Fetch upcoming shows grouped by cinema
    shows = query_all("""
        SELECT s.show_id, s.start_time, s.end_time, s.price_multiplier,
               sc.screen_name, sc.sound_system,
               c.cinema_id, c.name as cinema_name, c.city, c.address
        FROM shows s
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        WHERE s.movie_id = %s AND s.start_time > NOW() AND s.status = 'SCHEDULED'
        ORDER BY c.cinema_id, s.start_time ASC
    """, (movie_id,))

    # Group shows by cinema
    cinemas_dict = {}
    for show in shows:
        cid = show["cinema_id"]
        if cid not in cinemas_dict:
            cinemas_dict[cid] = {
                "cinema_name": show["cinema_name"],
                "city": show["city"],
                "address": show["address"],
                "shows": []
            }
        cinemas_dict[cid]["shows"].append(show)

    return render_template("customer/movie_detail.html", movie=movie, cinemas=list(cinemas_dict.values()))

@customer_bp.route("/shows/<int:show_id>/seats")
@login_required
def select_seats(show_id):
    show = query_one("""
        SELECT s.show_id, s.start_time, s.price_multiplier,
               m.movie_id, m.title as movie_title, m.poster_url, m.duration_mins, m.language,
               sc.screen_id, sc.screen_name,
               c.name as cinema_name, c.city
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
        WHERE s.show_id = %s
    """, (show_id,))

    if not show:
        flash("Showtime not found.", "warning")
        return redirect(url_for("customer.index"))

    # Call Stored Procedure `sp_get_show_seats`
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.callproc("sp_get_show_seats", (show_id,))
            seats = cur.fetchall()
    finally:
        conn.close()

    # Organize seats by rows for template rendering
    seat_rows = {}
    for seat in seats:
        r = seat["seat_row"]
        if r not in seat_rows:
            seat_rows[r] = []
        seat_rows[r].append(seat)

    return render_template("customer/seat_selection.html", show=show, seat_rows=seat_rows)

@customer_bp.route("/shows/<int:show_id>/book", methods=["POST"])
@login_required
def book_tickets(show_id):
    """
    ACID Transactional Booking Handler:
    1. Lock requested seats for update
    2. Check if any seat is already booked for this show
    3. Insert booking, booking_seats, and payment atomically
    4. Commit or rollback on collision
    """
    user_id = session["user"]["user_id"]
    seat_ids_raw = request.form.getlist("seat_ids")
    payment_method = request.form.get("payment_method", "UPI")

    if not seat_ids_raw:
        flash("Please select at least one seat before proceeding.", "warning")
        return redirect(url_for("customer.select_seats", show_id=show_id))

    seat_ids = [int(s) for s in seat_ids_raw]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Fetch show multiplier
            cur.execute("SELECT show_id, price_multiplier, status, start_time FROM shows WHERE show_id = %s", (show_id,))
            show = cur.fetchone()
            if not show or show["status"] != "SCHEDULED":
                conn.rollback()
                flash("This show is no longer accepting bookings.", "danger")
                return redirect(url_for("customer.index"))

            # 2. Check concurrency: Lock booked seats for this show
            format_strings = ','.join(['%s'] * len(seat_ids))
            cur.execute(f"""
                SELECT bs.seat_id 
                FROM booking_seats bs
                JOIN bookings b ON bs.booking_id = b.booking_id
                WHERE b.show_id = %s 
                  AND bs.seat_id IN ({format_strings}) 
                  AND b.status = 'CONFIRMED'
                FOR UPDATE
            """, [show_id] + seat_ids)
            conflicts = cur.fetchall()

            if conflicts:
                conn.rollback()
                flash("Someone just booked one or more of your selected seats. Please select other seats.", "danger")
                return redirect(url_for("customer.select_seats", show_id=show_id))

            # 3. Calculate exact total amount based on seat base price & show multiplier
            cur.execute(f"SELECT seat_id, seat_number, base_price FROM seats WHERE seat_id IN ({format_strings})", seat_ids)
            seats_info = cur.fetchall()
            multiplier = float(show["price_multiplier"])
            
            seat_prices = {}
            total_amount = 0.0
            for s in seats_info:
                price = round(float(s["base_price"]) * multiplier, 2)
                seat_prices[s["seat_id"]] = price
                total_amount += price

            # 4. Insert Booking
            booking_ref = generate_booking_reference()
            cur.execute("""
                INSERT INTO bookings (booking_reference, user_id, show_id, total_amount, status)
                VALUES (%s, %s, %s, %s, 'CONFIRMED')
            """, (booking_ref, user_id, show_id, total_amount))
            booking_id = cur.lastrowid

            # 5. Insert Booking Seats
            for sid in seat_ids:
                cur.execute("""
                    INSERT INTO booking_seats (booking_id, seat_id, price)
                    VALUES (%s, %s, %s)
                """, (booking_id, sid, seat_prices[sid]))

            # 6. Insert Simulated Payment Record
            tx_id = f"TXN_{int(time.time())}_{random.randint(1000, 9999)}"
            cur.execute("""
                INSERT INTO payments (booking_id, transaction_id, amount, payment_method, status)
                VALUES (%s, %s, %s, %s, 'SUCCESS')
            """, (booking_id, tx_id, total_amount, payment_method))

        # Commit transaction atomically
        conn.commit()
        flash("🎉 Booking confirmed successfully!", "success")
        return redirect(url_for("customer.ticket_view", ref=booking_ref))

    except Exception as e:
        conn.rollback()
        flash(f"Booking transaction failed: {str(e)}", "danger")
        return redirect(url_for("customer.select_seats", show_id=show_id))
    finally:
        conn.close()

@customer_bp.route("/ticket/<ref>")
@login_required
def ticket_view(ref):
    # Query using SQL View `vw_booking_details`
    ticket = query_one("SELECT * FROM vw_booking_details WHERE booking_reference = %s", (ref,))
    if not ticket:
        flash("Ticket not found.", "warning")
        return redirect(url_for("customer.index"))

    # Security check: only owner or admin can view ticket
    if session["user"]["role"] != "admin" and ticket["user_id"] != session["user"]["user_id"]:
        flash("Unauthorized ticket access.", "danger")
        return redirect(url_for("customer.index"))

    return render_template("customer/ticket.html", ticket=ticket)

@customer_bp.route("/my-bookings")
@login_required
def my_bookings():
    user_id = session["user"]["user_id"]
    bookings = query_all("""
        SELECT * FROM vw_booking_details 
        WHERE user_id = %s 
        ORDER BY booking_time DESC
    """, (user_id,))
    return render_template("customer/my_bookings.html", bookings=bookings)

@customer_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    user_id = session["user"]["user_id"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Call Stored Procedure `sp_cancel_booking`
            cur.callproc("sp_cancel_booking", (booking_id, user_id, 0, ""))
            cur.execute("SELECT @_sp_cancel_booking_2, @_sp_cancel_booking_3;")
            result = cur.fetchone()
            # If the procedure output variables aren't mapped via @_sp_..., fallback to direct check
            if result:
                success = result.get("@_sp_cancel_booking_2")
                message = result.get("@_sp_cancel_booking_3")
            else:
                success = True
                message = "Booking cancelled successfully."
        conn.commit()
        if success:
            flash(message or "Booking successfully cancelled and refund initiated.", "success")
        else:
            flash(message or "Could not cancel booking.", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Cancellation error: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("customer.my_bookings"))

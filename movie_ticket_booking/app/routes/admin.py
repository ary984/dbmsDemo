from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import query_all, query_one, execute_commit
from app.routes.auth import admin_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {}
    stats["total_movies"] = query_one("SELECT COUNT(*) as c FROM movies")["c"]
    stats["total_cinemas"] = query_one("SELECT COUNT(*) as c FROM cinemas")["c"]
    stats["total_shows"] = query_one("SELECT COUNT(*) as c FROM shows WHERE start_time > NOW()")["c"]
    stats["total_bookings"] = query_one("SELECT COUNT(*) as c FROM bookings WHERE status = 'CONFIRMED'")["c"]
    
    rev_data = query_one("SELECT COALESCE(SUM(total_amount), 0) as s FROM bookings WHERE status = 'CONFIRMED'")
    stats["total_revenue"] = rev_data["s"] if rev_data else 0.0

    recent_bookings = query_all("""
        SELECT * FROM vw_booking_details 
        ORDER BY booking_time DESC 
        LIMIT 8
    """)

    revenue_by_cinema = query_all("SELECT * FROM vw_cinema_revenue ORDER BY gross_revenue DESC")

    return render_template("admin/dashboard.html", stats=stats, recent_bookings=recent_bookings, revenue_by_cinema=revenue_by_cinema)

# ----------------- MOVIES MANAGEMENT -----------------

@admin_bp.route("/movies")
@admin_required
def movies_list():
    movies = query_all("SELECT * FROM movies ORDER BY created_at DESC")
    return render_template("admin/movies.html", movies=movies)

@admin_bp.route("/movies/add", methods=["POST"])
@admin_required
def add_movie():
    title = request.form.get("title")
    genre = request.form.get("genre")
    duration = int(request.form.get("duration_mins", 120))
    language = request.form.get("language", "English")
    rating = float(request.form.get("rating", 8.0))
    description = request.form.get("description", "")
    poster_url = request.form.get("poster_url", "")
    release_date = request.form.get("release_date") or None

    try:
        execute_commit("""
            INSERT INTO movies (title, description, genre, duration_mins, language, release_date, rating, poster_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, description, genre, duration, language, release_date, rating, poster_url))
        flash(f"Movie '{title}' added successfully!", "success")
    except Exception as e:
        flash(f"Error adding movie: {str(e)}", "danger")

    return redirect(url_for("admin.movies_list"))

@admin_bp.route("/movies/<int:movie_id>/delete", methods=["POST"])
@admin_required
def delete_movie(movie_id):
    try:
        execute_commit("DELETE FROM movies WHERE movie_id = %s", (movie_id,))
        flash("Movie deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting movie: {str(e)}", "danger")
    return redirect(url_for("admin.movies_list"))

# ----------------- SHOWS MANAGEMENT -----------------

@admin_bp.route("/shows")
@admin_required
def shows_list():
    shows = query_all("SELECT * FROM vw_active_shows ORDER BY start_time ASC")
    movies = query_all("SELECT movie_id, title FROM movies ORDER BY title ASC")
    screens = query_all("""
        SELECT sc.screen_id, sc.screen_name, c.name as cinema_name, c.city 
        FROM screens sc 
        JOIN cinemas c ON sc.cinema_id = c.cinema_id
    """)
    return render_template("admin/shows.html", shows=shows, movies=movies, screens=screens)

@admin_bp.route("/shows/add", methods=["POST"])
@admin_required
def add_show():
    movie_id = request.form.get("movie_id")
    screen_id = request.form.get("screen_id")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    price_multiplier = float(request.form.get("price_multiplier", 1.0))

    try:
        execute_commit("""
            INSERT INTO shows (movie_id, screen_id, start_time, end_time, price_multiplier, status)
            VALUES (%s, %s, %s, %s, %s, 'SCHEDULED')
        """, (movie_id, screen_id, start_time, end_time, price_multiplier))
        flash("New show scheduled successfully!", "success")
    except Exception as e:
        flash(f"Error scheduling show: {str(e)}", "danger")

    return redirect(url_for("admin.shows_list"))

@admin_bp.route("/shows/<int:show_id>/cancel", methods=["POST"])
@admin_required
def cancel_show(show_id):
    try:
        execute_commit("UPDATE shows SET status = 'CANCELLED' WHERE show_id = %s", (show_id,))
        flash("Show marked as CANCELLED.", "warning")
    except Exception as e:
        flash(f"Error cancelling show: {str(e)}", "danger")
    return redirect(url_for("admin.shows_list"))

# ----------------- AUDIT LOGS & DBMS INSPECTOR -----------------

@admin_bp.route("/audit-logs")
@admin_required
def audit_logs():
    logs = query_all("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50")
    return render_template("admin/audit_logs.html", logs=logs)

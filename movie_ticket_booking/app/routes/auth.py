from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_one, execute_commit

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for("auth.login"))
        if session["user"].get("role") != "admin":
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("customer.index"))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("customer.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register.html")

        # Check if user already exists
        existing_user = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
        if existing_user:
            flash("An account with this email address already exists.", "danger")
            return render_template("auth/register.html")

        password_hash = generate_password_hash(password)
        try:
            user_id = execute_commit(
                "INSERT INTO users (full_name, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, 'customer')",
                (full_name, email, password_hash, phone)
            )
            session["user"] = {
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "role": "customer"
            }
            flash(f"Welcome to CinePass, {full_name}! Your account has been created.", "success")
            return redirect(url_for("customer.index"))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("customer.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query_one("SELECT user_id, full_name, email, password_hash, role FROM users WHERE email = %s", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            if user["role"] == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("customer.index"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("customer.index"))

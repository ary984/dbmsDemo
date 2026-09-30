import os
from app import create_app
from app.db import query_one

app = create_app()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  [CinePass] - Movie Ticket Booking DBMS System")
    print("="*60)
    try:
        ver = query_one("SELECT VERSION() as v;")
        print(f"  [+] Connected to MySQL Server Version: {ver['v']}")
        print(f"  [+] Database: movie_booking_db (ACID & Triggers Active)")
    except Exception as e:
        print(f"  [!] Database Connection Warning: {e}")

    print("\n  Demo Credentials:")
    print("      * Admin:    admin@cinema.com  / Admin@123")
    print("      * Customer: john@example.com   / User@123")
    print("\n  Running server at http://127.0.0.1:5000")
    print("="*60 + "\n")

    app.run(host="127.0.0.1", port=5000, debug=False)

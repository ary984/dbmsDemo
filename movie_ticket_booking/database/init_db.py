"""
Database Initialization Script for Movie Ticket Booking System
Executes schema.sql, advanced_dbms.sql (procedures, triggers, views), and seed_data.sql.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "movie_booking_db")

MYSQL_PATH = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

def run_sql_file(filepath):
    print(f"[*] Executing {os.path.basename(filepath)}...")
    if not os.path.exists(filepath):
        print(f"    [!] Error: File not found: {filepath}")
        return False
        
    cmd = [
        MYSQL_PATH,
        f"-h{DB_HOST}",
        f"-P{DB_PORT}",
        f"-u{DB_USER}",
        f"-p{DB_PASSWORD}",
        "--default-character-set=utf8mb4"
    ]
    
    with open(filepath, "rb") as f:
        p = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
        if p.returncode != 0:
            print(f"    [!] MySQL Error:\n{p.stderr}")
            return False
        print(f"    [+] {os.path.basename(filepath)} applied successfully.")
        return True

def initialize_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(base_dir, "schema.sql")
    advanced_file = os.path.join(base_dir, "advanced_dbms.sql")
    seed_file = os.path.join(base_dir, "seed_data.sql")

    print(f"[*] Initializing Database `{DB_NAME}` on MySQL Server...")
    success = (
        run_sql_file(schema_file) and
        run_sql_file(advanced_file) and
        run_sql_file(seed_file)
    )

    if success:
        print(f"\n[+] Database `{DB_NAME}` is fully initialized with schemas, views, stored procedures, triggers, and seed data!")
    else:
        print("\n[!] Database initialization had some issues. Check messages above.")

if __name__ == "__main__":
    initialize_database()

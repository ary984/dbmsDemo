import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "movie_booking_db")

def get_db_connection():
    """Returns a new MySQL database connection with DictCursor."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False  # manual commit for transaction support
    )

def query_all(sql, params=None):
    """Executes a SELECT query and returns all matching rows as dictionaries."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

def query_one(sql, params=None):
    """Executes a SELECT query and returns a single row as a dictionary."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()
    finally:
        conn.close()

def execute_commit(sql, params=None):
    """Executes an INSERT/UPDATE/DELETE query and commits the transaction."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            last_id = cur.lastrowid
        conn.commit()
        return last_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

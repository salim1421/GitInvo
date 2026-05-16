from tkinter import *
import bcrypt
import os
import sqlite3
import threading
from config import DB_NAME   # ← single source of truth

db_lock = threading.Lock()   # ← shared lock


def connect_database():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

    first_time = not os.path.exists(DB_NAME)

    conn = sqlite3.connect(
        DB_NAME,
        timeout=10,
        check_same_thread=False
    )
    cursor = conn.cursor()

    # FIX 2: Enable WAL mode immediately after connecting
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")   # also enforce your FK constraints

    if first_time:
        initialize_database(cursor)
        conn.commit()

    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    if result != "ok":
        raise Exception("Database corruption detected")

    run_migrations(cursor)
    conn.commit()

    return conn, cursor


def run_migrations(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("SELECT value FROM app_meta WHERE key='db_version'")
    row = cursor.fetchone()
    version = row[0] if row else "1.0"

    if version == "1.0":
        try:
            cursor.execute("ALTER TABLE product_data ADD COLUMN barcode TEXT")
        except:
            pass

        cursor.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('db_version', '1.1')"
        )


def initialize_database(cursor):
    def create_default_user(cursor):
        cursor.execute("SELECT * FROM employee_data LIMIT 1")
        if cursor.fetchone():
            return

        default_username = "admin"
        default_user_type = 'Admin'
        default_phone_no = '0000000000'
        password = "admin123".encode()
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO employee_data (name, phone_number, user_type, password)
            VALUES (?, ?, ?, ?)
        """, (default_username, default_phone_no, default_user_type, hashed))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_data (
            empid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone_number TEXT,
            user_type TEXT,
            password BLOB
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_data(
            catid INTEGER PRIMARY KEY,
            name VARCHAR(50),
            description VARCHAR(15)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit_cost REAL NOT NULL,
            selling_price REAL NOT NULL DEFAULT 0,
            detail TEXT,
            category TEXT,
            supplier TEXT,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_product_updated_at
        AFTER UPDATE ON product_data
        FOR EACH ROW
        BEGIN
            UPDATE product_data
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            unit_cost REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            total REAL NOT NULL,
            profit REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sales_items_sale_id
        ON sales_items(sale_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            details TEXT,
            category TEXT,
            supplier TEXT,
            status TEXT CHECK(status IN ('Pending', 'Delivered', 'Cancelled')) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_no TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            customer_name TEXT,
            refund_total REAL NOT NULL,
            refund_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refund_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refund_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_cost REAL NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            profit REAL NOT NULL,
            FOREIGN KEY (refund_id) REFERENCES refunds(id) ON DELETE CASCADE
        )
    """)

    create_default_user(cursor)
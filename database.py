import bcrypt # type: ignore
import os
import sqlite3


DB_NAME = "myinventory.db"

def connect_database():
    first_time = not os.path.exists(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if first_time:
        initialize_database(cursor)
        conn.commit()

    return conn, cursor


def initialize_database(cursor):
    #creates user at first run!!
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


    # Employees
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_data (
            empid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone_number TEXT,
            user_type TEXT,
            password BLOB
        )
    """)


    # Sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            subtotal REAL,
            tax REAL,
            total REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sale Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            total REAL,
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        )
    """)

    #categories
    cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS category_data(
                catid INTEGER PRIMARY KEY,
                name VARCHAR(50),
                description VARCHAR(15)
            )
        '''
        )
    
    #products
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

    #sales
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

    #Purchase Order
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
    #Suppliers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_no TEXT UNIQUE
        )
    """)

    #refund sys
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
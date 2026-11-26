
import sqlite3
import os
os.makedirs("data", exist_ok=True)

DB_PATH = "data/factory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # User accounts and role-based access
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Add is_active to an existing users table if missing
    user_columns = [
        row["name"]
        for row in cursor.execute("PRAGMA table_info(users)").fetchall()
    ]

    if "is_active" not in user_columns:
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN is_active INTEGER DEFAULT 1
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        gst REAL,
        stock INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        state TEXT,
        customer_type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        quantity REAL,
        unit TEXT,
        rate REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        product TEXT,
        quantity INTEGER,
        total REAL,
        status TEXT
    )
    """)
        # Add approval fields to existing orders table if missing
    order_columns = [
        row["name"]
        for row in cursor.execute("PRAGMA table_info(orders)").fetchall()
    ]

    if "approved_by" not in order_columns:
        cursor.execute("""
        ALTER TABLE orders ADD COLUMN approved_by TEXT
        """)

    if "approved_at" not in order_columns:
        cursor.execute("""
        ALTER TABLE orders ADD COLUMN approved_at TEXT
        """)

    if "rejection_reason" not in order_columns:
        cursor.execute("""
        ALTER TABLE orders ADD COLUMN rejection_reason TEXT
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        material TEXT NOT NULL,
        quantity_per_unit REAL NOT NULL
    )
    """)
        # Dispatch Management
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dispatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        customer TEXT,
        product TEXT,
        quantity_dispatched INTEGER NOT NULL,
        dispatch_date TEXT NOT NULL,
        dispatch_status TEXT DEFAULT 'Dispatched',
        dispatched_by TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    # Payment Tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        customer TEXT,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_method TEXT,
        reference TEXT,
        received_by TEXT,
        notes TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        expected_output INTEGER,
        actual_output INTEGER,
        wastage INTEGER,
        variance REAL
    )
    """)

    # Add material category to existing inventory table
    material_columns = [
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(raw_materials)"
        ).fetchall()
    ]

    if "material_type" not in material_columns:
        cursor.execute("""
            ALTER TABLE raw_materials
            ADD COLUMN material_type TEXT DEFAULT 'Raw Material'
        """)

    # Supplier management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            email TEXT,
            gstin TEXT,
            address TEXT
        )
    """)

    # Purchase records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            material_id INTEGER,
            material_name TEXT NOT NULL,
            material_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            rate REAL NOT NULL,
            total REAL NOT NULL,
            invoice_no TEXT,
            purchase_date TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """)

    # Stock movement ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            item_id INTEGER,
            item_name TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            source_type TEXT,
            source_id INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_item
        ON stock_movements(item_type, item_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_purchase_date
        ON purchases(purchase_date)
    """)

    conn.commit()
    conn.close()

    create_tables()
    print("Database created successfully!")


import hashlib
import secrets
import hmac


def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    ).hex()

    return salt + "$" + hashed


def verify_password(password, stored_password):
    try:
        salt, stored_hash = stored_password.split("$")
        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000
        ).hex()

        return hmac.compare_digest(new_hash, stored_hash)

    except ValueError:
        return False


def create_user(username, password, role):
    if not username.strip():
        raise ValueError("Username cannot be empty.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    allowed_roles = [
        "Admin",
        "Salesman",
        "Production Supervisor",
        "Accountant/Auditor"
    ]

    if role not in allowed_roles:
        raise ValueError("Invalid role.")

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username.strip(), hash_password(password), role)
        )
        conn.commit()

    except sqlite3.IntegrityError:
        raise ValueError("This username already exists.")

    finally:
        conn.close()
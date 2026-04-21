"""
KisanCard - Database Models & Setup (MySQL Version)
"""
import os
from werkzeug.security import generate_password_hash
import MySQLdb.cursors

# This will be injected from app.py
mysql_app = None

def init_mysql(con):
    """Binds the Flask-MySQL instance from app.py to models."""
    global mysql_app
    mysql_app = con

class DBWrapper:
    """Wrapper that mimics SQLite's conn.execute() behavior using MySQL cursors."""
    def __init__(self, connection):
        self.conn = connection
        self.lastrowid = None
        
    def execute(self, query, params=()):
        # Convert SQLite bindings to MySQL bindings
        mysql_query = query.replace("?", "%s")
        cur = self.conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(mysql_query, params)
        self.lastrowid = cur.lastrowid
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        # We don't strictly close the Flask managed connection pool here
        pass

def get_db():
    """Get a database wrapper instance."""
    if mysql_app is None:
        raise Exception("MySQL has not been initialized.")
    return DBWrapper(mysql_app.connection)


def init_db():
    """Create all database tables if they don't exist in MySQL."""
    conn = get_db()

    # ── Users table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            phone VARCHAR(50) DEFAULT '',
            address TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            is_agent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Categories table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            icon VARCHAR(50) DEFAULT ''
        )
    """)

    # ── Products table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            custom_id VARCHAR(100) UNIQUE,
            name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            sale_price REAL DEFAULT 0,
            weight VARCHAR(100) DEFAULT '',
            category_id INT,
            image1 VARCHAR(255) DEFAULT 'default.jpg',
            image2 VARCHAR(255) DEFAULT 'default.jpg',
            image3 VARCHAR(255) DEFAULT 'default.jpg',
            stock INT DEFAULT 10,
            featured BOOLEAN DEFAULT FALSE,
            rating REAL DEFAULT 4.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # ── Orders table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total REAL NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            address TEXT NOT NULL,
            city VARCHAR(100) DEFAULT '',
            pincode VARCHAR(20) DEFAULT '',
            payment_method VARCHAR(50) DEFAULT 'COD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ── Order Items table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # ── Contact Messages table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            subject VARCHAR(255) DEFAULT '',
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Footer Ads table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS footer_ads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            image_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Delivery Boys table ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delivery_boys (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            zone VARCHAR(100) DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Database Migrations ──
    try:
        col_check = conn.execute("SHOW COLUMNS FROM users LIKE 'role'").fetchone()
        if not col_check:
            conn.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'")
            conn.execute("UPDATE users SET role = 'super_admin' WHERE is_admin = 1")
    except Exception as e:
        print("Migration error users:", e)

    try:
        col_check = conn.execute("SHOW COLUMNS FROM orders LIKE 'verification_code'").fetchone()
        if not col_check:
            conn.execute("ALTER TABLE orders ADD COLUMN verification_code VARCHAR(10) DEFAULT ''")
            conn.execute("ALTER TABLE orders ADD COLUMN delivery_boy_id INT NULL")
            conn.execute("ALTER TABLE orders ADD COLUMN delivery_status VARCHAR(50) DEFAULT 'Pending'")
    except Exception as e:
        print("Migration error orders:", e)

    conn.commit()
    print("MySQL Database tables created successfully!")


def seed_data():
    """Populate MySQL database safely with setup information."""
    conn = get_db()

    # Check if data already exists
    if conn.execute("SELECT COUNT(*) as cnt FROM categories").fetchone()['cnt'] > 0:
        print("Data already seeded. Skipping.")
        return

    # Seed Admin
    admin_hash = generate_password_hash("admin123")
    try:
        conn.execute("""
            INSERT INTO users (username, email, password_hash, is_admin, is_agent)
            VALUES (?, ?, ?, 1, 0)
        """, ("admin", "admin@kisancard.com", admin_hash))
    except Exception:
        pass

    # Seed Demo Customer
    demo_hash = generate_password_hash("demo123")
    try:
        conn.execute("""
            INSERT INTO users (username, email, password_hash, phone, address, is_admin, is_agent)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, ("demo", "demo@gmail.com", demo_hash, "9876543210", "123 Garden Street, Mumbai"))
    except Exception:
        pass

    # Seed Delivery Agent
    agent_hash = generate_password_hash("agent123")
    try:
        conn.execute("""
            INSERT INTO users (username, email, password_hash, is_admin, is_agent)
            VALUES (?, ?, ?, 0, 1)
        """, ("agent", "agent@kisancard.com", agent_hash))
    except Exception:
        pass

    # Seed Categories
    categories = [
        ("Khad", "High quality fertilizers for plant growth", '<i class="fas fa-box-open"></i>'),
        ("Plant", "Live plants for home and garden", '<i class="fas fa-leaf"></i>'),
        ("Beej", "Selected seeds for high yield", '<i class="fas fa-seedling"></i>'),
        ("Dava", "Medicines and pesticides for plant care", '<i class="fas fa-prescription-bottle-alt"></i>')
    ]
    cur = conn.conn.cursor()
    cur.executemany(
        "INSERT INTO categories (name, description, icon) VALUES (%s, %s, %s)",
        categories
    )

    # Seed Products
    products = [
        ("SKU-001", "Snake Plant", "Best plant for air purification. Requires very little water and light.", 499, 399, "1.2 kg", 1, "product_2.jpg"),
        ("SKU-002", "Monstera Deliciosa", "The famous Swiss Cheese plant. Perfect for bright indirect light.", 899, 750, "2.5 kg", 1, "product_1.jpg"),
        ("SKU-003", "Aloe Vera", "Healing succulent plant. Great for skin and easy to care for.", 299, 0, "500 g", 3, "product_3.jpg"),
        ("SKU-004", "Peace Lily", "Beautiful white hooded flowers and air-purifying qualities.", 599, 499, "1 kg", 1, "product_4.jpg"),
        ("SKU-005", "Jade Plant", "A popular succulent, considered a symbol of good luck.", 349, 299, "600 g", 3, "product_5.jpg"),
        ("SKU-006", "Areca Palm", "Creates a tropical vibe indoors and naturally humidifies air.", 999, 850, "3 kg", 1, "product_4.jpg"),
    ]
    cur.executemany("""
        INSERT INTO products (custom_id, name, description, price, sale_price, weight, category_id, image1)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, products)

    conn.commit()
    cur.close()
    print("Sample MySQL data inserted successfully!")

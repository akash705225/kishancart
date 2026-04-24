"""
KisanCard — Main Flask Application
=====================================
A complete e-commerce website for selling plants.
Features: Auth, Cart, Checkout, Admin Panel, Search, Filters.

Routes:
  /                 → Homepage
  /shop             → Browse all products
  /product/<id>     → Product detail
  /cart              → Shopping cart
  /cart/add/<id>     → Add to cart
  /cart/remove/<id>  → Remove from cart
  /cart/update       → Update cart quantity
  /checkout          → Checkout form
  /order-success/<id>→ Order confirmation
  /login             → Login
  /register          → Register
  /logout            → Logout
  /profile           → User profile & orders
  /about             → About us
  /contact           → Contact page
  /search            → Search products
  /admin/            → Admin dashboard
  /admin/products    → Manage products
  /admin/add-product → Add product
  /admin/edit-product/<id> → Edit product
  /admin/delete-product/<id> → Delete product
  /admin/orders      → View all orders
  /admin/order-status/<id>  → Update order status
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import secrets
import string
from dotenv import load_dotenv
import certifi
import config

import pymysql
pymysql.install_as_MySQLdb()

from flask_mysqldb import MySQL
from models import init_mysql, get_db, init_db, seed_data

# Load environment variables
load_dotenv()

# ══════════════════════════════════════════════
# APP INITIALIZATION
# ══════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "akash")
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# Database connection details from .env
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
app.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT", 4000))
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")

# Setup TLS connection required by TiDB Serverless 
app.config["MYSQL_CUSTOM_OPTIONS"] = {
    "ssl": {
        "ca": certifi.where()
    }
}

mysql = MySQL(app)
init_mysql(mysql)

# Ensure upload directory exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

try:
    with app.app_context():
        # Initialize database + seed on first run
        init_db()
        seed_data()
except Exception as e:
    print(f"Warning: Database initialization failed. Ensure MySQL server is running and database '{app.config['MYSQL_DB']}' exists.")
    import traceback
    traceback.print_exc()


# ══════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════

def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def login_required(f):
    """Decorator: redirect to login if user not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: restrict access to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login as admin.", "warning")
            return redirect(url_for("login"))
        if session.get("role") not in ["super_admin", "sub_admin"] and not session.get("is_admin"):
            flash("Access denied. Admin only.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    """Decorator: restrict access to super admin only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login as admin.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "super_admin" and not session.get("is_admin"):
            flash("Access denied. Super Admin only.", "danger")
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated


def delivery_required(f):
    """Decorator: restrict access to delivery boys."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "delivery_boy_id" not in session:
            flash("Please login to delivery portal.", "warning")
            return redirect(url_for("delivery_login"))
        return f(*args, **kwargs)
    return decorated


def get_cart_count():
    """Return total number of items in the session cart."""
    cart = session.get("cart", {})
    return sum(item["qty"] for item in cart.values())


def get_cart_total():
    """Calculate total price of all items in the session cart."""
    cart = session.get("cart", {})
    total = 0
    for item in cart.values():
        price = item.get("sale_price") if item.get("sale_price") and item["sale_price"] > 0 else item["price"]
        total += price * item["qty"]
    return round(total, 2)


# ── Make cart count available in all templates ──
@app.context_processor
def inject_cart():
    return dict(cart_count=get_cart_count())

@app.context_processor
def inject_footer_ads_global():
    try:
        db = get_db()
        ads = db.execute("SELECT * FROM footer_ads ORDER BY created_at DESC").fetchall()
        db.close()
        return dict(footer_ads=ads)
    except Exception:
        return dict(footer_ads=[])


# ══════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════

@app.route("/")
def home():
    """Homepage: featured products + categories."""
    db = get_db()
    # Get featured products
    featured = db.execute(
        "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.featured = 1 ORDER BY p.created_at DESC LIMIT 8"
    ).fetchall()
    # Get all categories with product counts
    categories = db.execute("""
        SELECT c.*, COUNT(p.id) as product_count 
        FROM categories c 
        LEFT JOIN products p ON c.id = p.category_id 
        GROUP BY c.id
    """).fetchall()
    # Get latest products
    latest = db.execute(
        "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.created_at DESC LIMIT 4"
    ).fetchall()
    db.close()
    return render_template("index.html", featured=featured, categories=categories, latest=latest)


@app.route("/shop")
def shop():
    """Shop page: all products with filtering & search."""
    db = get_db()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "newest")
    search = request.args.get("q", "").strip()

    # Base query
    query = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1"
    params = []

    # Apply filters
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Apply sorting
    if sort == "price_low":
        query += " ORDER BY p.price ASC"
    elif sort == "price_high":
        query += " ORDER BY p.price DESC"
    elif sort == "name":
        query += " ORDER BY p.name ASC"
    elif sort == "rating":
        query += " ORDER BY p.rating DESC"
    else:  # newest
        query += " ORDER BY p.created_at DESC"

    products = db.execute(query, params).fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    db.close()

    return render_template("shop.html",
                           products=products, categories=categories,
                           current_category=category_id, current_sort=sort,
                           search_query=search)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Single product detail page."""
    db = get_db()
    product = db.execute(
        "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = ?",
        (product_id,)
    ).fetchone()

    if not product:
        db.close()
        flash("Product not found.", "danger")
        return redirect(url_for("shop"))

    # Get related products from same category
    related = db.execute(
        "SELECT * FROM products WHERE category_id = ? AND id != ? ORDER BY RAND() LIMIT 4",
        (product["category_id"], product_id)
    ).fetchall()
    db.close()
    return render_template("product_detail.html", product=product, related=related)


def send_order_notification(phone, code, order_id):
    """
    Placeholder for Twilio/WhatsApp API integration.
    This function simulates sending the unique order code to the customer.
    """
    print(f"🔔 [MOCK API] Sending WhatsApp to {phone}: 'Your KisanCard order #{order_id} is confirmed! Verification Code for delivery: {code}'")

@app.route("/search")
def search():
    """Search endpoint — redirects to shop with search query."""
    q = request.args.get("q", "").strip()
    return redirect(url_for("shop", q=q))


@app.route("/about")
def about():
    """About us page."""
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page with message form."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Validation
        if not all([name, email, message]):
            flash("Please fill in all required fields.", "danger")
            return render_template("contact.html")

        # Save to database
        db = get_db()
        db.execute(
            "INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
            (name, email, subject, message)
        )
        db.commit()
        db.close()
        flash("Thank you! Your message has been sent successfully.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


# ══════════════════════════════════════════════
# CART ROUTES
# ══════════════════════════════════════════════

@app.route("/cart")
def cart():
    """View shopping cart."""
    cart_items = session.get("cart", {})
    total = get_cart_total()
    return render_template("cart.html", cart=cart_items, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    """Add a product to the session cart."""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("shop"))

    if product["stock"] <= 0:
        flash("Sorry, this product is out of stock.", "warning")
        return redirect(url_for("product_detail", product_id=product_id))

    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})
    pid = str(product_id)

    if pid in cart:
        cart[pid]["qty"] += qty
    else:
        cart[pid] = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "sale_price": product["sale_price"],
            "image": product["image1"],
            "qty": qty,
            "stock": product["stock"]
        }

    # Don't exceed stock
    if cart[pid]["qty"] > product["stock"]:
        cart[pid]["qty"] = product["stock"]

    session["cart"] = cart
    flash(f"'{product['name']}' added to cart! 🛒", "success")

    # If AJAX request, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "cart_count": get_cart_count()})

    return redirect(request.referrer or url_for("shop"))


@app.route("/buy_now/<int:product_id>", methods=["POST"])
def buy_now(product_id):
    """Directly buy a product by adding to cart and redirecting to checkout."""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("shop"))

    if product["stock"] <= 0:
        flash("Sorry, this product is out of stock.", "warning")
        return redirect(url_for("product_detail", product_id=product_id))

    qty = int(request.form.get("qty", 1))
    
    # "Buy Now" ignores the previous cart and immediately checks out with just this item
    cart = {}
    pid = str(product_id)

    cart[pid] = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "sale_price": product["sale_price"],
            "image": product["image1"],
            "qty": qty,
            "stock": product["stock"]
        }

    if cart[pid]["qty"] > product["stock"]:
        cart[pid]["qty"] = product["stock"]

    session["cart"] = cart
    return redirect(url_for("checkout"))


@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    """Remove a product from the cart."""
    cart = session.get("cart", {})
    pid = str(product_id)
    if pid in cart:
        removed_name = cart[pid]["name"]
        del cart[pid]
        session["cart"] = cart
        flash(f"'{removed_name}' removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
def update_cart():
    """Update quantity of items in cart."""
    cart = session.get("cart", {})
    for pid in cart:
        new_qty = request.form.get(f"qty_{pid}", type=int)
        if new_qty and new_qty > 0:
            cart[pid]["qty"] = min(new_qty, cart[pid]["stock"])
        elif new_qty == 0:
            del cart[pid]
            break  # dict changed size, redirect handles the rest
    session["cart"] = cart
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))


# ══════════════════════════════════════════════
# CHECKOUT & ORDERS
# ══════════════════════════════════════════════

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Checkout page: collect shipping info and place order."""
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("shop"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()
        payment = request.form.get("payment", "COD")

        # Validation
        if not all([name, email, phone, address, city, pincode]):
            flash("Please fill in all shipping details.", "danger")
            return render_template("checkout.html", cart=cart, total=get_cart_total())

        subtotal = get_cart_total()
        delivery_fee = 0 if subtotal >= 999 else 99
        final_total = subtotal + delivery_fee
        db = get_db()

        # Generate Verification Code
        verification_code = ''.join(secrets.choice(string.digits) for _ in range(6))

        # Create order
        cursor = db.execute("""
            INSERT INTO orders (user_id, total, name, email, phone, address, city, pincode, payment_method, verification_code, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (session["user_id"], final_total, name, email, phone, address, city, pincode, payment, verification_code))
        order_id = cursor.lastrowid

        # Create order items & update stock
        for pid, item in cart.items():
            db.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, item["id"], item["name"], item["qty"],
                  item["sale_price"] if item["sale_price"] and item["sale_price"] > 0 else item["price"]))

            # Reduce stock
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["qty"], item["id"])
            )

        db.commit()
        db.close()

        # Send notification
        send_order_notification(phone, verification_code, order_id)

        # Clear cart
        session.pop("cart", None)
        flash("Order placed successfully! 🎉", "success")
        return redirect(url_for("order_success", order_id=order_id))

    return render_template("checkout.html", cart=cart, total=get_cart_total())


@app.route("/order-success/<int:order_id>")
@login_required
def order_success(order_id):
    """Order confirmation page."""
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                       (order_id, session["user_id"])).fetchone()
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?",
                       (order_id,)).fetchall()
    db.close()
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("home"))
    return render_template("order_success.html", order=order, items=items)


# ══════════════════════════════════════════════
# AUTHENTICATION ROUTES
# ══════════════════════════════════════════════

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html")

        # Check if user exists
        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            db.close()
            flash("Username or email already registered.", "danger")
            return render_template("register.html")

        # Create user
        password_hash = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        db.commit()
        db.close()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user.get("role", "user")
            session["is_admin"] = bool(user.get("is_admin", 0))
            
            flash(f"Welcome back, {user['username']}! 🌱", "success")
            if session["role"] in ["super_admin", "sub_admin"] or session["is_admin"]:
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and clear session (keep cart)."""
    cart = session.get("cart", {})
    session.clear()
    session["cart"] = cart  # preserve cart after logout
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ══════════════════════════════════════════════
# PROFILE ROUTE
# ══════════════════════════════════════════════

@app.route("/profile")
@login_required
def profile():
    """User profile with order history."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    orders = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()

    # Get items for each order
    order_details = []
    for order in orders:
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()
        order_details.append({"order": order, "items": items})

    db.close()
    return render_template("profile.html", user=user, order_details=order_details)


# ══════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════

@app.route("/admin")
@app.route("/admin/")
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics."""
    db = get_db()
    stats = {
        "total_products": list(db.execute("SELECT COUNT(*) FROM products").fetchone().values())[0],
        "total_users": list(db.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0").fetchone().values())[0],
        "total_orders": list(db.execute("SELECT COUNT(*) FROM orders").fetchone().values())[0],
        "total_revenue": list(db.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'Cancelled'").fetchone().values())[0],
        "pending_orders": list(db.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'").fetchone().values())[0],
        "messages": list(db.execute("SELECT COUNT(*) FROM contact_messages").fetchone().values())[0],
    }
    recent_orders = db.execute(
        "SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC LIMIT 5"
    ).fetchall()
    db.close()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)


@app.route("/admin/products")
@admin_required
def admin_products():
    """List all products for admin management."""
    db = get_db()
    products = db.execute(
        "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.created_at DESC"
    ).fetchall()
    db.close()
    return render_template("admin/products.html", products=products)


@app.route("/admin/add-product", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    """Add a new product."""
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()

    if request.method == "POST":
        custom_id = request.form.get("custom_id", "").strip()
        weight = request.form.get("weight", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        sale_price = request.form.get("sale_price", 0, type=float)
        category_id = request.form.get("category_id", type=int)
        stock = request.form.get("stock", 10, type=int)
        featured = 1 if request.form.get("featured") else 0

        if not all([custom_id, name, description, price]):
            flash("Product ID, Name, description, and price are required.", "danger")
            return render_template("admin/add_product.html", categories=categories)

        # Handle image uploads
        image1_name = "default.jpg"
        image2_name = "default.jpg"
        image3_name = "default.jpg"
        
        for k in ["image1", "image2", "image3"]:
            if k in request.files:
                file = request.files[k]
                if file and file.filename and allowed_file(file.filename):
                    fname = secure_filename(file.filename)
                    file.save(os.path.join(config.UPLOAD_FOLDER, fname))
                    if k == "image1": image1_name = fname
                    elif k == "image2": image2_name = fname
                    elif k == "image3": image3_name = fname

        import sqlite3
        try:
            db.execute("""
                INSERT INTO products (custom_id, name, description, price, sale_price, weight, category_id, image1, image2, image3, stock, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (custom_id, name, description, price, sale_price, weight, category_id, image1_name, image2_name, image3_name, stock, featured))
            db.commit()
            db.close()
            flash(f"Product '{name}' added successfully! 🌿", "success")
            return redirect(url_for("admin_products"))
        except sqlite3.IntegrityError:
            db.close()
            flash("Product ID/SKU must be unique.", "danger")
            return render_template("admin/add_product.html", categories=categories)

    db.close()
    return render_template("admin/add_product.html", categories=categories)


@app.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    """Edit an existing product."""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()

    if not product:
        db.close()
        flash("Product not found.", "danger")
        return redirect(url_for("admin_products"))

    if request.method == "POST":
        custom_id = request.form.get("custom_id", "").strip()
        weight = request.form.get("weight", "").strip()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        sale_price = request.form.get("sale_price", 0, type=float)
        category_id = request.form.get("category_id", type=int)
        stock = request.form.get("stock", type=int)
        featured = 1 if request.form.get("featured") else 0

        # Handle image upload (keep old image if no new one)
        image1_name = product["image1"]
        image2_name = product["image2"]
        image3_name = product["image3"]
        
        for k in ["image1", "image2", "image3"]:
            if k in request.files:
                file = request.files[k]
                if file and file.filename and allowed_file(file.filename):
                    fname = secure_filename(file.filename)
                    file.save(os.path.join(config.UPLOAD_FOLDER, fname))
                    if k == "image1": image1_name = fname
                    elif k == "image2": image2_name = fname
                    elif k == "image3": image3_name = fname

        import sqlite3
        try:
            db.execute("""
                UPDATE products SET custom_id=?, name=?, description=?, price=?, sale_price=?, weight=?,
                category_id=?, image1=?, image2=?, image3=?, stock=?, featured=? WHERE id=?
            """, (custom_id, name, description, price, sale_price, weight, category_id, image1_name, image2_name, image3_name, stock, featured, product_id))
            db.commit()
            db.close()
            flash(f"Product '{name}' updated! ✅", "success")
            return redirect(url_for("admin_products"))
        except sqlite3.IntegrityError:
            db.close()
            flash("Product ID/SKU must be unique.", "danger")
            return render_template("admin/add_product.html", product=product, categories=categories, editing=True)

    db.close()
    return render_template("admin/add_product.html", product=product, categories=categories, editing=True)


@app.route("/admin/delete-product/<int:product_id>")
@admin_required
def admin_delete_product(product_id):
    """Delete a product."""
    db = get_db()
    product = db.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash(f"Product '{product['name']}' deleted.", "info")
    db.close()
    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    """View all orders."""
    db = get_db()
    orders = db.execute("""
        SELECT o.*, u.username FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """).fetchall()

    order_details = []
    for order in orders:
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()
        order_details.append({"order": order, "items": items})

    delivery_boys = db.execute("SELECT * FROM delivery_boys WHERE is_active = True").fetchall()

    db.close()
    return render_template("admin/orders.html", order_details=order_details, delivery_boys=delivery_boys)


@app.route("/admin/order-status/<int:order_id>", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    """Update order status."""
    new_status = request.form.get("status", "Pending")
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    db.commit()
    db.close()
    flash(f"Order #{order_id} status updated to '{new_status}'.", "success")
    return redirect(url_for("admin_orders"))


# ══════════════════════════════════════════════
# DELIVERY BOY & SUB-ADMIN MANAGEMENT (ADMIN)
# ══════════════════════════════════════════════

@app.route("/admin/sub_admins", methods=["GET", "POST"])
@super_admin_required
def admin_sub_admins():
    """Super Admin route to manage Sub Admins."""
    db = get_db()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if username and password:
            password_hash = generate_password_hash(password)
            try:
                db.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'sub_admin')",
                    (username, email, password_hash)
                )
                db.commit()
                flash("Sub Admin added successfully.", "success")
            except Exception:
                flash("Error adding Sub Admin. Make sure email/username is unique.", "danger")
        return redirect(url_for("admin_sub_admins"))

    sub_admins = db.execute("SELECT * FROM users WHERE role = 'sub_admin'").fetchall()
    db.close()
    return render_template("admin/sub_admins.html", sub_admins=sub_admins)

@app.route("/admin/sub_admins/delete/<int:user_id>", methods=["POST"])
@super_admin_required
def admin_delete_sub_admin(user_id):
    """Super Admin route to delete a Sub Admin."""
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ? AND role = 'sub_admin'", (user_id,))
    db.commit()
    db.close()
    flash("Sub Admin deleted successfully.", "info")
    return redirect(url_for("admin_sub_admins"))


@app.route("/admin/delivery_boys", methods=["GET", "POST"])
@admin_required
def admin_delivery_boys():
    """Admin route to manage Delivery Boys."""
    db = get_db()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()
        zone = request.form.get("zone", "").strip()
        if username and password:
            password_hash = generate_password_hash(password)
            try:
                db.execute(
                    "INSERT INTO delivery_boys (username, password_hash, phone, zone) VALUES (?, ?, ?, ?)",
                    (username, password_hash, phone, zone)
                )
                db.commit()
                flash("Delivery boy added successfully.", "success")
            except Exception:
                flash("Error adding Delivery boy.", "danger")
        return redirect(url_for("admin_delivery_boys"))

    delivery_boys = db.execute("SELECT * FROM delivery_boys").fetchall()
    db.close()
    return render_template("admin/delivery_boys.html", delivery_boys=delivery_boys)

@app.route("/admin/delivery_boys/delete/<int:boy_id>", methods=["POST"])
@admin_required
def admin_delete_delivery_boy(boy_id):
    """Admin route to delete a delivery boy."""
    db = get_db()
    # Safely detach assigned orders before deleting
    db.execute("UPDATE orders SET delivery_boy_id = NULL, delivery_status = 'Pending' WHERE delivery_boy_id = ? AND status != 'Delivered'", (boy_id,))
    db.execute("DELETE FROM delivery_boys WHERE id = ?", (boy_id,))
    db.commit()
    db.close()
    flash("Delivery Boy deleted successfully.", "info")
    return redirect(url_for("admin_delivery_boys"))
@app.route("/admin/assign-order/<int:order_id>", methods=["POST"])
@admin_required
def admin_assign_order(order_id):
    """Assign an order to a delivery boy."""
    delivery_boy_id = request.form.get("delivery_boy_id")
    if not delivery_boy_id:
        delivery_boy_id = None
        delivery_status = 'Pending'
    else:
        delivery_status = 'Assigned'
        
    db = get_db()
    db.execute("UPDATE orders SET delivery_boy_id = ?, delivery_status = ? WHERE id = ?", (delivery_boy_id, delivery_status, order_id))
    db.commit()
    db.close()
    flash(f"Order #{order_id} assignment updated successfully.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/ads", methods=["GET", "POST"])
@admin_required
def admin_ads():
    """Admin route to manage Footer Ads."""
    db = get_db()
    if request.method == "POST":
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                file.save(os.path.join(config.UPLOAD_FOLDER, fname))
                db.execute("INSERT INTO footer_ads (image_name) VALUES (?)", (fname,))
                db.commit()
                flash("Ad image uploaded successfully.", "success")
            else:
                flash("Invalid or missing image file.", "danger")
        return redirect(url_for("admin_ads"))

    ads = db.execute("SELECT * FROM footer_ads ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template("admin/ads.html", ads=ads)

@app.route("/admin/ads/delete/<int:ad_id>", methods=["POST"])
@admin_required
def admin_delete_ad(ad_id):
    """Admin route to delete a footer ad."""
    db = get_db()
    db.execute("DELETE FROM footer_ads WHERE id = ?", (ad_id,))
    db.commit()
    db.close()
    flash("Footer Ad deleted successfully.", "info")
    return redirect(url_for("admin_ads"))


# ══════════════════════════════════════════════
# DELIVERY BOY PORTAL
# ══════════════════════════════════════════════

@app.route("/delivery/login", methods=["GET", "POST"])
def delivery_login():
    """Delivery boy login portal."""
    if "delivery_boy_id" in session:
        return redirect(url_for("delivery_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        boy = db.execute("SELECT * FROM delivery_boys WHERE username = ?", (username,)).fetchone()
        db.close()

        if boy and check_password_hash(boy["password_hash"], password) and boy["is_active"]:
            session["delivery_boy_id"] = boy["id"]
            session["delivery_boy_username"] = boy["username"]
            flash("Logged in to delivery portal.", "success")
            return redirect(url_for("delivery_dashboard"))
        else:
            flash("Invalid credentials or inactive account.", "danger")

    return render_template("delivery_login.html")


@app.route("/delivery/dashboard")
@delivery_required
def delivery_dashboard():
    """Delivery boy dashboard returning all assigned pending orders."""
    db = get_db()
    orders = db.execute("""
        SELECT o.*, u.username 
        FROM orders o 
        JOIN users u ON o.user_id = u.id 
        WHERE o.delivery_boy_id = ? AND o.delivery_status != 'Delivered'
        ORDER BY o.created_at ASC
    """, (session["delivery_boy_id"],)).fetchall()
    
    order_details = []
    for order in orders:
        items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
        order_details.append({"order": order, "items": items})
    db.close()
    
    return render_template("delivery_dashboard.html", orders=order_details)

@app.route("/delivery/verify/<int:order_id>", methods=["POST"])
@delivery_required
def delivery_verify(order_id):
    """Delivery Boy marks an order as Delivered by inputting correct OTP."""
    otp = request.form.get("verification_code", "").strip()
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND delivery_boy_id = ?", (order_id, session["delivery_boy_id"])).fetchone()
    
    if order and order["verification_code"] == otp:
        db.execute("UPDATE orders SET delivery_status = 'Delivered', status = 'Delivered' WHERE id = ?", (order_id,))
        db.commit()
        flash(f"Order #{order_id} verified and marked as Delivered! ✅", "success")
    else:
        flash("Invalid Verification Code! Delivery NOT marked as complete.", "danger")
        
    db.close()
    return redirect(url_for("delivery_dashboard"))

@app.route("/delivery/logout")
def delivery_logout():
    session.pop("delivery_boy_id", None)
    session.pop("delivery_boy_username", None)
    flash("Logged out of delivery portal.", "info")
    return redirect(url_for("delivery_login"))

# ══════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", error_code=404, error_msg="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("base.html", error_code=500, error_msg="Internal server error"), 500


# ══════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', debug=debug_mode, port=5000)

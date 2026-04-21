from app import app
from models import get_db
from werkzeug.security import generate_password_hash

with app.app_context():
    db = get_db()
    username = "akash"
    password = "Akash@7408956686@"
    email = "akash.git6@gmial.com"
    pwd_hash = generate_password_hash(password)
    
    # Check if user exists
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        db.execute("UPDATE users SET password_hash = ?, email = ?, role = 'super_admin', is_admin = 1 WHERE username = ?", (pwd_hash, email, username))
    else:
        db.execute("INSERT INTO users (username, email, password_hash, role, is_admin) VALUES (?, ?, ?, 'super_admin', 1)", (username, email, pwd_hash))
    
    db.commit()
    db.close()
    print("Super Admin 'akash' successfully configured!")

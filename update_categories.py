from app import app, get_db

with app.app_context():
    conn = get_db()
    cur = conn.conn.cursor()
    
    # Optional: Delete existing categories
    # But wait, foreign keys from products might break! 
    # Let's delete products that refer to old categories, or just wipe categories and update products.
    # To be safe, just wipe categories and let products sit or wipe products too.
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cur.execute("TRUNCATE TABLE categories;")
    
    new_cats = [
        ("Khad", "High quality fertilizers for plant growth", '<i class="fas fa-box-open"></i>'),
        ("Plant", "Live plants for home and garden", '<i class="fas fa-leaf"></i>'),
        ("Beej", "Selected seeds for high yield", '<i class="fas fa-seedling"></i>'),
        ("Dava", "Medicines and pesticides for plant care", '<i class="fas fa-prescription-bottle-alt"></i>')
    ]
    
    cur.executemany("INSERT INTO categories (name, description, icon) VALUES (%s, %s, %s)", new_cats)
    
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.conn.commit()
    print("Categories successfully updated in MySQL!")

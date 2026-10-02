# 🌱 KisanCart — Plants & Fertilizers E-Commerce Website

<p align="center">
  <b>A full-featured e-commerce web application for buying plants, fertilizers, seeds and plant-care products.</b>
</p>

<p align="center">
  <a href="https://kishancart.onrender.com">🚀 Live Demo</a> •
  <a href="https://github.com/akash705225/kishancart">💻 GitHub Repository</a>
</p>

---

## 📌 About The Project

**KisanCart** is a full-stack e-commerce website developed using **Python Flask** that allows users to browse and purchase plants, fertilizers, seeds and other plant-care products online.

The application provides a complete shopping workflow including:

* User registration and login
* Product browsing and searching
* Product categories and filtering
* Product details
* Add to Cart
* Buy Now
* Checkout
* Order placement
* Order tracking/status
* Delivery management
* Admin product management
* Admin order management
* User profile and order history

The project is deployed online using **Render**.

### 🌐 Live Website

👉 **https://kishancart.onrender.com**

---

# ✨ Features

## 👤 User Features

* User registration
* User login/logout
* Secure password hashing
* User profile
* Saved contact information
* View previous orders
* Search products
* Browse products by category
* Sort products
* View product details

---

## 🛒 Shopping Features

* Add products to cart
* Update product quantity
* Remove products from cart
* Cart item count
* Automatic cart total calculation
* Stock validation
* Sale price support
* **Buy Now** functionality
* Checkout system

---

## 🌱 Product Categories

KisanCart supports different types of agriculture and plant-care products, including:

* 🌿 Plants
* 🧪 Fertilizers / Khad
* 🌾 Seeds / Beej
* 💊 Plant medicines / pesticides

Products contain information such as:

* Product name
* Description
* Price
* Sale price
* Weight
* Category
* Stock
* Product images
* Rating
* Featured status

---

# 📦 Order & Delivery System

The website includes an order management workflow.

### Customer

```text
Browse Product
      ↓
Add to Cart / Buy Now
      ↓
Checkout
      ↓
Place Order
      ↓
Order Confirmation
      ↓
Order Status
      ↓
Delivery
```

### Delivery Management

The application contains a delivery-agent/delivery-boy system for handling deliveries and order delivery status.

Orders can maintain information such as:

* Customer details
* Delivery address
* Phone number
* City
* Pincode
* Payment method
* Order status
* Delivery status
* Verification code
* Assigned delivery person

---

# 👨‍💼 Admin Panel

The admin side provides management functionality for the e-commerce platform.

### Admin can:

* View dashboard
* Add products
* Edit products
* Delete products
* Manage product categories
* Manage stock
* View orders
* Update order status
* Manage delivery-related information
* Manage users/admin roles

The application also supports different administrative roles such as **Super Admin and Sub Admin**.

---

# 🔍 Search & Filtering

Users can search products and filter the shop based on categories.

Products can also be sorted by:

* Newest
* Price — Low to High
* Price — High to Low
* Name
* Rating

---

# 🗄️ Database

KisanCart uses **MySQL** for storing application data.

Main database entities include:

```text
Users
  │
  ├── Orders
  │      │
  │      └── Order Items
  │
Categories
  │
  └── Products

Delivery Boys
Contact Messages
Footer Ads
```

### Main Tables

* `users`
* `categories`
* `products`
* `orders`
* `order_items`
* `delivery_boys`
* `contact_messages`
* `footer_ads`

---

# 🛠️ Technology Stack

## Backend

* 🐍 Python
* Flask
* Flask-MySQLdb
* PyMySQL

## Frontend

* HTML5
* CSS3
* JavaScript
* Jinja2 Templates

## Database

* MySQL

## Security

* Werkzeug password hashing
* Session-based authentication
* Role-based access control

## Deployment

* Render
* Gunicorn

## Development Tools

* Git
* GitHub
* VS Code

---

# 📁 Project Structure

```text
kishancart/
│
├── app.py
├── models.py
├── config.py
├── set_admin.py
├── update_categories.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
└── templates/
    ├── index.html
    ├── shop.html
    ├── product_detail.html
    ├── cart.html
    ├── checkout.html
    ├── login.html
    ├── register.html
    ├── profile.html
    ├── about.html
    ├── contact.html
    └── admin/
```

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/akash705225/kishancart.git
```

```bash
cd kishancart
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your_secret_key

MYSQL_HOST=your_mysql_host
MYSQL_PORT=4000
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=your_database_name
```

> ⚠️ Never upload your real `.env` file, database password, API keys or other secrets to GitHub.

---

## 5. Run the Application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# 🚀 Deployment

The project is deployed on **Render**.

### Live Application

🌐 https://kishancart.onrender.com

For production deployment, the project uses **Gunicorn**.

Example:

```bash
gunicorn app:app
```

---

# 🔐 Security

The project implements:

* Password hashing
* Login authentication
* Session management
* Admin authorization
* Super-admin authorization
* Delivery-agent authorization
* Secure file handling
* Environment variables for database configuration

---

# 📊 Application Workflow

```text
                  KisanCart
                      │
          ┌───────────┴───────────┐
          │                       │
       Customer                  Admin
          │                       │
     Browse Products         Manage Products
          │                       │
     Search / Filter         Manage Orders
          │                       │
     Product Details        Manage Delivery
          │
     Add to Cart
          │
       Buy Now
          │
       Checkout
          │
     Place Order
          │
    Order Tracking
          │
       Delivery
```

---

# 🎯 Project Objectives

The main objectives of KisanCart are:

1. Build a complete e-commerce platform using Python Flask.
2. Provide an easy way to purchase plants and plant-care products online.
3. Implement product and inventory management.
4. Implement shopping cart and checkout functionality.
5. Implement order management and delivery workflow.
6. Use MySQL for persistent application data.
7. Deploy the application as a live web application.

---

# 💡 What I Learned

Through this project, I worked with:

* Flask web development
* Python backend development
* MySQL database integration
* CRUD operations
* Authentication and authorization
* Password hashing
* Session management
* E-commerce workflows
* Shopping cart implementation
* Order management
* Admin dashboards
* File uploads
* Environment variables
* Git & GitHub
* Cloud deployment

---

# 🔮 Future Improvements

Possible future improvements include:

* Online payment gateway integration
* Email/SMS order notifications
* WhatsApp notifications
* Advanced product recommendations
* AI-based plant/product recommendations
* Weather-based farming recommendations
* Real-time delivery tracking
* Customer reviews and ratings
* Sales analytics dashboard
* Mobile application

---

# 👨‍💻 Developer

**Akash Kumar**

Aspiring Data Scientist | Machine Learning & Python | NLP | Analytics | GenAI

### GitHub

https://github.com/akash705225

### Project

https://github.com/akash705225/kishancart

### Live Demo

https://kishancart.onrender.com

---

## ⭐ If you like this project

Give the repository a ⭐ on GitHub and feel free to explore the project.

---

**Built with Python, Flask, MySQL and ❤️**

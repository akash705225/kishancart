"""
KisanCard - Configuration Settings
Defines database, secret key, and upload paths.
"""
import os

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "kisancard_secret_2026")
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# SQLite database path
DATABASE = os.path.join(BASE_DIR, "kisancard.db")

# Upload folder for product images
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images", "plants")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload

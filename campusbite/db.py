import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    student_id TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS food_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    image_url TEXT NOT NULL DEFAULT '',
    available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0, 1)),
    popular_score INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_key TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    food_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
    UNIQUE(cart_key, food_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'confirmed',
    total REAL NOT NULL CHECK(total >= 0),
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    eta_minutes INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    food_id INTEGER REFERENCES food_items(id) ON DELETE SET NULL,
    item_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0)
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    method TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    transaction_ref TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id INTEGER REFERENCES food_items(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    feedback_type TEXT NOT NULL DEFAULT 'review',
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cart_key ON cart(cart_key);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);
"""

SEED_FOODS = [
    ("Veg Burger", "Crispy veggie patty, fresh lettuce and house sauce.", "Fast Food", 40, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85", 96),
    ("Chicken Burger", "Juicy grilled chicken with a toasted sesame bun.", "Fast Food", 60, "https://images.unsplash.com/photo-1571091718767-18b5b1457add?auto=format&fit=crop&w=900&q=85", 88),
    ("Veg Sandwich", "Grilled garden vegetables, mint chutney and cheese.", "Breakfast", 35, "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=85", 76),
    ("Samosa", "Golden, flaky pastry with a spiced potato filling.", "Snacks", 15, "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=85", 100),
    ("Maggi", "A warm, quick noodle bowl with a campus-style masala twist.", "Snacks", 30, "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=900&q=85", 92),
    ("Tea", "Freshly brewed chai, served hot.", "Beverages", 10, "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&w=900&q=85", 99),
    ("Coffee", "Rich, aromatic coffee for your next study break.", "Beverages", 20, "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=85", 81),
    ("Cold Coffee", "Chilled creamy coffee topped with a light froth.", "Beverages", 40, "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85", 84),
    ("Veg Fried Rice", "Wok-tossed rice with crunchy seasonal vegetables.", "Lunch", 60, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=85", 90),
    ("Paneer Roll", "Soft paneer tikka wrapped with onions and chutney.", "Fast Food", 50, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=900&q=85", 87),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM food_items").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO food_items(name, description, category, price, image_url, popular_score) VALUES (?, ?, ?, ?, ?, ?)",
            SEED_FOODS,
        )
    if db.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
        db.execute(
            "INSERT INTO admins(name, email, password_hash) VALUES (?, ?, ?)",
            (
                os.environ.get("CAMPUSBITE_ADMIN_NAME", "Canteen Admin"),
                os.environ.get("CAMPUSBITE_ADMIN_EMAIL", "admin@campusbite.local"),
                generate_password_hash(os.environ.get("CAMPUSBITE_ADMIN_PASSWORD", "CampusBite@2026")),
            ),
        )
    db.commit()

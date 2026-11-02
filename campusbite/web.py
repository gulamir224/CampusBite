import secrets
from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

web = Blueprint("web", __name__)
CATEGORIES = ["Breakfast", "Lunch", "Snacks", "Beverages", "Fast Food"]
ORDER_STATUSES = {
    "confirmed": "Order confirmed",
    "preparing": "Preparing",
    "ready": "Ready for pickup",
    "completed": "Completed",
}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Sign in to continue with your order.", "info")
            return redirect(url_for("web.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("web.admin_login"))
        return view(*args, **kwargs)
    return wrapped


def cart_key():
    if not session.get("cart_key"):
        session["cart_key"] = secrets.token_urlsafe(24)
    return session["cart_key"]


def get_cart():
    return get_db().execute(
        """SELECT c.id, c.food_id, c.quantity, f.name, f.description, f.category,
                  f.price, f.image_url, f.available, f.popular_score,
                  c.quantity * f.price AS line_total
           FROM cart c JOIN food_items f ON f.id = c.food_id
           WHERE c.cart_key = ? ORDER BY f.name""",
        (cart_key(),),
    ).fetchall()


def cart_total(items=None):
    return sum(row["line_total"] for row in (items if items is not None else get_cart()))


def attach_cart(user_id):
    get_db().execute("UPDATE cart SET user_id = ? WHERE cart_key = ?", (user_id, cart_key()))
    get_db().commit()


def safe_next(value):
    return value if value and value.startswith("/") and not value.startswith("//") else url_for("web.menu")


def fetch_order(order_id):
    order = get_db().execute(
        """SELECT o.*, u.full_name, u.email FROM orders o JOIN users u ON u.id = o.user_id
           WHERE o.id = ? AND o.user_id = ?""",
        (order_id, session.get("user_id")),
    ).fetchone()
    if order is None:
        abort(404)
    items = get_db().execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return order, items


def recommendation_items(user_id=None, category=None, limit=4):
    db = get_db()
    if user_id:
        history_sql = """SELECT f.*, COUNT(oi.id) AS history_count
                         FROM food_items f JOIN order_items oi ON oi.food_id = f.id
                         JOIN orders o ON o.id = oi.order_id
                         WHERE o.user_id = ? AND f.available = 1"""
        history_values = [user_id]
        if category:
            history_sql += " AND f.category = ?"
            history_values.append(category)
        history_sql += " GROUP BY f.id ORDER BY history_count DESC, f.popular_score DESC LIMIT ?"
        history_values.append(limit)
        rows = db.execute(
            history_sql,
            history_values,
        ).fetchall()
        if len(rows) >= limit:
            return rows
        used = [row["id"] for row in rows]
        clauses = ["available = 1"]
        values = []
        if category:
            clauses.append("category = ?")
            values.append(category)
        if used:
            clauses.append(f"id NOT IN ({','.join('?' for _ in used)})")
            values.extend(used)
        values.append(limit - len(rows))
        extra = db.execute(
            f"SELECT * FROM food_items WHERE {' AND '.join(clauses)} ORDER BY popular_score DESC LIMIT ?",
            values,
        ).fetchall()
        return list(rows) + list(extra)
    if category:
        rows = db.execute(
            "SELECT * FROM food_items WHERE available = 1 AND category = ? ORDER BY popular_score DESC LIMIT ?",
            (category, limit),
        ).fetchall()
        if rows:
            return rows
    return db.execute(
        "SELECT * FROM food_items WHERE available = 1 ORDER BY popular_score DESC LIMIT ?", (limit,)
    ).fetchall()


@web.app_context_processor
def inject_cart_count():
    count = 0
    if session.get("cart_key"):
        row = get_db().execute("SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE cart_key = ?", (session["cart_key"],)).fetchone()
        count = row[0]
    return {"cart_count": count, "categories": CATEGORIES, "order_statuses": ORDER_STATUSES}


@web.route("/")
def home():
    db = get_db()
    specials = db.execute("SELECT * FROM food_items WHERE available = 1 ORDER BY popular_score DESC LIMIT 3").fetchall()
    return render_template(
        "index.html",
        specials=specials,
        recommendations=recommendation_items(session.get("user_id"), limit=4),
        open_now=8 <= datetime.now().hour < 17,
    )


@web.route("/menu")
def menu():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    clauses, values = [], []
    if search:
        clauses.append("(name LIKE ? OR description LIKE ?)")
        values.extend([f"%{search}%", f"%{search}%"])
    if category in CATEGORIES:
        clauses.append("category = ?")
        values.append(category)
    sql = "SELECT * FROM food_items"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY available DESC, popular_score DESC, name"
    items = get_db().execute(sql, values).fetchall()
    return render_template(
        "menu.html",
        items=items,
        search=search,
        selected_category=category,
        suggestions=recommendation_items(session.get("user_id"), category=category, limit=3),
    )


@web.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")
        if not name or "@" not in email or not student_id or len(password) < 8:
            flash("Enter your name, a valid college email, student ID, and a password of at least 8 characters.", "error")
        else:
            db = get_db()
            try:
                cursor = db.execute(
                    "INSERT INTO users(full_name, email, student_id, password_hash) VALUES (?, ?, ?, ?)",
                    (name, email, student_id, generate_password_hash(password)),
                )
                db.commit()
                existing_cart_key = session.get("cart_key")
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["cart_key"] = existing_cart_key or secrets.token_urlsafe(24)
                attach_cart(cursor.lastrowid)
                flash("Welcome to CampusBite! Your student account is ready.", "success")
                return redirect(url_for("web.menu"))
            except Exception as error:
                db.rollback()
                if "UNIQUE constraint failed" in str(error):
                    flash("That email or student ID is already registered.", "error")
                else:
                    raise
    return render_template("register.html")


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email or password didn't match. Try again.", "error")
        else:
            existing_cart_key = session.get("cart_key")
            session.clear()
            if existing_cart_key:
                session["cart_key"] = existing_cart_key
            session["user_id"] = user["id"]
            attach_cart(user["id"])
            flash(f"Good to see you, {user['full_name'].split()[0]}!", "success")
            return redirect(safe_next(request.args.get("next") or request.form.get("next")))
    return render_template("login.html", next_url=request.args.get("next", ""))


@web.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("admin_id", None)
    flash("You've been signed out.", "success")
    return redirect(url_for("web.home"))


@web.route("/profile")
@login_required
def profile():
    user = get_db().execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    count = get_db().execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
    return render_template("profile.html", user=user, order_count=count)


@web.route("/cart")
def cart():
    items = get_cart()
    return render_template("cart.html", items=items, subtotal=cart_total(items))


@web.route("/cart/add/<int:food_id>", methods=["POST"])
def add_to_cart(food_id):
    db = get_db()
    food = db.execute("SELECT id, name, available FROM food_items WHERE id = ?", (food_id,)).fetchone()
    if not food:
        abort(404)
    if not food["available"]:
        flash("That item is currently unavailable.", "error")
    else:
        key = cart_key()
        db.execute(
            """INSERT INTO cart(cart_key, user_id, food_id, quantity) VALUES (?, ?, ?, 1)
               ON CONFLICT(cart_key, food_id) DO UPDATE SET quantity = quantity + 1""",
            (key, session.get("user_id"), food_id),
        )
        db.commit()
        flash(f"{food['name']} added to your cart.", "success")
    return redirect(request.referrer or url_for("web.menu"))


@web.route("/cart/update/<int:food_id>", methods=["POST"])
def update_cart(food_id):
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 1
    db = get_db()
    if quantity <= 0:
        db.execute("DELETE FROM cart WHERE cart_key = ? AND food_id = ?", (cart_key(), food_id))
    else:
        db.execute("UPDATE cart SET quantity = ? WHERE cart_key = ? AND food_id = ?", (min(quantity, 99), cart_key(), food_id))
    db.commit()
    flash("Cart updated.", "success")
    return redirect(url_for("web.cart"))


@web.route("/cart/remove/<int:food_id>", methods=["POST"])
def remove_from_cart(food_id):
    db = get_db()
    db.execute("DELETE FROM cart WHERE cart_key = ? AND food_id = ?", (cart_key(), food_id))
    db.commit()
    flash("Item removed from your cart.", "info")
    return redirect(url_for("web.cart"))


@web.route("/cart/clear", methods=["POST"])
def clear_cart():
    get_db().execute("DELETE FROM cart WHERE cart_key = ?", (cart_key(),))
    get_db().commit()
    flash("Your cart is cleared.", "info")
    return redirect(url_for("web.cart"))


@web.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = get_cart()
    if not items:
        flash("Your cart is empty. Add something tasty first.", "info")
        return redirect(url_for("web.menu"))
    if request.method == "POST":
        if any(not item["available"] for item in items):
            flash("One or more items are unavailable. Remove them before checkout.", "error")
            return redirect(url_for("web.cart"))
        method = request.form.get("payment_method")
        if method not in {"cash", "upi"}:
            flash("Choose Cash on pickup or UPI demo payment.", "error")
            return redirect(url_for("web.checkout"))
        db = get_db()
        total = cart_total(items)
        payment_status = "pending" if method == "cash" else "awaiting_demo_payment"
        order_status = "confirmed" if method == "cash" else "payment_pending"
        with db:
            cursor = db.execute(
                """INSERT INTO orders(user_id, token, status, total, payment_method, payment_status, eta_minutes)
                   VALUES (?, '', ?, ?, ?, ?, ?)""",
                (
                    session["user_id"],
                    order_status,
                    total,
                    "Cash on pickup" if method == "cash" else "UPI demo",
                    payment_status,
                    10,
                ),
            )
            order_id = cursor.lastrowid
            token = f"CB{1000 + order_id:04d}"
            db.execute("UPDATE orders SET token = ? WHERE id = ?", (token, order_id))
            for item in items:
                db.execute(
                    "INSERT INTO order_items(order_id, food_id, item_name, unit_price, quantity) VALUES (?, ?, ?, ?, ?)",
                    (order_id, item["food_id"], item["name"], item["price"], item["quantity"]),
                )
            db.execute(
                "INSERT INTO payments(order_id, method, amount, status) VALUES (?, ?, ?, ?)",
                (order_id, "Cash on pickup" if method == "cash" else "UPI demo", total, payment_status),
            )
            db.execute("DELETE FROM cart WHERE cart_key = ?", (cart_key(),))
        if method == "upi":
            return redirect(url_for("web.payment", order_id=order_id))
        flash("Order confirmed. Pay at the canteen pickup counter.", "success")
        return redirect(url_for("web.token", order_id=order_id))
    return render_template("checkout.html", items=items, subtotal=cart_total(items))


@web.route("/payment/<int:order_id>", methods=["GET", "POST"])
@login_required
def payment(order_id):
    order, items = fetch_order(order_id)
    if order["payment_method"] != "UPI demo":
        return redirect(url_for("web.token", order_id=order_id))
    if order["payment_status"] == "paid":
        return redirect(url_for("web.token", order_id=order_id))
    if request.method == "POST":
        reference = f"DEMO-{secrets.token_hex(4).upper()}"
        db = get_db()
        with db:
            db.execute("UPDATE payments SET status = 'paid', transaction_ref = ? WHERE order_id = ?", (reference, order_id))
            db.execute("UPDATE orders SET payment_status = 'paid', status = 'confirmed' WHERE id = ?", (order_id,))
        flash("Demo Payment Successful — no actual money was transferred.", "success")
        return redirect(url_for("web.token", order_id=order_id))
    return render_template("payment.html", order=order, items=items)


@web.route("/token/<int:order_id>")
@login_required
def token(order_id):
    order, items = fetch_order(order_id)
    if order["payment_method"] == "UPI demo" and order["payment_status"] != "paid":
        return redirect(url_for("web.payment", order_id=order_id))
    return render_template("token.html", order=order, items=items)


@web.route("/orders")
@login_required
def orders():
    rows = get_db().execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC, id DESC", (session["user_id"],)
    ).fetchall()
    return render_template("orders.html", orders=rows)


@web.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order, items = fetch_order(order_id)
    return render_template("order_detail.html", order=order, items=items)


@web.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    db = get_db()
    foods = db.execute("SELECT id, name FROM food_items ORDER BY name").fetchall()
    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", "5"))
            food_id = int(request.form["food_id"]) if request.form.get("food_id") else None
        except ValueError:
            rating, food_id = 0, None
        kind = request.form.get("feedback_type", "review")
        comment = request.form.get("comment", "").strip()
        valid_food = not food_id or db.execute("SELECT 1 FROM food_items WHERE id = ?", (food_id,)).fetchone()
        if rating not in range(1, 6) or kind not in {"review", "suggestion"} or not comment or len(comment) > 1000 or not valid_food:
            flash("Choose a 1–5 star rating and add a short comment (up to 1,000 characters).", "error")
        else:
            db.execute(
                "INSERT INTO feedback(user_id, food_id, rating, feedback_type, comment) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], food_id, rating, kind, comment),
            )
            db.commit()
            flash("Thanks! Your feedback has been sent to the canteen team.", "success")
            return redirect(url_for("web.feedback"))
    recent = db.execute(
        """SELECT f.*, food.name AS food_name FROM feedback f LEFT JOIN food_items food ON food.id = f.food_id
           WHERE f.user_id = ? ORDER BY f.created_at DESC LIMIT 5""", (session["user_id"],)
    ).fetchall()
    return render_template("feedback.html", foods=foods, recent=recent)


@web.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = get_db().execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
        if not admin or not check_password_hash(admin["password_hash"], password):
            flash("Admin email or password didn't match.", "error")
        else:
            session.clear()
            session["admin_id"] = admin["id"]
            flash("Admin signed in.", "success")
            return redirect(url_for("web.admin"))
    return render_template("admin_login.html")


@web.route("/admin")
@admin_required
def admin():
    db = get_db()
    stats = {
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "students": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "sales": db.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE payment_status IN ('paid', 'pending')").fetchone()[0],
        "menu": db.execute("SELECT COUNT(*) FROM food_items").fetchone()[0],
    }
    orders = db.execute(
        """SELECT o.*, u.full_name FROM orders o JOIN users u ON u.id = o.user_id
           ORDER BY o.created_at DESC, o.id DESC LIMIT 12"""
    ).fetchall()
    foods = db.execute("SELECT * FROM food_items ORDER BY category, name").fetchall()
    feedback_rows = db.execute(
        """SELECT f.*, u.full_name, food.name AS food_name FROM feedback f
           JOIN users u ON u.id = f.user_id LEFT JOIN food_items food ON food.id = f.food_id
           ORDER BY f.created_at DESC LIMIT 8"""
    ).fetchall()
    return render_template("admin.html", stats=stats, orders=orders, foods=foods, feedback_rows=feedback_rows)


@web.route("/admin/foods", methods=["POST"])
@admin_required
def admin_foods():
    db = get_db()
    action = request.form.get("action", "save")
    try:
        food_id = int(request.form.get("food_id", "0"))
    except ValueError:
        food_id = 0
    if action == "delete":
        db.execute("DELETE FROM food_items WHERE id = ?", (food_id,))
        db.commit()
        flash("Menu item deleted.", "success")
        return redirect(url_for("web.admin") + "#menu")
    if action == "toggle":
        db.execute("UPDATE food_items SET available = CASE available WHEN 1 THEN 0 ELSE 1 END WHERE id = ?", (food_id,))
        db.commit()
        flash("Availability updated.", "success")
        return redirect(url_for("web.admin") + "#menu")
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "")
    image_url = request.form.get("image_url", "").strip()
    try:
        price = float(request.form.get("price", "-1"))
    except ValueError:
        price = -1
    if not name or category not in CATEGORIES or not 0 <= price <= 100000:
        flash("Enter a name, valid category, and price.", "error")
    elif food_id:
        db.execute(
            "UPDATE food_items SET name = ?, description = ?, category = ?, price = ?, image_url = ? WHERE id = ?",
            (name, description, category, price, image_url, food_id),
        )
        db.commit()
        flash("Menu item updated.", "success")
    else:
        db.execute(
            "INSERT INTO food_items(name, description, category, price, image_url) VALUES (?, ?, ?, ?, ?)",
            (name, description, category, price, image_url),
        )
        db.commit()
        flash("New menu item added.", "success")
    return redirect(url_for("web.admin") + "#menu")


@web.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        flash("Choose a valid order status.", "error")
    else:
        get_db().execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        get_db().commit()
        flash("Order status updated.", "success")
    return redirect(url_for("web.admin") + "#orders")


@web.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin signed out.", "success")
    return redirect(url_for("web.admin_login"))

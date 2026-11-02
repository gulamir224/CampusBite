import hmac
import os
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, g, render_template, request, session

from .db import close_db, get_db, init_db
from .web import web


def create_app(test_config=None):
    root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("CAMPUSBITE_SECRET", "campusbite-local-development-key-change-me"),
        DATABASE=os.environ.get("CAMPUSBITE_DATABASE", str(root / "database.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.register_blueprint(web)

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and not app.config.get("TESTING"):
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not sent or not expected or not hmac.compare_digest(sent, expected):
                abort(400, description="Your form expired. Refresh the page and try again.")

    @app.context_processor
    def common_template_values():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        user = None
        admin = None
        if session.get("user_id"):
            user = get_db().execute(
                "SELECT id, full_name, email, student_id FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        if session.get("admin_id"):
            admin = get_db().execute(
                "SELECT id, name, email FROM admins WHERE id = ?", (session["admin_id"],)
            ).fetchone()
        canteen_open = 8 <= datetime.now().hour < 17
        return {
            "csrf_token": session["csrf_token"],
            "current_user": user,
            "current_admin": admin,
            "canteen_open": canteen_open,
        }

    @app.template_filter("inr")
    def inr(value):
        return f"₹{float(value or 0):,.0f}"

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="We couldn't find that page."), 404

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", code=400, message=getattr(error, "description", "Please check your request.")), 400

    with app.app_context():
        init_db()
    return app

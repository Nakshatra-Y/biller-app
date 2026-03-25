from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    abort,
    flash,
)
from werkzeug.security import generate_password_hash

import logging

from database.db import db
from database.models import Business, User, CafeTable

logger = logging.getLogger(__name__)



auth_bp = Blueprint("auth", __name__)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def get_current_business_id():
    return session.get("business_id")


def login_required(role: str | None = None):
    def decorator(view_func):
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.accept_mimetypes.best == "application/json" or request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("auth.login"))
            business_id = get_current_business_id()
            if not business_id:
                session.clear()
                if request.accept_mimetypes.best == "application/json" or request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("auth.login"))
            if role and user.role != role:
                if request.accept_mimetypes.best == "application/json" or request.is_json:
                    return jsonify({"error": "Forbidden"}), 403
                abort(403)
            return view_func(*args, **kwargs)

        wrapped.__name__ = view_func.__name__
        return wrapped

    return decorator


@auth_bp.app_context_processor
def inject_globals():
    return {
        "current_user": get_current_user(),
        "now": datetime.utcnow(),
    }


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json(silent=True) or request.form
    business_name = data.get("business_name", "").strip()
    owner_name = data.get("owner_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not (business_name and owner_name and email and password):
        msg = "All fields are required."
        if request.is_json:
            return jsonify({"error": msg}), 400
        flash(msg, "error")
        return render_template("signup.html"), 400

    existing = Business.query.filter_by(email=email).first()
    if existing:
        msg = "A business with this email already exists."
        if request.is_json:
            return jsonify({"error": msg}), 400
        flash(msg, "error")
        return render_template("signup.html"), 400

    business = Business(name=business_name, email=email)
    db.session.add(business)
    db.session.flush()

    logger.info(f"Registering business {business.name} with email {email}")



    user = User(
        business_id=business.id,
        name=owner_name,
        email=email,
        password_hash=generate_password_hash(password),
        role="admin",
    )
    db.session.add(user)

    default_tables = [CafeTable(business_id=business.id, table_number=str(i)) for i in range(1, 6)]
    db.session.add_all(default_tables)

    try:
        db.session.commit()
        logger.info(f"Successfully registered user and business: {email}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering user {email}: {e}")
        raise

    session["user_id"] = user.id
    session["business_id"] = business.id

    if request.is_json:
        return jsonify({"message": "Signup successful"}), 201
    return redirect(url_for("bills.dashboard"))



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not (email and password):
        msg = "Email and password are required."
        logger.warning("Login failed: Missing email or password.")
        if request.is_json:
            return jsonify({"error": msg}), 400
        flash(msg, "error")
        return render_template("login.html"), 400

    # owner email is stored at business level; staff have their own emails
    user = User.query.filter(User.email == email).first()
    if not user:
        logger.warning(f"Login failed: No user found for email '{email}'.")
        msg = "Invalid credentials."
        if request.is_json:
            return jsonify({"error": msg}), 401
        flash(msg, "error")
        return render_template("login.html"), 401

    if not user.check_password(password):
        logger.warning(f"Login failed: Incorrect password for email '{email}'.")
        msg = "Invalid credentials."
        if request.is_json:
            return jsonify({"error": msg}), 401
        flash(msg, "error")
        return render_template("login.html"), 401

    logger.info(f"User '{email}' logged in successfully.")
    session["user_id"] = user.id
    session["business_id"] = user.business_id

    if request.is_json:
        return jsonify({"message": "Login successful"}), 200
    return redirect(url_for("bills.dashboard"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    if request.is_json:
        return jsonify({"message": "Logged out"}), 200
    return redirect(url_for("auth.login"))


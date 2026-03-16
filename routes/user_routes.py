from flask import Blueprint, render_template, request, flash
from werkzeug.security import generate_password_hash

from database.db import db
from database.models import User
from routes.auth_routes import login_required, get_current_business_id


user_bp = Blueprint("users", __name__)


@user_bp.route("/staff", methods=["GET", "POST"])
@login_required(role="admin")
def staff_management():
    business_id = get_current_business_id()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "staff")
        if not (name and email and password):
            flash("All fields are required", "error")
        else:
            user = User(
                business_id=business_id,
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            flash("User created", "success")
    users = User.query.filter_by(business_id=business_id).all()
    return render_template("staff_management.html", users=users)


import os

from flask import Flask, redirect, url_for

from config import get_config
from database.db import db
from database.models import Business, User  # noqa: F401
from routes.auth_routes import auth_bp
from routes.bill_routes import bill_bp
from routes.menu_routes import menu_bp
from routes.report_routes import report_bp
from routes.user_routes import user_bp
from services.report_service import calculate_daily_report  # noqa: F401


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(get_config())

    # simple upload folder for shop logos/images
    app.config.setdefault("UPLOAD_FOLDER", "static/uploads")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(bill_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(user_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


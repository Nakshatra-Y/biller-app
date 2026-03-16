from flask import Blueprint, jsonify, render_template

from routes.auth_routes import login_required, get_current_business_id
from services.report_service import (
    calculate_daily_report,
    build_analytics_payload,
)


report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/today", methods=["GET"])
@login_required(role="admin")
def reports_today():
    business_id = get_current_business_id()
    report = calculate_daily_report(business_id)
    return jsonify(report)


@report_bp.route("/reports/metrics", methods=["GET"])
@login_required(role="admin")
def reports_metrics():
    business_id = get_current_business_id()
    payload = build_analytics_payload(business_id)
    return jsonify(payload)


@report_bp.route("/reports")
@login_required(role="admin")
def reports_page():
    return render_template("reports.html")


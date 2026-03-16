import os

from flask import Blueprint, jsonify, request, render_template, current_app, flash, redirect, url_for
from werkzeug.utils import secure_filename

from database.db import db
from database.models import Bill, CafeTable, Category, Product, ShopProfile
from routes.auth_routes import login_required, get_current_business_id, get_current_user
from services.billing_service import (
    create_bill as create_bill_service,
    complete_bill as complete_bill_service,
    update_bill as update_bill_service,
)
from services.report_service import calculate_daily_report


bill_bp = Blueprint("bills", __name__)


@bill_bp.route("/bills", methods=["POST"])
@login_required()
def create_bill():
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or request.form
    table_no = data.get("table_no", "").strip()
    items = data.get("items") or []
    gst_rate = float(data.get("gst_rate", 0) or 0)

    if not table_no:
        return jsonify({"error": "Table number is required"}), 400
    if not items:
        return jsonify({"error": "At least one item is required"}), 400

    bill = create_bill_service(business_id, table_no, items, gst_rate=gst_rate)
    return jsonify({"message": "Bill created", "id": bill.id}), 201


@bill_bp.route("/bills", methods=["GET"])
@login_required()
def list_bills():
    business_id = get_current_business_id()
    status = request.args.get("status")
    query = Bill.query.filter_by(business_id=business_id)
    if status:
        query = query.filter_by(status=status.upper())
    bills = query.order_by(Bill.created_at.desc()).all()
    data = [
        {
            "id": b.id,
            "table_no": b.table_no,
            "status": b.status,
            "total": b.total,
            "created_at": b.created_at.isoformat(),
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
        }
        for b in bills
    ]
    return jsonify(data)


@bill_bp.route("/bills/<int:bill_id>", methods=["GET"])
@login_required()
def get_bill(bill_id):
    business_id = get_current_business_id()
    bill = Bill.query.filter_by(id=bill_id, business_id=business_id).first_or_404()
    data = {
        "id": bill.id,
        "table_no": bill.table_no,
        "status": bill.status,
        "total": bill.total,
        "created_at": bill.created_at.isoformat(),
        "completed_at": bill.completed_at.isoformat() if bill.completed_at else None,
        "items": [
            {
                "id": i.id,
                "product_name": i.product_name,
                "price": i.price,
                "quantity": i.quantity,
            }
            for i in bill.items
        ],
    }
    return jsonify(data)


@bill_bp.route("/api/table-status", methods=["GET"])
@login_required()
def api_table_status():
    """Return all tables with current status (available / pending / occupied) for real-time UI."""
    business_id = get_current_business_id()
    tables = CafeTable.query.filter_by(business_id=business_id).all()
    pending_bills = {
        r[0]: r[1]
        for r in db.session.query(Bill.table_no, Bill.id).filter_by(
            business_id=business_id, status="PENDING"
        ).all()
    }
    out = []
    for t in tables:
        if t.table_number in pending_bills:
            status = "pending"
            pending_bill_id = pending_bills[t.table_number]
        else:
            status = "available"
            pending_bill_id = None
            
        out.append({
            "id": t.id,
            "table_number": t.table_number,
            "status": status,
            "pending_bill_id": pending_bill_id,
        })
    return jsonify({"tables": out})


@bill_bp.route("/api/bills/by-table/<table_no>", methods=["GET"])
@login_required()
def api_bill_by_table(table_no):
    """Return the pending bill for the given table number, if any."""
    business_id = get_current_business_id()
    bill = (
        Bill.query.filter_by(
            business_id=business_id,
            table_no=table_no,
            status="PENDING",
        )
        .order_by(Bill.created_at.desc())
        .first()
    )
    if not bill:
        return jsonify({"error": "No pending bill for this table"}), 404
    return jsonify({
        "id": bill.id,
        "table_no": bill.table_no,
        "status": bill.status,
        "total": bill.total,
        "created_at": bill.created_at.isoformat(),
        "items": [
            {"id": i.id, "product_name": i.product_name, "price": i.price, "quantity": i.quantity}
            for i in bill.items
        ],
    })


@bill_bp.route("/api/tables/<int:table_id>", methods=["PUT"])
@login_required()
def api_update_table(table_id):
    """Update table number for the given table."""
    business_id = get_current_business_id()
    table = CafeTable.query.filter_by(id=table_id, business_id=business_id).first_or_404()
    data = request.get_json(silent=True) or request.form
    new_number = (data.get("table_number") or data.get("table_no") or "").strip()
    if not new_number:
        return jsonify({"error": "Table number is required"}), 400
    existing = CafeTable.query.filter_by(
        business_id=business_id, table_number=new_number
    ).first()
    if existing and existing.id != table_id:
        return jsonify({"error": "Table number already in use"}), 400
    table.table_number = new_number
    db.session.commit()
    return jsonify({"id": table.id, "table_number": table.table_number})


@bill_bp.route("/api/tables", methods=["POST"])
@login_required()
def api_add_table():
    """Add a new table for the current business."""
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or request.form
    table_number = (data.get("table_number") or data.get("table_no") or "").strip()
    if not table_number:
        return jsonify({"error": "Table number is required"}), 400
    existing = CafeTable.query.filter_by(
        business_id=business_id, table_number=table_number
    ).first()
    if existing:
        return jsonify({"error": "Table already exists"}), 400
    table = CafeTable(business_id=business_id, table_number=table_number)
    db.session.add(table)
    db.session.commit()
    return jsonify({"id": table.id, "table_number": table.table_number}), 201


@bill_bp.route("/bills/<int:bill_id>/complete", methods=["PUT"])
@login_required()
def complete_bill(bill_id):
    business_id = get_current_business_id()
    bill = Bill.query.filter_by(id=bill_id, business_id=business_id).first_or_404()
    complete_bill_service(bill)
    return jsonify({"message": "Bill completed"})


@bill_bp.route("/bills/<int:bill_id>", methods=["PUT"])
@login_required()
def update_bill(bill_id):
    business_id = get_current_business_id()
    user = get_current_user()
    bill = Bill.query.filter_by(id=bill_id, business_id=business_id).first_or_404()
    if bill.status == "COMPLETED" and user.role != "admin":
        return jsonify({"error": "Only admin can edit completed bills"}), 403
    data = request.get_json(silent=True) or request.form
    items = data.get("items") or []
    gst_rate = float(data.get("gst_rate", 0) or 0)
    if not items:
        return jsonify({"error": "At least one item is required"}), 400
    update_bill_service(bill, items, gst_rate=gst_rate)
    return jsonify({"message": "Bill updated", "total": bill.total})


@bill_bp.route("/bills/<int:bill_id>/receipt")
@login_required()
def bill_receipt(bill_id):
    business_id = get_current_business_id()
    user = get_current_user()
    bill = Bill.query.filter_by(id=bill_id, business_id=business_id).first_or_404()
    profile = ShopProfile.query.filter_by(user_id=user.id).first()
    shop_name = (profile and profile.shop_name) or (user.business and user.business.name) or "Cafe"
    address = (profile and profile.address) or ""
    subtotal = sum(i.price * i.quantity for i in bill.items)
    tax = bill.total - subtotal
    return render_template(
        "receipt.html",
        bill=bill,
        shop_name=shop_name,
        address=address,
        subtotal=subtotal,
        tax=tax,
    )


# POS pages


@bill_bp.route("/dashboard", methods=["GET", "POST"])
@login_required()
def dashboard():
    business_id = get_current_business_id()
    user = get_current_user()
    profile = ShopProfile.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        if user.role != "admin":
            flash("Only admins can edit shop profile.", "error")
            return redirect(url_for("bills.dashboard"))

        if not profile:
            profile = ShopProfile(user_id=user.id)

        profile.shop_name = request.form.get("shop_name") or profile.shop_name
        profile.owner_name = request.form.get("owner_name") or profile.owner_name
        profile.email = request.form.get("email") or profile.email
        profile.phone = request.form.get("phone") or profile.phone
        profile.address = request.form.get("address") or profile.address

        upload_folder = os.path.join(current_app.root_path, current_app.config["UPLOAD_FOLDER"])
        os.makedirs(upload_folder, exist_ok=True)

        logo_file = request.files.get("shop_logo")
        if logo_file and logo_file.filename:
            logo_name = secure_filename(logo_file.filename)
            logo_path = os.path.join(upload_folder, logo_name)
            logo_file.save(logo_path)
            profile.shop_logo = os.path.join(current_app.config["UPLOAD_FOLDER"], logo_name)

        images_files = request.files.getlist("shop_images")
        image_paths = []
        for f in images_files:
            if f and f.filename:
                fname = secure_filename(f.filename)
                fpath = os.path.join(upload_folder, fname)
                f.save(fpath)
                image_paths.append(os.path.join(current_app.config["UPLOAD_FOLDER"], fname))
        if image_paths:
            existing = profile.shop_images.split(",") if profile.shop_images else []
            profile.shop_images = ",".join(existing + image_paths)

        db.session.add(profile)
        db.session.commit()
        flash("Shop profile updated.", "success")
        return redirect(url_for("bills.dashboard"))

    pending_count = Bill.query.filter_by(business_id=business_id, status="PENDING").count()
    completed_count = Bill.query.filter_by(business_id=business_id, status="COMPLETED").count()
    today_report = calculate_daily_report(business_id)
    return render_template(
        "dashboard.html",
        pending_count=pending_count,
        completed_count=completed_count,
        today_report=today_report,
        profile=profile,
    )


@bill_bp.route("/create-bill")
@login_required()
def create_bill_page():
    business_id = get_current_business_id()
    tables = CafeTable.query.filter_by(business_id=business_id).all()
    categories = Category.query.filter_by(business_id=business_id).all()
    products = Product.query.filter_by(business_id=business_id).all()

    # compute table statuses
    pending = (
        db.session.query(Bill.table_no)
        .filter_by(business_id=business_id, status="PENDING")
        .all()
    )
    completed = (
        db.session.query(Bill.table_no)
        .filter_by(business_id=business_id, status="COMPLETED")
        .all()
    )
    pending_tables = {t[0] for t in pending}
    completed_tables = {t[0] for t in completed}
    table_statuses = {}
    for t in tables:
        if t.table_number in pending_tables:
            table_statuses[t.table_number] = "pending"
        elif t.table_number in completed_tables:
            table_statuses[t.table_number] = "occupied"
        else:
            table_statuses[t.table_number] = "available"
    return render_template(
        "create_bill.html",
        tables=tables,
        categories=categories,
        products=products,
        table_statuses=table_statuses,
    )


@bill_bp.route("/pending-bills")
@login_required()
def pending_bills_page():
    business_id = get_current_business_id()
    bills = (
        Bill.query.filter_by(business_id=business_id, status="PENDING")
        .order_by(Bill.created_at.desc())
        .all()
    )
    categories = Category.query.filter_by(business_id=business_id).all()
    products = Product.query.filter_by(business_id=business_id).all()
    return render_template(
        "pending_bills.html",
        bills=bills,
        categories=categories,
        products=products,
    )


@bill_bp.route("/completed-bills")
@login_required()
def completed_bills_page():
    business_id = get_current_business_id()
    bills = (
        Bill.query.filter_by(business_id=business_id, status="COMPLETED")
        .order_by(Bill.completed_at.desc())
        .all()
    )
    return render_template("completed_bills.html", bills=bills)


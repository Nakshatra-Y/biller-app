from flask import Blueprint, jsonify, request, render_template, redirect, url_for

from database.db import db
from database.models import Category, Product
from routes.auth_routes import login_required, get_current_business_id


menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/menu", methods=["GET"])
@login_required()
def get_menu():
    business_id = get_current_business_id()
    categories = Category.query.filter_by(business_id=business_id).all()
    products = Product.query.filter_by(business_id=business_id).all()
    data = {
        "categories": [
            {"id": c.id, "name": c.name}
            for c in categories
        ],
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "category_id": p.category_id,
                "category": p.category.name if p.category else None,
                "price": p.price,
            }
            for p in products
        ],
    }
    return jsonify(data)


@menu_bp.route("/menu/category", methods=["POST"])
@login_required(role="admin")
def create_category():
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400
    category = Category(business_id=business_id, name=name)
    db.session.add(category)
    db.session.commit()
    if request.is_json:
        return jsonify({"message": "Category created", "id": category.id}), 201
    return redirect(url_for("menu.manage_menu"))


@menu_bp.route("/menu/category/<int:category_id>", methods=["PUT"])
@login_required(role="admin")
def update_category(category_id):
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    category = Category.query.filter_by(id=category_id, business_id=business_id).first_or_404()
    category.name = name
    db.session.commit()
    return jsonify({"message": "Category updated"})


@menu_bp.route("/menu/category/<int:category_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_category(category_id):
    business_id = get_current_business_id()
    category = Category.query.filter_by(id=category_id, business_id=business_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted"})


@menu_bp.route("/menu/product", methods=["POST"])
@login_required(role="admin")
def create_product():
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    price = data.get("price")
    category_id = data.get("category_id")
    try:
        price_val = float(price)
    except (TypeError, ValueError):
        return jsonify({"error": "Valid price is required"}), 400

    category = Category.query.filter_by(id=category_id, business_id=business_id).first()
    if not category:
        return jsonify({"error": "Invalid category"}), 400

    product = Product(
        business_id=business_id,
        name=name,
        category_id=category.id,
        price=price_val,
    )
    db.session.add(product)
    db.session.commit()
    if request.is_json:
        return jsonify({"message": "Product created", "id": product.id}), 201
    return redirect(url_for("menu.manage_menu"))


@menu_bp.route("/menu/product", methods=["DELETE"])
@login_required(role="admin")
def delete_product():
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or request.form
    product_id = data.get("id")
    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200


@menu_bp.route("/menu/product/<int:product_id>", methods=["PUT"])
@login_required(role="admin")
def update_product(product_id):
    business_id = get_current_business_id()
    data = request.get_json(silent=True) or {}
    product = Product.query.filter_by(id=product_id, business_id=business_id).first_or_404()
    if "name" in data:
        product.name = (data["name"] or "").strip() or product.name
    if "price" in data:
        try:
            product.price = float(data["price"])
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid price"}), 400
    if "category_id" in data:
        category = Category.query.filter_by(id=data["category_id"], business_id=business_id).first()
        if category:
            product.category_id = category.id
    db.session.commit()
    return jsonify({"message": "Product updated"})


@menu_bp.route("/manage-menu")
@login_required(role="admin")
def manage_menu():
    business_id = get_current_business_id()
    categories = Category.query.filter_by(business_id=business_id).all()
    products = Product.query.filter_by(business_id=business_id).all()
    return render_template("manage_menu.html", categories=categories, products=products)


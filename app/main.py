from flask import render_template, request, redirect, url_for, jsonify, send_file, session
from app import app, dao, utils
from app.decorator import login_required
import json


@app.route("/")
def index():
    return render_template("index.html", latest_products=dao.read_products(latest=True))


@app.route("/products")
def product_list():
    kw = request.args.get("keyword")
    from_price = request.args.get("from_price")
    to_price = request.args.get("to_price")

    return render_template("products.html",
                           products=dao.read_products(keyword=kw,
                                                      from_price=from_price,
                                                      to_price=to_price))


@app.route("/api/pay", methods=['post'])
def pay():
    if 'cart' in session and session['cart']:
        if dao.add_receipt(session['cart'].values()):
            del session['cart']
            return jsonify({"status": 200, "message": "successful"})

    return jsonify({"status": 500, "message": "failed"})


@app.route("/api/products", methods=["get", "post"])
def api_product_list():
    if request.method == "POST":
        err = ""
        product_id = request.args.get("product_id")
        product = None
        if product_id:
            product = dao.read_product_by_id(product_id=int(product_id))

        if request.method.lower() == "post":
            if product_id:  # Cap nhat
                data = dict(request.form.copy())
                data["product_id"] = product_id
                if dao.update_product(**data):
                    return redirect(url_for("product_list"))
            else:  # Them

                import json
                product = dao.add_product(**dict(json.loads(request.data)))
                if product:
                    return jsonify(product)

            err = "Something wrong!!! Please back later!"

        return jsonify({"error_message": err})

    kw = request.args.get("keyword")

    return jsonify(dao.read_products(keyword=kw))


@app.route("/products/<int:category_id>")
def products_by_cate_id(category_id):
    return render_template("products.html",
                           products=dao.read_products(category_id=category_id))


@app.route("/products/add", methods=["get", "post"])
@login_required
def add_or_update_product():

    err = ""
    product_id = request.args.get("product_id")
    product = None
    if product_id:
        product = dao.read_product_by_id(product_id=int(product_id))

    if request.method.lower() == "post":
        # name = request.form.get("name")
        # price = request.form.get("price", 0)
        # images = request.form.get("images")
        # description = request.form.get("description")
        # category_id = request.form.get("category_id", 0)
        # import pdb
        # pdb.set_trace()
        if product_id: # Cap nhat
            data = dict(request.form.copy())
            data["product_id"] = product_id
            if dao.update_product(**data):
                return redirect(url_for("product_list"))
        else: # Them
            if dao.add_product(**dict(request.form)):
                return redirect(url_for("product_list"))

        err = "Something wrong!!! Please back later!"

    return render_template("product-add.html",
                           categories=dao.read_categories(),
                           product=product,
                           err=err)


@app.route("/api/products/<int:product_id>", methods=["delete"])
def delete_product(product_id):
    if dao.delete_product(product_id=product_id):
        return jsonify({
            "status": 200,
            "message": "Successful",
            "data": {"product_id": product_id}
        })

    return jsonify({
        "status": 500,
        "message": "Failed"
    })


@app.route("/products/export")
@login_required
def export_product():
    return send_file(utils.export_csv())


@app.route("/login", methods=["get", "post"])
def login():
    err_msg = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.validate_user(username=username, password=password)
        if user:
            session["user"] = user

            if "next" in request.args:
                return redirect(request.args["next"])

            return redirect(url_for("index"))
        else:
            err_msg = "DANG NHAP KHONG THANH CONG"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout():
    session["user"] = None
    return redirect(url_for("index"))


@app.route("/register", methods=["get", "post"])
def register():
    err_msg = ""
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if password.strip() != confirm.strip():
            err_msg = "The password does not match!"
        else:
            path = utils.upload_avatar(file=request.files["avatar"])
            if dao.add_user(name=name, username=username,
                            password=password, avatar=path):
                return redirect(url_for('login'))
            else:
                err_msg = "Something wrong!!!"

    return render_template("register.html", err_msg=err_msg)


@app.route('/cart')
def cart():
    return render_template('cart.html')


@app.route("/api/cart", methods=['post'])
def add_to_cart():
    data = json.loads(request.data)
    product_id = data["id"]
    name = data["name"]
    price = data["price"]

    try:
        q, s = utils.add_to_cart(id=product_id, name=name, price=price)

        return jsonify({"status": 200, "error_message": "successful", "quantity": q, "sum_cart": s})
    except Exception as ex:
        return jsonify({"status": 500, "error_message": str(ex)})


@app.context_processor
def common_data():
    q, s = utils.cart_stats()
    return {
        'categories': dao.read_categories(),
        'cart_quantity': q,
        'cart_sum': s
    }


if __name__ == "__main__":
    from app.admin import *
    app.run(debug=False, port=5050)

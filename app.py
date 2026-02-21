# imports
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -------------------------
# MODELS
# -------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # "admin", "designer", "customer"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    stock = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # link to User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/collections")
def collections():
    products = Product.query.all()
    return render_template("collections.html", products=products)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash("Login successful!", "success")
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("collections"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))
    return "Welcome Admin! Here you can manage products, orders, and stock."

def seed_products():
    if Product.query.count() == 0:  # only seed if empty
        sample_products = [
            Product(
                name="Spiritual & Peacewear",
                description="Comfortable, serene clothing designed for meditation and inner peace.",
                price=49.99,
                stock=20,
                image="images/spiritual.jpg"
            ),
            Product(
                name="Nomad Carry",
                description="Functional bags and accessories for the mindful traveler.",
                price=79.99,
                stock=15,
                image="images/nomad.jpg"
            ),
            Product(
                name="Mindful Sip",
                description="Eco-friendly bottles and cups for conscious living.",
                price=19.99,
                stock=50,
                image="images/mindful.jpg"
            )
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()
        print("Sample products seeded!")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_products()  # seed sample products
    app.run(debug=True)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        # Create new user
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/admin/products")
@login_required
def admin_products():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))
    products = Product.query.all()
    return render_template("admin_products.html", products=products)

@app.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        stock = int(request.form.get("stock"))
        image = request.form.get("image")

        new_product = Product(name=name, description=description, price=price, stock=stock, image=image)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
        return redirect(url_for("admin_products"))
    return render_template("add_product.html")

@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.price = float(request.form.get("price"))
        product.stock = int(request.form.get("stock"))
        product.image = request.form.get("image")

        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("admin_products"))

    return render_template("edit_product.html", product=product)

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for("admin_products"))
@app.route("/designer/products/add", methods=["GET", "POST"])
@login_required
def designer_add_product():
    if current_user.role != "designer":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = float(request.form.get("price"))
        stock = int(request.form.get("stock"))
        image = request.form.get("image")

        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image,
            created_by=current_user.id
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product uploaded successfully!", "success")
        return redirect(url_for("collections"))

    return render_template("designer_add_product.html")
@app.route("/designer/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def designer_edit_product(product_id):
    if current_user.role != "designer":
        flash("Access denied!", "danger")
        return redirect(url_for("home"))

    product = Product.query.get_or_404(product_id)
    if product.created_by != current_user.id:
        flash("You can only edit your own products!", "danger")
        return redirect(url_for("collections"))

    if request.method == "POST":
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.price = float(request.form.get("price"))
        product.stock = int(request.form.get("stock"))
        product.image = request.form.get("image")

        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("collections"))

    return render_template("designer_edit_product.html", product=product)
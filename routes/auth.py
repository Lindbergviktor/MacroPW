from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.user_service import create_user, delete_user_account, get_user_by_email, get_user_for_login

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Skyddar routes som kräver inloggning."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.start_page"))
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/start")
def start_page():
    """Visar startsida för icke-inloggade användare."""
    return render_template("start_page.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            user = get_user_for_login(email, password)
        except Exception:
            flash("Database error in login.", "danger")
            return render_template("login.html")

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("dashboard.index"))

        flash("Wrong email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/delete_account", methods=["POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    delete_user_account(session["user_id"])
    session.clear()
    return redirect(url_for("auth.start_page"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Hanterar registrering av användare."""
    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    gender = request.form["gender"]
    height = request.form["height"]
    weight = request.form["weight"]
    activity_level = request.form["activity_level"]
    birthdate = request.form["birthdate"]
    weight_goal = request.form["weight_goal"]

    if not name.strip():
        flash("Name cannot be empty.", "danger")
        return redirect(url_for("auth.register"))

    if not email.strip():
        flash("Email cannot be empty.", "danger")
        return redirect(url_for("auth.register"))

    if not password.strip():
        flash("Password cannot be empty.", "danger")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("auth.register"))

    if not any(c.isupper() for c in password):
        flash("Password must contain at least one uppercase letter.", "danger")
        return redirect(url_for("auth.register"))

    if not any(c.isdigit() for c in password):
        flash("Password must contain at least one number.", "danger")
        return redirect(url_for("auth.register"))

    if not height or not weight or not activity_level:
        flash("Height, weight and activity level are required.", "danger")
        return redirect(url_for("auth.register"))

    if not birthdate:
        flash("Date of birth is required.", "danger")
        return redirect(url_for("auth.register"))

    if not weight_goal:
        flash("Goal is required.", "danger")
        return redirect(url_for("auth.register"))

    try:
        height_value = int(height)
    except ValueError:
        flash("Height must be a whole number.", "danger")
        return redirect(url_for("auth.register"))

    if height_value <= 0:
        flash("Height must be a positive number.", "danger")
        return redirect(url_for("auth.register"))

    try:
        weight_value = float(weight)
    except ValueError:
        flash("Weight must be a number.", "danger")
        return redirect(url_for("auth.register"))

    if weight_value <= 0:
        flash("Weight must be a positive number.", "danger")
        return redirect(url_for("auth.register"))

    try:
        existing = get_user_by_email(email)
        if not existing:
            create_user(
                name,
                email,
                password,
                gender,
                height_value,
                weight_value,
                activity_level,
                birthdate,
                weight_goal,
            )
    except Exception:
        flash("Database error during registration", "danger")
        return redirect(url_for("auth.register"))

    if existing:
        flash("Email already registered.", "danger")
        return redirect(url_for("auth.register"))

    flash("Account created! You can now log in.", "success")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

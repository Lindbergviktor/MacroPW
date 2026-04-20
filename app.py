from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_db_connection
from psycopg2 import errors
from functools import wraps

"""
Flask-applikation för kost- och träningshantering.

Funktioner:
- Registrering och inloggning av användare
- Hantering av livsmedel
- Skapande av måltider med ingredienser
- Visning av statistik och träningssidor

Observera:
- Applikationen är för utveckling och saknar säker lösenordshantering.
"""

app = Flask(__name__)
app.secret_key = "secret_key"

def login_required(f):
    """
    Decorator som skyddar routes som kräver inloggning. Redirectar till startsidan om användaren inte är inloggad.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('start_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    """
    Startsida för användaren.
    Hämtar dagens loggade kalorier och makron från databasen.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Hämta totala makron och kalorier för idag
    cur.execute("""
        SELECT 
            COALESCE(SUM(f.calories * mli.amount / 100), 0),
            COALESCE(SUM(f.protein * mli.amount / 100), 0),
            COALESCE(SUM(f.fat * mli.amount / 100), 0),
            COALESCE(SUM(f.carbs * mli.amount / 100), 0)
        FROM meal_log ml
        JOIN meal_log_item mli ON ml.log_id = mli.log_id
        JOIN food f ON mli.food_id = f.food_id
        WHERE ml.user_id = %s
        AND DATE(ml.log_date) = CURRENT_DATE
    """, (session['user_id'],))
    totals = cur.fetchone()

    # Hämta kalorier per kategori för idag
    cur.execute("""
        SELECT ml.name, COALESCE(SUM(f.calories * mli.amount / 100), 0)
        FROM meal_log ml
        JOIN meal_log_item mli ON ml.log_id = mli.log_id
        JOIN food f ON mli.food_id = f.food_id
        WHERE ml.user_id = %s
        AND DATE(ml.log_date) = CURRENT_DATE
        GROUP BY ml.name
    """, (session['user_id'],))
    category_rows = cur.fetchall()

    cur.close()
    conn.close()

    # Bygg en dict med kalorier per kategori
    category_calories = {row[0]: round(row[1]) for row in category_rows}

    return render_template("index.html",
        calories=round(totals[0]),
        protein=round(totals[1]),
        fat=round(totals[2]),
        carbs=round(totals[3]),
        category_calories=category_calories
    )

@app.route("/start")
def start_page():
    """Visar startsida för icke-inloggade användare"""
    return render_template("start_page.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Hanterar inloggning. GET visar inloggningsformuläret, POST validerar email och lösenord mot databasen."""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Wrong email or password.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Hanterar registrering av användare. GET visar formuläret, POST behandlar det."""
    if request.method == "GET":
        return render_template("register.html")
    
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    gender = request.form["gender"]
    height = request.form.get("height") or None
    weight = request.form.get("weight") or None
    activity_level = request.form.get("activity_level") or None

    # Validering
    if not name.strip():
        flash("Name cannot be empty.", "danger")
        return redirect(url_for("register"))

    if not email.strip():
        flash("Email cannot be empty.", "danger")
        return redirect(url_for("register"))

    if not password.strip():
        flash("Password cannot be empty.", "danger")
        return redirect(url_for("register"))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "danger")
        return redirect(url_for("register"))

    if not any(c.isupper() for c in password):
        flash("Password must contain at least one uppercase letter.", "danger")
        return redirect(url_for("register"))

    if not any(c.isdigit() for c in password):
        flash("Password must contain at least one number.", "danger")
        return redirect(url_for("register"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Kolla om emailen redan finns
    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        flash("Email already registered.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for("register"))

    cur.execute(
        "INSERT INTO users (name, email, password, gender, height, weight, activity_level) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (name, email, password, gender, height, weight, activity_level)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Account created! You can now log in.", "success")
    return render_template("login.html")

@app.route("/meals")
@login_required
def meals():
    """
    Visar användarens måltider och tillgängliga livsmedel.

    Hämtar:
    -Alla livsmedel från databasen.
    -Alla måltider med ingredienser för aktuell användare.

    Returnerar: meals.html med strukturerad måltidsdata
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM food;")
    foods = cur.fetchall()

    cur.execute("""
        SELECT m.meal_id, m.name, f.name, mi.amount
        FROM meal m
        JOIN meal_ingredient mi ON m.meal_id = mi.meal_id
        JOIN food f ON mi.food_id = f.food_id
        WHERE m.user_id = %s
        ORDER BY m.meal_id
    """, (session['user_id'],))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Grupperar databasrader till måltider med tillhörande ingredienser.
    meals_dict = {}
    for meal_id, meal_name, food_name, amount in rows:
        if meal_id not in meals_dict:
            meals_dict[meal_id] = {"name": meal_name, "meal_id": meal_id, "ingredients": []}
        meals_dict[meal_id]["ingredients"].append({"food": food_name, "amount": amount})

    return render_template("meals.html", foods=foods, meals=meals_dict.values())

@app.route("/foods")
@login_required
def foods():
    """
    Visar alla livsmedel i databasen.

    Kräver att användaren är inloggad.

    Returnerar: foods.html med lista över livsmedel.

    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM food;")
    foods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("foods.html", foods=foods)

@app.route("/add_food", methods=["POST"])
@login_required
def add_food():
    """
    Lägger till ett nytt livsmedel i databasen.

    Kräver att användaren är inloggad.

    Förväntar formulärdata
    - name
    - calories
    - protein
    - fats
    - carbs

    Validerar input och sparar i databasen
    """
    name = request.form["name"].strip().lower()
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]

    if not name.strip():
        flash("Name cannot be empty", "danger")
        return redirect(url_for("foods"))

    if int(calories) <= 0:
        flash("Calories must be greater than 0", "danger")
        return redirect(url_for("foods"))

    for value in [protein, fat, carbs]:
        if float(value) < 0:
            flash("Nutritional values cannot be negative", "danger")
            return redirect(url_for("foods"))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO food (name, calories, protein, fat, carbs) VALUES (%s, %s, %s, %s, %s)",
            (name, calories, protein, fat, carbs)
        )
        conn.commit()
        flash("Food added!", "success")
    except errors.UniqueViolation:
        conn.rollback()
        flash("A food with that name already exists.", "danger")
        return redirect(url_for("foods"))
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("foods"))

@app.route("/add-lunch")
@login_required
def add_lunch():
    return render_template("add_lunch.html")


@app.route("/add_meal", methods=["POST"])
@login_required
def add_meal():
    """
    Skapar en måltid med valda ingredienser.
    
    Förväntar sig formulärdata
    - meal_name (sträng)
    - food_id[] (lista av id:n)
    - amount[] (lista av mängder)

    Validerar input och sparar i databasen.
    """
    meal_name = request.form["meal_name"].strip().lower()
    food_ids = request.form.getlist("food_id[]")
    amounts = request.form.getlist("amount[]")

    if not meal_name.strip():
        flash("Name cannot be empty", "danger")
        return redirect(url_for("meals"))

    for amount in amounts:
        if float(amount) <= 0:
            flash("Amount must be greater than 0", "danger")
            return redirect(url_for("meals"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO meal (name, user_id) VALUES (%s, %s) RETURNING meal_id",
        (meal_name, session['user_id'])
    )
    meal_id = cur.fetchone()[0]

    for food_id, amount in zip(food_ids, amounts):
        cur.execute(
            "INSERT INTO meal_ingredient (meal_id, food_id, amount) VALUES (%s, %s, %s)",
            (meal_id, food_id, amount)
        )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("meals"))

@app.route("/statistics")
@login_required
def statistics():
    return render_template("statistics.html")

@app.route("/workouts")
@login_required
def workouts():
    return render_template("workouts.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/log_meal/<int:meal_id>", methods=["POST"])
@login_required
def log_meal(meal_id):
    """Loggar en sparad måltid för dagens datum."""

    conn = get_db_connection()
    cur = conn.cursor()

    # Hämta måltidsnamnet
    cur.execute("SELECT name FROM meal WHERE meal_id = %s", (meal_id,))
    meal = cur.fetchone()

    if not meal:
        flash("Måltiden hittades inte.", "danger")
        return redirect(url_for('meals'))

    # Skapa en rad i meal_log
    meal_category = request.form["meal_category"]

    cur.execute(
        "INSERT INTO meal_log (name, meal_id, user_id) VALUES (%s, %s, %s) RETURNING log_id",
        (meal_category, meal_id, session['user_id'])
    )
    log_id = cur.fetchone()[0]

    # Kopiera ingredienserna till meal_log_item
    cur.execute(
        "SELECT food_id, amount FROM meal_ingredient WHERE meal_id = %s",
        (meal_id,)
    )
    ingredients = cur.fetchall()

    for food_id, amount in ingredients:
        cur.execute(
            "INSERT INTO meal_log_item (log_id, food_id, amount) VALUES (%s, %s, %s)",
            (log_id, food_id, amount)
        )

    conn.commit()
    cur.close()
    conn.close()

    flash("Måltid loggad!", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
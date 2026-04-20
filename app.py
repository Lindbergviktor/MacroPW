from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_db_connection

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

@app.route("/")
def index():
    """
    Startsida för användaren.

    Omdirigerar till startsidan om användaren inte är inloggad.
    """
    if 'user_id' not in session:
        return redirect(url_for('start_page'))
    return render_template("index.html")

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
def meals():
    """
    Visar användarens måltider och tillgängliga livsmedel.

    Hämtar:
    - Alla livsmedel från databasen.
    - Alla måltider med ingredienser för aktuell användare.

    Returnerar: meals.html med strukturerad måltidsdata.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

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

    meals_dict = {}
    for meal_id, meal_name, food_name, amount in rows:
        if meal_id not in meals_dict:
            meals_dict[meal_id] = {"name": meal_name, "ingredients": []}
        meals_dict[meal_id]["ingredients"].append({"food": food_name, "amount": amount})

    return render_template("meals.html", foods=foods, meals=meals_dict.values())

@app.route("/foods")
def foods():
    """
    Visar alla livsmedel i databasen.

    Kräver att användaren är inloggad.

    Returnerar: foods.html med lista över livsmedel.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM food;")
    foods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("foods.html", foods=foods)

@app.route("/add_food", methods=["POST"])
def add_food():
    """
    Lägger till ett nytt livsmedel i databasen.

    Kräver att användaren är inloggad.

    Förväntar formulärdata:
    - name, calories, protein, fat, carbs

    Validerar input och sparar i databasen.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form["name"]
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]

    if not name.strip():
        flash("Name cannot be empty", "danger")
        return redirect(url_for("foods"))

    # FIX: wrap in try/except to avoid 500 crash on non-numeric input
    try:
        calories_val = int(calories)
        protein_val = float(protein)
        fat_val = float(fat)
        carbs_val = float(carbs)
    except ValueError:
        flash("Calories, protein, fat and carbs must be valid numbers.", "danger")
        return redirect(url_for("foods"))

    if calories_val <= 0:
        flash("Calories must be greater than 0", "danger")
        return redirect(url_for("foods"))

    for value in [protein_val, fat_val, carbs_val]:
        if value < 0:
            flash("Nutritional values cannot be negative", "danger")
            return redirect(url_for("foods"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO food (name, calories, protein, fat, carbs) VALUES (%s, %s, %s, %s, %s)",
        (name, calories_val, protein_val, fat_val, carbs_val)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("foods"))

@app.route("/add-lunch")
def add_lunch():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("add_lunch.html")

@app.route("/add_workout", methods=["GET", "POST"])
def add_workout():
    """
    GET:  Visar formulär med befintliga workouts att välja mellan.
    POST: Sparar ett träningspass med vald workout och duration.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        workout_id = request.form.get("workout_id")
        duration = request.form.get("duration")

        if not workout_id:
            flash("Choose a workout.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("add_workout"))

        # FIX: wrap in try/except to handle non-numeric duration input
        try:
            duration_val = float(duration)
        except (TypeError, ValueError):
            flash("Duration must be a valid number.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("add_workout"))

        if duration_val <= 0:
            flash("Duration must be greater than 0.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("add_workout"))

        cur.execute("""
            INSERT INTO workout_log (duration, user_id, workout_id)
            VALUES (%s, %s, %s)
        """, (duration_val, session["user_id"], workout_id))

        conn.commit()
        cur.close()
        conn.close()

        flash("Workout saved.", "success")
        return redirect(url_for("statistics"))

    # GET: fetch available workouts to populate the dropdown
    cur.execute("SELECT workout_id, name, calories FROM workout ORDER BY name")
    workouts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("add_workout.html", workouts=workouts)


@app.route("/add_meal", methods=["POST"])
def add_meal():
    """
    Skapar en måltid med valda ingredienser.

    Förväntar sig formulärdata:
    - meal_name (sträng)
    - food_id[] (lista av id:n)
    - amount[] (lista av mängder)

    Validerar input och sparar i databasen.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    meal_name = request.form["meal_name"]
    food_ids = request.form.getlist("food_id[]")
    amounts = request.form.getlist("amount[]")

    if not meal_name.strip():
        flash("Name cannot be empty", "danger")
        return redirect(url_for("meals"))

    for amount in amounts:
        try:
            if float(amount) <= 0:
                flash("Amount must be greater than 0", "danger")
                return redirect(url_for("meals"))
        except ValueError:
            flash("Amount must be a valid number.", "danger")
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
def statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    user_id = session["user_id"]

    # Today's nutrition totals
    cur.execute("""
        SELECT
            COALESCE(SUM(f.calories * mli.amount / 100.0), 0),
            COALESCE(SUM(f.protein  * mli.amount / 100.0), 0),
            COALESCE(SUM(f.fat      * mli.amount / 100.0), 0),
            COALESCE(SUM(f.carbs    * mli.amount / 100.0), 0)
        FROM meal_log ml
        JOIN meal_log_item mli ON ml.log_id = mli.log_id
        JOIN food f ON mli.food_id = f.food_id
        WHERE ml.user_id = %s
          AND DATE(ml.log_date) = CURRENT_DATE
    """, (user_id,))
    nutrition_today = cur.fetchone()

    # This week's workout summary
    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(wl.duration), 0),
            COALESCE(SUM((w.calories / 60.0) * wl.duration), 0)
        FROM workout_log wl
        JOIN workout w ON wl.workout_id = w.workout_id
        WHERE wl.user_id = %s
          AND wl.log_date >= CURRENT_DATE - INTERVAL '6 days'
    """, (user_id,))
    workouts_week = cur.fetchone()

    # Today's water intake
    cur.execute("""
        SELECT COALESCE(SUM(nr_of_glasses), 0)
        FROM water_log
        WHERE user_id = %s
          AND DATE(log_date) = CURRENT_DATE
    """, (user_id,))
    water_today = cur.fetchone()[0]

    # FIX: was incorrectly querying workouts instead of nutrition per day
    cur.execute("""
        SELECT
            DATE(ml.log_date),
            COALESCE(SUM(f.calories * mli.amount / 100.0), 0),
            COALESCE(SUM(f.protein  * mli.amount / 100.0), 0)
        FROM meal_log ml
        JOIN meal_log_item mli ON ml.log_id = mli.log_id
        JOIN food f ON mli.food_id = f.food_id
        WHERE ml.user_id = %s
          AND ml.log_date >= CURRENT_DATE - INTERVAL '6 days'
        GROUP BY DATE(ml.log_date)
        ORDER BY DATE(ml.log_date) DESC
    """, (user_id,))
    nutrition_last_7 = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "statistics.html",
        calories_today=round(nutrition_today[0] or 0),
        protein_today=round(nutrition_today[1] or 0, 1),
        fat_today=round(nutrition_today[2] or 0, 1),
        carbs_today=round(nutrition_today[3] or 0, 1),
        workouts_this_week=workouts_week[0] or 0,
        workout_minutes_this_week=round(workouts_week[1] or 0),
        workout_calories_this_week=round(workouts_week[2] or 0),
        water_today=water_today or 0,
        nutrition_last_7=nutrition_last_7
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)

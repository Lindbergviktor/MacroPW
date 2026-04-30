from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection
from psycopg2 import errors
from datetime import date
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

from contextlib import contextmanager

@contextmanager
def get_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
               
def get_all_foods():
    """Hämtar alla livsmedel från databasen, sorterade i bokstavsordning."""
    with get_db() as cur:
        cur.execute("SELECT * FROM food ORDER BY name")
        return cur.fetchall()

def get_meals_dict(rows):
    """
    Tar fram en dict på ingredienser och makrovärden från databasraden
    """
    meals_dict = {}
    for meal_id, meal_name, food_name, amount, cal, prot, fat, carbs in rows:
        if meal_id not in meals_dict:
            meals_dict[meal_id] = {
                "name": meal_name,
                "meal_id": meal_id,
                "ingredients": [],
                "total_calories": 0,
                "total_protein": 0,
                "total_fat": 0,
                "total_carbs": 0
            }
        meals_dict[meal_id]["ingredients"].append({"food": food_name, "amount": amount})
        meals_dict[meal_id]["total_calories"] += cal * amount / 100
        meals_dict[meal_id]["total_protein"] += prot * amount / 100
        meals_dict[meal_id]["total_fat"] += fat * amount / 100
        meals_dict[meal_id]["total_carbs"] += carbs * amount / 100
    return meals_dict

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
    try:
        with get_db() as cur:
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

            cur.execute("""
            SELECT w.name, wl.duration,
                   ROUND(w.met * wl.weight * wl.duration / 60.0) as calories_burned
            FROM workout_log wl
            JOIN workout w ON wl.workout_id = w.workout_id
            WHERE wl.user_id = %s AND DATE(wl.log_date) = CURRENT_DATE
            ORDER BY wl.log_date DESC
        """, (session['user_id'],))
            workouts_today = cur.fetchall()

    except Exception:
        flash("Kunde inte hämta data.", "danger")  
        return redirect(url_for("start_page"))      

    # Bygger en dict med kalorier per kategori
    category_calories = {row[0]: round(row[1]) for row in category_rows}

    return render_template("index.html",
        calories=round(totals[0]),
        protein=round(totals[1]),
        fat=round(totals[2]),
        carbs=round(totals[3]),
        category_calories=category_calories,
        workouts_today=workouts_today
    )



@app.route("/start")
def start_page():
    """Visar startsida för icke-inloggade användare"""
    return render_template("start_page.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            with get_db() as cur:
                cur.execute(
                    "SELECT user_id, name FROM users WHERE email = %s AND password = %s",
                    (email, password)
                )
                user = cur.fetchone()
        except Exception:
            flash("Databasfel vid inloggning.", "danger")
            return render_template("login.html")

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Wrong email or password.", "danger")

    return render_template("login.html")

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        name          = request.form['name']
        email         = request.form['email']
        gender        = request.form['gender']
        height        = request.form['height']
        weight        = request.form['weight']
        weight_goal   = request.form['weight_goal']
        activity_level = request.form['activity_level']
        birthdate     = request.form['birthdate']

        with get_db() as cur:
            cur.execute("""
                UPDATE users
                SET name=%s, email=%s, gender=%s, height=%s, weight=%s,
                    weight_goal=%s, activity_level=%s, birthdate=%s
                WHERE user_id=%s
            """, (name, email, gender, height, weight, weight_goal, activity_level, birthdate, user_id))

        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))

    with get_db() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
        cols = [c[0] for c in cur.fetchall()]

    user = dict(zip(cols, row))
    return render_template('profile.html', user=user)


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as cur:
        cur.execute("DELETE FROM users WHERE user_id=%s", (session['user_id'],))
    session.clear()
    return redirect(url_for('start_page'))
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
    birthdate = request.form.get("birthdate") or None
    weight_goal = request.form.get("weight_goal") or None

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

    if not height or not weight or not activity_level:
        flash("Height, weight and activity level are required.", "danger")
        return redirect(url_for("register"))

    if not birthdate:
        flash("Date of birth is required.", "danger")
        return redirect(url_for("register"))

    if not weight_goal:
        flash("Goal is required.", "danger")
        return redirect(url_for("register"))
    
    try:
        with get_db() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()

            if not existing:
                cur.execute(
                    """INSERT INTO users
                    (name, email, password, gender, height, weight, activity_level, birthdate, weight_goal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (name, email, password, gender, height, weight, activity_level, birthdate, weight_goal)
                )

    except Exception:
        flash("Databasfel vid registrering.", "danger") 
        return redirect(url_for("register"))  

    if existing:
        flash("Email already registered.", "danger") 
        return redirect(url_for("register"))    

    flash("Account created! You can now log in.", "success")
    return render_template("login.html")

@app.route("/meals")
@login_required
def meals():
    """
    Visar användarens måltider och tillgängliga livsmedel.

    Hämtar:
    - Alla livsmedel från databasen.
    - Alla måltider med ingredienser för aktuell användare.

    Returnerar: meals.html med strukturerad måltidsdata.
    """
    try:
        foods = get_all_foods()
        with get_db() as cur:
            cur.execute("""
                SELECT m.meal_id, m.name, f.name, mi.amount,
                        f.calories, f.protein, f.fat, f.carbs
                FROM meal m
                JOIN meal_ingredient mi ON m.meal_id = mi.meal_id
                JOIN food f ON mi.food_id = f.food_id
                WHERE m.user_id = %s
                ORDER BY m.meal_id
            """, (session['user_id'],))
            rows = cur.fetchall()
    except Exception:
        flash("Kunde inte hämta måltider.", "danger")
        return redirect(url_for("index"))

    meals_dict = get_meals_dict(rows)

    return render_template("meals.html", foods=foods, meals=meals_dict.values())

@app.route("/foods")
@login_required
def foods():
    """
    Visar alla livsmedel i databasen.

    Kräver att användaren är inloggad.

    Returnerar: foods.html med lista över livsmedel.
    """
    try:
        foods = get_all_foods()
    except Exception:
        flash("Kunde inte hämta livsmedel.", "danger")
        return redirect(url_for("index"))   
     
    return render_template("foods.html", foods=foods)

@app.route("/add_food", methods=["POST"])
@login_required
def add_food():
    """
    Lägger till ett nytt livsmedel i databasen.

    Kräver att användaren är inloggad.

    Förväntar formulärdata:
    - name, calories, protein, fat, carbs

    Validerar input och sparar i databasen.
    """
    name = request.form["name"].strip().lower()
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]

    if not name.strip():
        flash("Name cannot be empty", "danger")
        return redirect(url_for("foods"))

    # Ser till så att programmet inte kraschar om användaren skriver text i fälten
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
    if protein_val + fat_val + carbs_val > 100:
        flash("Protein, fat and carbs cannot exceed 100g combined.", "danger")
        return redirect(url_for("foods"))

    try:
        with get_db() as cur:
            cur.execute(
                "INSERT INTO food (name, calories, protein, fat, carbs) VALUES (%s, %s, %s, %s, %s)",
                (name, calories_val, protein_val, fat_val, carbs_val)
            )
        flash("Food added!", "success")

    except errors.UniqueViolation:
        flash("A food with that name already exists.", "danger")
        return redirect(url_for("foods"))

    except errors.NumericValueOutOfRange:
        flash("One or more values are too large.", "danger")
        return redirect(url_for("foods"))

    except Exception:
        flash("Database error when adding food.", "danger")
        return redirect(url_for("foods"))

    return redirect(url_for("foods"))


@app.route("/add-lunch")
@login_required
def add_lunch():
    return render_template("add_lunch.html")



@app.route("/add_workout", methods=["GET", "POST"])
@login_required
def add_workout():

    if request.method == "POST":
        workout_id = request.form.get("workout_id")
        duration = request.form.get("duration")
        log_date = request.form.get("log_date") or date.today().isoformat()

        if not workout_id:
            flash("Choose a workout.", "danger")
            return redirect(url_for("add_workout"))

        try:
            duration_val = float(duration)
        except (TypeError, ValueError):
            flash("Duration must be a valid number.", "danger")
            return redirect(url_for("add_workout"))

        if duration_val <= 0:
            flash("Duration must be greater than 0.", "danger")
            return redirect(url_for("add_workout"))

        try:
            with get_db() as cur:
                cur.execute("""
                    INSERT INTO workout_log (duration, user_id, workout_id, weight, log_date)
                    VALUES (%s, %s, %s, (SELECT weight FROM users WHERE user_id = %s), %s)
                """, (duration_val, session["user_id"], workout_id, session["user_id"], log_date))
        except Exception:
            app.logger.exception("Failed to save workout")
            flash("Databasfel vid sparande av träningspass.", "danger")
            return redirect(url_for("add_workout"))

        flash("Workout saved.", "success")
        return redirect(url_for("statistics"))

    try:
        with get_db() as cur:
            cur.execute("""
                SELECT w.workout_id, w.name, w.met, u.weight
                FROM workout w, users u
                WHERE u.user_id = %s
                ORDER BY w.name
            """, (session["user_id"],))
            workouts = cur.fetchall()
    except Exception:
        flash("Kunde inte hämta träningspass.", "danger")
        return redirect(url_for("index"))

    return render_template("add_workout.html", workouts=workouts, today=date.today().isoformat())


@app.route("/add_meal", methods=["POST"])
@login_required
def add_meal():
    """
    Skapar en måltid med valda ingredienser.

    Förväntar sig formulärdata:
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
        try:
            if float(amount) <= 0:
                flash("Amount must be greater than 0", "danger")
                return redirect(url_for("meals"))
        except ValueError:
            flash("Amount must be a valid number.", "danger")
            return redirect(url_for("meals"))

    try:
        with get_db() as cur:
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
    except Exception:
        flash("Databasfel vid skapande av måltid.", "danger")
        return redirect(url_for("meals"))

    return redirect(url_for("meals"))

@app.route("/statistics")
@login_required
def statistics():
    user_id = session["user_id"]

    try:

        calorie_goal = 2200
        weekly_goal = calorie_goal * 7
        
        with get_db() as cur:
            cur.execute("""
                SELECT
                    COALESCE(SUM(f.calories * mli.amount / 100.0), 0),
                    COALESCE(SUM(f.protein  * mli.amount / 100.0), 0),
                    COALESCE(SUM(f.fat      * mli.amount / 100.0), 0),
                    COALESCE(SUM(f.carbs    * mli.amount / 100.0), 0)
                FROM meal_log ml
                JOIN meal_log_item mli ON ml.log_id = mli.log_id
                JOIN food f ON mli.food_id = f.food_id
                WHERE ml.user_id = %s AND DATE(ml.log_date) = CURRENT_DATE
            """, (user_id,))
            nutrition_today = cur.fetchone()

            cur.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(wl.duration), 0),
                    COALESCE(SUM(w.met * wl.weight * wl.duration / 60.0), 0)
                FROM workout_log wl
                JOIN workout w ON wl.workout_id = w.workout_id
                WHERE wl.user_id = %s
                AND wl.log_date >= date_trunc('week', CURRENT_DATE)
            """, (user_id,))
            workouts_week = cur.fetchone()

            cur.execute("""
                SELECT COALESCE(SUM(nr_of_glasses), 0)
                FROM water_log
                WHERE user_id = %s AND DATE(log_date) = CURRENT_DATE
            """, (user_id,))
            water_today = cur.fetchone()[0]

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
                    AND ml.log_date >= CURRENT_DATE - INTERVAL '6 days'
            """, (user_id,))
            nutrition_week = cur.fetchone()            

    except Exception:
        flash("Kunde inte hämta statistik.", "danger")
        return redirect(url_for("index"))

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
        nutrition_last_7=nutrition_last_7,
        calories_week=round(nutrition_week[0] or 0),
        protein_week=round(nutrition_week[1] or 0, 1),
        fat_week=round(nutrition_week[2] or 0, 1),
        carbs_week=round(nutrition_week[3] or 0, 1),
        weekly_goal=weekly_goal,
        calorie_goal=calorie_goal
        )
    



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/log_meal/<int:meal_id>", methods=["POST"])
@login_required
def log_meal(meal_id):
    """Loggar en sparad måltid för dagens datum."""

    try:
        with get_db() as cur:
            cur.execute("SELECT name FROM meal WHERE meal_id = %s", (meal_id,))
            meal = cur.fetchone()

            if not meal:
                flash("Måltiden hittades inte.", "danger")
                return redirect(url_for('meals'))

            meal_category = request.form["meal_category"]

            cur.execute(
                "INSERT INTO meal_log (name, meal_id, user_id) VALUES (%s, %s, %s) RETURNING log_id",
                (meal_category, meal_id, session['user_id'])
            )
            log_id = cur.fetchone()[0]

            cur.execute(
                "SELECT food_id, amount FROM meal_ingredient WHERE meal_id = %s", (meal_id,)
            )
            ingredients = cur.fetchall()

            for food_id, amount in ingredients:
                cur.execute(
                     "INSERT INTO meal_log_item (log_id, food_id, amount) VALUES (%s, %s, %s)",
                     (log_id, food_id, amount)
                )
    except Exception:
        flash("Databasfel vid loggning av måltid.", "danger")
        return redirect(url_for('meals'))

    flash("Måltid loggad!", "success")
    return redirect(url_for('index'))

@app.route("/delete_meal/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    try:
        with get_db() as cur:
            cur.execute("SELECT user_id FROM meal WHERE meal_id = %s", (meal_id,))
            meal = cur.fetchone()
            if not meal or meal[0] != session['user_id']:
                flash("Måltiden hittades inte.", "danger")
                return redirect(url_for('meals'))

            # Bryt kopplingen till logg-historiken innan radering
            cur.execute("UPDATE meal_log SET meal_id = NULL WHERE meal_id = %s", (meal_id,))
            cur.execute("DELETE FROM meal_ingredient WHERE meal_id = %s", (meal_id,))
            cur.execute("DELETE FROM meal WHERE meal_id = %s", (meal_id,))
    except Exception:
        flash("Databasfel vid borttagning av måltid.", "danger")
        return redirect(url_for('meals'))

    flash("Meal deleted.", "success")
    return redirect(url_for('meals'))


@app.route("/edit_meal/<int:meal_id>", methods=["GET", "POST"])
@login_required
def edit_meal(meal_id):
    """GET: visar redigeringsformulär. POST: sparar ändringar."""
    if request.method == "POST":
        meal_name = request.form["meal_name"].strip().lower()
        food_ids = request.form.getlist("food_id[]")
        amounts = request.form.getlist("amount[]")

        if not meal_name:
            flash("Name cannot be empty.", "danger")
            return redirect(url_for('edit_meal', meal_id=meal_id))

        for amount in amounts:
            try:
                if float(amount) <= 0:
                    flash("Amount must be greater than 0.", "danger")
                    return redirect(url_for('edit_meal', meal_id=meal_id))
            except ValueError:
                flash("Amount must be a valid number.", "danger")
                return redirect(url_for('edit_meal', meal_id=meal_id))

        try:
            with get_db() as cur:
                cur.execute("SELECT user_id FROM meal WHERE meal_id = %s", (meal_id,))
                meal = cur.fetchone()
                if not meal or meal[0] != session['user_id']:
                    flash("Måltiden hittades inte.", "danger")
                    return redirect(url_for('meals'))

                cur.execute("UPDATE meal SET name = %s WHERE meal_id = %s", (meal_name, meal_id))
                cur.execute("DELETE FROM meal_ingredient WHERE meal_id = %s", (meal_id,))
                for food_id, amount in zip(food_ids, amounts):
                    cur.execute(
                        "INSERT INTO meal_ingredient (meal_id, food_id, amount) VALUES (%s, %s, %s)",
                        (meal_id, food_id, amount)
                    )
        except Exception:
            flash("Databasfel vid uppdatering av måltid.", "danger")
            return redirect(url_for('edit_meal', meal_id=meal_id))

        flash("Meal updated!", "success")
        return redirect(url_for('meals'))

    # GET hämta befintlig data
    try:
        foods = get_all_foods()
        with get_db() as cur:
            cur.execute("SELECT name FROM meal WHERE meal_id = %s AND user_id = %s",
                        (meal_id, session['user_id']))
            meal = cur.fetchone()
            if not meal:
                flash("Måltiden hittades inte.", "danger")
                return redirect(url_for('meals'))

            cur.execute("""
                SELECT mi.food_id, f.name, mi.amount
                FROM meal_ingredient mi
                JOIN food f ON mi.food_id = f.food_id
                WHERE mi.meal_id = %s
            """, (meal_id,))
            ingredients = cur.fetchall()
    except Exception:
        flash("Kunde inte hämta måltid.", "danger")
        return redirect(url_for('meals'))

    return render_template("edit_meal.html",
        meal_id=meal_id,
        meal_name=meal[0],
        ingredients=ingredients,
        foods=foods
    )

if __name__ == "__main__":
    app.run(debug=True)

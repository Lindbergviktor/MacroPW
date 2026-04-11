from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "secret_key"

@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error_modal = request.args.get("modal", "loginModal")
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

    return render_template("login.html", error_modal=error_modal)

@app.route("/register", methods=["POST"])
def register():
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
        return redirect(url_for("login", modal="registerModal"))

    if not email.strip():
        flash("Email cannot be empty.", "danger")
        return redirect(url_for("login", modal="registerModal"))

    if not password.strip():
        flash("Password cannot be empty.", "danger")
        return redirect(url_for("login", modal="registerModal"))

    if len(password) < 6:
        flash("Password must be at least 6 characters.", "danger")
        return redirect(url_for("login", modal="registerModal"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Kolla om emailen redan finns
    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        flash("Email already registered.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for("login", modal="registerModal"))

    cur.execute(
        "INSERT INTO users (name, email, password, gender, height, weight, activity_level) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (name, email, password, gender, height, weight, activity_level)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Account created! You can now log in.", "success")
    return redirect(url_for("login", modal="loginModal"))

@app.route("/meals")
def meals():
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

    if int(calories) <= 0:
        flash("Calories must be greater than 0", "danger")
        return redirect(url_for("foods"))

    for value in [protein, fat, carbs]:
        if float(value) < 0:
            flash("Nutritional values cannot be negative", "danger")
            return redirect(url_for("foods"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO food (name, calories, protein, fat, carbs) VALUES (%s, %s, %s, %s, %s)",
        (name, calories, protein, fat, carbs)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("foods"))

@app.route("/add_meal", methods=["POST"])
def add_meal():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    meal_name = request.form["meal_name"]
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
def statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("statistics.html")

@app.route("/workouts")
def workouts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("workouts.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
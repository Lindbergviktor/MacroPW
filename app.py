from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "hemlig_nyckel"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/meals")
def meals():
    conn = get_db_connection()
    cur = conn.cursor()

    # Hämta livsmedel
    cur.execute("SELECT * FROM food;")
    foods = cur.fetchall()

    # Hämta sparade recept med ingredienser
    cur.execute("""
        SELECT m.meal_id, m.name, f.name, mi.amount
        FROM meal m
        JOIN meal_ingredient mi ON m.meal_id = mi.meal_id
        JOIN food f ON mi.food_id = f.food_id
        ORDER BY m.meal_id
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Gruppera ingredienser per recept
    meals_dict = {}
    for meal_id, meal_name, food_name, amount in rows:
        if meal_id not in meals_dict:
            meals_dict[meal_id] = {"name": meal_name, "ingredients": []}
        meals_dict[meal_id]["ingredients"].append({"food": food_name, "amount": amount})

    return render_template("meals.html", foods=foods, meals=meals_dict.values())

@app.route("/foods")
def foods():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM food;")
    foods = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("foods.html", foods=foods)

@app.route("/add_food", methods=["POST"])
def add_food():
    name = request.form["name"]
    calories = request.form["calories"]
    protein = request.form["protein"]
    fat = request.form["fat"]
    carbs = request.form["carbs"]

    # Validering
    if not name.strip():
        flash("Namnet får inte vara tomt.", "danger")
        return redirect(url_for("foods"))

    if int(calories) <= 0:
        flash("Kalorier måste vara större än 0.", "danger")
        return redirect(url_for("foods"))

    for value in [protein, fat, carbs]:
        if float(value) < 0:
            flash("Näringsvärden kan inte vara negativa.", "danger")
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
    meal_name = request.form["meal_name"]
    food_ids = request.form.getlist("food_id[]")
    amounts = request.form.getlist("amount[]")

    # Validering
    if not meal_name.strip():
        flash("Namnet får inte vara tomt.", "danger")
        return redirect(url_for("meals"))

    for amount in amounts:
        if float(amount) <= 0:
            flash("Mängd måste vara större än 0.", "danger")
            return redirect(url_for("meals"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO meal (name, user_id) VALUES (%s, %s) RETURNING meal_id",
        (meal_name, 1)
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
    return render_template("statistics.html")

@app.route("/workouts")
def workouts():
    return render_template("workouts.html")


if __name__ == "__main__":
    app.run(debug=True)


"""Tjänster för dashboardens datainsamling och formatering.

Den här filen ansvarar för att hämta dagens sammanställda data till startsidan
och för att strukturera loggade poster i ett format som templates enkelt kan
rendera.
"""

from db import get_db


def get_dashboard_data(user_id):
    with get_db() as cur:
        cur.execute(
            """
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
        """,
            (user_id,),
        )
        totals = cur.fetchone()

        cur.execute(
            """
            SELECT ml.name, COALESCE(SUM(f.calories * mli.amount / 100), 0)
            FROM meal_log ml
            JOIN meal_log_item mli ON ml.log_id = mli.log_id
            JOIN food f ON mli.food_id = f.food_id
            WHERE ml.user_id = %s
            AND DATE(ml.log_date) = CURRENT_DATE
            GROUP BY ml.name
        """,
            (user_id,),
        )
        category_rows = cur.fetchall()

        cur.execute(
            """
            SELECT w.name, wl.duration,
                   ROUND(w.met * wl.weight * wl.duration / 60.0) as calories_burned
            FROM workout_log wl
            JOIN workout w ON wl.workout_id = w.workout_id
            WHERE wl.user_id = %s AND DATE(wl.log_date) = CURRENT_DATE
            ORDER BY wl.log_date DESC
        """,
            (user_id,),
        )
        workouts_today = cur.fetchall()

        cur.execute(
            """
            SELECT ml.log_id, ml.name AS category,
                   COALESCE(m.name, 'Custom') AS meal_name,
                   f.food_id, f.name, mli.amount,
                   ROUND(f.calories * mli.amount / 100.0) as kal
            FROM meal_log ml
            JOIN meal_log_item mli ON ml.log_id = mli.log_id
            JOIN food f ON mli.food_id = f.food_id
            LEFT JOIN meal m ON ml.meal_id = m.meal_id
            WHERE ml.user_id = %s AND DATE(ml.log_date) = CURRENT_DATE
            ORDER BY ml.name, ml.log_id
        """,
            (user_id,),
        )
        logged_items = cur.fetchall()

    return {
        "totals": totals,
        "category_rows": category_rows,
        "workouts_today": workouts_today,
        "logged_items": logged_items,
    }


def build_logged_by_category(logged_items):
    logged_by_category = {}
    for log_id, category, meal_name, food_id, food_name, amount, kcal in logged_items:
        if category not in logged_by_category:
            logged_by_category[category] = {}
        if log_id not in logged_by_category[category]:
            logged_by_category[category][log_id] = {
                "log_id": log_id,
                "meal_name": meal_name,
                "ingredients": [],
            }
        logged_by_category[category][log_id]["ingredients"].append(
            {
                "food_id": food_id,
                "food": food_name,
                "amount": amount,
                "kcal": kcal,
            }
        )
    return logged_by_category

"""Tjänster för användardata och användarmål.

Den här filen ansvarar för databasoperationer och hjälplogik kopplad till
användare, såsom inloggningsuppslag, profiluppdateringar, kontoskapande
och beräkning av kalori- och makromål.
"""

from db import get_db
import nutrition


def get_user_for_login(email, password):
    with get_db() as cur:
        cur.execute(
            "SELECT user_id, name FROM users WHERE email = %s AND password = %s",
            (email, password),
        )
        return cur.fetchone()


def get_user_by_email(email):
    with get_db() as cur:
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        return cur.fetchone()
    

def email_exists(email):
    with get_db() as cur:
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        return cur.fetchone() is not None
    

def create_user(
    name,
    email,
    password,
    gender,
    height,
    weight,
    activity_level,
    birthdate,
    weight_goal,
):
    with get_db() as cur:
        cur.execute(
            """INSERT INTO users
            (name, email, password, gender, height, weight, activity_level, birthdate, weight_goal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, email, password, gender, height, weight, activity_level, birthdate, weight_goal),
        )


def get_user_profile_row(user_id):
    with get_db() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position"
        )
        cols = [c[0] for c in cur.fetchall()]
    return row, cols


def update_user_profile(
    user_id,
    name,
    email,
    gender,
    height,
    weight,
    weight_goal,
    activity_level,
    birthdate,
):
    with get_db() as cur:
        cur.execute(
            """
            UPDATE users
            SET name=%s, email=%s, gender=%s, height=%s, weight=%s,
                weight_goal=%s, activity_level=%s, birthdate=%s
            WHERE user_id=%s
        """,
            (name, email, gender, height, weight, weight_goal, activity_level, birthdate, user_id),
        )


def get_user_goal_data(user_id):
    with get_db() as cur:
        cur.execute(
            """
            SELECT gender, height, weight, activity_level, birthdate, weight_goal
            FROM users WHERE user_id = %s
        """,
            (user_id,),
        )
        return cur.fetchone()


def get_calorie_goal(user_id):
    row = get_user_goal_data(user_id)
    if not row:
        return None

    gender, height, weight, activity_level, birthdate, weight_goal = row
    age = nutrition.calculate_age(birthdate)
    return nutrition.calculate_calorie_goal(
        weight, height, age, gender, activity_level, weight_goal
    )


def get_macro_goals(user_id, calories_burned=0):
    """Returnerar dagliga mål för kalorier, protein, fett och kolhydrater."""
    row = get_user_goal_data(user_id)
    if not row:
        return None

    gender, height, weight, activity_level, birthdate, weight_goal = row
    age = nutrition.calculate_age(birthdate)
    calorie_goal = nutrition.calculate_calorie_goal(
        weight, height, age, gender, activity_level, weight_goal
    )
    calorie_goal += round(calories_burned)
    protein_goal = nutrition.calculate_protein_goal(weight)
    fat_goal = nutrition.calculate_fat_goal(calorie_goal)
    carb_goal = nutrition.calculate_carb_goal(calorie_goal, protein_goal, fat_goal)

    return {
        "calories": calorie_goal,
        "protein": protein_goal,
        "fat": fat_goal,
        "carbs": carb_goal,
    }

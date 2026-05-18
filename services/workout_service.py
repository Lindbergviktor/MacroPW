"""Tjänster för träningsdata.

Den här filen ansvarar för databasoperationer kopplade till träningspass,
som att hämta tillgängliga workouts och spara användarens träningsloggar.
"""

from db import get_db


def add_workout_log(duration, user_id, workout_id, log_date):
    with get_db() as cur:
        cur.execute(
            """
            INSERT INTO workout_log (duration, user_id, workout_id, weight, log_date)
            VALUES (%s, %s, %s, (SELECT weight FROM users WHERE user_id = %s), %s)
        """,
            (duration, user_id, workout_id, user_id, log_date),
        )


def get_workouts_for_user(user_id):
    with get_db() as cur:
        cur.execute(
            """
            SELECT w.workout_id, w.name, w.met, u.weight
            FROM workout w, users u
            WHERE u.user_id = %s
            ORDER BY w.name
        """,
            (user_id,),
        )
        return cur.fetchall()

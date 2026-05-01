"""Beräkning av personligt kalorimål (BMR, TDEE, viktmålsjustering)."""
from datetime import date

activity_factors = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

weight_goal_adjustment = {
    "loss": -500,
    "maintain": 0,
    "gain": +500,
}

def calculate_age(birthdate):
    """Räknar ut ålder i hela år utifrån födelsedatum."""
    today = date.today()
    age = today.year - birthdate.year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age

def calculate_bmr(weight, height, age, gender):
    """Mifflin-St Jeor BMR i kcal/dag."""
    bmr = (10 * float(weight)) + (6.25 * float(height)) - (5 * age)
    if gender == "male":
        bmr += 5
    else:
        bmr -= 161
    return bmr

def calculate_tdee(bmr, activity_level):
    """BMR multiplicerat med PAL."""
    return bmr * activity_factors.get(activity_level, 1.2)

def calculate_calorie_goal(weight, height, age, gender, activity_level, weight_goal):
    """TDEE justerat efter viktmål, avrundat till heltal."""
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    return round(tdee + weight_goal_adjustment.get(weight_goal, 0))


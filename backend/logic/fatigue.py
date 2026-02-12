from datetime import date, timedelta
from backend.db import save_fatigue_score, get_connection

BASE_DAILY_CAPACITY = 6  # hours


# ==============================
# Helper functions
# ==============================

def get_previous_fatigue(today):
    """
    Fetches fatigue score of the previous day.
    """
    conn = get_connection()
    if conn is None:
        return 0
    cursor = conn.cursor(dictionary=True)

    yesterday = today - timedelta(days=1)

    cursor.execute(
        "SELECT fatigue_score FROM fatigue_history WHERE date = %s",
        (yesterday,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["fatigue_score"] if result else 0


def get_today_planned_hours(today):
    """
    Fetches planned workload for today.
    """
    conn = get_connection()
    if conn is None:
        return 0
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT planned_hours FROM daily_workload WHERE date = %s",
        (today,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["planned_hours"] if result else 0


def determine_risk_level(score):
    """
    Converts fatigue score into risk category.
    """
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    else:
        return "high"


# ==============================
# Core Fatigue Logic
# ==============================

def calculate_and_store_fatigue():
    """
    Calculates fatigue score for today and stores it.
    """
    today = date.today()

    planned_hours = get_today_planned_hours(today)
    previous_fatigue = get_previous_fatigue(today)

    load_ratio = planned_hours / BASE_DAILY_CAPACITY if BASE_DAILY_CAPACITY else 0
    daily_fatigue = load_ratio * 30

    fatigue_score = previous_fatigue * 0.7 + daily_fatigue
    fatigue_score = min(int(fatigue_score), 100)

    risk_level = determine_risk_level(fatigue_score)

    save_fatigue_score(today, fatigue_score, risk_level)

    return {
        "date": today,
        "fatigue_score": fatigue_score,
        "risk_level": risk_level
    }

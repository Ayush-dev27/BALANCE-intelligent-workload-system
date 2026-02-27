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


def get_task_load_and_penalties(today):
    """
    Computes today's planned hours from tasks and
    fatigue penalties for overdue and near-deadline tasks.
    Completed tasks are ignored for both load and penalties.
    """
    conn = get_connection()
    if conn is None:
        return 0, 0, 0

    cursor = conn.cursor(dictionary=True)

    # Consider all non-completed tasks up to tomorrow
    cursor.execute(
        """
        SELECT planned_hours, due_date, status
        FROM tasks
        WHERE status != 'completed'
          AND due_date <= DATE_ADD(%s, INTERVAL 1 DAY)
        """,
        (today,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    planned_today = 0
    overdue_count = 0
    near_deadline_count = 0

    tomorrow = today + timedelta(days=1)

    for row in rows:
        due_date = row.get("due_date")
        hours = row.get("planned_hours") or 0

        if due_date == today:
            planned_today += hours
        elif due_date and due_date < today:
            overdue_count += 1
        elif due_date == tomorrow:
            near_deadline_count += 1

    return planned_today, overdue_count, near_deadline_count


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

    planned_hours, overdue_count, near_deadline_count = get_task_load_and_penalties(today)
    previous_fatigue = get_previous_fatigue(today)

    load_ratio = planned_hours / BASE_DAILY_CAPACITY if BASE_DAILY_CAPACITY else 0
    daily_fatigue = load_ratio * 30

    # Penalties: overdue tasks add more fatigue, near-deadline add a bit
    daily_fatigue += overdue_count * 2
    daily_fatigue += near_deadline_count * 1

    fatigue_score = previous_fatigue * 0.7 + daily_fatigue
    fatigue_score = min(int(fatigue_score), 100)

    risk_level = determine_risk_level(fatigue_score)

    save_fatigue_score(today, fatigue_score, risk_level)

    return {
        "date": today,
        "fatigue_score": fatigue_score,
        "risk_level": risk_level
    }

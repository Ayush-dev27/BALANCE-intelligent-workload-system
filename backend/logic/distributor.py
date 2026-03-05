from datetime import date
from backend.logic.fatigue import calculate_and_store_fatigue
from backend.db import update_daily_capacity

def calculate_adjusted_capacity(base_capacity, risk_level):
    if risk_level == "low":
        return base_capacity
    elif risk_level == "medium":
        return int(base_capacity * 0.75)
    elif risk_level == "high":
        return int(base_capacity * 0.5)
    else:
        return base_capacity


def apply_intelligent_distribution(user_id=None):
    today = date.today()

    # Step 1: Get fatigue + risk
    fatigue_data = calculate_and_store_fatigue(user_id=user_id)
    risk_level = fatigue_data["risk_level"]

    # Step 2: Base capacity (for now fixed) 
    base_capacity = 8

    # Step 3: Adjust capacity
    adjusted_capacity = calculate_adjusted_capacity(base_capacity, risk_level)

    # Step 4: Save to DB
    update_daily_capacity(today, adjusted_capacity)

    return {
        "date": today,
        "risk_level": risk_level,
        "adjusted_capacity": adjusted_capacity
    } 

from backend.db import get_tasks_for_date 


def analyze_task_distribution(user_id=None):
    today = date.today()

    # Step 1: Get tasks for today
    tasks = get_tasks_for_date(today, user_id=user_id)

    total_planned = sum(task["planned_hours"] for task in tasks)

    # Step 2: Get adjusted capacity (already calculated today)
    fatigue_data = calculate_and_store_fatigue(user_id=user_id)
    risk_level = fatigue_data["risk_level"]

    base_capacity = 8
    adjusted_capacity = calculate_adjusted_capacity(base_capacity, risk_level)

    overload = total_planned - adjusted_capacity

    return {
        "date": today,
        "risk_level": risk_level,
        "adjusted_capacity": adjusted_capacity,
        "total_planned_hours": total_planned,
        "overload_hours": overload if overload > 0 else 0,
        "status": "OVERLOADED" if overload > 0 else "BALANCED"
    } 
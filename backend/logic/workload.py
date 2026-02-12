from datetime import date
from backend.db import get_all_tasks, update_daily_workload

# ==============================
# Configuration
# ==============================

BASE_DAILY_CAPACITY = 6  # hours

DIFFICULTY_WEIGHTS = {
    1: 0.8,
    2: 0.9,
    3: 1.0,
    4: 1.2,
    5: 1.4
}


# ==============================
# Core Logic
# ==============================

def calculate_effective_hours(task):
    """
    Calculates fatigue-adjusted workload for a task.
    """
    weight = DIFFICULTY_WEIGHTS.get(task["difficulty"], 1.0)
    return task["estimated_hours"] * weight


def distribute_today_workload():
    """
    Assigns tasks to today based on capacity and priority.
    """
    today = date.today()
    tasks = get_all_tasks() or []

    # Only consider pending tasks
    pending_tasks = [t for t in tasks if t["status"] == "pending"]

    # Sort by priority (higher first)
    pending_tasks.sort(key=lambda x: x["priority"], reverse=True)

    remaining_capacity = BASE_DAILY_CAPACITY
    planned_hours = 0

    for task in pending_tasks:
        effective_hours = calculate_effective_hours(task)

        if effective_hours <= remaining_capacity:
            planned_hours += effective_hours
            remaining_capacity -= effective_hours
        else:
            break  # capacity reached

    update_daily_workload(today, planned_hours=planned_hours)

    return {
        "date": today,
        "planned_hours": planned_hours,
        "remaining_capacity": remaining_capacity
    }

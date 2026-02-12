from backend.logic.workload import distribute_today_workload
from backend.logic.fatigue import calculate_and_store_fatigue
from backend.logic.recommendations import generate_recommendations


def run_daily_cycle():
    """
    Runs workload planning, fatigue calculation, and recommendation generation.
    """
    workload_result = distribute_today_workload()
    fatigue_result = calculate_and_store_fatigue()

    recommendations = generate_recommendations(
        fatigue_score=fatigue_result["fatigue_score"],
        planned_hours=workload_result["planned_hours"],
        remaining_capacity=workload_result["remaining_capacity"],
    )

    return {
        "workload": workload_result,
        "fatigue": fatigue_result,
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    print(run_daily_cycle())

def generate_recommendations(fatigue_score, planned_hours, remaining_capacity):
    """
    Returns practical recommendations based on fatigue and today's workload.
    """
    recommendations = []

    if fatigue_score >= 70:
        recommendations.append("Reduce workload tomorrow and schedule recovery time.")
    elif fatigue_score >= 40:
        recommendations.append("Keep tasks moderate and include short breaks.")
    else:
        recommendations.append("Current load looks sustainable.")

    if planned_hours >= 6:
        recommendations.append("Avoid adding extra tasks today.")

    if remaining_capacity > 0:
        recommendations.append("Use remaining capacity for low-effort tasks.")

    return recommendations 
def generate_recommendations(distribution_data, fatigue_data):
    recommendations = []

    planned = distribution_data.get("total_planned_hours", 0)
    capacity = distribution_data.get("adjusted_capacity", 0)
    fatigue_score = fatigue_data.get("fatigue_score", 0)

    remaining = capacity - planned

    # Workload-based logic
    if remaining < 0:
        recommendations.append("You are overloaded. Reduce workload tomorrow.")
    else:
        recommendations.append("Workload is balanced. Maintain current pace.")

    # Fatigue-based logic
    if fatigue_score >= 75:
        recommendations.append("High fatigue detected. Prioritize recovery and rest.")
    elif fatigue_score >= 40:
        recommendations.append("Moderate fatigue. Avoid heavy tasks today.")
    else:
        recommendations.append("Low fatigue. You can take on focused deep work.")

    return recommendations 
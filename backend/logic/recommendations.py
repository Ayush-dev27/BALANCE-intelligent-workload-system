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

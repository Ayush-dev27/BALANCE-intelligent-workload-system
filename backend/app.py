from backend.logic.distributor import analyze_task_distribution
from backend.logic.fatigue import calculate_and_store_fatigue
from backend.logic.recommendations import generate_recommendations 
from flask import Flask, jsonify 
from flask import request

app = Flask(__name__) 


def run_daily_cycle():
    distribution = analyze_task_distribution() 
    fatigue_result = calculate_and_store_fatigue()

    recommendations = generate_recommendations(
    distribution_data=distribution,
    fatigue_data=fatigue_result
) 

    return {
        "distribution": distribution,
        "fatigue": fatigue_result,
        "recommendations": recommendations,
    } 


if __name__ == "__main__":
    print(run_daily_cycle()) 

from flask import Flask, jsonify
from backend.logic.distributor import analyze_task_distribution
from backend.logic.recommendations import generate_recommendations

def run_balance_engine():
    distribution = analyze_task_distribution()
    fatigue_result = calculate_and_store_fatigue()

    recommendations = generate_recommendations(
        distribution_data=distribution,
        fatigue_data=fatigue_result
    )

    return {
        "distribution": distribution,
        "fatigue": fatigue_result,
        "recommendations": recommendations
    } 
from flask import render_template

@app.route("/")
def home():
    return render_template("index.html") 


@app.route("/analyze", methods=["GET"])
def analyze():
    result = run_balance_engine()
    return jsonify(result)


@app.route("/add-task", methods=["POST"])
def add_task():
    data = request.json

    task = {
        "name": data.get("name"),
        "estimated_hours": float(data.get("estimated_hours")),
        "difficulty": int(data.get("difficulty")),
        "priority": int(data.get("priority")),
        "status": "pending"
    }

    from backend.db import add_task_to_db
    add_task_to_db(task)

    return {"message": "Task added successfully"}, 201


@app.route("/tasks", methods=["GET"])
def list_tasks():
    from backend.db import get_all_tasks
    tasks = get_all_tasks()
    for t in tasks:
        if t.get("due_date"):
            t["due_date"] = t["due_date"].isoformat() 
    return jsonify(tasks)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task_route(task_id):
    from backend.db import delete_task
    deleted = delete_task(task_id)
    if not deleted:
        return jsonify({"error": "Task not found"}), 404
    result = run_balance_engine()
    return jsonify({
        "message": "Task deleted",
        "distribution": result["distribution"],
        "fatigue": result["fatigue"],
        "recommendations": result["recommendations"]
    })


@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task_route(task_id):
    from backend.db import update_task_status
    updated = update_task_status(task_id, "completed")
    if not updated:
        return jsonify({"error": "Task not found"}), 404
    result = run_balance_engine()
    return jsonify({
        "message": "Task completed",
        "distribution": result["distribution"],
        "fatigue": result["fatigue"],
        "recommendations": result["recommendations"]
    })


if __name__ == "__main__":
    app.run(debug=True) 

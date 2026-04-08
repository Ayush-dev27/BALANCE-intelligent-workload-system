from backend.logic.distributor import analyze_task_distribution
from backend.logic.fatigue import calculate_and_store_fatigue
from backend.logic.recommendations import generate_recommendations 
from flask import Flask, jsonify 
from flask import request, session, redirect, url_for
from datetime import date, timedelta
from functools import wraps

app = Flask(__name__) 
app.config["SECRET_KEY"] = "change-this-secret-key"


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


from flask import Flask, jsonify
from backend.logic.distributor import analyze_task_distribution
from backend.logic.recommendations import generate_recommendations


def run_balance_engine(user_id=None):
    distribution = analyze_task_distribution(user_id=user_id)
    fatigue_result = calculate_and_store_fatigue(user_id=user_id)

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


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)

    return wrapper
# --- ADD THIS SECTION ---
def init_db():
    from backend.db import get_connection # Assuming this helper exists in your db.py
    conn = get_connection() 
    if conn is None:
        print("CRITICAL: Could not connect to the database. Check your Render Environment Variables!")
        return # Stop here so it doesn't try to call .cursor() and crash 
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        );
    """) 
    
    # Create Tasks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            title VARCHAR(200) NOT NULL,
            planned_hours FLOAT,
            difficulty INT,
            priority INT,
            status VARCHAR(50) DEFAULT 'pending',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit() 
    cursor.close()
    conn.close()



@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html") 


@app.route("/analyze", methods=["GET"])
@login_required
def analyze():
    user_id = session["user_id"]
    result = run_balance_engine(user_id=user_id)
    return jsonify(result)


@app.route("/add-task", methods=["POST"])
@login_required
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
    user_id = session["user_id"]
    add_task_to_db(task, user_id)

    return {"message": "Task added successfully"}, 201


@app.route("/tasks", methods=["GET"])
@login_required
def list_tasks():
    from backend.db import get_all_tasks
    user_id = session["user_id"]
    tasks = get_all_tasks(user_id=user_id)
    for t in tasks:
        if t.get("due_date"):
            t["due_date"] = t["due_date"].isoformat() 
    return jsonify(tasks)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task_route(task_id):
    from backend.db import delete_task
    user_id = session["user_id"]
    deleted = delete_task(task_id, user_id=user_id)
    if not deleted:
        return jsonify({"error": "Task not found"}), 404
    result = run_balance_engine(user_id=user_id)
    return jsonify({
        "message": "Task deleted",
        "distribution": result["distribution"],
        "fatigue": result["fatigue"],
        "recommendations": result["recommendations"]
    })


@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
@login_required
def complete_task_route(task_id):
    from backend.db import update_task_status
    user_id = session["user_id"]
    updated = update_task_status(task_id, "completed", user_id=user_id)
    if not updated:
        return jsonify({"error": "Task not found"}), 404
    result = run_balance_engine(user_id=user_id)
    return jsonify({
        "message": "Task completed",
        "distribution": result["distribution"],
        "fatigue": result["fatigue"],
        "recommendations": result["recommendations"]
    })


@app.route("/analytics", methods=["GET"])
@login_required
def analytics():
    from backend.db import get_all_tasks

    mode = request.args.get("mode", "daily")

    user_id = session["user_id"]
    tasks = get_all_tasks(user_id=user_id)
    today = date.today()

    difficulty_distribution = {str(i): 0 for i in range(1, 6)}
    priority_distribution = {str(i): 0 for i in range(1, 4)}
    status_distribution = {"pending": 0, "completed": 0, "overdue": 0}

    # Scope of tasks for aggregation
    if mode == "weekly":
        window_start = today - timedelta(days=6)
        tasks_scope = []
        for t in tasks:
            due_date = t.get("due_date")
            if due_date is not None and hasattr(due_date, "toordinal") and window_start <= due_date <= today:
                tasks_scope.append(t)
    else:
        # daily mode keeps existing behavior: consider all tasks
        tasks_scope = tasks

    total_tasks = len(tasks_scope)
    completed_tasks = 0

    for t in tasks_scope:
        diff = str(t.get("difficulty") or "")
        if diff in difficulty_distribution:
            difficulty_distribution[diff] += 1

        prio_raw = t.get("priority")
        if prio_raw is not None:
            prio_bucket = min(int(prio_raw), 3)
            priority_distribution[str(prio_bucket)] += 1

        status = t.get("status") or "pending"
        due_date = t.get("due_date")

        is_overdue = (
            due_date is not None
            and hasattr(due_date, "toordinal")
            and due_date < today
            and status != "completed"
        )

        if status == "completed":
            completed_tasks += 1
            status_distribution["completed"] += 1
        elif is_overdue:
            status_distribution["overdue"] += 1
        else:
            # Treat non-completed, non-overdue (including in_progress) as pending bucket
            status_distribution["pending"] += 1

    # Aggregate total planned hours per day
    if mode == "weekly":
        window_start = today - timedelta(days=6)
        total_planned_hours_per_day = {
            (window_start + timedelta(days=offset)).isoformat(): 0 for offset in range(7)
        }
        for t in tasks_scope:
            due_date = t.get("due_date")
            hours = t.get("planned_hours") or 0
            if (
                due_date is not None
                and hasattr(due_date, "toordinal")
                and window_start <= due_date <= today
            ):
                total_planned_hours_per_day[due_date.isoformat()] += hours
    else:
        key = today.isoformat()
        total_planned_hours_per_day = {key: 0}
        for t in tasks_scope:
            due_date = t.get("due_date")
            hours = t.get("planned_hours") or 0
            if due_date is not None and hasattr(due_date, "toordinal") and due_date == today:
                total_planned_hours_per_day[key] += hours

    return jsonify({
        "difficulty_distribution": difficulty_distribution,
        "priority_distribution": priority_distribution,
        "status_distribution": status_distribution,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_planned_hours_per_day": total_planned_hours_per_day,
    })


@app.route("/register", methods=["GET", "POST"])
def register():
    from backend.db import create_user, get_user_by_username
    from werkzeug.security import generate_password_hash

    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing = get_user_by_username(username)
    if existing:
        return jsonify({"error": "Username already taken"}), 400

    password_hash = generate_password_hash(password)
    created = create_user(username, password_hash)
    if not created:
        return jsonify({"error": "Failed to create user"}), 500

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["GET", "POST"])
def login():
    from backend.db import get_user_by_username
    from werkzeug.security import check_password_hash

    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({"message": "Login successful"}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


if __name__ == "__main__":
    import os
    # Use the port Render provides, or default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port) 
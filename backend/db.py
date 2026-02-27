import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="AIWEEB",
            database="balance"
        )
        return connection
    except Error as e:
        print("Database connection failed:", e)
        return None 
    
def save_fatigue_score(date, fatigue_score, risk_level):
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    query = """
    INSERT INTO fatigue_history (date, fatigue_score, risk_level)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        fatigue_score = VALUES(fatigue_score),
        risk_level = VALUES(risk_level)
    """

    cursor.execute(query, (date, fatigue_score, risk_level))
    conn.commit()

    cursor.close()
    conn.close()  

def update_daily_capacity(date, adjusted_capacity):
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    query = """
    INSERT INTO daily_workload (date, capacity_hours)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
        capacity_hours = VALUES(capacity_hours)
    """

    cursor.execute(query, (date, adjusted_capacity))
    conn.commit()

    cursor.close()
    conn.close() 

def get_tasks_for_date(target_date):
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT id, title, planned_hours, priority
    FROM tasks
    WHERE due_date = %s AND status != 'completed'
    """

    cursor.execute(query, (target_date,))
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return tasks 
def add_task_to_db(task):
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    query = """
        INSERT INTO tasks (title, planned_hours, difficulty, priority, status, due_date)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
    """

    values = (
        task["name"],
        task["estimated_hours"],
        task["difficulty"],
        task["priority"],
        task["status"]
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


def get_all_tasks():
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT id, title, planned_hours, difficulty, priority, status, due_date
    FROM tasks
    ORDER BY due_date, priority DESC
    """
    cursor.execute(query)
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return tasks


def delete_task(task_id):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    query = "DELETE FROM tasks WHERE id = %s"
    cursor.execute(query, (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return deleted


def update_task_status(task_id, status):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    query = "UPDATE tasks SET status = %s WHERE id = %s"
    cursor.execute(query, (status, task_id))
    updated = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return updated
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


def create_user(username, password_hash):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, password_hash),
        )
        conn.commit()
        return True
    except Error as e:
        # Likely duplicate username
        print("Failed to create user:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (username,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
    
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

def get_tasks_for_date(target_date, user_id=None):
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)

    if user_id is not None:
        query = """
        SELECT id, title, planned_hours, priority
        FROM tasks
        WHERE due_date = %s AND status != 'completed'
          AND user_id = %s
        """
        cursor.execute(query, (target_date, user_id))
    else:
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
def add_task_to_db(task, user_id):
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    query = """
        INSERT INTO tasks (title, planned_hours, difficulty, priority, status, due_date, user_id)
        VALUES (%s, %s, %s, %s, %s, CURDATE(), %s)
    """

    values = (
        task["name"],
        task["estimated_hours"],
        task["difficulty"],
        task["priority"],
        task["status"],
        user_id,
    )

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


def get_all_tasks(user_id=None):
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    if user_id is not None:
        query = """
        SELECT id, title, planned_hours, difficulty, priority, status, due_date
        FROM tasks
        WHERE user_id = %s
        ORDER BY due_date, priority DESC
        """
        cursor.execute(query, (user_id,))
    else:
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


def delete_task(task_id, user_id=None):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    if user_id is not None:
        query = "DELETE FROM tasks WHERE id = %s AND user_id = %s"
        cursor.execute(query, (task_id, user_id))
    else:
        query = "DELETE FROM tasks WHERE id = %s"
        cursor.execute(query, (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return deleted


def update_task_status(task_id, status, user_id=None):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    if user_id is not None:
        query = "UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s"
        cursor.execute(query, (status, task_id, user_id))
    else:
        query = "UPDATE tasks SET status = %s WHERE id = %s"
        cursor.execute(query, (status, task_id))
    updated = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return updated
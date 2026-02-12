import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="your_password_here",
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
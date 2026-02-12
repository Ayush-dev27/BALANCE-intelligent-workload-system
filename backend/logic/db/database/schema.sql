-- =========================
-- BALANCE Database Schema
-- =========================

CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    estimated_hours FLOAT NOT NULL,
    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),
    priority INT CHECK (priority BETWEEN 1 AND 5),
    status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
    created_at DATE DEFAULT CURRENT_DATE
);

CREATE TABLE daily_workload (
    date DATE PRIMARY KEY,
    planned_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0
);

CREATE TABLE task_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT,
    date DATE,
    hours_spent FLOAT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE fatigue_history (
    date DATE PRIMARY KEY,
    fatigue_score INT CHECK (fatigue_score BETWEEN 0 AND 100),
    risk_level ENUM('low', 'medium', 'high')
);

function updateDashboard(data) {
    const distribution = data.distribution;
    document.getElementById("date").textContent = distribution.date;
    document.getElementById("planned").textContent = distribution.total_planned_hours;
    document.getElementById("capacity").textContent = distribution.adjusted_capacity;

    const statusElement = document.getElementById("status");
    const status = distribution.status;
    statusElement.textContent = status;
    statusElement.classList.remove("status-balanced", "status-overloaded", "status-risk");
    if (status === "BALANCED") {
        statusElement.classList.add("status-balanced");
    } else if (status === "OVERLOADED") {
        statusElement.classList.add("status-overloaded");
    } else {
        statusElement.classList.add("status-risk");
    }

    const fatigueScore = data.fatigue.fatigue_score;
    document.getElementById("fatigue").textContent = fatigueScore;
    const fatigueFill = document.getElementById("fatigue-fill");
    fatigueFill.style.width = fatigueScore + "%";
    const fatigueLabel = document.getElementById("fatigue-label");
    if (fatigueScore < 40) {
        fatigueFill.style.background = "#28a745";
        fatigueLabel.textContent = "Low Fatigue";
        fatigueLabel.className = "fatigue-label fatigue-low";
    } else if (fatigueScore < 70) {
        fatigueFill.style.background = "#ffc107";
        fatigueLabel.textContent = "Moderate Fatigue";
        fatigueLabel.className = "fatigue-label fatigue-moderate";
    } else {
        fatigueFill.style.background = "#dc3545";
        fatigueLabel.textContent = "High Fatigue";
        fatigueLabel.className = "fatigue-label fatigue-high";
    }

    const recommendationsContainer = document.getElementById("recommendations");
    recommendationsContainer.innerHTML = "";
    data.recommendations.forEach(rec => {
        const div = document.createElement("div");
        div.className = "recommendation-card";
        div.textContent = rec;
        recommendationsContainer.appendChild(div);
    });
}

function renderTaskList(tasks) {
    const tbody = document.getElementById("task-list-body");
    tbody.innerHTML = "";
    tasks.forEach(task => {
        const tr = document.createElement("tr");
        const dueDate = task.due_date || "";

        const rawStatus = task.status || "pending";
        let displayStatus = rawStatus;
        let statusClass = "task-status-pending";

        if (rawStatus === "completed") {
            statusClass = "task-status-completed";
            tr.classList.add("task-completed");
        } else if (dueDate) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const due = new Date(dueDate);
            due.setHours(0, 0, 0, 0);

            if (due < today) {
                displayStatus = "overdue";
                statusClass = "task-status-overdue";
            }
        }

        tr.innerHTML = `
            <td>${escapeHtml(task.title)}</td>
            <td>${task.planned_hours}</td>
            <td>${task.difficulty}</td>
            <td>${task.priority}</td>
            <td><span class="task-status-badge ${statusClass}">${escapeHtml(displayStatus)}</span></td>
            <td>${escapeHtml(dueDate)}</td>
            <td>
                <button type="button" class="btn-complete" data-id="${task.id}" ${rawStatus === "completed" ? "disabled" : ""}>Complete</button>
                <button type="button" class="btn-delete" data-id="${task.id}">Delete</button>
            </td>
        `;

        const completeBtn = tr.querySelector(".btn-complete");
        if (completeBtn && !completeBtn.disabled) {
            completeBtn.addEventListener("click", () => completeTask(task.id));
        }

        tr.querySelector(".btn-delete").addEventListener("click", () => deleteTask(task.id));
        tbody.appendChild(tr);
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function loadTasks() {
    fetch("/tasks")
        .then(response => response.json())
        .then(tasks => {
            renderTaskList(tasks);
            loadAnalytics();
        });
}

let difficultyChartInstance = null;
let priorityChartInstance = null;
let statusChartInstance = null;

function loadAnalytics() {
    fetch("/analytics")
        .then(response => response.json())
        .then(data => {
            const difficultyCtx = document.getElementById("difficultyChart").getContext("2d");
            const priorityCtx = document.getElementById("priorityChart").getContext("2d");
            const statusCtx = document.getElementById("statusChart").getContext("2d");

            if (difficultyChartInstance) {
                difficultyChartInstance.destroy();
            }
            if (priorityChartInstance) {
                priorityChartInstance.destroy();
            }
            if (statusChartInstance) {
                statusChartInstance.destroy();
            }

            difficultyChartInstance = new Chart(difficultyCtx, {
                type: "bar",
                data: {
                    labels: ["1", "2", "3", "4", "5"],
                    datasets: [{
                        label: "Tasks",
                        data: [
                            data.difficulty_distribution["1"],
                            data.difficulty_distribution["2"],
                            data.difficulty_distribution["3"],
                            data.difficulty_distribution["4"],
                            data.difficulty_distribution["5"],
                        ],
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgba(54, 162, 235, 1)",
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                            },
                        },
                    },
                },
            });

            const priorityColors = [
                "rgba(40, 167, 69, 0.7)",
                "rgba(255, 193, 7, 0.7)",
                "rgba(220, 53, 69, 0.7)",
            ];

            priorityChartInstance = new Chart(priorityCtx, {
                type: "pie",
                data: {
                    labels: ["Priority 1", "Priority 2", "Priority 3+"],
                    datasets: [{
                        data: [
                            data.priority_distribution["1"],
                            data.priority_distribution["2"],
                            data.priority_distribution["3"],
                        ],
                        backgroundColor: priorityColors,
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                },
            });

            const statusColors = [
                "rgba(255, 193, 7, 0.7)",  // pending
                "rgba(40, 167, 69, 0.7)",  // completed
                "rgba(220, 53, 69, 0.7)",  // overdue
            ];

            statusChartInstance = new Chart(statusCtx, {
                type: "doughnut",
                data: {
                    labels: ["Pending", "Completed", "Overdue"],
                    datasets: [{
                        data: [
                            data.status_distribution.pending,
                            data.status_distribution.completed,
                            data.status_distribution.overdue,
                        ],
                        backgroundColor: statusColors,
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                },
            });
        });
}

async function deleteTask(taskId) {
    const res = await fetch(`/tasks/${taskId}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || "Failed to delete task");
        return;
    }
    updateDashboard(data);
    loadTasks();
}

async function completeTask(taskId) {
    const res = await fetch(`/tasks/${taskId}/complete`, { method: "PUT" });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || "Failed to complete task");
        return;
    }
    updateDashboard(data);
    loadTasks();
}

fetch("/analyze")
    .then(response => response.json())
    .then(data => {
        updateDashboard(data);
        loadTasks();
    });

async function addTask() {
    const name = document.getElementById("task-name").value;
    const hours = document.getElementById("task-hours").value;
    const difficulty = document.getElementById("task-difficulty").value;
    const priority = document.getElementById("task-priority").value;

    if (!name || !hours) {
        alert("Please fill all required fields.");
        return;
    }

    const res = await fetch("/add-task", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            estimated_hours: hours,
            difficulty: difficulty,
            priority: priority
        })
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(data.error || "Failed to add task");
        return;
    }

    // After creating a task, refresh dashboard and analytics without full reload
    const analyzeRes = await fetch("/analyze");
    if (analyzeRes.ok) {
        const analyzeData = await analyzeRes.json();
        updateDashboard(analyzeData);
    }
    loadTasks();
} 
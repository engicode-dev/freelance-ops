from datetime import date, datetime

VALID_TRANSITIONS = {
    "todo":        {"in_progress", "cancelled"},
    "in_progress": {"done", "todo", "cancelled"},
    "done":        {"in_progress"},
    "cancelled":   {"todo"},
}

def change_status(conn, task_id: int, new_status: str) -> None:
    row = conn.execute("SELECT status FROM task WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise ValueError(f"task {task_id} not found")
    old = row["status"]
    if new_status not in VALID_TRANSITIONS[old]:
        raise ValueError(f"нельзя перейти {old} → {new_status}")
    completed_at = datetime.now().isoformat() if new_status == "done" else None
    conn.execute(
        "UPDATE task SET status = ?, completed_at = ? WHERE id = ?",
        (new_status, completed_at, task_id),
    )
    conn.commit()

def overdue(conn) -> list[dict]:
    today = date.today().isoformat()
    rows = conn.execute(
        """SELECT * FROM task
           WHERE status NOT IN ('done','cancelled')
             AND due_date IS NOT NULL AND due_date < ?
           ORDER BY due_date""",
        (today,),
    ).fetchall()
    return [dict(r) for r in rows]

def planned_for(conn, day: date) -> list[dict]:
    rows = conn.execute(
        """SELECT * FROM task
           WHERE planned_date = ?
             AND status NOT IN ('done','cancelled')
           ORDER BY priority, id""",
        (day.isoformat(),),
    ).fetchall()
    return [dict(r) for r in rows]

def delete_task(conn, task_id: int) -> None:
    # Сначала удаляем все сессии времени, привязанные к задаче
    conn.execute("DELETE FROM time_session WHERE task_id = ?", (task_id,))
    # Удаляем саму задачу
    conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
    conn.commit()
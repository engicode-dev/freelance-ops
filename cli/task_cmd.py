from datetime import datetime

from models import Task

def register(sub):
    p = sub.add_parser("task", help="задачи")
    s = p.add_subparsers(dest="action", required=True)

    a = s.add_parser("add")
    a.add_argument("--title", required=True)
    a.add_argument("--client", type=int)
    a.add_argument("--desc", default="")
    a.add_argument("--priority", type=int, choices=[1, 2, 3], default=2)
    a.add_argument("--due", help="YYYY-MM-DD")
    a.add_argument("--plan", help="YYYY-MM-DD, на какой день планирую")
    a.add_argument("--price", type=float, help="ожидаемая сумма, ₽")
    a.add_argument("--est-hours", type=float)
    a.set_defaults(func=add)

    l = s.add_parser("list")
    l.add_argument("--status", choices=["todo", "in_progress", "done", "cancelled"])
    l.add_argument("--client", type=int)
    l.set_defaults(func=list_tasks)

    m = s.add_parser("move")
    m.add_argument("id", type=int)
    m.add_argument("status", choices=["todo", "in_progress", "done", "cancelled"])
    m.set_defaults(func=move)

    e = s.add_parser("edit")
    e.add_argument("id", type=int)
    e.add_argument("--title")
    e.add_argument("--due", help="YYYY-MM-DD")
    e.add_argument("--plan", help="YYYY-MM-DD")
    e.add_argument("--priority", type=int, choices=[1, 2, 3])
    e.set_defaults(func=edit)

def _date_or_none(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None

def _price_to_kop(v):
    return int(round(v * 100)) if v is not None else None

def add(conn, args):
    conn.execute(
        """INSERT INTO task
           (title, client_id, description, priority, due_date, planned_date,
            price_kopecks, hours_estimated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            args.title,
            args.client,
            args.desc,
            args.priority,
            args.due,
            args.plan,
            _price_to_kop(args.price),
            args.est_hours,
        ),
    )
    conn.commit()
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"✔ задача #{tid} «{args.title}» создана")

def list_tasks(conn, args):
    sql = "SELECT t.*, c.name AS client_name FROM task t LEFT JOIN client c ON c.id = t.client_id WHERE 1=1"
    params = []
    if args.status:
        sql += " AND t.status = ?"
        params.append(args.status)
    if args.client:
        sql += " AND t.client_id = ?"
        params.append(args.client)
    sql += " ORDER BY t.priority, COALESCE(t.due_date, '9999-12-31'), t.id"

    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("задач нет")
        return
    for r in rows:
        mark = {"todo": "·", "in_progress": "▶", "done": "✔", "cancelled": "✖"}[r["status"]]
        due = f" due={r['due_date']}" if r["due_date"] else ""
        client = f" [{r['client_name']}]" if r["client_name"] else ""
        hours = f" {r['hours_spent']:.1f}ч" if r["hours_spent"] else ""
        print(f"  {mark} [{r['id']:>3}] {r['title']}{client}{due}{hours}")

def move(conn, args):
    from services.tasks import change_status
    try:
        change_status(conn, args.id, args.status)
        print(f"✔ задача #{args.id} → {args.status}")
    except ValueError as e:
        print(f"✖ {e}")

def edit(conn, args):
    fields, params = [], []
    if args.title is not None:
        fields.append("title = ?"); params.append(args.title)
    if args.due is not None:
        fields.append("due_date = ?"); params.append(args.due)
    if args.plan is not None:
        fields.append("planned_date = ?"); params.append(args.plan)
    if args.priority is not None:
        fields.append("priority = ?"); params.append(args.priority)
    if not fields:
        print("нечего менять"); return
    params.append(args.id)
    conn.execute(f"UPDATE task SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    print(f"✔ задача #{args.id} обновлена")
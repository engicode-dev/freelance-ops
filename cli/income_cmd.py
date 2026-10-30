from datetime import date as _date, datetime

def register(sub):
    p = sub.add_parser("income", help="доходы")
    s = p.add_subparsers(dest="action", required=True)

    a = s.add_parser("add")
    a.add_argument("--amount", type=float, required=True, help="₽")
    a.add_argument("--type", choices=["active", "passive"], required=True)
    a.add_argument("--date", default=_date.today().isoformat())
    a.add_argument("--task", type=int, help="id задачи")
    a.add_argument("--desc", default="")
    a.set_defaults(func=add)

    l = s.add_parser("list")
    l.add_argument("--start", default=_date.today().replace(day=1).isoformat())
    l.add_argument("--end", default=_date.today().isoformat())
    l.set_defaults(func=list_incomes)

def add(conn, args):
    kop = int(round(args.amount * 100))
    conn.execute(
        "INSERT INTO income (date, amount_kopecks, type, task_id, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (args.date, kop, args.type, args.task, args.desc),
    )
    conn.commit()
    print(f"✔ доход {args.amount:.2f} ₽ [{args.type}] за {args.date}")

def list_incomes(conn, args):
    rows = conn.execute(
        "SELECT * FROM income WHERE date BETWEEN ? AND ? ORDER BY date",
        (args.start, args.end),
    ).fetchall()
    if not rows:
        print("доходов за период нет"); return
    for r in rows:
        task = f" task#{r['task_id']}" if r["task_id"] else ""
        print(f"  {r['date']}  {r['amount_kopecks']/100:>10,.2f} ₽  {r['type']:<7}{task}  {r['description']}")
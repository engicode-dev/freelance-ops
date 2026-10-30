def register(sub):
    p = sub.add_parser("client", help="клиенты")
    s = p.add_subparsers(dest="action", required=True)

    a = s.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--contact")
    a.add_argument("--notes", default="")
    a.set_defaults(func=add)

    l = s.add_parser("list")
    l.set_defaults(func=list_clients)

def add(conn, args):
    conn.execute(
        "INSERT INTO client (name, contact, notes) VALUES (?, ?, ?)",
        (args.name, args.contact, args.notes),
    )
    conn.commit()
    print(f"✔ клиент «{args.name}» добавлен")

def list_clients(conn, args):
    rows = conn.execute("SELECT id, name, contact FROM client ORDER BY name").fetchall()
    if not rows:
        print("клиентов нет"); return
    for r in rows:
        print(f"  [{r['id']:>3}] {r['name']:<30} {r['contact'] or ''}")
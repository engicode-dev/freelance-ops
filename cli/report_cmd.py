from datetime import date, datetime, timedelta

from services.stats import calculate

DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def register(sub):
    p = sub.add_parser("report", help="отчёт за период")
    p.add_argument("--start", default=date.today().replace(day=1).isoformat())
    p.add_argument("--end", default=date.today().isoformat())
    p.set_defaults(func=report)

    t = sub.add_parser("today", help="что делать сегодня")
    t.set_defaults(func=today)

    w = sub.add_parser("week", help="неделя вперёд")
    w.set_defaults(func=week)


# ───────────────────────── report ─────────────────────────

def report(conn, args):
    incomes = [dict(r) for r in conn.execute(
        "SELECT * FROM income WHERE date BETWEEN ? AND ?",
        (args.start, args.end),
    ).fetchall()]

    hours_by_income = {}
    for inc in incomes:
        if not inc["task_id"]:
            continue
        row = conn.execute(
            "SELECT COALESCE(SUM((julianday(COALESCE(end, datetime('now'))) "
            "                    - julianday(start)) * 24.0), 0) AS h "
            "FROM time_session WHERE task_id = ?",
            (inc["task_id"],),
        ).fetchone()
        hours_by_income[inc["id"]] = row["h"] or 0.0

    s = calculate(incomes, hours_by_income)

    print(f"\nПериод: {args.start} … {args.end}")
    print(f"Записей: {len(incomes)}")
    print(f"  актив:  {s.active_kop/100:>12,.2f} ₽")
    print(f"  пассив: {s.passive_kop/100:>12,.2f} ₽")
    print(f"  ИТОГО:  {s.total_kop/100:>12,.2f} ₽")
    print(f"  часов по активу: {s.paid_hours:.2f}")
    if s.effective_rate_kop is not None:
        print(f"  ставка в час (по периоду): {s.effective_rate_kop/100:,.0f} ₽/ч")
    else:
        print("  ставка в час (по периоду): — (нет оплаченных часов)")
    print(f"  доля пассива:    {s.passive_share*100:.1f}%")

    _print_by_task(conn, args)


def _print_by_task(conn, args):
    """Ставка по каждой задаче — осмысленная единица анализа."""
    rows = conn.execute(
        """SELECT t.id, t.title, t.status,
                  COALESCE(SUM(i.amount_kopecks), 0) AS income_kop,
                  COALESCE(SUM(CASE WHEN ts.end IS NOT NULL
                     THEN (julianday(ts.end) - julianday(ts.start)) * 24.0
                     ELSE (julianday('now') - julianday(ts.start)) * 24.0
                  END), 0) AS hours
           FROM task t
           LEFT JOIN income i ON i.task_id = t.id AND i.date BETWEEN ? AND ?
           LEFT JOIN time_session ts ON ts.task_id = t.id
           GROUP BY t.id
           HAVING income_kop > 0 OR hours > 0
           ORDER BY income_kop DESC""",
        (args.start, args.end),
    ).fetchall()

    if not rows:
        return

    print("\n  ── по задачам ──")
    for r in rows:
        mark = {"todo": "·", "in_progress": "▶", "done": "✔", "cancelled": "✖"}[r["status"]]
        rate = ""
        if r["hours"] > 0.05:                # меньше 3 минут — не считаем
            rate_kop = r["income_kop"] / r["hours"]
            rate = f"  {rate_kop/100:>8,.0f} ₽/ч"
        print(f"  {mark} [{r['id']:>3}] {r['title'][:40]:<40} "
              f"{r['income_kop']/100:>10,.2f} ₽  {r['hours']:>5.1f}ч{rate}")


# ───────────────────────── today ─────────────────────────

def today(conn, args):
    from services.tasks import overdue, planned_for

    print("\n── ПРОСРОЧЕНО ──")
    rows = overdue(conn)
    if not rows:
        print("  (пусто)")
    for t in rows:
        print(f"  ! [{t['id']:>3}] {t['title']} (due {t['due_date']})")

    print("\n── НА СЕГОДНЯ ──")
    rows = planned_for(conn, date.today())
    if not rows:
        print("  (пусто)")
    for t in rows:
        mark = "▶" if t["status"] == "in_progress" else "·"
        print(f"  {mark} [{t['id']:>3}] {t['title']}")
    print()


# ───────────────────────── week ─────────────────────────

def week(conn, args):
    base = date.today()
    for i in range(7):
        day = base + timedelta(days=i)
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM task WHERE planned_date = ? "
            "AND status NOT IN ('done','cancelled') ORDER BY priority, id",
            (day.isoformat(),),
        ).fetchall()]
        print(f"\n{DAYS_RU[day.weekday()]} {day.strftime('%d.%m')}:")
        if not rows:
            print("  —")
        for t in rows:
            print(f"  · [{t['id']:>3}] {t['title']}")
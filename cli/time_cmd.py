from services import timer

def register(sub):
    p = sub.add_parser("time", help="таймер")
    s = p.add_subparsers(dest="action", required=True)

    st = s.add_parser("start")
    st.add_argument("task_id", type=int)
    st.set_defaults(func=start)

    sp = s.add_parser("stop")
    sp.set_defaults(func=stop)

    s.add_parser("status").set_defaults(func=status)

def start(conn, args):
    try:
        timer.start(conn, args.task_id)
        print(f"▶ таймер запущен на задачу #{args.task_id}")
    except RuntimeError as e:
        print(f"✖ {e}")

def stop(conn, args):
    try:
        hours = timer.stop(conn)
        print(f"■ таймер остановлен, +{hours*60:.0f} мин")
    except RuntimeError as e:
        print(f"✖ {e}")

def status(conn, args):
    s = timer.active_session(conn)
    if not s:
        print("таймер не запущен"); return
    print(f"▶ активен с {s['start']} на задаче #{s['task_id']}")
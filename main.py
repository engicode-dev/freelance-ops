import argparse
import sys

from db import connect
from cli import client_cmd, task_cmd, income_cmd, time_cmd, report_cmd


def build_parser():
    p = argparse.ArgumentParser(prog="tracker", description="Менеджмент фрилансера")
    sub = p.add_subparsers(dest="cmd", required=True)
    for mod in (client_cmd, task_cmd, income_cmd, time_cmd, report_cmd):
        if hasattr(mod, "register"):
            mod.register(sub)
    return p


def main():
    if len(sys.argv) == 1:
        # без аргументов → GUI
        from ui.app import run
        run(connect())
        return

    args = build_parser().parse_args()
    conn = connect()
    try:
        args.func(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
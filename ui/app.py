import tkinter as tk
import sys
import os

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.tab_today import TodayTab
from ui.tab_tasks import TasksTab
from ui.tab_money import MoneyTab
from ui.tab_journal import JournalTab
from ui.tab_charts import ChartsTab


class App(ttk.Window):
    def __init__(self, conn):
        # 1. Достаем сохраненный размер из БД
        geom_row = conn.execute("SELECT value FROM settings WHERE key='window_geometry'").fetchone()
        geom = geom_row["value"] if geom_row else "1100x700+100+100"

        # 2. Создаем окно (className задает WM_CLASS для Linux)
        super().__init__(themename="catppuccin-dark", title="Freelance Ops", className="FreelanceOps")
        self.conn = conn

        # 3. Применяем размер и позицию
        self.geometry(geom)

        # 4. Иконка
        def get_resource_path(relative_path):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)

        try:
            self.iconphoto(True, tk.PhotoImage(file=get_resource_path("icon.png")))
        except Exception as e:
            print("Не удалось загрузить иконку:", e)

        # 5. Вкладки
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, padx=8, pady=8)

        self.tab_today = TodayTab(self.notebook, conn)
        self.tab_tasks = TasksTab(self.notebook, conn)
        self.tab_money = MoneyTab(self.notebook, conn)
        self.tab_journal = JournalTab(self.notebook, conn)
        self.tab_charts = ChartsTab(self.notebook, conn)

        self.notebook.add(self.tab_today, text="Сегодня")
        self.notebook.add(self.tab_tasks, text="Задачи")
        self.notebook.add(self.tab_money, text="Деньги")
        self.notebook.add(self.tab_journal, text="Дневник")
        self.notebook.add(self.tab_charts, text="Графики")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self.after(1000, self._tick)

        # 6. Обработчик закрытия окна для сохранения геометрии
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_tab_change(self, _event):
        current = self.notebook.select()
        widget = self.nametowidget(current)
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _tick(self):
        if hasattr(self.tab_today, "tick"):
            self.tab_today.tick()
        self.after(1000, self._tick)

    def _on_close(self):
        # Сохраняем геометрию перед выходом
        try:
            self.conn.execute(
                "INSERT INTO settings (key, value) VALUES ('window_geometry', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self.geometry(),)
            )
            self.conn.commit()
        except Exception:
            pass
        self.destroy()


def run(conn):
    app = App(conn)
    app.mainloop()
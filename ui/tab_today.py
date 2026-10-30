from datetime import date, datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from services.tasks import overdue, planned_for
from services import timer


class TodayTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.refresh()

    def _build(self):
        # Верхняя панель: Таймер, Помодоро и Заметка
        top = ttk.Labelframe(self, text="Таймер и Помодоро", bootstyle="info")
        top.pack(fill=X, padx=8, pady=8)

        self.timer_label = ttk.Label(top, text="—", font=("TkDefaultFont", 16, "bold"))
        self.timer_label.pack(side=LEFT, padx=12, pady=8)

        # Переключатель Помодоро
        self.pomo_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="🍅 25 мин", variable=self.pomo_var,
                        bootstyle="round-toggle").pack(side=LEFT, padx=(0, 12))

        # Поле для заметки
        self.note_var = ttk.StringVar()
        ttk.Entry(top, textvariable=self.note_var, width=35).pack(side=LEFT, padx=4)
        ttk.Label(top, text="(что делаю)", bootstyle="secondary").pack(side=LEFT)

        ttk.Button(top, text="Стоп", bootstyle="danger",
                   command=self._stop).pack(side=RIGHT, padx=8, pady=8)

        # Две колонки: просрочено / на сегодня
        body = ttk.Frame(self)
        body.pack(fill=BOTH, expand=True, padx=8, pady=4)

        left = ttk.Labelframe(body, text="Просрочено", bootstyle="danger")
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 4))
        self.overdue_list = ttk.Treeview(
            left, columns=("due",), show="tree headings", height=15
        )
        self.overdue_list.heading("#0", text="Задача")
        self.overdue_list.heading("due", text="Дедлайн")
        self.overdue_list.column("due", width=100, anchor=E)
        self.overdue_list.pack(fill=BOTH, expand=True, padx=4, pady=4)

        right = ttk.Labelframe(body, text="На сегодня", bootstyle="primary")
        right.pack(side=LEFT, fill=BOTH, expand=True, padx=(4, 0))
        self.today_list = ttk.Treeview(
            right, columns=("status",), show="tree headings", height=15
        )
        self.today_list.heading("#0", text="Задача")
        self.today_list.heading("status", text="Статус")
        self.today_list.column("status", width=100, anchor=E)
        self.today_list.pack(fill=BOTH, expand=True, padx=4, pady=4)

        # Кнопка «в работу» под каждым списком
        ttk.Button(left, text="▶ В работу", bootstyle="warning",
                   command=lambda: self._start(self.overdue_list)).pack(pady=4)
        ttk.Button(right, text="▶ В работу", bootstyle="warning",
                   command=lambda: self._start(self.today_list)).pack(pady=4)

    def refresh(self):
        self.overdue_list.delete(*self.overdue_list.get_children())
        for t in overdue(self.conn):
            self.overdue_list.insert("", END, iid=str(t["id"]),
                                     text=t["title"], values=(t["due_date"],))

        self.today_list.delete(*self.today_list.get_children())
        for t in planned_for(self.conn, date.today()):
            mark = "▶ " if t["status"] == "in_progress" else ""
            self.today_list.insert("", END, iid=str(t["id"]),
                                   text=mark + t["title"], values=(t["status"],))

    def _start(self, tree):
        sel = tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        try:
            timer.start(self.conn, task_id)
            self.note_var.set("")  # Очищаем поле заметки для новой задачи
            self.refresh()
        except RuntimeError as e:
            ttk.dialogs.Messagebox.show_error(str(e), title="Таймер")

    def _stop(self):
        try:
            # Получаем активную сессию перед остановкой, чтобы привязать к ней заметку
            s = timer.active_session(self.conn)
            if s:
                note = self.note_var.get().strip()
                # Сохраняем заметку в time_session
                self.conn.execute("UPDATE time_session SET note = ? WHERE id = ?", (note, s["id"]))
                self.conn.commit()
                self.note_var.set("")  # Очищаем поле после сохранения

            timer.stop(self.conn)
            self.refresh()
        except RuntimeError as e:
            ttk.dialogs.Messagebox.show_error(str(e), title="Таймер")

    def tick(self):
        """Вызывается раз в секунду из App."""
        s = timer.active_session(self.conn)
        if not s:
            self.timer_label.config(text="—")
            return

        start = datetime.fromisoformat(s["start"])
        elapsed = int((datetime.now() - start).total_seconds())

        # Логика Помодоро
        if self.pomo_var.get():
            remaining = 25 * 60 - elapsed
            if remaining > 0:
                m, s_sec = divmod(remaining, 60)
                self.timer_label.config(text=f"🍅 {m:02d}:{s_sec:02d}", bootstyle="success")
            else:
                # Время вышло, показываем, сколько прошло сверх помидора
                over = elapsed - 25 * 60
                m, s_sec = divmod(over, 60)
                self.timer_label.config(text=f"🍅 Перерыв! (+{m:02d}:{s_sec:02d})", bootstyle="danger")
        else:
            hh, rem = divmod(elapsed, 3600)
            mm, ss = divmod(rem, 60)
            self.timer_label.config(text=f"▶ {hh:02d}:{mm:02d}:{ss:02d}", bootstyle="default")
from datetime import date, datetime, timedelta
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from services.personal import get_journal, save_journal, get_personal_tasks, add_personal_task
import tkinter as tk
from tkinter import messagebox


class JournalTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.current_date = date.today()
        self._build()
        self.refresh()

    def _build(self):
        # Верхняя панель: навигация по датам
        top = ttk.Frame(self)
        top.pack(fill=X, padx=8, pady=8)

        ttk.Button(top, text="<", bootstyle="link", command=lambda: self._change_day(-1)).pack(side=LEFT)
        self.date_label = ttk.Label(top, text="", font=("TkDefaultFont", 12, "bold"))
        self.date_label.pack(side=LEFT, padx=16)
        ttk.Button(top, text=">", bootstyle="link", command=lambda: self._change_day(1)).pack(side=LEFT)

        ttk.Button(top, text="Сегодня", bootstyle="secondary-outline",
                   command=self._go_today).pack(side=LEFT, padx=16)

        # Основной контент: 2 колонки
        body = ttk.Panedwindow(self, orient=HORIZONTAL)
        body.pack(fill=BOTH, expand=True, padx=8, pady=4)

        # Левая часть: Личные задачи
        left = ttk.Labelframe(body, text="Личные задачи", bootstyle="primary")
        body.add(left, weight=1)

        self.tasks_tree = ttk.Treeview(left, columns=("status",), show="tree headings", height=10)
        self.tasks_tree.heading("#0", text="Задача")
        self.tasks_tree.heading("status", text="Статус")
        self.tasks_tree.pack(fill=BOTH, expand=True, padx=4, pady=4)
        self.tasks_tree.bind("<Double-1>", lambda e: self._edit_task())
        self.tasks_tree.bind("<Button-3>", self._show_context_menu)

        self.ctx_menu = tk.Menu(self, tearoff=0)
        self.ctx_menu.add_command(label="Редактировать", command=self._edit_task)
        self.ctx_menu.add_command(label="Удалить", command=self._delete_task)

        # Форма быстрого добавления
        add_frame = ttk.Frame(left)
        add_frame.pack(fill=X, padx=4, pady=4)
        self.new_task_var = ttk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_task_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(add_frame, text="+", bootstyle="success", width=3,
                   command=self._add_task).pack(side=LEFT, padx=(4, 0))

        # Правая часть: Дневник
        right = ttk.Labelframe(body, text="На чем я остановился", bootstyle="info")
        body.add(right, weight=2)

        # Тип дня
        type_frame = ttk.Frame(right)
        type_frame.pack(fill=X, padx=8, pady=8)
        ttk.Label(type_frame, text="Тип дня:").pack(side=LEFT)
        self.day_type_var = ttk.StringVar(value="work")
        ttk.Combobox(type_frame, textvariable=self.day_type_var, state="readonly", width=15,
                     values=["work (рабочий)", "study (учеба)", "rest (отдых)"]).pack(side=LEFT, padx=8)

        # Текстовое поле для заметок
        self.note_text = ttk.Text(right, height=15, font=("TkDefaultFont", 11))
        self.note_text.pack(fill=BOTH, expand=True, padx=8, pady=4)

        ttk.Button(right, text="Сохранить заметку", bootstyle="success",
                   command=self._save_note).pack(anchor=E, padx=8, pady=8)

    def _change_day(self, delta):
        self.current_date += timedelta(days=delta)
        self.refresh()

    def _go_today(self):
        self.current_date = date.today()
        self.refresh()

    def refresh(self):
        # Название дня
        months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        d = self.current_date
        self.date_label.config(text=f"{days_ru[d.weekday()]} {d.day} {months[d.month]} {d.year}")

        # Заметки и тип дня
        j = get_journal(self.conn, self.current_date)
        if j:
            self.note_text.delete("1.0", END)
            self.note_text.insert("1.0", j["note"])

            # Парсим тип дня
            dt_map = {"work": "work (рабочий)", "study": "study (учеба)", "rest": "rest (отдых)"}
            self.day_type_var.set(dt_map.get(j["day_type"], "work (рабочий)"))

        # Личные задачи
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        for t in get_personal_tasks(self.conn, self.current_date):
            mark = "✔ " if t["status"] == "done" else "· "
            self.tasks_tree.insert("", END, iid=str(t["id"]), text=mark + t["title"], values=(t["status"],))

    def _save_note(self):
        note = self.note_text.get("1.0", END).strip()
        day_type = self.day_type_var.get().split()[0]
        save_journal(self.conn, self.current_date, day_type, note)
        Messagebox.show_info("Заметка сохранена!", title="Дневник")

    def _add_task(self):
        title = self.new_task_var.get().strip()
        if not title: return
        add_personal_task(self.conn, title, "", self.current_date)
        self.new_task_var.set("")
        self.refresh()

    def _show_context_menu(self, event):
        item = self.tasks_tree.identify_row(event.y)
        if item:
            self.tasks_tree.selection_set(item)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _edit_task(self):
        sel = self.tasks_tree.selection()
        if not sel:
            return
        task_id = int(sel[0])

        # Достаем данные задачи из БД
        r = self.conn.execute("SELECT * FROM personal_task WHERE id = ?", (task_id,)).fetchone()
        if not r:
            return

        from ui.dialog_personal import PersonalTaskDialog
        dlg = PersonalTaskDialog(self.winfo_toplevel(), self.conn, dict(r))
        if dlg.result:
            self.refresh()

    def _delete_task(self):
        sel = self.tasks_tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        title = self.tasks_tree.item(sel[0], "text").replace("✔ ", "").replace("· ", "")

        if messagebox.askyesno("Удаление", f"Удалить задачу?\n\n{title}", parent=self):
            from services.personal import delete_personal_task
            delete_personal_task(self.conn, task_id)
            self.refresh()
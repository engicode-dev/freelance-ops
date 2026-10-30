from datetime import date, datetime, timedelta
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ui.widgets import DateInput


class TaskDialog(ttk.Toplevel):
    """Модальное окно создания/редактирования задачи."""

    def __init__(self, parent, conn, task_id=None):
        super().__init__(master=parent)
        self.conn = conn
        self.task_id = task_id
        self.result = None

        self.title("Редактировать задачу" if task_id else "Новая задача")

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self._build()
        self._load_clients()

        if self.task_id:
            self._load_task_data()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._save())

        self.wait_window()

    def _build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=BOTH, expand=True)
        row = 0

        ttk.Label(frm, text="Название *").grid(row=row, column=0, sticky=W, pady=4)
        self.title_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.title_var, width=40).grid(
            row=row, column=1, columnspan=3, sticky=EW, pady=4)
        row += 1

        ttk.Label(frm, text="Клиент").grid(row=row, column=0, sticky=W, pady=4)
        self.client_var = ttk.StringVar()
        self.client_cb = ttk.Combobox(frm, textvariable=self.client_var,
                                      state="readonly", width=37)
        self.client_cb.grid(row=row, column=1, columnspan=3, sticky=EW, pady=4)
        row += 1

        ttk.Label(frm, text="Описание").grid(row=row, column=0, sticky=NW, pady=4)
        self.desc_text = ttk.Text(frm, width=40, height=3)
        self.desc_text.grid(row=row, column=1, columnspan=3, sticky=EW, pady=4)
        row += 1

        ttk.Label(frm, text="Приоритет").grid(row=row, column=0, sticky=W, pady=4)
        self.priority_var = ttk.StringVar(value="2 — обычный")
        ttk.Combobox(frm, textvariable=self.priority_var, state="readonly", width=15,
                     values=["1 — высокий", "2 — обычный", "3 — низкий"]).grid(
            row=row, column=1, sticky=W, pady=4)

        ttk.Label(frm, text="Цена, ₽").grid(row=row, column=2, sticky=W, pady=4, padx=(12, 0))
        self.price_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.price_var, width=12).grid(
            row=row, column=3, sticky=W, pady=4)
        row += 1

        ttk.Label(frm, text="Дедлайн").grid(row=row, column=0, sticky=W, pady=4)
        self.due_widget = DateInput(frm)
        self.due_widget.grid(row=row, column=1, sticky=NW, pady=4)

        ttk.Label(frm, text="План, часы").grid(row=row, column=2, sticky=W, pady=4, padx=(12, 0))
        self.est_hours_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.est_hours_var, width=12).grid(
            row=row, column=3, sticky=W, pady=4)
        row += 1

        ttk.Label(frm, text="Запланировать на").grid(row=row, column=0, sticky=W, pady=4)
        self.plan_widget = DateInput(frm)
        self.plan_widget.grid(row=row, column=1, sticky=NW, pady=4)

        quick = ttk.Frame(frm)
        quick.grid(row=row, column=2, columnspan=2, sticky=W, pady=4)
        ttk.Button(quick, text="сегодня", bootstyle="link",
                   command=lambda: self.plan_widget.set(date.today().isoformat())).pack(side=LEFT)
        ttk.Button(quick, text="+1", bootstyle="link",
                   command=lambda: self.plan_widget.set((date.today() + timedelta(days=1)).isoformat())).pack(side=LEFT)
        ttk.Button(quick, text="+7", bootstyle="link",
                   command=lambda: self.plan_widget.set((date.today() + timedelta(days=7)).isoformat())).pack(side=LEFT)
        row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=4, sticky=EW, pady=(16, 0))
        ttk.Button(btns, text="Сохранить" if self.task_id else "Создать",
                   bootstyle="success", command=self._save).pack(side=RIGHT, padx=4)
        ttk.Button(btns, text="Отмена", bootstyle="secondary", command=self.destroy).pack(side=RIGHT)

    def _load_clients(self):
        rows = self.conn.execute("SELECT id, name FROM client ORDER BY name").fetchall()
        self._clients = {r["name"]: r["id"] for r in rows}
        names = ["(без клиента)"] + list(self._clients.keys())
        self.client_cb["values"] = names
        if not self.task_id:
            self.client_var.set("(без клиента)")

    def _load_task_data(self):
        r = self.conn.execute("SELECT * FROM task WHERE id = ?", (self.task_id,)).fetchone()
        if not r: return

        self.title_var.set(r["title"])
        self.desc_text.insert("1.0", r["description"] or "")

        # Приоритет
        p_map = {1: "1 — высокий", 2: "2 — обычный", 3: "3 — низкий"}
        self.priority_var.set(p_map.get(r["priority"], "2 — обычный"))

        # Клиент
        if r["client_id"]:
            for name, cid in self._clients.items():
                if cid == r["client_id"]:
                    self.client_var.set(name)
                    break
        else:
            self.client_var.set("(без клиента)")

        # Числа
        if r["price_kopecks"]:
            self.price_var.set(str(r["price_kopecks"] / 100))
        if r["hours_estimated"]:
            self.est_hours_var.set(str(r["hours_estimated"]))

        # Даты
        self.due_widget.set(r["due_date"] or "")
        self.plan_widget.set(r["planned_date"] or "")

    def _parse_date(self, date_str, field_name):
        date_str = date_str.strip()
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except ValueError:
            Messagebox.show_warning(f"Поле '{field_name}' содержит неверную дату.\nНужен формат: ГГГГ-ММ-ДД",
                                    title="Ошибка даты")
            raise ValueError("invalid date")

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            Messagebox.show_warning("Название обязательно", title="Проверка")
            return

        price_kop = None
        if self.price_var.get().strip():
            try:
                price_kop = int(round(float(self.price_var.get().replace(",", ".")) * 100))
            except ValueError:
                Messagebox.show_warning("Цена должна быть числом", title="Проверка")
                return

        est_hours = None
        if self.est_hours_var.get().strip():
            try:
                est_hours = float(self.est_hours_var.get().replace(",", "."))
            except ValueError:
                Messagebox.show_warning("Плановые часы должны быть числом", title="Проверка")
                return

        try:
            due_str = self._parse_date(self.due_widget.get(), "Дедлайн")
            plan_str = self._parse_date(self.plan_widget.get(), "Запланировать на")
        except ValueError:
            return

        client_id = self._clients.get(self.client_var.get())
        priority = int(self.priority_var.get().split()[0])
        desc = self.desc_text.get("1.0", END).strip()

        if self.task_id:
            # UPDATE
            self.conn.execute(
                """UPDATE task SET 
                   title=?, client_id=?, description=?, priority=?, 
                   due_date=?, planned_date=?, price_kopecks=?, hours_estimated=?
                   WHERE id=?""",
                (title, client_id, desc, priority, due_str, plan_str, price_kop, est_hours, self.task_id)
            )
            self.conn.commit()
            self.result = self.task_id
        else:
            # INSERT
            cur = self.conn.execute(
                """INSERT INTO task
                   (title, client_id, description, priority, due_date, planned_date,
                    price_kopecks, hours_estimated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, client_id, desc, priority, due_str, plan_str, price_kop, est_hours)
            )
            self.conn.commit()
            self.result = cur.lastrowid

        self.destroy()
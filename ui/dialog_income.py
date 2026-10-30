from datetime import date, timedelta
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox


class IncomeDialog(ttk.Toplevel):
    def __init__(self, parent, conn):
        super().__init__(master=parent)
        self.title("Новый доход")
        self.conn = conn
        self.result = None

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self._build()
        self._load_tasks()

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
        ttk.Label(frm, text="Сумма, ₽ *").grid(row=row, column=0, sticky=W, pady=4)
        self.amount_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.amount_var, width=30).grid(
            row=row, column=1, sticky=EW, pady=4)
        row += 1

        ttk.Label(frm, text="Тип *").grid(row=row, column=0, sticky=W, pady=4)
        self.type_var = ttk.StringVar(value="active")
        ttk.Combobox(frm, textvariable=self.type_var, state="readonly", width=28,
                     values=["active", "passive"]).grid(
            row=row, column=1, sticky=EW, pady=4)
        row += 1

        # Дата + быстрые кнопки
        ttk.Label(frm, text="Дата").grid(row=row, column=0, sticky=W, pady=4)
        self.date_var = ttk.StringVar(value=date.today().isoformat())
        ttk.Entry(frm, textvariable=self.date_var, width=15).grid(
            row=row, column=1, sticky=W, pady=4)

        quick = ttk.Frame(frm)
        quick.grid(row=row, column=1, sticky=E, pady=4)
        ttk.Button(quick, text="сегодня", bootstyle="link",
                   command=lambda: self.date_var.set(date.today().isoformat())).pack(side=LEFT)
        ttk.Button(quick, text="вчера", bootstyle="link",
                   command=lambda: self.date_var.set((date.today() - timedelta(days=1)).isoformat())).pack(side=LEFT)
        row += 1

        ttk.Label(frm, text="Задача").grid(row=row, column=0, sticky=W, pady=4)
        self.task_var = ttk.StringVar()
        self.task_cb = ttk.Combobox(frm, textvariable=self.task_var,
                                    state="readonly", width=28)
        self.task_cb.grid(row=row, column=1, sticky=EW, pady=4)
        row += 1

        ttk.Label(frm, text="Описание").grid(row=row, column=0, sticky=W, pady=4)
        self.desc_var = ttk.StringVar()
        ttk.Entry(frm, textvariable=self.desc_var, width=30).grid(
            row=row, column=1, sticky=EW, pady=4)
        row += 1

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=2, sticky=EW, pady=(16, 0))
        ttk.Button(btns, text="Добавить", bootstyle="success",
                   command=self._save).pack(side=RIGHT, padx=4)
        ttk.Button(btns, text="Отмена", bootstyle="secondary",
                   command=self.destroy).pack(side=RIGHT)

    def _load_tasks(self):
        rows = self.conn.execute(
            "SELECT id, title FROM task WHERE status != 'cancelled' ORDER BY id DESC"
        ).fetchall()
        self._tasks = {f"#{r['id']} {r['title'][:40]}": r["id"] for r in rows}
        self.task_cb["values"] = ["(без задачи)"] + list(self._tasks.keys())
        self.task_var.set("(без задачи)")

    def _save(self):
        try:
            amount_kop = int(round(float(self.amount_var.get().replace(",", ".")) * 100))
        except ValueError:
            Messagebox.show_warning("Сумма должна быть числом", title="Проверка")
            return
        if amount_kop <= 0:
            Messagebox.show_warning("Сумма должна быть больше нуля", title="Проверка")
            return

        task_id = self._tasks.get(self.task_var.get())

        self.conn.execute(
            "INSERT INTO income (date, amount_kopecks, type, task_id, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (self.date_var.get(), amount_kop, self.type_var.get(), task_id,
             self.desc_var.get()),
        )
        self.conn.commit()
        self.result = True
        self.destroy()
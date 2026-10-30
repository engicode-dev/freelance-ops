import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox

STATUS_RU = {"todo": "· к выполнению", "in_progress": "▶ в работе",
             "done": "✔ готово", "cancelled": "✖ отменено"}


class TasksTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.refresh()

    def _build(self):
        # фильтр
        bar = ttk.Frame(self)
        bar.pack(fill=X, padx=8, pady=8)
        ttk.Label(bar, text="Статус:").pack(side=LEFT)
        self.status_var = ttk.StringVar(value="все")
        cb = ttk.Combobox(bar, textvariable=self.status_var, state="readonly", width=15,
                          values=["все", "todo", "in_progress", "done", "cancelled"])
        cb.pack(side=LEFT, padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # таблица
        self.tree = ttk.Treeview(self, columns=("status", "client", "due", "plan", "hours", "price"),
                                 show="tree headings")
        self.tree.heading("#0", text="Задача")
        self.tree.heading("status", text="Статус")
        self.tree.heading("client", text="Клиент")
        self.tree.heading("due", text="Дедлайн")
        self.tree.heading("plan", text="План")
        self.tree.heading("hours", text="Часы")
        self.tree.heading("price", text="Цена")
        self.tree.column("#0", width=280)
        self.tree.column("status", width=130, anchor=W)
        self.tree.column("client", width=140)
        self.tree.column("due", width=90, anchor=CENTER)
        self.tree.column("plan", width=90, anchor=CENTER)
        self.tree.column("hours", width=60, anchor=E)
        self.tree.column("price", width=90, anchor=E)
        self.tree.pack(fill=BOTH, expand=True, padx=8, pady=4)
        # --- Контекстное меню и события ---
        self.tree.bind("<Double-1>", lambda e: self._edit_task())
        self.tree.bind("<Button-3>", self._show_context_menu)

        self.ctx_menu = tk.Menu(self, tearoff=0)
        self.ctx_menu.add_command(label="Редактировать", command=self._edit_task)
        self.ctx_menu.add_command(label="Удалить", command=self._delete_task)

        # кнопки
        bar2 = ttk.Frame(self)
        bar2.pack(fill=X, padx=8, pady=8)
        ttk.Button(bar2, text="Обновить", bootstyle="secondary",
                   command=self.refresh).pack(side=LEFT)
        ttk.Button(bar2, text="▶ В работу", bootstyle="warning",
                   command=lambda: self._move("in_progress")).pack(side=LEFT, padx=4)
        ttk.Button(bar2, text="✔ Готово", bootstyle="success",
                   command=lambda: self._move("done")).pack(side=LEFT, padx=4)
        ttk.Button(bar2, text="✖ Отменить", bootstyle="danger",
                   command=lambda: self._move("cancelled")).pack(side=LEFT, padx=4)
        ttk.Button(bar2, text="+ Задача", bootstyle="success",
                   command=self._add_task).pack(side=RIGHT)


    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        sql = ("SELECT t.*, c.name AS client_name FROM task t "
               "LEFT JOIN client c ON c.id = t.client_id")
        params = []
        if self.status_var.get() != "все":
            sql += " WHERE t.status = ?"
            params.append(self.status_var.get())
        sql += " ORDER BY t.priority, COALESCE(t.due_date,'9999'), t.id"

        for r in self.conn.execute(sql, params).fetchall():
            price = f"{r['price_kopecks']/100:.0f}₽" if r["price_kopecks"] else ""
            self.tree.insert("", END, iid=str(r["id"]), text=r["title"], values=(
                STATUS_RU.get(r["status"], r["status"]),
                r["client_name"] or "",
                r["due_date"] or "",
                r["planned_date"] or "",
                f"{r['hours_spent']:.1f}" if r["hours_spent"] else "",
                price,
            ))

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _edit_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        from ui.dialog_task import TaskDialog
        dlg = TaskDialog(self.winfo_toplevel(), self.conn, task_id=task_id)
        if dlg.result:
            self.refresh()

    def _delete_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        title = self.tree.item(sel[0], "text")

        if messagebox.askyesno("Удаление", f"Удалить задачу?\n\n{title}", parent=self):
            from services.tasks import delete_task
            delete_task(self.conn, task_id)
            self.refresh()

    def _move(self, status):
        sel = self.tree.selection()
        if not sel:
            return
        from services.tasks import change_status
        try:
            change_status(self.conn, int(sel[0]), status)
            self.refresh()
        except ValueError as e:
            ttk.dialogs.Messagebox.show_error(str(e), title="Смена статуса")

    def _add_task(self):
        from ui.dialog_task import TaskDialog
        dlg = TaskDialog(self.winfo_toplevel(), self.conn)
        if dlg.result:
            self.refresh()
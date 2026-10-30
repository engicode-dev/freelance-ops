from datetime import date
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox

from services.stats import calculate


class MoneyTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.refresh()

    def _build(self):
        # период
        top = ttk.Frame(self)
        top.pack(fill=X, padx=8, pady=8)
        ttk.Label(top, text="С:").pack(side=LEFT)
        self.start_var = ttk.StringVar(value=date.today().replace(day=1).isoformat())
        ttk.Entry(top, textvariable=self.start_var, width=12).pack(side=LEFT, padx=4)
        ttk.Label(top, text="По:").pack(side=LEFT)
        self.end_var = ttk.StringVar(value=date.today().isoformat())
        ttk.Entry(top, textvariable=self.end_var, width=12).pack(side=LEFT, padx=4)
        ttk.Button(top, text="Показать", bootstyle="primary",
                   command=self.refresh).pack(side=LEFT, padx=8)
        ttk.Button(top, text="+ Доход", bootstyle="success",
                   command=self._add_income).pack(side=RIGHT)

        # сводка
        self.summary = ttk.Label(self, text="", font=("TkDefaultFont", 11))
        self.summary.pack(fill=X, padx=12, pady=4)

        # таблица доходов
        self.tree = ttk.Treeview(self, columns=("date", "amount", "type", "task", "desc"),
                                 show="headings")
        for col, txt, w, anchor in [
            ("date", "Дата", 90, CENTER),
            ("amount", "Сумма", 110, E),
            ("type", "Тип", 80, CENTER),
            ("task", "Задача", 70, CENTER),
            ("desc", "Описание", 300, W),
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor=anchor)
        self.tree.pack(fill=BOTH, expand=True, padx=8, pady=4)
        # --- Контекстное меню ---
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.ctx_menu = tk.Menu(self, tearoff=0)
        self.ctx_menu.add_command(label="Удалить доход", command=self._delete_income)

    def refresh(self):
        rows = [dict(r) for r in self.conn.execute(
            "SELECT * FROM income WHERE date BETWEEN ? AND ? ORDER BY date",
            (self.start_var.get(), self.end_var.get()),
        ).fetchall()]

        hours_by_income = {}
        for inc in rows:
            if inc["task_id"]:
                h = self.conn.execute(
                    "SELECT COALESCE(SUM((julianday(COALESCE(end, datetime('now'))) "
                    "- julianday(start)) * 24.0), 0) FROM time_session WHERE task_id=?",
                    (inc["task_id"],),
                ).fetchone()[0]
                hours_by_income[inc["id"]] = h or 0.0

        s = calculate(rows, hours_by_income)
        rate = f"{s.effective_rate_kop/100:,.0f} ₽/ч" if s.effective_rate_kop else "—"
        self.summary.config(
            text=f"Актив: {s.active_kop/100:,.0f} ₽   "
                 f"Пассив: {s.passive_kop/100:,.0f} ₽   "
                 f"ИТОГО: {s.total_kop/100:,.0f} ₽   "
                 f"Часов: {s.paid_hours:.1f}   Ставка: {rate}"
        )

        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", END, values=(
                r["date"],
                f"{r['amount_kopecks']/100:,.2f}",
                r["type"],
                f"#{r['task_id']}" if r["task_id"] else "",
                r["description"] or "",
            ))

    def _add_income(self):
        from ui.dialog_income import IncomeDialog
        dlg = IncomeDialog(self.winfo_toplevel(), self.conn)
        if dlg.result:
            self.refresh()

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _delete_income(self):
        sel = self.tree.selection()
        if not sel:
            return

        # Поскольку в таблице доходов нет iid (id записи),
        # нам нужно достать его из базы по индексу.
        # Проще: настроить сохранение iid при вставке.
        # Но чтобы не переписывать весь refresh, достанем строку и сумму:

        # Быстрый фикс: добавим iid в refresh, но здесь просто спросим подтверждение

        if messagebox.askyesno("Удаление", "Удалить эту запись о доходе?", parent=self):
            # Получаем данные выбранной строки
            values = self.tree.item(sel[0], "values")
            if not values: return
            inc_date = values[0]
            inc_amount = values[1].replace(",", "")

            # Находим ID в базе
            row = self.conn.execute(
                "SELECT id FROM income WHERE date = ? AND amount_kopecks = ? LIMIT 1",
                (inc_date, int(float(inc_amount) * 100))
            ).fetchone()

            if row:
                self.conn.execute("DELETE FROM income WHERE id = ?", (row["id"],))
                self.conn.commit()
                self.refresh()
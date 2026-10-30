import calendar
from datetime import date
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class DateInput(ttk.Frame):
    """Поле ввода даты со встроенным раскрывающимся календарем (без Toplevel)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var = ttk.StringVar()

        # Верхняя строка: поле + кнопка
        top = ttk.Frame(self)
        top.pack(fill=X)

        self.entry = ttk.Entry(top, textvariable=self.var, width=12)
        self.entry.pack(side=LEFT)

        self.btn = ttk.Button(top, text="📅", bootstyle="secondary-outline",
                              command=self._toggle_cal, width=3)
        self.btn.pack(side=LEFT, padx=(2, 0))

        # Фрейм для календаря (изначально скрыт)
        self.cal_frame = ttk.Frame(self, borderwidth=1, relief="solid")

        self.view_year = date.today().year
        self.view_month = date.today().month
        self.is_open = False

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(val)

    def _toggle_cal(self):
        if self.is_open:
            self.cal_frame.pack_forget()
            self.is_open = False
        else:
            self._draw_calendar()
            self.cal_frame.pack(fill=X, pady=(2, 0))
            self.is_open = True

    def _draw_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        # Навигация по месяцам
        top = ttk.Frame(self.cal_frame, padding=2)
        top.pack(fill=X)

        ttk.Button(top, text="<", bootstyle="link", width=2,
                   command=lambda: self._change_month(-1)).pack(side=LEFT)
        ttk.Label(top, text=f"{self.view_month:02d}.{self.view_year}",
                  font=("TkDefaultFont", 9, "bold")).pack(side=LEFT, expand=True)
        ttk.Button(top, text=">", bootstyle="link", width=2,
                   command=lambda: self._change_month(1)).pack(side=RIGHT)

        # Сетка дней
        grid = ttk.Frame(self.cal_frame, padding=2)
        grid.pack()

        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, d in enumerate(days):
            ttk.Label(grid, text=d, font=("TkDefaultFont", 8, "bold")).grid(row=0, column=i, padx=1, pady=1)

        cal = calendar.Calendar(firstweekday=0)
        for r, week in enumerate(cal.monthdayscalendar(self.view_year, self.view_month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(grid, text="").grid(row=r, column=c)
                else:
                    btn = ttk.Button(grid, text=str(day), bootstyle="link", width=2,
                                     command=lambda d=day: self._select_date(d))
                    btn.grid(row=r, column=c)

    def _change_month(self, delta):
        self.view_month += delta
        if self.view_month > 12:
            self.view_month = 1
            self.view_year += 1
        elif self.view_month < 1:
            self.view_month = 12
            self.view_year -= 1
        self._draw_calendar()

    def _select_date(self, day):
        d = date(self.view_year, self.view_month, day)
        self.var.set(d.isoformat())
        self._toggle_cal()  # Свернуть после выбора
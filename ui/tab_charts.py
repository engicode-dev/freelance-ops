from datetime import date
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib

matplotlib.use("TkAgg")  # Важно для работы с Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker


class ChartsTab(ttk.Frame):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.refresh()

    def _build(self):
        # Верхняя панель управления
        top = ttk.Frame(self)
        top.pack(fill=X, padx=8, pady=8)

        ttk.Label(top, text="Графики доходов", font=("TkDefaultFont", 12, "bold")).pack(side=LEFT)

        ttk.Button(top, text="Обновить", bootstyle="secondary",
                   command=self.refresh).pack(side=RIGHT)

        # Контейнер для графиков
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(fill=BOTH, expand=True, padx=8, pady=4)

    def refresh(self):
        # Очищаем старые графики, если они были
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # Получаем данные из БД (группируем по месяцам)
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(CASE WHEN type = 'active' THEN amount_kopecks ELSE 0 END) / 100.0 as active,
                SUM(CASE WHEN type = 'passive' THEN amount_kopecks ELSE 0 END) / 100.0 as passive
            FROM income
            GROUP BY month
            ORDER BY month
        """
        rows = self.conn.execute(query).fetchall()

        if not rows:
            ttk.Label(self.chart_frame, text="Нет данных для отображения.\nДобавьте доходы во вкладке «Деньги».",
                      font=("TkDefaultFont", 12)).pack(expand=True)
            return

        months = [r["month"] for r in rows]
        active_vals = [r["active"] for r in rows]
        passive_vals = [r["passive"] for r in rows]

        # Настраиваем фигуру matplotlib
        fig = Figure(figsize=(10, 5), dpi=100)
        fig.patch.set_facecolor('#1e1e2e')  # Цвет фона Catppuccin (примерно)

        # --- График 1: Доход по месяцам (Bar Chart) ---
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor('#1e1e2e')

        # Рисуем столбцы
        x = range(len(months))
        width = 0.35

        rects1 = ax1.bar([i - width / 2 for i in x], active_vals, width, label='Активный', color='#89b4fa')
        rects2 = ax1.bar([i + width / 2 for i in x], passive_vals, width, label='Пассивный', color='#a6e3a1')

        ax1.set_ylabel('Доход, ₽', color='white')
        ax1.set_title('Доход по месяцам', color='white', pad=15)
        ax1.set_xticks(x)
        ax1.set_xticklabels(months, color='white', rotation=45 if len(months) > 4 else 0)
        ax1.tick_params(colors='white')

        # Красивые подписи осей (не в экспоненте)
        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
        ax1.legend(facecolor='#313244', labelcolor='white', edgecolor='none')

        # Убираем лишние рамки
        for spine in ax1.spines.values():
            spine.set_color('#585b70')

        # --- График 2: Доля пассива (Pie Chart) ---
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor('#1e1e2e')

        total_active = sum(active_vals)
        total_passive = sum(passive_vals)

        if total_active > 0 or total_passive > 0:
            labels = ['Активный', 'Пассивный']
            sizes = [total_active, total_passive]
            colors = ['#89b4fa', '#a6e3a1']

            # Отсекаем нули, чтобы не было пустых кусков на пироге
            filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
            labels = [f[0] for f in filtered]
            sizes = [f[1] for f in filtered]
            colors = [f[2] for f in filtered]

            wedges, texts, autotexts = ax2.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, textprops={'color': 'white'}
            )
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_weight('bold')

        ax2.set_title('Соотношение доходов', color='white', pad=15)

        fig.tight_layout()

        # Встраиваем в Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
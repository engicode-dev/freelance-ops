import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox


class PersonalTaskDialog(ttk.Toplevel):
    def __init__(self, parent, conn, task_data):
        super().__init__(master=parent)
        self.title("Редактировать задачу")
        self.conn = conn
        self.task_id = task_data["id"]
        self.result = False

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self._build(task_data)

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._save())

        self.wait_window()

    def _build(self, data):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=BOTH, expand=True)

        ttk.Label(frm, text="Название:").pack(anchor=W, pady=(0, 4))
        self.title_var = ttk.StringVar(value=data["title"])
        ttk.Entry(frm, textvariable=self.title_var, width=40).pack(fill=X, pady=(0, 12))

        ttk.Label(frm, text="Описание (опционально):").pack(anchor=W, pady=(0, 4))
        self.desc_text = ttk.Text(frm, width=40, height=4)
        self.desc_text.insert("1.0", data["description"] or "")
        self.desc_text.pack(fill=X, pady=(0, 12))

        btns = ttk.Frame(frm)
        btns.pack(fill=X)

        ttk.Button(btns, text="Сохранить", bootstyle="success", command=self._save).pack(side=RIGHT, padx=(4, 0))
        ttk.Button(btns, text="Отмена", bootstyle="secondary", command=self.destroy).pack(side=RIGHT)

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            Messagebox.show_warning("Название обязательно", title="Проверка")
            return

        desc = self.desc_text.get("1.0", END).strip()

        from services.personal import update_personal_task
        update_personal_task(self.conn, self.task_id, title, desc)
        self.result = True
        self.destroy()
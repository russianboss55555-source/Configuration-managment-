"""Графический REPL на Tkinter."""

import tkinter as tk
from tkinter import scrolledtext, ttk

from src.startup import execute_line, run_script


class TerminalWindow:
    """Окно ввода команд и просмотра истории текущего сеанса."""

    def __init__(self, root, shell, config, vfs_name):
        """Создать окно и связать элементы с обработчиком команд."""
        self.root = root
        self.shell = shell
        root.title(f"Эмулятор оболочки — {vfs_name}")
        root.geometry("850x520")
        root.minsize(580, 340)
        self.build_widgets(vfs_name)
        self.write("Вариант 22 • Этап 5 • Python\n")
        self.write("Команды: ls, cd, tac, cal, du, touch, exit.\n\n")
        self.write(config.describe() + "\n\n")
        self.entry.focus_set()
        if config.script_path is not None:
            root.after_idle(self.start, config.script_path)

    def start(self, path):
        """Воспроизвести сценарий после создания окна."""
        should_exit, _ = run_script(self.shell, path, self.write)
        if should_exit:
            self.root.destroy()
        else:
            self.update_prompt()

    def build_widgets(self, vfs_name):
        """Разместить историю, строку ввода и подпись текущего этапа."""
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        self.history = scrolledtext.ScrolledText(
            frame, wrap="word", state="disabled", font=("Consolas", 11),
            background="#17212b", foreground="#e8eef4",
        )
        self.history.pack(fill="both", expand=True)
        command_bar = ttk.Frame(frame, padding=(0, 10, 0, 0))
        command_bar.pack(fill="x")
        self.prompt = ttk.Label(command_bar, text=self.shell.prompt)
        self.prompt.pack(side="left")
        self.entry = ttk.Entry(command_bar, font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.submit)
        ttk.Button(
            command_bar, text="Выполнить", command=self.submit,
        ).pack(side="left", padx=(8, 0))
        ttk.Label(
            frame, text=f"VFS: {vfs_name} • данные в памяти",
        ).pack(anchor="w", pady=(8, 0))

    def update_prompt(self):
        """Показать актуальный путь в строке ввода."""
        self.prompt.configure(text=self.shell.prompt)

    def write(self, text):
        """Добавить текст в защищённую от редактирования историю."""
        self.history.configure(state="normal")
        self.history.insert("end", text)
        self.history.configure(state="disabled")
        self.history.see("end")

    def submit(self, event=None):
        """Выполнить введённую команду по Enter или кнопке."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        result = execute_line(self.shell, line, self.write)
        if result.should_exit:
            self.root.destroy()
        else:
            self.update_prompt()
            self.entry.focus_set()
        return "break"

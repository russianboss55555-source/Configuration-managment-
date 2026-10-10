"""Графический REPL на Tkinter."""

import tkinter as tk
from tkinter import scrolledtext, ttk

from src.shell import Shell


DEFAULT_VFS_NAME = "demo_vfs.zip"


class TerminalWindow:
    """Окно ввода команд и просмотра истории текущего сеанса."""

    def __init__(self, root, vfs_name=DEFAULT_VFS_NAME):
        """Создать окно и связать элементы с обработчиком команд."""
        self.root = root
        self.shell = Shell()
        root.title(f"Эмулятор оболочки — {vfs_name}")
        root.geometry("850x520")
        root.minsize(580, 340)
        self.build_widgets(vfs_name)
        self.write("Вариант 22 • Этап 1 • Python\n")
        self.write("Команды: ls [путь], cd [путь], exit.\n")
        self.write("ls и cd работают как заглушки.\n\n")
        self.entry.focus_set()

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
        ttk.Label(command_bar, text="shell $ ").pack(side="left")
        self.entry = ttk.Entry(command_bar, font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.submit)
        ttk.Button(
            command_bar, text="Выполнить", command=self.submit,
        ).pack(side="left", padx=(8, 0))
        ttk.Label(
            frame, text=f"VFS: {vfs_name} • загрузка появится на этапе 3",
        ).pack(anchor="w", pady=(8, 0))

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
        self.write(f"shell $ {line}\n")
        result = self.shell.execute(line)
        if result.output:
            self.write(result.output + "\n")
        if result.should_exit:
            self.root.destroy()
        else:
            self.entry.focus_set()
        return "break"

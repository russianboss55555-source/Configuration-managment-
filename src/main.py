"""Точка входа: python -m src.main из корня проекта."""

import sys
import tkinter as tk

from src.gui import TerminalWindow


def main():
    """Запустить графическое приложение и обработать ошибку дисплея."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Не удалось открыть окно Tkinter: {error}", file=sys.stderr)
        return 1
    TerminalWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

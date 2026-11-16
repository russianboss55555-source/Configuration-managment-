"""Точка входа: python -m src.main из корня проекта."""

import sys

from src.config import parse_args
from src.shell import Shell
from src.startup import run_script


def launch_gui(shell, config, vfs_name):
    """Создать окно и запустить цикл событий Tkinter."""
    try:
        import tkinter as tk

        from src.gui import TerminalWindow
    except ImportError:
        print("Установите Python с поддержкой Tkinter.", file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Не удалось открыть окно Tkinter: {error}", file=sys.stderr)
        return 1
    TerminalWindow(root, shell, config, vfs_name)
    root.mainloop()
    return 0


def main(argv=None):
    """Прочитать конфигурацию и выбрать интерфейс выполнения."""
    config = parse_args(argv)
    shell = Shell()
    name = config.vfs_path.name if config.vfs_path else "demo_vfs.zip"
    if config.headless:
        print(config.describe())
        _, read_ok = run_script(shell, config.script_path, sys.stdout.write)
        return 0 if read_ok else 1
    return launch_gui(shell, config, name)


if __name__ == "__main__":
    raise SystemExit(main())

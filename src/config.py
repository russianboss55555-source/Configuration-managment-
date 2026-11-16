"""Аргументы запуска и их представление для отладочного вывода."""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Параметры одного сеанса эмулятора."""

    vfs_path: Path | None
    script_path: Path | None
    headless: bool

    def describe(self):
        """Вернуть значения всех параметров запуска."""
        vfs = self.vfs_path or "(в памяти)"
        script = self.script_path or "(не задан)"
        return f"Конфигурация: VFS={vfs}; скрипт={script}; CLI={self.headless}"


def parse_args(argv=None):
    """Прочитать опции запуска; для текстового режима требуется скрипт."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки, №22")
    parser.add_argument("--vfs", type=Path, help="путь к ZIP-архиву VFS")
    parser.add_argument("--script", type=Path, help="стартовый скрипт UTF-8")
    parser.add_argument(
        "--headless", action="store_true",
        help="выполнить скрипт в терминале без окна",
    )
    args = parser.parse_args(argv)
    if args.headless and args.script is None:
        parser.error("--headless требует --script")
    return Config(args.vfs, args.script, args.headless)

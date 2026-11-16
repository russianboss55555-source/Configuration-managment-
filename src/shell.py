"""Сеанс оболочки и диспетчеризация команд."""

from dataclasses import dataclass

from src.commands import (
    disk_usage, list_directory, one_path, parse_flags, reverse_files,
    show_calendar, touch_paths,
)
from src.parser import parse_command
from src.vfs import Directory, VfsError, VirtualFileSystem


@dataclass
class CommandResult:
    """Текст результата и признак завершения приложения."""

    output: str = ""
    should_exit: bool = False


class Shell:
    """Хранит текущий каталог и направляет команду обработчику."""

    def __init__(self, vfs=None):
        """Подключить VFS и зарегистрировать команды."""
        self.vfs = vfs if vfs is not None else VirtualFileSystem()
        self.cwd = "/"
        self.commands = {
            "ls": self.ls,
            "cd": self.cd,
            "tac": self.tac,
            "cal": self.cal,
            "du": self.du,
            "touch": self.touch,
            "exit": self.exit_command,
        }

    @property
    def prompt(self):
        """Вернуть приглашение оболочки с текущим каталогом."""
        return f"shell:{self.cwd} $ "

    def execute(self, line):
        """Разобрать строку, вызвать обработчик и показать ошибки."""
        try:
            words = parse_command(line)
            if not words:
                return CommandResult()
            command, *arguments = words
            handler = self.commands.get(command)
            if handler is None:
                raise ValueError(f"Неизвестная команда: {command}")
            return handler(arguments)
        except ValueError as error:
            return CommandResult(f"Ошибка: {error}")

    def ls(self, arguments):
        """Вывести содержимое каталога или сведения о файле."""
        return CommandResult(list_directory(self.vfs, self.cwd, arguments))

    def cd(self, arguments):
        """Перейти в виртуальный каталог или в корень при пустом вводе."""
        usage = "Использование: cd [--] [каталог]"
        _, paths = parse_flags(arguments, "", usage)
        path = one_path(paths, "/", usage)
        absolute, node = self.vfs.resolve(self.cwd, path)
        if not isinstance(node, Directory):
            raise VfsError(f"Не каталог: {path}")
        self.cwd = absolute
        return CommandResult()

    def tac(self, arguments):
        """Вывести строки виртуальных текстовых файлов в обратном порядке."""
        return CommandResult(reverse_files(self.vfs, self.cwd, arguments))

    def cal(self, arguments):
        """Вывести календарь в одном из поддерживаемых режимов."""
        return CommandResult(show_calendar(arguments))

    def du(self, arguments):
        """Вывести объём виртуального дерева или файла."""
        return CommandResult(disk_usage(self.vfs, self.cwd, arguments))

    def touch(self, arguments):
        """Изменить временные метки или создать файлы в памяти."""
        touch_paths(self.vfs, self.cwd, arguments)
        return CommandResult()

    def exit_command(self, arguments):
        """Запросить завершение, если exit вызвана без аргументов."""
        if arguments:
            raise ValueError("Использование: exit")
        return CommandResult("Завершение работы.", should_exit=True)

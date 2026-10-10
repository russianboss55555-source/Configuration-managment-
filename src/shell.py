"""Обработка команд первого этапа независимо от интерфейса."""

from dataclasses import dataclass

from src.parser import parse_command


MAX_PATH_ARGUMENTS = 1


@dataclass
class CommandResult:
    """Текст результата и признак завершения приложения."""

    output: str = ""
    should_exit: bool = False


class Shell:
    """Минимальная оболочка с заглушками ls/cd и командой exit."""

    def execute(self, line):
        """Обработать строку и преобразовать ошибки ввода в результат."""
        try:
            words = parse_command(line)
            if not words:
                return CommandResult()
            command, *arguments = words
            if command == "exit":
                return self.exit_command(arguments)
            if command in ("ls", "cd"):
                return self.stub_command(command, arguments)
            raise ValueError(f"Неизвестная команда: {command}")
        except ValueError as error:
            return CommandResult(f"Ошибка: {error}")

    def stub_command(self, command, arguments):
        """Проверить аргументы и вывести имя команды-заглушки."""
        if len(arguments) > MAX_PATH_ARGUMENTS:
            raise ValueError(f"Использование: {command} [путь]")
        if arguments and arguments[0].startswith("-"):
            raise ValueError(f"Флаги {command} пока не поддерживаются.")
        return CommandResult(
            f"[Заглушка] Команда: {command}; аргументы: {arguments!r}"
        )

    def exit_command(self, arguments):
        """Запросить завершение, если exit вызвана без аргументов."""
        if arguments:
            raise ValueError("Использование: exit")
        return CommandResult("Завершение работы.", should_exit=True)

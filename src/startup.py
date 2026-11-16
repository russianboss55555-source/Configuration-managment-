"""Общий цикл выполнения команд интерактивного и сценарного режима."""


def execute_line(shell, line, write):
    """Вывести приглашение, исходный ввод и результат одной команды."""
    write(f"{shell.prompt}{line}\n")
    result = shell.execute(line)
    if result.output:
        write(result.output + "\n")
    return result


def read_script(path):
    """Прочитать стартовый сценарий UTF-8, включая файлы с BOM."""
    try:
        return path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        message = f"Не удалось прочитать скрипт {path}: {error}"
        raise ValueError(message) from error


def run_script(shell, path, write):
    """Вернуть (запрошен выход, скрипт прочитан) после обработки строк."""
    try:
        lines = read_script(path)
    except ValueError as error:
        write(f"Ошибка: {error}\n")
        return False, False
    commands = (
        line for line in lines if line.strip()[:1] not in ("", "#")
    )
    should_exit = any(
        execute_line(shell, line, write).should_exit for line in commands
    )
    return should_exit, True

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
        raise ValueError(f"Не удалось прочитать скрипт {path}: {error}") from error


def run_script(shell, path, write):
    """Вернуть (запрошен выход, скрипт прочитан) после обработки строк."""
    try:
        lines = read_script(path)
    except ValueError as error:
        write(f"Ошибка: {error}\n")
        return False, False
    for line in lines:
        command = line.strip()
        if command and not command.startswith("#"):
            result = execute_line(shell, line, write)
            if result.should_exit:
                return True, True
    return False, True

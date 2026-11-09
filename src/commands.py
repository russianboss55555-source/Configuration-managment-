"""Реализация команд чтения виртуальной файловой системы."""

import calendar
from datetime import date
from posixpath import join

from src.vfs import Directory, VfsError, VirtualFile


ONE_PATH = 1
MONTH_YEAR_COUNT = 2
KIBIBYTE = 1024
HUMAN_UNITS = ("B", "KiB", "MiB", "GiB", "TiB")


def parse_flags(arguments, allowed, usage):
    """Разделить короткие флаги и пути; -- завершает разбор флагов."""
    flags = set()
    paths = []
    read_flags = True
    for item in arguments:
        if read_flags and item == "--":
            read_flags = False
        elif read_flags and item.startswith("-") and item != "-":
            for flag in item[1:]:
                if flag not in allowed:
                    raise VfsError(f"Неизвестный флаг -{flag}. {usage}")
                flags.add(flag)
        else:
            paths.append(item)
    return flags, paths


def one_path(paths, default, usage):
    """Вернуть указанный путь или значение по умолчанию."""
    if len(paths) > ONE_PATH:
        raise VfsError(usage)
    return paths[0] if paths else default


def format_entry(name, node, long_format):
    """Сформировать имя или строку с типом, размером и временем."""
    directory = isinstance(node, Directory)
    display = name + "/" if directory else name
    if not long_format:
        return display
    kind = "d" if directory else "-"
    size = 0 if directory else node.size
    stamp = node.modified_at.isoformat(timespec="seconds")
    return f"{kind} {size:>8} {stamp}  {display}"


def list_directory(vfs, cwd, arguments):
    """Показать файл или имена дочерних элементов каталога."""
    usage = "Использование: ls [-al] [--] [путь]"
    flags, paths = parse_flags(arguments, "al", usage)
    path = one_path(paths, ".", usage)
    absolute, node = vfs.resolve(cwd, path)
    if isinstance(node, VirtualFile):
        return format_entry(absolute, node, "l" in flags)
    names = sorted(node.children)
    lines = [".", ".."] if "a" in flags else []
    entries = ((name, node.children[name]) for name in names)
    lines.extend(
        format_entry(name, child, "l" in flags)
        for name, child in entries
        if "a" in flags or not name.startswith(".")
    )
    return "\n".join(lines)


def reverse_file(vfs, cwd, path):
    """Прочитать UTF-8 файл и развернуть порядок его строк."""
    _, node = vfs.resolve(cwd, path)
    if isinstance(node, Directory):
        raise VfsError(f"Это каталог: {path}")
    try:
        content = node.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise VfsError(f"Файл не является текстом UTF-8: {path}") from error
    if "\0" in content:
        raise VfsError(f"Файл не является текстом UTF-8: {path}")
    return "".join(reversed(content.splitlines(keepends=True)))


def reverse_files(vfs, cwd, arguments):
    """Вывести записи одного или нескольких файлов в обратном порядке."""
    usage = "Использование: tac [--] файл [файл ...]"
    _, paths = parse_flags(arguments, "", usage)
    if not paths:
        raise VfsError(usage)
    return "".join(reverse_file(vfs, cwd, path) for path in paths)


def show_calendar(arguments):
    """Вернуть календарь текущего месяца, заданного месяца или года."""
    usage = "Использование: cal [год | месяц год]"
    if len(arguments) > MONTH_YEAR_COUNT:
        raise VfsError(usage)
    try:
        numbers = [int(value) for value in arguments]
        today = date.today()
        view = calendar.TextCalendar(calendar.MONDAY)
        if not numbers:
            return view.formatmonth(today.year, today.month).rstrip()
        if len(numbers) == ONE_PATH:
            date(numbers[0], today.month, 1)
            return view.formatyear(numbers[0]).rstrip()
        month, year = numbers
        date(year, month, 1)
        return view.formatmonth(year, month).rstrip()
    except ValueError as error:
        raise VfsError(f"Неверный месяц или год. {usage}") from error


def collect_sizes(node, path, rows, include_files):
    """Накопить размер файлов и каталогов снизу вверх."""
    if isinstance(node, VirtualFile):
        if include_files:
            rows.append((path, node.size))
        return node.size
    total = sum(
        collect_sizes(child, join(path, name), rows, include_files)
        for name, child in sorted(node.children.items())
    )
    rows.append((path, total))
    return total


def human_size(size):
    """Представить размер в байтах или кратных 1024 единицах."""
    value = float(size)
    for unit in HUMAN_UNITS:
        if value < KIBIBYTE or unit == HUMAN_UNITS[-1]:
            return f"{size} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= KIBIBYTE


def disk_usage(vfs, cwd, arguments):
    """Подсчитать объём несжатых файлов внутри виртуального пути."""
    usage = "Использование: du [-ash] [--] [путь]"
    flags, paths = parse_flags(arguments, "ash", usage)
    if {"a", "s"} <= flags:
        raise VfsError("Флаги -a и -s нельзя использовать вместе.")
    path = one_path(paths, ".", usage)
    absolute, node = vfs.resolve(cwd, path)
    rows = []
    collect_sizes(node, absolute, rows, "a" in flags or path_is_file(node))
    if "s" in flags:
        rows = rows[-1:]
    return "\n".join(
        f"{human_size(size) if 'h' in flags else size}\t{name}"
        for name, size in rows
    )


def path_is_file(node):
    """Вернуть признак обычного файла."""
    return isinstance(node, VirtualFile)

"""Разбор команд и подстановка переменных окружения реальной ОС."""

import os
import re


TOKEN_PATTERN = re.compile(r"\s+|'[^']*'|\"[^\"]*\"|[^\s'\"]+")
VARIABLE_PATTERN = re.compile(
    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))"
)


def expand_variables(text):
    """Подставить $NAME и ${NAME}; неизвестное имя вызывает ошибку."""
    def replace(match):
        """Получить значение одной переменной без повторного раскрытия."""
        name = match.group(1) or match.group(2)
        if name not in os.environ:
            raise ValueError(f"Переменная окружения {name} не задана.")
        return os.environ[name]

    return VARIABLE_PATTERN.sub(replace, text)


def decode_fragment(fragment):
    """Снять кавычки; одинарные кавычки сохраняют текст буквально."""
    if fragment.startswith("'"):
        return fragment[1:-1]
    if fragment.startswith('"'):
        fragment = fragment[1:-1]
    return expand_variables(fragment)


def parse_command(line):
    """Разобрать строку на слова с кавычками и раскрытием переменных."""
    words = []
    fragments = []
    position = 0
    for match in TOKEN_PATTERN.finditer(line):
        if match.start() != position:
            raise ValueError("Незакрытая кавычка.")
        position = match.end()
        token = match.group()
        if token.isspace():
            if fragments:
                words.append("".join(fragments))
                fragments = []
        else:
            fragments.append(decode_fragment(token))
    if position != len(line):
        raise ValueError("Незакрытая кавычка.")
    if fragments:
        words.append("".join(fragments))
    return words

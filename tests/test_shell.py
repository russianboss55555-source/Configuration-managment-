"""Проверка парсера и поведения команд без графического дисплея."""

import unittest
from unittest.mock import patch

from src.parser import parse_command
from src.shell import Shell


class ParserTests(unittest.TestCase):
    """Проверки пользовательского ввода и окружения ОС."""

    def test_whitespace(self):
        """Пробелы и табуляции разделяют слова."""
        self.assertEqual(parse_command("  ls\t /docs  "), ["ls", "/docs"])

    def test_blank(self):
        """Пустые строки дают пустой список слов."""
        for line in ("", "  ", "\t"):
            with self.subTest(line=line):
                self.assertEqual(parse_command(line), [])

    def test_quotes(self):
        """Кавычки сохраняют пробелы внутри одного аргумента."""
        for line in ('cd "my docs"', "cd 'my docs'"):
            with self.subTest(line=line):
                self.assertEqual(parse_command(line), ["cd", "my docs"])

    def test_empty_argument(self):
        """Пустой аргумент в кавычках сохраняется."""
        self.assertEqual(parse_command('ls ""'), ["ls", ""])

    def test_adjacent_fragments(self):
        """Смежные фрагменты составляют один аргумент."""
        self.assertEqual(parse_command('ls /"my docs"/a'),
                         ["ls", "/my docs/a"])

    def test_environment(self):
        """Обе формы переменных читаются из окружения ОС."""
        with patch.dict("os.environ", {"DEMO": "/my docs"}, clear=True):
            for line in ('cd $DEMO', 'cd "${DEMO}"'):
                with self.subTest(line=line):
                    self.assertEqual(parse_command(line),
                                     ["cd", "/my docs"])

    def test_literal_single_quotes(self):
        """Одинарные кавычки защищают доллар от раскрытия."""
        self.assertEqual(parse_command("ls '$DEMO'"), ["ls", "$DEMO"])

    def test_missing_environment(self):
        """Отсутствующая переменная даёт понятную ошибку."""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "не задана"):
                parse_command("ls $MISSING")

    def test_no_recursive_expansion(self):
        """Подставленное значение повторно не интерпретируется."""
        with patch.dict("os.environ", {"DEMO": "$INNER"}, clear=True):
            self.assertEqual(parse_command("ls $DEMO"), ["ls", "$INNER"])

    def test_unclosed_quotes(self):
        """Незакрытые кавычки отклоняются в любой позиции."""
        for line in ('ls "abc', "ls abc'", 'ls "'):
            with self.subTest(line=line):
                with self.assertRaisesRegex(ValueError, "кавычка"):
                    parse_command(line)


class ShellTests(unittest.TestCase):
    """Проверки команд, ошибок и завершения работы."""

    def setUp(self):
        """Создать оболочку для отдельного теста."""
        self.shell = Shell()

    def test_empty_vfs(self):
        """Корень пустой VFS можно просмотреть и использовать как каталог."""
        self.assertEqual(self.shell.execute("ls").output, "")
        self.assertEqual(self.shell.execute("cd /").output, "")
        self.assertEqual(self.shell.cwd, "/")

    def test_exit(self):
        """exit без аргументов завершает сеанс."""
        self.assertTrue(self.shell.execute("exit").should_exit)

    def test_bad_arguments(self):
        """Ошибочные аргументы не завершают оболочку."""
        for line in ("ls a b", "cd a b", "exit now", "ls -z"):
            with self.subTest(line=line):
                result = self.shell.execute(line)
                self.assertTrue(result.output.startswith("Ошибка:"))
                self.assertFalse(result.should_exit)

    def test_unknown_command_and_recovery(self):
        """После неизвестной команды следующий ввод обрабатывается."""
        self.assertIn("Неизвестная", self.shell.execute("pwd").output)
        self.assertEqual(self.shell.execute("ls").output, "")

    def test_blank_input(self):
        """Пустой ввод безопасен для текущего сеанса."""
        result = self.shell.execute("   ")
        self.assertEqual(result.output, "")
        self.assertFalse(result.should_exit)

    def test_parser_error_is_visible(self):
        """Ошибка парсера становится текстом для пользователя."""
        self.assertIn("кавычка", self.shell.execute('ls "').output)


if __name__ == "__main__":
    unittest.main()

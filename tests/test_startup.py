"""Проверки параметров запуска и обработки стартового сценария."""

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.config import parse_args
from src.shell import Shell
from src.startup import run_script


class StartupTests(unittest.TestCase):
    """Выполнение строк сценария с настоящим обработчиком команд."""

    def test_options_with_spaces(self):
        """CLI принимает пути с пробелами и текстовый режим."""
        argv = ["--vfs", "my files/a.zip", "--script", "a b.txt", "--headless"]
        config = parse_args(argv)
        self.assertEqual(config.vfs_path, Path("my files/a.zip"))
        self.assertEqual(config.script_path, Path("a b.txt"))
        self.assertIn("CLI=True", config.describe())

    def test_headless_requires_script(self):
        """Текстовый режим требует источник команд."""
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            parse_args(["--headless"])

    def test_continue_after_errors(self):
        """Ошибочная команда отображается, а следующая выполняется."""
        with TemporaryDirectory() as folder:
            path = Path(folder) / "start.txt"
            path.write_text(
                '# comment\n\nunknown\nls "unfinished\nls\nexit\ncd /',
                encoding="utf-8-sig",
            )
            output = StringIO()
            self.assertEqual(
                run_script(Shell(), path, output.write), (True, True),
            )
        dialogue = output.getvalue()
        self.assertIn("Неизвестная команда", dialogue)
        self.assertIn("Незакрытая кавычка", dialogue)
        self.assertIn("shell:/ $ ls\n", dialogue)
        self.assertIn("shell:/ $ exit\n", dialogue)
        self.assertNotIn("shell:/ $ cd /", dialogue)
        self.assertNotIn("# comment", dialogue)

    def test_missing_script(self):
        """Ошибка чтения скрипта доступна пользователю."""
        output = StringIO()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "absent.txt"
            self.assertEqual(
                run_script(Shell(), path, output.write), (False, False),
            )
        self.assertIn("Не удалось прочитать скрипт", output.getvalue())

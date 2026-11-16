"""Проверки команд на реальной виртуальной файловой системе."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from examples.make_vfs import DATASETS, create_zip
from src.shell import Shell
from src.vfs import load_zip


class CommandTests(unittest.TestCase):
    """Тесты вывода и изменения текущего каталога."""

    def setUp(self):
        """Загрузить демонстрационный архив с вложенными каталогами."""
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        archive = Path(folder.name) / "nested.zip"
        create_zip("nested", archive)
        self.shell = Shell(load_zip(archive))

    def run_line(self, line):
        """Получить текст ответа на команду."""
        return self.shell.execute(line).output

    def test_ls_modes(self):
        """Скрытые элементы, длинный формат, файлы и пути с пробелами."""
        self.assertNotIn(".secret", self.run_line("ls"))
        self.assertIn(".secret", self.run_line("ls -al /"))
        self.assertIn("docs/", self.run_line("ls"))
        self.assertIn("intro.txt", self.run_line("ls /docs"))
        self.assertEqual(self.run_line('ls -- "/my documents"'), "plan.txt")
        self.assertIn("/docs/intro.txt", self.run_line("ls /docs/intro.txt"))

    def test_cd_relative_and_failures(self):
        """cd изменяет путь лишь при переходе в существующий каталог."""
        self.assertEqual(self.run_line("cd /docs/projects/demo"), "")
        self.assertIn("notes.txt", self.run_line("ls"))
        self.assertEqual(self.run_line("cd .."), "")
        self.assertEqual(self.shell.cwd, "/docs/projects")
        self.assertIn("Не каталог", self.run_line("cd /docs/intro.txt"))
        self.assertIn("не найден", self.run_line("cd ../absent"))
        self.assertEqual(self.shell.cwd, "/docs/projects")
        self.assertEqual(self.run_line("cd"), "")
        self.assertEqual(self.shell.cwd, "/")

    def test_tac_two_files(self):
        """tac переворачивает строки каждого файла в исходном порядке."""
        line = "tac /docs/intro.txt /docs/projects/demo/notes.txt"
        self.assertEqual(
            self.run_line(line), "третья\nвторая\nпервая\nthree\ntwo\none\n",
        )

    def test_tac_errors(self):
        """Для каталога, двоичного и отсутствующего файла есть ошибки."""
        for line in ("tac", "tac /empty", "tac /data.bin", "tac /absent"):
            with self.subTest(line=line):
                self.assertTrue(self.run_line(line).startswith("Ошибка:"))

    def test_calendar(self):
        """Поддерживаются текущий месяц, полный год и выбранный месяц."""
        self.assertTrue(self.run_line("cal"))
        self.assertIn("2026", self.run_line("cal 2026"))
        self.assertIn("November 2026", self.run_line("cal 11 2026"))
        for line in ("cal 13 2026", "cal 0", "cal abc", "cal 1 2 3"):
            with self.subTest(line=line):
                self.assertTrue(self.run_line(line).startswith("Ошибка:"))

    def test_du_reports_raw_sizes(self):
        """du считает исходные байты и учитывает скрытые файлы."""
        total = sum(len(payload) for payload in DATASETS["nested"].values())
        self.assertEqual(self.run_line("du -s /"), f"{total}\t/")
        self.assertEqual(self.run_line("du /data.bin"), "4\t/data.bin")
        self.assertEqual(self.run_line("du -h /data.bin"), "4 B\t/data.bin")
        self.assertIn("/data.bin", self.run_line("du -a /"))
        self.assertNotIn("/data.bin", self.run_line("du /"))
        self.assertTrue(self.run_line("du -as /").startswith("Ошибка:"))

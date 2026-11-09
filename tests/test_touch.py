"""Проверки создания файлов, изменения меток и неизменности ZIP."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from examples.make_vfs import create_zip
from src.shell import Shell
from src.vfs import VfsError, load_zip


STAMP = datetime(2030, 3, 9, tzinfo=timezone.utc)


class TouchTests(unittest.TestCase):
    """Проверить изменения VFS в границах одного сеанса."""

    def setUp(self):
        """Подготовить архив и сохранить его исходное содержимое."""
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "nested.zip"
        create_zip("nested", self.path)
        self.before = self.path.read_bytes()
        self.shell = Shell(load_zip(self.path))

    def test_create_and_keep_in_memory(self):
        """Новый файл пуст, а повторная загрузка ZIP его не видит."""
        self.shell.execute("cd /docs")
        self.assertEqual(self.shell.execute('touch "new file.txt"').output, "")
        _, node = self.shell.vfs.resolve("/", "/docs/new file.txt")
        self.assertEqual(node.read_bytes(), b"")
        self.assertIn("new file.txt", self.shell.execute("ls").output)
        self.assertEqual(self.path.read_bytes(), self.before)
        with self.assertRaises(VfsError):
            load_zip(self.path).resolve("/", "/docs/new file.txt")

    def test_existing_keeps_payload_and_updates_times(self):
        """Метки меняются, байты существующего файла сохраняются."""
        path = "/docs/intro.txt"
        _, node = self.shell.vfs.resolve("/", path)
        before = node.read_bytes()
        with patch("src.vfs.now", return_value=STAMP):
            self.assertEqual(self.shell.execute(f"touch -c {path}").output, "")
        self.assertEqual(node.read_bytes(), before)
        self.assertEqual(node.modified_at, STAMP)
        self.assertEqual(node.accessed_at, STAMP)
        self.assertIn("2030-03-09", self.shell.execute(f"ls -l {path}").output)

    def test_no_create_and_dash_path(self):
        """-c пропускает отсутствующий файл, -- допускает имя с дефисом."""
        self.assertEqual(self.shell.execute("touch -c missing").output, "")
        with self.assertRaises(VfsError):
            self.shell.vfs.resolve("/", "missing")
        self.assertEqual(self.shell.execute("touch -- -note").output, "")
        self.assertEqual(self.shell.vfs.resolve("/", "-note")[1].size, 0)

    def test_directory_timestamp(self):
        """Для существующего каталога touch тоже обновляет метки."""
        with patch("src.vfs.now", return_value=STAMP):
            self.assertEqual(self.shell.execute("touch /empty/").output, "")
        _, directory = self.shell.vfs.resolve("/", "/empty")
        self.assertEqual(directory.modified_at, STAMP)

    def test_errors_and_multiple_paths(self):
        """Ошибка одного пути не мешает обработать следующий."""
        for line in ("touch", "touch -z file", "touch /data.bin/child"):
            with self.subTest(line=line):
                self.assertTrue(
                    self.shell.execute(line).output.startswith("Ошибка:"),
                )
        result = self.shell.execute("touch /missing/child after.txt")
        self.assertIn("Путь не найден", result.output)
        self.assertEqual(self.shell.vfs.resolve("/", "after.txt")[1].size, 0)

"""Загрузка ZIP, изоляция, пути и работа с двоичными данными."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from examples.make_vfs import create_zip
from src.vfs import Directory, VfsError, load_zip


class VfsTests(unittest.TestCase):
    """Проверки на отдельных временных архивах."""

    def test_load_samples(self):
        """Все три примера загружаются без извлечения файлов."""
        with TemporaryDirectory() as folder:
            root = Path(folder)
            for dataset in ("minimal", "multiple", "nested"):
                with self.subTest(dataset=dataset):
                    archive = root / f"{dataset}.zip"
                    create_zip(dataset, archive)
                    before = archive.read_bytes()
                    vfs = load_zip(archive)
                    self.assertEqual(vfs.name, archive.name)
                    if dataset == "minimal":
                        self.assertEqual(vfs.root.children, {})
                    else:
                        _, binary = vfs.resolve("/", "/data.bin")
                        self.assertEqual(binary.read_bytes(), b"\0\xff\x80\n")
                        self.assertEqual(binary.size, len(binary.read_bytes()))
                        _, empty = vfs.resolve("/", "/empty/")
                        self.assertIsInstance(empty, Directory)
                    self.assertEqual(archive.read_bytes(), before)
            self.assertEqual(len(list(root.iterdir())), 3)

    def test_paths(self):
        """Пути учитывают текущий каталог, точки и реальное дерево."""
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "nested.zip"
            create_zip("nested", archive)
            vfs = load_zip(archive)
        name, node = vfs.resolve("/docs/projects", "./demo/../demo/notes.txt")
        self.assertEqual(name, "/docs/projects/demo/notes.txt")
        self.assertEqual(node.read_bytes(), b"one\ntwo\nthree\n")
        self.assertEqual(vfs.resolve("/", "../../")[0], "/")
        for path in ("/absent/..", "/data.bin/..", "/data.bin/"):
            with self.subTest(path=path), self.assertRaises(VfsError):
                vfs.resolve("/", path)

    def test_missing_and_invalid_zip(self):
        """Отсутствующий и повреждённый архивы дают разные ошибки."""
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "bad.zip"
            with self.assertRaisesRegex(VfsError, "не найден"):
                load_zip(archive)
            archive.write_text("это не ZIP", encoding="utf-8")
            with self.assertRaisesRegex(VfsError, "Неверный формат"):
                load_zip(archive)

    def test_unsafe_names_and_conflicts(self):
        """Пути вне корня и коллизии имён отклоняются."""
        with TemporaryDirectory() as folder:
            archive = Path(folder) / "bad.zip"
            for names in (("../escape",), ("/absolute",), ("a", "a/b")):
                with self.subTest(names=names):
                    with ZipFile(archive, "w") as file:
                        for name in names:
                            file.writestr(name, b"")
                    with self.assertRaises(VfsError):
                        load_zip(archive)

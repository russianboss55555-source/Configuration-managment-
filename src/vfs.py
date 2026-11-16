"""Виртуальная файловая система: дерево каталогов и файлы в памяти."""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import stat
from zipfile import BadZipFile, ZipFile


def now():
    """Вернуть текущее время в UTC."""
    return datetime.now(timezone.utc)


class VfsError(ValueError):
    """Ошибка загрузки архива или операции с виртуальным путём."""


@dataclass
class Directory:
    """Каталог с дочерними узлами и временными метками."""

    children: dict[str, "Directory | VirtualFile"] = field(default_factory=dict)
    modified_at: datetime = field(default_factory=now)
    accessed_at: datetime = field(default_factory=now)


@dataclass
class VirtualFile:
    """Содержимое в Base64, размер исходных данных и временные метки."""

    data: str
    size: int
    modified_at: datetime
    accessed_at: datetime

    @classmethod
    def from_bytes(cls, payload, stamp):
        """Упаковать текстовые или двоичные данные в Base64."""
        data = base64.b64encode(payload).decode("ascii")
        return cls(data, len(payload), stamp, stamp)

    def read_bytes(self):
        """Восстановить исходные байты файла."""
        return base64.b64decode(self.data)


class VirtualFileSystem:
    """Выполняет операции с деревом файлов без обращения к диску."""

    def __init__(self, name="memory"):
        """Создать пустую VFS с корневым каталогом."""
        self.name = name
        self.root = Directory()

    def resolve(self, cwd, path):
        """Вернуть абсолютный путь и узел, пройдя по компонентам пути."""
        if not path:
            raise VfsError("Пустой путь.")
        prefix = [] if path.startswith("/") else cwd.strip("/").split("/")
        stack = [("", self.root)]
        for component in prefix + path.split("/"):
            parent = stack[-1][1]
            if not isinstance(parent, Directory):
                raise VfsError(f"Не каталог: {stack[-1][0]}")
            if component == "..":
                if len(stack) > ROOT_DEPTH:
                    stack.pop()
            elif component not in ("", "."):
                child = parent.children.get(component)
                if child is None:
                    raise VfsError(f"Путь не найден: {path}")
                stack.append((component, child))
        name = "/".join(part for part, _ in stack)
        return name or "/", stack[-1][1]


ROOT_DEPTH = 1


def archive_parts(info):
    """Проверить имя и тип ZIP-записи до добавления в дерево."""
    name = info.orig_filename
    if not name or name.startswith("/") or "\\" in name or "\0" in name:
        raise VfsError(f"Недопустимый путь в ZIP: {name!r}")
    parts = name.removesuffix("/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise VfsError(f"Недопустимый путь в ZIP: {name!r}")
    mode = stat.S_IFMT(info.external_attr >> 16)
    if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise VfsError(f"Неподдерживаемый тип записи в ZIP: {name!r}")
    return parts


def ensure_directory(parent, name):
    """Получить дочерний каталог или создать отсутствующий."""
    node = parent.children.get(name)
    if node is None:
        node = Directory()
        parent.children[name] = node
    if not isinstance(node, Directory):
        raise VfsError(f"Файл и каталог имеют одно имя: {name}")
    return node


def add_archive_entry(vfs, archive, info):
    """Добавить одну запись ZIP, создав промежуточные каталоги."""
    *parents, name = archive_parts(info)
    parent = vfs.root
    for component in parents:
        parent = ensure_directory(parent, component)
    stamp = datetime(*info.date_time, tzinfo=timezone.utc)
    if info.is_dir():
        node = ensure_directory(parent, name)
        node.modified_at = stamp
        node.accessed_at = stamp
        return
    if name in parent.children:
        raise VfsError(f"Повторяющееся имя в ZIP: {info.filename}")
    parent.children[name] = VirtualFile.from_bytes(archive.read(info), stamp)


def load_zip(path):
    """Прочитать ZIP в память и сообщить об ошибке загрузки."""
    path = Path(path)
    vfs = VirtualFileSystem(path.name)
    try:
        with ZipFile(path) as archive:
            for info in archive.infolist():
                add_archive_entry(vfs, archive, info)
    except FileNotFoundError as error:
        raise VfsError(f"ZIP-архив не найден: {path}") from error
    except BadZipFile as error:
        raise VfsError(f"Неверный формат ZIP: {path}") from error
    except (OSError, RuntimeError, NotImplementedError, ValueError) as error:
        raise VfsError(f"Не удалось загрузить VFS {path}: {error}") from error
    return vfs

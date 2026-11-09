"""Создание трёх тестовых ZIP-архивов из исходного кода."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


DOCUMENTS = {
    "docs/intro.txt": "первая\nвторая\nтретья\n".encode("utf-8"),
    ".secret": b"hidden\n",
    "empty/": b"",
    "data.bin": bytes((0, 255, 128, 10)),
}
DATASETS = {
    "minimal": {},
    "multiple": DOCUMENTS,
    "nested": {
        **DOCUMENTS,
        "docs/projects/demo/notes.txt": b"one\ntwo\nthree\n",
        "my documents/plan.txt": "План\n".encode("utf-8"),
    },
}
OUTPUT_DIR = Path(__file__).with_name("generated")


def create_zip(dataset, path):
    """Создать один ZIP с выбранным деревом."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name, payload in DATASETS[dataset].items():
            info = ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            archive.writestr(info, payload, compress_type=ZIP_DEFLATED)


def main():
    """Сгенерировать выбранный архив или все демонстрационные архивы."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset", choices=(*DATASETS, "all"), default="all", nargs="?",
    )
    args = parser.parse_args()
    datasets = DATASETS if args.dataset == "all" else (args.dataset,)
    for dataset in datasets:
        path = OUTPUT_DIR / f"{dataset}.zip"
        create_zip(dataset, path)
        print(f"Создан архив: {path}")


if __name__ == "__main__":
    main()

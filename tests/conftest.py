"""
tests/itu/conftest.py — Общие фикстуры для тестов ITU-R.

Файл обеспечивает:
    * Добавление корня проекта в sys.path, чтобы `import core` работал
      независимо от того, из какой папки запущен pytest.
    * Фикстуру `reference_dir` — путь к папке с CSV-эталонами.
    * Хелпер `load_reference_csv` — загрузку CSV-эталонов с автоматическим
      `pytest.skip`, если файл не найден (это позволяет запускать тесты
      P.835/P.676/P.528 без CSV-эталонов — они просто пропускаются).
"""

import sys
import os
import csv

import pytest


# =====================================================================
# ДОБАВЛЯЕМ КОРЕНЬ ПРОЕКТА В sys.path
# =====================================================================
# Файл лежит в <project_root>/tests/itu/conftest.py.
# Корень проекта — это на два уровня выше: <project_root>/.
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# =====================================================================
# ПУТЬ К CSV-ЭТАЛОНАМ
# =====================================================================
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")


# =====================================================================
# ФИКСТУРЫ
# =====================================================================

@pytest.fixture
def reference_dir() -> str:
    """Путь к папке с CSV-эталонами (tests/itu/reference/)."""
    return REFERENCE_DIR


@pytest.fixture
def load_reference():
    """
    Фикстура-обёртка над load_reference_csv.

    Пример использования в тесте:

        def test_reference_csv(self, load_reference):
            rows = load_reference('p835_reference.csv')
            ...
    """
    return load_reference_csv


# =====================================================================
# ХЕЛПЕР
# =====================================================================

def load_reference_csv(filename: str):
    """
    Загружает CSV-эталон из tests/itu/reference/<filename>.

    Args:
        filename: имя файла (например, 'p835_reference.csv').

    Returns:
        list[dict] — каждая строка CSV как dict (ключи — имена колонок).

    Raises:
        pytest.skip: если файл не найден. Это позволяет запускать
            тесты без CSV-эталонов — они будут помечены как skipped,
            а не упадут с ошибкой.
    """
    filepath = os.path.join(REFERENCE_DIR, filename)
    if not os.path.exists(filepath):
        pytest.skip(f"CSV-эталон не найден: {filepath}")

    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


__all__ = [
    'REFERENCE_DIR',
    'load_reference_csv',
]

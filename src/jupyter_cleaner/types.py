"""Типы данных на границе с форматом Jupyter notebook."""

from typing import NotRequired, TypedDict

type NotebookOutput = dict[str, object]


class NotebookCell(TypedDict):
    """Поля ячейки, используемые конвертером."""

    cell_type: str
    source: list[str]
    outputs: NotRequired[list[NotebookOutput]]


class Notebook(TypedDict):
    """Проверенная часть структуры notebook."""

    cells: list[NotebookCell]

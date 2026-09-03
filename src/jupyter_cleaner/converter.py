import json  # Импортируем модуль json для работы с JSON-файлами
from pathlib import Path
from typing import Any, cast

from .cells import Cell, CodeCell, MarkdownCell
from .config import ConversionConfig
from .exceptions import InvalidNotebookError, NotebookNotFoundError
from .models import ConversionResult, ConversionStats
from .outputs import OutputProcessor
from .types import Notebook, NotebookCell, NotebookOutput


def load_notebook(file_path: Path | str) -> Notebook:
    """
    Загружает Jupyter notebook из файла.

    Args:
        file_path: Путь к файлу notebook'а (.ipynb).

    Returns:
        Проверенная часть содержимого notebook'а.
    """
    path = Path(file_path)
    try:
        # Открываем файл для чтения с указанием кодировки UTF-8
        with path.open("r", encoding="utf-8") as file:
            # Парсим JSON и возвращаем результат
            raw_notebook: Any = json.load(file)
    except FileNotFoundError as error:
        raise NotebookNotFoundError(path) from error
    except json.JSONDecodeError as error:
        raise InvalidNotebookError(path) from error

    if not isinstance(raw_notebook, dict) or not isinstance(raw_notebook.get("cells"), list):
        raise InvalidNotebookError(path)

    cells: list[NotebookCell] = []
    for raw_cell in raw_notebook["cells"]:
        if not isinstance(raw_cell, dict):
            raise InvalidNotebookError(path)
        cell_type = raw_cell.get("cell_type")
        source = raw_cell.get("source")
        if not isinstance(cell_type, str) or not isinstance(source, list) or not all(
                isinstance(line, str) for line in source
        ):
            raise InvalidNotebookError(path)
        cell: NotebookCell = {"cell_type": cell_type, "source": cast(list[str], source)}
        raw_outputs = raw_cell.get("outputs", [])
        if not isinstance(raw_outputs, list) or not all(
                isinstance(output, dict) for output in raw_outputs
        ):
            raise InvalidNotebookError(path)
        cell["outputs"] = cast(list[NotebookOutput], raw_outputs)
        cells.append(cell)
    return {"cells": cells}


class NotebookConverter:
    """Оркестрирует преобразование ячеек notebook'а в Markdown."""

    def __init__(self, config: ConversionConfig) -> None:
        self.config: ConversionConfig = config
        self.output_processor: OutputProcessor = OutputProcessor()

    def convert(self, notebook: Notebook) -> ConversionResult:
        """Преобразует notebook и возвращает его текст вместе со статистикой."""
        cells = notebook["cells"]
        stats = ConversionStats(cells_total=len(cells))
        converted_cells: list[str] = []

        for cell_data in cells:
            cell_type = cell_data["cell_type"]
            if cell_type not in ("markdown", "code"):
                continue

            source = "".join(cell_data["source"])
            cell: Cell
            if cell_type == "markdown":
                cell = MarkdownCell(source)
            else:
                cell = CodeCell(
                    source,
                    cell_data.get("outputs", []),
                    self.output_processor,
                )
            if cell.is_empty() and self.config.remove_empty_cells:
                if cell_type == "code":
                    self.output_processor.count_outputs(cell_data.get("outputs", []), stats)
                stats.empty_cells_removed += 1
                continue

            if cell_type == "markdown":
                stats.markdown_cells += 1
                converted_cells.append(cell.convert())
            else:
                stats.code_cells += 1
                converted_cells.append(cell.convert(self.config, stats))

        return ConversionResult("\n\n".join(converted_cells), stats)


def convert_notebook(
        notebook: Notebook, config: ConversionConfig | None = None
) -> ConversionResult:
    """Возвращает результат преобразования, сохраняя прежний интерфейс функции."""
    config = config if config is not None else ConversionConfig()
    return NotebookConverter(config).convert(notebook)

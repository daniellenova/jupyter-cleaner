import json  # Импортируем модуль json для работы с JSON-файлами

from .cells import CodeCell, MarkdownCell
from .config import ConversionConfig
from .exceptions import InvalidNotebookError, NotebookNotFoundError
from .models import ConversionResult, ConversionStats
from .outputs import OutputProcessor


def load_notebook(file_path):
    """
    Загружает Jupyter notebook из файла.

    Args:
        file_path (str): Путь к файлу notebook'а (.ipynb)

    Returns:
        dict: Содержимое notebook'а в виде словаря Python
    """
    try:
        # Открываем файл для чтения с указанием кодировки UTF-8
        with open(file_path, "r", encoding="utf-8") as file:
            # Парсим JSON и возвращаем результат
            return json.load(file)
    except FileNotFoundError as error:
        raise NotebookNotFoundError(file_path) from error
    except json.JSONDecodeError as error:
        raise InvalidNotebookError(file_path) from error


class NotebookConverter:
    """Оркестрирует преобразование ячеек notebook'а в Markdown."""

    def __init__(self, config):
        self.config = config
        self.output_processor = OutputProcessor()

    def convert(self, notebook):
        """Преобразует notebook и возвращает его текст вместе со статистикой."""
        cells = notebook["cells"]
        stats = ConversionStats(cells_total=len(cells))
        converted_cells = []

        for cell_data in cells:
            cell_type = cell_data["cell_type"]
            if cell_type not in ("markdown", "code"):
                continue

            source = "".join(cell_data["source"])
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
                    self.output_processor.count_outputs(cell.outputs, stats)
                stats.empty_cells_removed += 1
                continue

            if cell_type == "markdown":
                stats.markdown_cells += 1
                converted_cells.append(cell.convert())
            else:
                stats.code_cells += 1
                converted_cells.append(cell.convert(self.config, stats))

        return ConversionResult("\n\n".join(converted_cells), stats)


def convert_notebook(notebook, config=None):
    """Возвращает результат преобразования, сохраняя прежний интерфейс функции."""
    config = config if config is not None else ConversionConfig()
    return NotebookConverter(config).convert(notebook)

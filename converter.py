import json  # Импортируем модуль json для работы с JSON-файлами
import os  # Импортируем модуль os для получения размеров файлов
import sys  # Импортируем модуль sys для работы с аргументами командной строки

from cells import CodeCell, MarkdownCell
from config import ConversionConfig
from exceptions import InvalidNotebookError, NotebookNotFoundError
from models import ConversionResult, ConversionStats
from outputs import OutputProcessor


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


def print_stats(stats):
    """Печатает понятную пользователю сводку преобразования."""
    print(f"Обработано ячеек: {stats.cells_total}")
    print(f"Кодовых: {stats.code_cells}")
    print(f"Текстовых: {stats.markdown_cells}")
    print(f"Удалено пустых: {stats.empty_cells_removed}")
    print(f"Всего результатов выполнения: {stats.outputs_total}")
    print(f"Сохранено текстовых результатов: {stats.text_outputs_kept}")
    print(f"HTML-представлений исключено: {stats.html_outputs_skipped}")
    print(f"Преобразовано таблиц: {stats.tables_converted}")


def get_output_path(input_path):
    """Возвращает путь к Markdown-файлу вместо пути к notebook'у."""
    return input_path[:-len(".ipynb")] + ".md"


def save_markdown(markdown_text, output_path):
    """Сохраняет Markdown в файл в кодировке UTF-8."""
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown_text)


def format_file_size(size_bytes):
    """Возвращает размер файла в удобочитаемом виде (Б, КБ или МБ)."""
    if size_bytes < 1024:
        return f"{size_bytes} Б"

    size_kilobytes = size_bytes / 1024
    if size_kilobytes < 1024:
        value = f"{size_kilobytes:.1f}".rstrip("0").rstrip(".")
        return f"{value} КБ"

    size_megabytes = size_kilobytes / 1024
    value = f"{size_megabytes:.1f}".rstrip("0").rstrip(".")
    return f"{value} МБ"


def add_file_size_stats(stats, input_size, output_size):
    """Добавляет размеры файлов и процент их изменения в статистику."""
    stats.input_size_bytes = input_size
    stats.output_size_bytes = output_size
    stats.size_reduction_percent = (
        (input_size - output_size) / input_size * 100
        if input_size else 0.0
    )


def print_file_size_stats(stats):
    """Печатает размеры исходного и итогового файлов и их изменение."""
    input_size = stats.input_size_bytes
    output_size = stats.output_size_bytes
    reduction = stats.size_reduction_percent

    print("Размер:")
    print(f"{format_file_size(input_size)} → {format_file_size(output_size)}")
    if reduction >= 0:
        print(f"Уменьшение: {reduction:.1f} %")
    else:
        change = (output_size - input_size) / input_size * 100 if input_size else 0.0
        print(f"Изменение размера: +{change:.1f} %")


def main():
    """
    Главная функция программы.
    Проверяет аргументы командной строки и сохраняет notebook в виде Markdown.
    """
    # Проверяем, передан ли путь к файлу в аргументах командной строки
    if len(sys.argv) < 2:
        # Если аргументов недостаточно, выводим инструкцию по использованию
        print("Использование: python converter.py <notebook.ipynb> [--keep-outputs]")
        return

    if len(sys.argv) > 3 or (len(sys.argv) == 3 and sys.argv[2] != "--keep-outputs"):
        print("Ошибка: поддерживается только дополнительный флаг --keep-outputs.")
        print("Использование: python converter.py <notebook.ipynb> [--keep-outputs]")
        return

    # Получаем путь к файлу из первого аргумента командной строки
    file_path = sys.argv[1]
    config = ConversionConfig(keep_outputs=len(sys.argv) == 3)

    # Загружаем notebook из файла и сообщаем об ожидаемых ошибках ввода
    try:
        notebook = load_notebook(file_path)
    except NotebookNotFoundError:
        print(f"Ошибка: файл '{file_path}' не найден.")
        return
    except InvalidNotebookError:
        print(f"Ошибка: файл '{file_path}' содержит некорректный JSON.")
        return

    input_size = os.path.getsize(file_path)

    # Преобразуем notebook, определяем путь результата и сохраняем Markdown
    converter = NotebookConverter(config)
    result = converter.convert(notebook)
    output_path = get_output_path(file_path)
    save_markdown(result.markdown_text, output_path)
    output_size = os.path.getsize(output_path)
    add_file_size_stats(result.stats, input_size, output_size)

    print(f"Создан файл: {output_path}")
    print_stats(result.stats)
    print_file_size_stats(result.stats)


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если да, вызываем главную функцию
    main()

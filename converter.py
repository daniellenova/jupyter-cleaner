import html  # Импортируем стандартный модуль для декодирования HTML-сущностей
import json  # Импортируем модуль json для работы с JSON-файлами
import os  # Импортируем модуль os для получения размеров файлов
import sys  # Импортируем модуль sys для работы с аргументами командной строки


def load_notebook(file_path):
    """
    Загружает Jupyter notebook из файла.

    Args:
        file_path (str): Путь к файлу notebook'а (.ipynb)

    Returns:
        dict: Содержимое notebook'а в виде словаря Python
    """
    # Открываем файл для чтения с указанием кодировки UTF-8
    with open(file_path, "r", encoding="utf-8") as file:
        # Парсим JSON и возвращаем результат
        return json.load(file)


def normalize_output_text(value):
    """Приводит строку или список строк результата к одной строке."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(value)
    return None


def _opening_tag_end(html_text, tag_name, start):
    """Возвращает позицию конца ожидаемого открывающего HTML-тега."""
    prefix = f"<{tag_name}"
    if not html_text.startswith(prefix, start):
        return -1

    name_end = start + len(prefix)
    if name_end >= len(html_text) or html_text[name_end] not in " \t\r\n>":
        return -1
    return html_text.find(">", name_end)


def _extract_blocks(html_text, tag_name):
    """Извлекает последовательные блоки одного типа без посторонней разметки."""
    blocks = []
    position = 0
    closing_tag = f"</{tag_name}>"

    while position < len(html_text):
        while position < len(html_text) and html_text[position].isspace():
            position += 1
        if position == len(html_text):
            break

        opening_end = _opening_tag_end(html_text, tag_name, position)
        if opening_end == -1:
            return None
        closing_start = html_text.find(closing_tag, opening_end + 1)
        if closing_start == -1:
            return None

        blocks.append(html_text[opening_end + 1:closing_start])
        position = closing_start + len(closing_tag)

    return blocks


def _extract_cells(row_html):
    """Извлекает простые ячейки th/td из одной строки таблицы."""
    cells = []
    position = 0

    while position < len(row_html):
        while position < len(row_html) and row_html[position].isspace():
            position += 1
        if position == len(row_html):
            break

        tag_name = None
        for candidate in ("th", "td"):
            if _opening_tag_end(row_html, candidate, position) != -1:
                tag_name = candidate
                break
        if tag_name is None:
            return None

        opening_end = _opening_tag_end(row_html, tag_name, position)
        opening_tag = row_html[position:opening_end + 1].lower()
        if "rowspan" in opening_tag or "colspan" in opening_tag:
            return None

        closing_tag = f"</{tag_name}>"
        closing_start = row_html.find(closing_tag, opening_end + 1)
        if closing_start == -1:
            return None
        value = row_html[opening_end + 1:closing_start]
        if "<" in value or ">" in value:
            return None

        value = html.unescape(value)
        value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        cells.append((tag_name, value.strip().replace("|", "\\|")))
        position = closing_start + len(closing_tag)

    return cells


def _has_supported_table_wrapper(prefix, suffix):
    """Проверяет необязательную обёртку div/style вокруг таблицы Pandas."""
    position = 0
    while position < len(prefix) and prefix[position].isspace():
        position += 1

    has_div = False
    div_end = _opening_tag_end(prefix, "div", position)
    if div_end != -1:
        has_div = True
        position = div_end + 1
        while position < len(prefix) and prefix[position].isspace():
            position += 1

    style_end = _opening_tag_end(prefix, "style", position)
    if style_end != -1:
        style_close = prefix.find("</style>", style_end + 1)
        if style_close == -1:
            return False
        style_content = prefix[style_end + 1:style_close]
        if "<" in style_content or ">" in style_content:
            return False
        position = style_close + len("</style>")

    if prefix[position:].strip():
        return False

    expected_suffix = "</div>" if has_div else ""
    return suffix.strip() == expected_suffix


def _parse_pandas_table(html_text):
    """Разбирает только простой формат Pandas, описанный в документации."""
    if not isinstance(html_text, str):
        return None

    table_start = html_text.find("<table")
    if table_start == -1:
        return None
    table_open_end = _opening_tag_end(html_text, "table", table_start)
    if table_open_end == -1:
        return None

    opening_tag = html_text[table_start:table_open_end + 1]
    attributes = opening_tag[len("<table"):-1].replace("'", '"')
    class_marker = 'class="'
    class_start = attributes.find(class_marker)
    while class_start > 0 and not attributes[class_start - 1].isspace():
        class_start = attributes.find(class_marker, class_start + len(class_marker))
    if class_start == -1:
        return None
    class_end = attributes.find('"', class_start + len(class_marker))
    if class_end == -1:
        return None
    classes = attributes[class_start + len(class_marker):class_end].split()
    if "dataframe" not in classes:
        return None

    table_close = html_text.find("</table>", table_open_end + 1)
    if table_close == -1:
        return None
    if not _has_supported_table_wrapper(
            html_text[:table_start],
            html_text[table_close + len("</table>"):],
    ):
        return None
    table_body = html_text[table_open_end + 1:table_close]
    if "<table" in table_body or "rowspan" in table_body.lower() or "colspan" in table_body.lower():
        return None

    sections = []
    position = 0
    for section_name in ("thead", "tbody"):
        while position < len(table_body) and table_body[position].isspace():
            position += 1
        section_open_end = _opening_tag_end(table_body, section_name, position)
        if section_open_end == -1:
            return None
        section_close_tag = f"</{section_name}>"
        section_close = table_body.find(section_close_tag, section_open_end + 1)
        if section_close == -1:
            return None
        sections.append(table_body[section_open_end + 1:section_close])
        position = section_close + len(section_close_tag)
    if table_body[position:].strip():
        return None

    header_rows = _extract_blocks(sections[0], "tr")
    data_rows = _extract_blocks(sections[1], "tr")
    if header_rows is None or len(header_rows) != 1 or not data_rows:
        return None

    parsed_rows = []
    for row_html in header_rows + data_rows:
        cells = _extract_cells(row_html)
        if not cells:
            return None
        parsed_rows.append(cells)

    column_count = len(parsed_rows[0])
    if any(len(row) != column_count for row in parsed_rows):
        return None
    if any(tag_name != "th" for tag_name, value in parsed_rows[0]):
        return None
    if any(row[0][0] != "th" or any(tag != "td" for tag, value in row[1:])
           for row in parsed_rows[1:]):
        return None

    return [[value for tag_name, value in row] for row in parsed_rows]


def is_pandas_table(html_text):
    """Проверяет, соответствует ли HTML поддерживаемой простой таблице Pandas."""
    return _parse_pandas_table(html_text) is not None


def convert_pandas_table(html_text):
    """Преобразует поддерживаемую простую HTML-таблицу Pandas в Markdown."""
    rows = _parse_pandas_table(html_text)
    if rows is None:
        return None

    markdown_rows = ["| " + " | ".join(row) + " |" for row in rows]
    separator = "|" + "---|" * len(rows[0])
    markdown_rows.insert(1, separator)
    return "\n".join(markdown_rows)


def convert_output(output, stats=None):
    """Преобразует один поддерживаемый текстовый результат в Markdown."""
    output_type = output.get("output_type")
    output_text = None

    if output_type == "stream":
        output_text = normalize_output_text(output.get("text"))

    elif output_type in ("execute_result", "display_data"):
        data = output.get("data", {})
        if isinstance(data, dict):
            html_text = normalize_output_text(data.get("text/html"))
            if html_text is not None:
                markdown_table = convert_pandas_table(html_text)
                if markdown_table is not None:
                    if stats is not None:
                        stats["tables_converted"] += 1
                    return markdown_table
            if "text/plain" in data:
                output_text = normalize_output_text(data["text/plain"])

    if output_text is None:
        return ""

    if stats is not None:
        stats["text_outputs_kept"] += 1
    closing_separator = "" if output_text.endswith("\n") else "\n"
    return f"```text\n{output_text}{closing_separator}```"


def convert_markdown_cell(cell):
    """Возвращает текст Markdown-ячейки без дополнительного оформления."""
    return "".join(cell["source"])


def convert_code_cell(cell, keep_outputs=False, stats=None):
    """Возвращает код ячейки и, при необходимости, её текстовые результаты."""
    code = "".join(cell["source"])
    converted_parts = [f"```python\n{code}\n```"]

    if keep_outputs:
        for output in cell.get("outputs", []):
            converted_output = convert_output(output, stats)
            if converted_output:
                converted_parts.append(converted_output)

    return "\n\n".join(converted_parts)


def convert_notebook(notebook, keep_outputs=False):
    """Возвращает Markdown и словарь статистики преобразования notebook'а."""
    converted_cells = []
    cells = notebook["cells"]
    stats = {
        "cells_total": len(cells),
        "code_cells": 0,
        "markdown_cells": 0,
        "empty_cells_removed": 0,
        "outputs_total": 0,
        "text_outputs_kept": 0,
        "html_outputs_skipped": 0,
        "tables_converted": 0,
    }

    for cell in cells:
        cell_type = cell["cell_type"]
        if cell_type not in ("markdown", "code"):
            continue

        if cell_type == "code":
            outputs = cell.get("outputs", [])
            stats["outputs_total"] += len(outputs)
            for output in outputs:
                data = output.get("data", {})
                if isinstance(data, dict) and "text/html" in data:
                    stats["html_outputs_skipped"] += 1

        source = "".join(cell["source"])
        if source.strip() == "":
            stats["empty_cells_removed"] += 1
            continue

        if cell_type == "markdown":
            stats["markdown_cells"] += 1
            converted_cells.append(convert_markdown_cell(cell))
        else:
            stats["code_cells"] += 1
            converted_cells.append(convert_code_cell(cell, keep_outputs, stats))

    return "\n\n".join(converted_cells), stats


def print_stats(stats):
    """Печатает понятную пользователю сводку преобразования."""
    print(f"Обработано ячеек: {stats['cells_total']}")
    print(f"Кодовых: {stats['code_cells']}")
    print(f"Текстовых: {stats['markdown_cells']}")
    print(f"Удалено пустых: {stats['empty_cells_removed']}")
    print(f"Всего результатов выполнения: {stats['outputs_total']}")
    print(f"Сохранено текстовых результатов: {stats['text_outputs_kept']}")
    print(f"HTML-представлений исключено: {stats['html_outputs_skipped']}")
    print(f"Преобразовано таблиц: {stats['tables_converted']}")


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
    stats["input_size_bytes"] = input_size
    stats["output_size_bytes"] = output_size
    stats["size_reduction_percent"] = (
        (input_size - output_size) / input_size * 100
        if input_size else 0.0
    )


def print_file_size_stats(stats):
    """Печатает размеры исходного и итогового файлов и их изменение."""
    input_size = stats["input_size_bytes"]
    output_size = stats["output_size_bytes"]
    reduction = stats["size_reduction_percent"]

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
    keep_outputs = len(sys.argv) == 3

    # Загружаем notebook из файла и сообщаем об ожидаемых ошибках ввода
    try:
        input_size = os.path.getsize(file_path)
        notebook = load_notebook(file_path)
    except FileNotFoundError:
        print(f"Ошибка: файл '{file_path}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: файл '{file_path}' содержит некорректный JSON.")
        return

    # Преобразуем notebook, определяем путь результата и сохраняем Markdown
    markdown_text, stats = convert_notebook(notebook, keep_outputs)
    output_path = get_output_path(file_path)
    save_markdown(markdown_text, output_path)
    output_size = os.path.getsize(output_path)
    add_file_size_stats(stats, input_size, output_size)

    print(f"Создан файл: {output_path}")
    print_stats(stats)
    print_file_size_stats(stats)


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если да, вызываем главную функцию
    main()

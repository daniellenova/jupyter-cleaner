import json  # Импортируем модуль json для работы с JSON-файлами
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


def has_html_output(output):
    """Возвращает True, если у результата есть HTML-представление."""
    data = output.get("data")
    return isinstance(data, dict) and "text/html" in data


def extract_text_output(output):
    """Извлекает поддерживаемое текстовое представление результата."""
    output_type = output.get("output_type")

    if output_type == "stream":
        return normalize_output_text(output.get("text"))

    if output_type in ("execute_result", "display_data"):
        data = output.get("data", {})
        if "text/plain" in data:
            return normalize_output_text(data["text/plain"])

    return None


def convert_markdown_cell(cell):
    """Возвращает текст Markdown-ячейки без дополнительного оформления."""
    return "".join(cell["source"])


def convert_code_cell(cell, keep_outputs=False):
    """Возвращает код ячейки и, при необходимости, её текстовые результаты."""
    code = "".join(cell["source"])
    converted_parts = [f"```python\n{code}\n```"]

    if keep_outputs:
        for output in cell.get("outputs", []):
            output_text = extract_text_output(output)
            if output_text is not None:
                closing_separator = "" if output_text.endswith("\n") else "\n"
                converted_parts.append(
                    f"```text\n{output_text}{closing_separator}```"
                )

    return "\n\n".join(converted_parts)


def convert_notebook(notebook, keep_outputs=False):
    """Преобразует поддерживаемые ячейки notebook'а в одну Markdown-строку."""
    converted_cells = []

    for cell in notebook["cells"]:
        if cell["cell_type"] == "markdown":
            converted_cells.append(convert_markdown_cell(cell))
        elif cell["cell_type"] == "code":
            converted_cells.append(convert_code_cell(cell, keep_outputs))

    return "\n\n".join(converted_cells)


def get_output_path(input_path):
    """Возвращает путь к Markdown-файлу вместо пути к notebook'у."""
    return input_path[:-len(".ipynb")] + ".md"


def save_markdown(markdown_text, output_path):
    """Сохраняет Markdown в файл в кодировке UTF-8."""
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown_text)


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
        notebook = load_notebook(file_path)
    except FileNotFoundError:
        print(f"Ошибка: файл '{file_path}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: файл '{file_path}' содержит некорректный JSON.")
        return

    # Преобразуем notebook, определяем путь результата и сохраняем Markdown
    markdown_text = convert_notebook(notebook, keep_outputs)
    output_path = get_output_path(file_path)
    save_markdown(markdown_text, output_path)

    print(f"Создан файл: {output_path}")


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если да, вызываем главную функцию
    main()

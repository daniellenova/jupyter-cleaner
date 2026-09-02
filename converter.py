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


def convert_markdown_cell(cell):
    """Возвращает текст Markdown-ячейки без дополнительного оформления."""
    return "".join(cell["source"])


def convert_code_cell(cell):
    """Возвращает код ячейки в виде блока Python для Markdown."""
    code = "".join(cell["source"])
    return f"```python\n{code}\n```"


def main():
    """
    Главная функция программы.
    Проверяет аргументы командной строки и выводит первую кодовую ячейку.
    """
    # Проверяем, передан ли путь к файлу в аргументах командной строки
    if len(sys.argv) < 2:
        # Если аргументов недостаточно, выводим инструкцию по использованию
        print("Usage: python converter.py <notebook.ipynb>")
        return

    # Получаем путь к файлу из первого аргумента командной строки
    file_path = sys.argv[1]

    # Загружаем notebook из файла
    notebook = load_notebook(file_path)

    # Находим первую кодовую ячейку в notebook'е
    code_cell = next(
        cell for cell in notebook["cells"] if cell["cell_type"] == "code"
    )

    # Выводим кодовую ячейку как блок Python для Markdown
    print(convert_code_cell(code_cell))


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если да, вызываем главную функцию
    main()

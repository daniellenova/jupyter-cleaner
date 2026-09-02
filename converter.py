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


def main():
    """
    Главная функция программы.
    Проверяет аргументы командной строки и выводит количество ячеек в notebook'е.
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

    # Извлекаем список ячеек из notebook'а
    cells = notebook["cells"]

    # Выводим количество ячеек в notebook'е
    print(len(cells))


# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если да, вызываем главную функцию
    main()

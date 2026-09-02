import unittest  # Импортируем модуль unittest для создания и запуска тестов

# Импортируем тестируемые функции из модуля converter
from converter import convert_code_cell, convert_notebook, load_notebook


class SourceOnlyCodeCell(dict):
    """
    Специальный класс ячейки кода для тестирования.
    Наследуется от dict, но вызывает ошибку при попытке доступа
    к любому полю, кроме "source".

    Это позволяет проверить, что функция convert_code_cell
    обращается ТОЛЬКО к полю "source" и не пытается читать
    другие данные ячейки (например, "outputs", "execution_count" и т.д.)
    """

    def __getitem__(self, key):
        """
        Переопределяем метод доступа к элементам словаря.

        Args:
            key: Ключ, к которому пытаются получить доступ

        Returns:
            Значение по ключу, если это "source"

        Raises:
            AssertionError: Если пытаются получить доступ к любому ключу,
                          кроме "source"
        """
        # Проверяем, что запрашивают именно поле "source"
        if key != "source":
            # Если это другое поле — вызываем ошибку с понятным сообщением
            raise AssertionError(f"unexpected code-cell field access: {key}")
        # Если это "source" — возвращаем значение как обычный словарь
        return super().__getitem__(key)


class ConverterOutputTests(unittest.TestCase):
    """
    Класс тестов для проверки конвертации Jupyter notebook в Markdown.
    Наследуется от unittest.TestCase для интеграции с фреймворком тестирования.
    """

    def test_code_cell_conversion_reads_only_source(self):
        """
        Тест проверяет, что функция convert_code_cell читает только поле "source"
        из ячейки кода и не обращается к другим полям.

        Создаём специальную ячейку, которая "взорвётся" (вызовет ошибку),
        если кто-то попытается прочитать любое поле, кроме "source".
        """
        # Создаём тестовую ячейку с исходным кодом
        cell = SourceOnlyCodeCell(source=["print('hello')"])

        # Проверяем, что результат конвертации соответствует ожидаемому
        # Если функция попытается прочитать другие поля — тест упадёт с ошибкой
        self.assertEqual(convert_code_cell(cell), "```python\nprint('hello')\n```")

    def test_example_outputs_are_ignored(self):
        """
        Тест проверяет, что выходные данные (outputs) ячеек игнорируются
        при конвертации notebook в Markdown.

        В тесте используются реальные примеры notebook'ов из папки examples/,
        где в outputs содержатся HTML-таблицы, div'ы и другие элементы,
        которые НЕ должны появляться в итоговом Markdown.
        """
        # Словарь с путями к тестовым notebook'ам и списками "запрещённых" строк
        expectations = {
            # В basic.ipynb не должно быть строки "Привет, Даня!\n"
            "examples/basic.ipynb": ["Привет, Даня!\n"],

            # В table.ipynb не должно быть HTML-таблиц
            "examples/table.ipynb": [
                "SHOULD_NOT_APPEAR_HTML_TABLE",  # Маркер из ячейки
                "<table>",  # HTML тег таблицы
                "<tr>",  # HTML тег строки
                "<td>",  # HTML тег ячейки
            ],

            # В html_output.ipynb не должно быть HTML-вывода
            "examples/html_output.ipynb": [
                "SHOULD_NOT_APPEAR_HTML_OUTPUT",  # Маркер из ячейки
                "<div>",  # HTML тег div
                "<h2>",  # HTML тег заголовка
                "<p>",  # HTML тег параграфа
            ],
        }

        # Проходим по всем тестовым случаям
        for notebook_path, forbidden_values in expectations.items():
            # subTest позволяет увидеть, какой именно notebook упал в тесте
            with self.subTest(notebook=notebook_path):
                # Загружаем notebook и конвертируем его в Markdown
                markdown = convert_notebook(load_notebook(notebook_path))

                # Проверяем, что ни одна из "запрещённых" строк не появилась
                for forbidden_value in forbidden_values:
                    self.assertNotIn(forbidden_value, markdown)


# Стандартная конструкция для запуска тестов при прямом вызове файла
if __name__ == "__main__":
    # Запускаем все тесты из этого файла
    unittest.main()

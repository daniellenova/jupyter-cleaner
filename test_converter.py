import unittest  # Импортируем модуль unittest для создания и запуска тестов

# Импортируем тестируемые функции из модуля converter
from converter import (
    convert_code_cell,
    convert_notebook,
    convert_output,
    convert_pandas_table,
    is_pandas_table,
    load_notebook,
)


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

        def test_converts_supported_pandas_table(self):
            """Поддерживаемая таблица превращается в Markdown без дублирования."""
            notebook = load_notebook("examples/table.ipynb")
            output = notebook["cells"][1]["outputs"][0]
            html_text = "".join(output["data"]["text/html"])

            self.assertTrue(is_pandas_table(html_text))
            self.assertEqual(
                convert_pandas_table(html_text),
                "|  | age | salary |\n"
                "|---|---|---|\n"
                "| 0 | 25 | 50000 |\n"
                "| 1 | 31 | 72000 |",
            )
            converted = convert_output(output)
            self.assertNotIn("<table", converted)
            self.assertNotIn("age  salary", converted)
            self.assertEqual(converted.count("| 0 | 25 | 50000 |"), 1)

        def test_decodes_and_normalizes_cell_text(self):
            """Сущности, переносы и Markdown-разделитель обрабатываются в ячейке."""
            html_text = """<table class="dataframe">
    <thead><tr><th></th><th>name</th></tr></thead>
    <tbody><tr><th>0</th><td> Alice &amp;
    Bob | team </td></tr></tbody>
    </table>"""

            self.assertEqual(
                convert_pandas_table(html_text),
                "|  | name |\n|---|---|\n| 0 | Alice & Bob \\| team |",
            )

        def test_unsupported_table_falls_back_to_plain_text(self):
            """Неподдерживаемая HTML-таблица не мешает сохранить text/plain."""
            output = {
                "output_type": "display_data",
                "data": {
                    "text/html": "<table><tr><td>HTML</td></tr></table>",
                    "text/plain": "safe fallback",
                },
            }

            self.assertFalse(is_pandas_table(output["data"]["text/html"]))
            self.assertEqual(convert_output(output), "```text\nsafe fallback\n```")

        def test_rejects_arbitrary_content_around_table(self):
            """Разрешённая обёртка не превращает парсер в обработчик любого HTML."""
            table = (
                '<table class="dataframe"><thead><tr><th>x</th></tr></thead>'
                '<tbody><tr><th>0</th></tr></tbody></table>'
            )

            self.assertFalse(is_pandas_table("<p>unexpected</p>" + table))
            self.assertFalse(is_pandas_table("<div>text" + table + "</div>"))
            self.assertFalse(is_pandas_table("<div>" + table + "</div><p>extra</p>"))

        def test_malformed_pandas_table_falls_back_or_is_skipped(self):
            """Повреждённая таблица не создаёт частичный Markdown."""
            malformed = (
                '<table class="dataframe"><thead><tr><th>x</th></tr></thead>'
                '<tbody><tr><th>0</th><td>extra</td></tr></tbody></table>'
            )
            with_plain = {
                "output_type": "execute_result",
                "data": {"text/html": malformed, "text/plain": "fallback"},
            }
            without_plain = {
                "output_type": "execute_result",
                "data": {"text/html": malformed},
            }

            self.assertIsNone(convert_pandas_table(malformed))
            self.assertEqual(convert_output(with_plain), "```text\nfallback\n```")
            self.assertEqual(convert_output(without_plain), "")

        def test_regular_html_is_not_a_pandas_table(self):
            """Обычный строковый результат корректно использует text/plain."""
            notebook = load_notebook("examples/html_output.ipynb")
            output = notebook["cells"][1]["outputs"][0]

            self.assertNotIn("text/html", output["data"])
            self.assertEqual(
                convert_output(output),
                "```text\n'<strong>Готово</strong>'\n```",
            )


# Стандартная конструкция для запуска тестов при прямом вызове файла
if __name__ == "__main__":
    # Запускаем все тесты из этого файла
    unittest.main()

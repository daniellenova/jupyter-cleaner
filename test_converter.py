import unittest  # Импортируем модуль unittest для создания и запуска тестов

from cells import Cell, CodeCell, MarkdownCell
# Импортируем тестируемые функции из модуля converter
from converter import (
    convert_notebook,
    convert_output,
    convert_pandas_table,
    is_pandas_table,
    load_notebook,
)
from models import ConversionResult, ConversionStats


class ConversionModelTests(unittest.TestCase):
    """Проверяет начальное состояние объектов результата и статистики."""

    def test_stats_have_zero_defaults(self):
        stats = ConversionStats()

        self.assertEqual(stats.cells_total, 0)
        self.assertEqual(stats.code_cells, 0)
        self.assertEqual(stats.markdown_cells, 0)
        self.assertEqual(stats.empty_cells_removed, 0)
        self.assertEqual(stats.outputs_total, 0)
        self.assertEqual(stats.text_outputs_kept, 0)
        self.assertEqual(stats.html_outputs_skipped, 0)
        self.assertEqual(stats.tables_converted, 0)
        self.assertEqual(stats.input_size_bytes, 0)
        self.assertEqual(stats.output_size_bytes, 0)
        self.assertEqual(stats.size_reduction_percent, 0.0)

    def test_result_owns_independent_default_stats(self):
        first = ConversionResult("first")
        second = ConversionResult("second")

        self.assertIsInstance(first.stats, ConversionStats)
        self.assertIsNot(first.stats, second.stats)


class ConverterOutputTests(unittest.TestCase):
    """
    Класс тестов для проверки конвертации Jupyter notebook в Markdown.
    Наследуется от unittest.TestCase для интеграции с фреймворком тестирования.
    """

    def test_cell_classes_convert_their_own_source(self):
        markdown = MarkdownCell("# Заголовок\n")
        code = CodeCell("print('hello')")

        self.assertIsInstance(markdown, Cell)
        self.assertIsInstance(code, Cell)
        self.assertEqual(markdown.convert(), "# Заголовок\n")
        self.assertEqual(code.convert(), "```python\nprint('hello')\n```")

    def test_cell_empty_check_is_inherited(self):
        self.assertTrue(MarkdownCell(" \n").is_empty())
        self.assertTrue(CodeCell("").is_empty())
        self.assertFalse(CodeCell("pass").is_empty())

    def test_base_cell_does_not_implement_conversion(self):
        with self.assertRaises(NotImplementedError):
            Cell("text").convert()

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
                result = convert_notebook(load_notebook(notebook_path))

                # Проверяем, что ни одна из "запрещённых" строк не появилась
                for forbidden_value in forbidden_values:
                    self.assertNotIn(forbidden_value, result.markdown_text)


class ConversionStatsTests(unittest.TestCase):
    """Проверяет значения статистики в обоих режимах преобразования."""

    def test_stats_without_outputs(self):
        notebook = load_notebook("examples/table.ipynb")

        result = convert_notebook(notebook)
        markdown = result.markdown_text
        stats = result.stats

        self.assertNotIn("| 0 | 25 | 50000 |", markdown)
        self.assertIsInstance(result, ConversionResult)
        self.assertIsInstance(stats, ConversionStats)
        self.assertEqual(stats.cells_total, len(notebook["cells"]))
        self.assertEqual(
            stats.outputs_total,
            sum(len(cell.get("outputs", [])) for cell in notebook["cells"]
                if cell["cell_type"] == "code"),
        )
        self.assertEqual(stats.text_outputs_kept, 0)
        self.assertEqual(stats.tables_converted, 0)
        self.assertEqual(stats.html_outputs_skipped, 1)

    def test_stats_with_outputs(self):
        notebook = load_notebook("examples/table.ipynb")

        result = convert_notebook(notebook, keep_outputs=True)
        markdown = result.markdown_text
        stats = result.stats

        self.assertIn("| 0 | 25 | 50000 |", markdown)
        self.assertEqual(stats.cells_total, len(notebook["cells"]))
        self.assertEqual(stats.outputs_total, 1)
        self.assertEqual(stats.text_outputs_kept, 0)
        self.assertEqual(stats.tables_converted, 1)
        self.assertEqual(stats.html_outputs_skipped, 1)

    def test_counts_empty_cells_and_plain_outputs(self):
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["heading"]},
                {"cell_type": "markdown", "source": ["  \n"]},
                {"cell_type": "code", "source": ["print(1)"], "outputs": [
                    {"output_type": "stream", "text": ["1\n"]},
                ]},
                {"cell_type": "code", "source": [], "outputs": [
                    {"output_type": "stream", "text": "not kept"},
                ]},
                {"cell_type": "raw", "source": ["ignored"]},
            ],
        }

        result = convert_notebook(notebook, keep_outputs=True)
        markdown = result.markdown_text
        stats = result.stats

        self.assertIn("```text\n1\n```", markdown)
        self.assertEqual(stats, ConversionStats(
            cells_total=5,
            code_cells=1,
            markdown_cells=1,
            empty_cells_removed=2,
            outputs_total=2,
            text_outputs_kept=1,
        ))

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

import unittest  # Импортируем модуль unittest для создания и запуска тестов
from copy import deepcopy
from dataclasses import FrozenInstanceError
from json import JSONDecodeError
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from jupyter_cleaner.cells import Cell, CodeCell, MarkdownCell
from jupyter_cleaner.cli import app
from jupyter_cleaner.config import ConversionConfig
from jupyter_cleaner.converter import (
    NotebookConverter,
    convert_notebook,
    load_notebook,
)
from jupyter_cleaner.exceptions import (
    InvalidNotebookError,
    NotebookError,
    NotebookNotFoundError,
)
from jupyter_cleaner.models import ConversionResult, ConversionStats
from jupyter_cleaner.outputs import OutputProcessor, convert_output
from jupyter_cleaner.tables import TableConverter


# Импортируем тестируемые функции из модуля converter


class NotebookLoadingTests(unittest.TestCase):
    """Проверяет преобразование ошибок ввода в исключения предметной области."""

    def test_missing_file_raises_notebook_error_with_original_cause(self):
        with self.assertRaises(NotebookNotFoundError) as context:
            load_notebook("definitely_missing.ipynb")

        self.assertIsInstance(context.exception, NotebookError)
        self.assertIsInstance(context.exception.__cause__, FileNotFoundError)

    def test_invalid_json_raises_notebook_error_with_original_cause(self):
        with TemporaryDirectory() as directory:
            notebook_path = Path(directory) / "broken.ipynb"
            notebook_path.write_text("{broken", encoding="utf-8")

            with self.assertRaises(InvalidNotebookError) as context:
                load_notebook(notebook_path)

        self.assertIsInstance(context.exception, NotebookError)
        self.assertIsInstance(context.exception.__cause__, JSONDecodeError)


class ConvertCommandTests(unittest.TestCase):
    """Проверяет основной пользовательский сценарий ``convert FILE``."""

    def setUp(self):
        self.runner = CliRunner()

    def test_convert_writes_markdown_next_to_notebook(self):
        with TemporaryDirectory() as directory:
            notebook_path = Path(directory) / "sample.ipynb"
            notebook_path.write_text(
                '{"cells": [{"cell_type": "markdown", "source": ["# Test"]}]}',
                encoding="utf-8",
            )

            result = self.runner.invoke(app, ["convert", str(notebook_path)])

            output_path = notebook_path.with_suffix(".md")
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "# Test")
            self.assertIn(f"Создан файл: {output_path}", result.stdout)
            self.assertIn("Обработано ячеек: 1", result.stdout)

    def test_convert_writes_to_explicit_output_path(self):
        with TemporaryDirectory() as directory:
            notebook_path = Path(directory) / "sample.ipynb"
            output_path = Path(directory) / "custom.md"
            notebook_path.write_text(
                '{"cells": [{"cell_type": "markdown", "source": ["# Test"]}]}',
                encoding="utf-8",
            )

            result = self.runner.invoke(
                app, ["convert", str(notebook_path), "-o", str(output_path)]
            )

            self.assertEqual(result.exit_code, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "# Test")
            self.assertFalse(notebook_path.with_suffix(".md").exists())

    def test_convert_options_control_output_and_table_conversion(self):
        notebook_path = Path("examples/table.ipynb")
        with TemporaryDirectory() as directory:
            tables_path = Path(directory) / "tables.md"
            plain_path = Path(directory) / "plain.md"

            with_tables = self.runner.invoke(
                app,
                [
                    "convert",
                    str(notebook_path),
                    "--keep-outputs",
                    "--output",
                    str(tables_path),
                ],
            )
            without_tables = self.runner.invoke(
                app,
                [
                    "convert",
                    str(notebook_path),
                    "--keep-outputs",
                    "--no-tables",
                    "-o",
                    str(plain_path),
                ],
            )

            self.assertEqual(with_tables.exit_code, 0)
            self.assertEqual(without_tables.exit_code, 0)
            self.assertIn("| 0 | 25 | 50000 |", tables_path.read_text("utf-8"))
            plain_text = plain_path.read_text("utf-8")
            self.assertNotIn("<table", plain_text)
            self.assertNotIn("| 0 | 25 | 50000 |", plain_text)
            self.assertIn("0   25   50000", plain_text)

    def test_convert_help_lists_supported_options(self):
        result = self.runner.invoke(app, ["convert", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("PATH", result.stdout)
        self.assertIn("--keep-outputs", result.stdout)
        self.assertIn("--no-tables", result.stdout)
        self.assertIn("--output", result.stdout)
        self.assertIn("-o", result.stdout)

    def test_convert_reports_missing_file_without_traceback(self):
        result = self.runner.invoke(app, ["convert", "definitely_missing.ipynb"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("не найден", result.output)
        self.assertNotIn("Traceback", result.output)

    def test_convert_reports_invalid_json_without_traceback(self):
        with TemporaryDirectory() as directory:
            notebook_path = Path(directory) / "broken.ipynb"
            notebook_path.write_text("{broken", encoding="utf-8")

            result = self.runner.invoke(app, ["convert", str(notebook_path)])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("некорректный JSON", result.output)
        self.assertNotIn("Traceback", result.output)

    def test_convert_directory_processes_sorted_top_level_notebooks(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            nested = path / "nested"
            nested.mkdir()
            for notebook_path, heading in (
                    (path / "b.ipynb", "# B"),
                    (path / "a.ipynb", "# A"),
                    (nested / "ignored.ipynb", "# Ignored"),
            ):
                notebook_path.write_text(
                    '{"cells": [{"cell_type": "markdown", "source": ['
                    f'"{heading}"]}}]}}',
                    encoding="utf-8",
                )

            result = self.runner.invoke(app, ["convert", str(path)])

            self.assertEqual(result.exit_code, 0)
            self.assertEqual((path / "a.md").read_text("utf-8"), "# A")
            self.assertEqual((path / "b.md").read_text("utf-8"), "# B")
            self.assertFalse((nested / "ignored.md").exists())
            self.assertLess(
                result.stdout.index("a.md"), result.stdout.index("b.md")
            )
            self.assertIn("Преобразовано: 2", result.stdout)
            self.assertIn("Ошибок: 0", result.stdout)
            self.assertIn("Всего: 2", result.stdout)

    def test_convert_directory_continues_after_invalid_notebook(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "broken.ipynb").write_text("{broken", encoding="utf-8")
            valid = path / "valid.ipynb"
            valid.write_text(
                '{"cells": [{"cell_type": "markdown", "source": ["ok"]}]}',
                encoding="utf-8",
            )

            result = self.runner.invoke(app, ["convert", str(path)])

            self.assertEqual(result.exit_code, 1)
            self.assertTrue(valid.with_suffix(".md").exists())
            self.assertIn("broken.ipynb", result.output)
            self.assertIn("Преобразовано: 1", result.output)
            self.assertIn("Ошибок: 1", result.output)
            self.assertIn("Всего: 2", result.output)

    def test_convert_empty_directory_fails_with_clear_message(self):
        with TemporaryDirectory() as directory:
            result = self.runner.invoke(app, ["convert", directory])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("В каталоге не найдено файлов .ipynb.", result.output)

    def test_convert_directory_rejects_output_option(self):
        with TemporaryDirectory() as directory:
            result = self.runner.invoke(
                app, ["convert", directory, "--output", "combined.md"]
            )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--output нельзя использовать", result.output)

    def test_convert_directory_applies_conversion_options_to_every_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            for name in ("first.ipynb", "second.ipynb"):
                (path / name).write_text(
                    '{"cells": [{"cell_type": "code", "source": ["print(1)"], '
                    '"outputs": [{"output_type": "stream", "text": ["1\\n"]}]}]}',
                    encoding="utf-8",
                )

            result = self.runner.invoke(
                app, ["convert", str(path), "--keep-outputs", "--no-tables"]
            )

            self.assertEqual(result.exit_code, 0)
            output_paths = list(path.glob("*.md"))
            self.assertEqual(len(output_paths), 2)
            for output_path in output_paths:
                self.assertIn("```text\n1\n```", output_path.read_text("utf-8"))


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

    def test_config_has_current_defaults_and_is_immutable(self):
        config = ConversionConfig()

        self.assertFalse(config.keep_outputs)
        self.assertTrue(config.remove_empty_cells)
        self.assertTrue(config.convert_tables)
        with self.assertRaises(FrozenInstanceError):
            config.keep_outputs = True


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

    def test_notebook_converter_owns_config_and_shared_processors(self):
        config = ConversionConfig(keep_outputs=True)
        converter = NotebookConverter(config)

        self.assertIs(converter.config, config)
        self.assertIsInstance(converter.output_processor, OutputProcessor)
        self.assertIsInstance(
            converter.output_processor.table_converter, TableConverter
        )

    def test_notebook_converter_returns_conversion_result(self):
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Heading"]},
                {"cell_type": "code", "source": ["answer = 42"], "outputs": []},
                {"cell_type": "raw", "source": ["ignored"]},
            ],
        }

        result = NotebookConverter(ConversionConfig()).convert(notebook)

        self.assertIsInstance(result, ConversionResult)
        self.assertEqual(
            result.markdown_text,
            "# Heading\n\n```python\nanswer = 42\n```",
        )
        self.assertEqual(result.stats.cells_total, 3)
        self.assertEqual(result.stats.markdown_cells, 1)
        self.assertEqual(result.stats.code_cells, 1)

    def test_conversion_does_not_mutate_notebook_or_config(self):
        """Исходные данные и неизменяемые настройки используются только для чтения."""
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Heading"]},
                {
                    "cell_type": "code",
                    "source": ["print(1)"],
                    "outputs": [
                        {"output_type": "stream", "text": ["1\n"]},
                        {
                            "output_type": "display_data",
                            "data": {"text/plain": ["fallback"]},
                        },
                    ],
                },
            ],
        }
        original_notebook = deepcopy(notebook)
        config = ConversionConfig(keep_outputs=True)

        result = NotebookConverter(config).convert(notebook)

        self.assertIn("```text\n1\n```", result.markdown_text)
        self.assertEqual(notebook, original_notebook)
        self.assertEqual(config, ConversionConfig(keep_outputs=True))

    def test_code_cell_does_not_own_hidden_statistics(self):
        """Без явного параметра статистика не создаётся ради побочного эффекта."""
        processor = OutputProcessor()
        cell = CodeCell(
            "print(1)",
            [{"output_type": "stream", "text": "1\n"}],
            processor,
        )

        self.assertEqual(
            cell.convert(ConversionConfig(keep_outputs=True)),
            "```python\nprint(1)\n```\n\n```text\n1\n```",
        )
        self.assertFalse(hasattr(cell, "stats"))

    def test_cell_empty_check_is_inherited(self):
        self.assertTrue(MarkdownCell(" \n").is_empty())
        self.assertTrue(CodeCell("").is_empty())
        self.assertFalse(CodeCell("pass").is_empty())

    def test_empty_cells_can_be_preserved_by_config(self):
        notebook = {
            "cells": [
                {"cell_type": "markdown", "source": [" "]},
                {"cell_type": "code", "source": [], "outputs": []},
            ],
        }

        result = convert_notebook(
            notebook, ConversionConfig(remove_empty_cells=False)
        )

        self.assertIn("```python\n\n```", result.markdown_text)
        self.assertEqual(result.stats.empty_cells_removed, 0)
        self.assertEqual(result.stats.markdown_cells, 1)
        self.assertEqual(result.stats.code_cells, 1)

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

        result = convert_notebook(notebook, ConversionConfig(keep_outputs=True))
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

        result = convert_notebook(notebook, ConversionConfig(keep_outputs=True))
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

        converter = TableConverter()
        self.assertTrue(converter.is_supported(html_text))
        self.assertEqual(
            converter.convert(html_text),
            "|  | age | salary |\n"
            "|---|---|---|\n"
            "| 0 | 25 | 50000 |\n"
            "| 1 | 31 | 72000 |",
        )
        converted = convert_output(output)
        self.assertNotIn("<table", converted)
        self.assertNotIn("age  salary", converted)
        self.assertEqual(converted.count("| 0 | 25 | 50000 |"), 1)

    def test_output_processor_delegates_html_table_conversion(self):
        """OutputProcessor принимает решение и делегирует обработку таблицы."""

        class RecordingTableConverter:
            def __init__(self):
                self.checked = []
                self.converted = []

            def is_supported(self, html_text):
                self.checked.append(html_text)
                return True

            def convert(self, html_text):
                self.converted.append(html_text)
                return "| delegated |\n|---|"

        converter = RecordingTableConverter()
        processor = OutputProcessor(converter)
        output = {
            "output_type": "display_data",
            "data": {"text/html": "<table>only table input</table>"},
        }
        stats = ConversionStats()

        result = processor.process([output], ConversionConfig(keep_outputs=True), stats)

        self.assertEqual(result, "| delegated |\n|---|")
        self.assertEqual(converter.checked, ["<table>only table input</table>"])
        self.assertEqual(converter.converted, ["<table>only table input</table>"])
        self.assertEqual(stats.tables_converted, 1)

    def test_decodes_and_normalizes_cell_text(self):
        """Сущности, переносы и Markdown-разделитель обрабатываются в ячейке."""
        html_text = """<table class="dataframe">
<thead><tr><th></th><th>name</th></tr></thead>
<tbody><tr><th>0</th><td> Alice &amp;
Bob | team </td></tr></tbody>
</table>"""

        self.assertEqual(
            TableConverter().convert(html_text),
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

        self.assertFalse(TableConverter().is_supported(output["data"]["text/html"]))
        self.assertEqual(convert_output(output), "```text\nsafe fallback\n```")

    def test_table_conversion_can_be_disabled_by_config(self):
        notebook = load_notebook("examples/table.ipynb")
        output = notebook["cells"][1]["outputs"][0]

        converted = convert_output(
            output, ConversionConfig(keep_outputs=True, convert_tables=False)
        )

        self.assertNotIn("| 0 | 25 | 50000 |", converted)
        self.assertIn("age  salary", converted)

    def test_rejects_arbitrary_content_around_table(self):
        """Разрешённая обёртка не превращает парсер в обработчик любого HTML."""
        table = (
            '<table class="dataframe"><thead><tr><th>x</th></tr></thead>'
            '<tbody><tr><th>0</th></tr></tbody></table>'
        )

        converter = TableConverter()
        self.assertFalse(converter.is_supported("<p>unexpected</p>" + table))
        self.assertFalse(converter.is_supported("<div>text" + table + "</div>"))
        self.assertFalse(converter.is_supported("<div>" + table + "</div><p>extra</p>"))

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

        self.assertIsNone(TableConverter().convert(malformed))
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

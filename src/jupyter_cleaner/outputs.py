"""Преобразование результатов выполнения Jupyter в Markdown."""

from collections.abc import Sequence

from .config import ConversionConfig
from .models import ConversionStats
from .tables import TableConverter
from .types import NotebookOutput


def normalize_output_text(value: object) -> str | None:
    """Приводит строку или список строк результата к одной строке."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        return "".join(value)
    return None


def extract_text_output(output: NotebookOutput) -> str | None:
    """Возвращает обычный текст поддерживаемого результата, если он есть."""
    output_type = output.get("output_type")
    if output_type == "stream":
        return normalize_output_text(output.get("text"))
    if output_type in ("execute_result", "display_data"):
        data = output.get("data", {})
        if isinstance(data, dict) and "text/plain" in data:
            return normalize_output_text(data["text/plain"])
    return None


def extract_html_output(output: NotebookOutput) -> str | None:
    """Возвращает HTML-представление поддерживаемого результата, если оно есть."""
    if output.get("output_type") not in ("execute_result", "display_data"):
        return None
    data = output.get("data", {})
    if not isinstance(data, dict):
        return None
    return normalize_output_text(data.get("text/html"))


def has_html_output(output: NotebookOutput) -> bool:
    """Проверяет наличие MIME-представления text/html."""
    data = output.get("data", {})
    return isinstance(data, dict) and "text/html" in data


def _format_text_output(output_text: str) -> str:
    closing_separator = "" if output_text.endswith("\n") else "\n"
    return f"```text\n{output_text}{closing_separator}```"


def convert_output(
        output: NotebookOutput,
        config: ConversionConfig | None = None,
        stats: ConversionStats | None = None,
        table_converter: TableConverter | None = None,
) -> str:
    """Преобразует один поддерживаемый результат выполнения в Markdown."""
    config = config if config is not None else ConversionConfig()
    html_text = extract_html_output(output)
    table_converter = table_converter or TableConverter()
    if (config.convert_tables and html_text is not None
            and table_converter.is_supported(html_text)):
        table = table_converter.convert(html_text)
        if table is not None:
            if stats is not None:
                stats.tables_converted += 1
            return table

    text = extract_text_output(output)
    if text is None:
        return ""
    if stats is not None:
        stats.text_outputs_kept += 1
    return _format_text_output(text)


class OutputProcessor:
    """Преобразует поддерживаемые результаты выполнения в Markdown."""

    def __init__(self, table_converter: TableConverter | None = None) -> None:
        self.table_converter: TableConverter = table_converter or TableConverter()

    @staticmethod
    def count_outputs(
            outputs: Sequence[NotebookOutput], stats: ConversionStats | None
    ) -> None:
        """Учитывает найденные outputs без их преобразования."""
        if stats is None:
            return
        stats.outputs_total += len(outputs)
        stats.html_outputs_skipped += sum(has_html_output(output) for output in outputs)

    def process(
            self,
            outputs: Sequence[NotebookOutput],
            config: ConversionConfig,
            stats: ConversionStats | None = None,
    ) -> str:
        """Возвращает Markdown и, если передана статистика, явно обновляет её."""
        self.count_outputs(outputs, stats)
        if not config.keep_outputs:
            return ""

        converted = [convert_output(output, config, stats, self.table_converter)
                     for output in outputs]
        return "\n\n".join(part for part in converted if part)

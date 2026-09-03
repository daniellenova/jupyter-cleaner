from .config import ConversionConfig
from .outputs import OutputProcessor


class Cell:
    """Базовое представление ячейки notebook'а."""

    def __init__(self, source):
        self.source = source

    def is_empty(self):
        """Проверяет, содержит ли ячейка значимый текст."""
        return self.source.strip() == ""

    def convert(self, *args, **kwargs):
        """Преобразует ячейку в Markdown в классах-наследниках."""
        raise NotImplementedError


class MarkdownCell(Cell):
    """Markdown-ячейка, текст которой не требует оформления."""

    def convert(self):
        return self.source


class CodeCell(Cell):
    """Кодовая ячейка, делегирующая обработку результатов OutputProcessor."""

    def __init__(self, source, outputs=None, output_processor=None):
        super().__init__(source)
        # The cell only reads output objects.  Keeping the collection immutable
        # prevents conversion code from accidentally changing the notebook's
        # original list (individual output mappings are likewise only read).
        self.outputs = tuple(outputs) if outputs is not None else ()
        self.output_processor = output_processor or OutputProcessor()

    def convert(self, config=None, stats=None):
        config = config if config is not None else ConversionConfig()
        converted_parts = [f"```python\n{self.source}\n```"]

        converted_outputs = self.output_processor.process(self.outputs, config, stats)
        if converted_outputs:
            converted_parts.append(converted_outputs)

        return "\n\n".join(converted_parts)

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
    """Кодовая ячейка и связанные с ней результаты выполнения."""

    def __init__(self, source, outputs=None):
        super().__init__(source)
        self.outputs = outputs if outputs is not None else []

    def convert(self, keep_outputs=False, stats=None):
        converted_parts = [f"```python\n{self.source}\n```"]

        if keep_outputs:
            # Обработка результатов пока остаётся ответственностью converter.py.
            from converter import convert_output

            for output in self.outputs:
                converted_output = convert_output(output, stats)
                if converted_output:
                    converted_parts.append(converted_output)

        return "\n\n".join(converted_parts)

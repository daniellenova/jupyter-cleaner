from collections.abc import Sequence

import pytest

from jupyter_cleaner.cells import Cell, CodeCell, MarkdownCell
from jupyter_cleaner.config import ConversionConfig
from jupyter_cleaner.models import ConversionStats
from jupyter_cleaner.types import NotebookOutput


@pytest.mark.parametrize("source", ["", "   \t", "\n\r\n"])
def test_cell_is_empty_for_whitespace(source: str) -> None:
    assert Cell(source).is_empty()


def test_cell_is_not_empty_for_text() -> None:
    assert not Cell("meaningful text").is_empty()


def test_markdown_cell_preserves_source() -> None:
    source = "# Heading\n\n*emphasis*  \n"

    assert MarkdownCell(source).convert() == source


def test_code_cell_uses_python_fence_boundaries() -> None:
    converted = CodeCell("answer = 42").convert()

    assert converted.startswith("```python\n")
    assert converted.endswith("\n```")


def test_code_cell_preserves_source_inside_fence() -> None:
    source = "for number in range(2):\n    print(number)"

    assert CodeCell(source).convert() == f"```python\n{source}\n```"


def test_code_cell_without_outputs_only_returns_code() -> None:
    assert CodeCell("pass").convert() == "```python\npass\n```"


def test_code_cell_uses_output_processor() -> None:
    class StubOutputProcessor:
        def process(
            self,
            outputs: Sequence[NotebookOutput],
            config: ConversionConfig,
            stats: ConversionStats | None = None,
        ) -> str:
            assert outputs == ({"output_type": "stream", "text": "result"},)
            assert config.keep_outputs
            return "processed result"

    output: NotebookOutput = {"output_type": "stream", "text": "result"}
    cell = CodeCell("print('result')", [output], StubOutputProcessor())  # type: ignore[arg-type]

    converted = cell.convert(ConversionConfig(keep_outputs=True))

    assert converted.endswith("\n\nprocessed result")

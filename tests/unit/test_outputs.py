from jupyter_cleaner.config import ConversionConfig
from jupyter_cleaner.models import ConversionStats
from jupyter_cleaner.outputs import OutputProcessor, convert_output
from jupyter_cleaner.types import NotebookOutput

PANDAS_TABLE = """
<table class="dataframe">
  <thead><tr><th></th><th>name</th></tr></thead>
  <tbody><tr><th>0</th><td>Ada</td></tr></tbody>
</table>
"""


def keep_outputs_config() -> ConversionConfig:
    return ConversionConfig(keep_outputs=True)


def test_stream_text_is_preserved() -> None:
    output: NotebookOutput = {"output_type": "stream", "text": "hello\n"}

    assert convert_output(output) == "```text\nhello\n```"


def test_execute_result_plain_text_is_preserved() -> None:
    output: NotebookOutput = {
        "output_type": "execute_result",
        "data": {"text/plain": "42"},
    }

    assert convert_output(output) == "```text\n42\n```"


def test_display_data_plain_text_is_preserved() -> None:
    output: NotebookOutput = {
        "output_type": "display_data",
        "data": {"text/plain": ["first", " line"]},
    }

    assert convert_output(output) == "```text\nfirst line\n```"


def test_unsupported_html_without_text_is_skipped() -> None:
    output: NotebookOutput = {
        "output_type": "display_data",
        "data": {"text/html": "<strong>hello</strong>"},
    }

    assert convert_output(output) == ""


def test_plain_text_is_used_when_html_is_unsupported() -> None:
    output: NotebookOutput = {
        "output_type": "display_data",
        "data": {"text/plain": "hello", "text/html": "<strong>hello</strong>"},
    }

    assert convert_output(output) == "```text\nhello\n```"


def test_supported_table_replaces_duplicate_plain_text() -> None:
    output: NotebookOutput = {
        "output_type": "execute_result",
        "data": {"text/plain": "  name\n0 Ada", "text/html": PANDAS_TABLE},
    }

    converted = convert_output(output)

    assert converted == "|  | name |\n|---|---|\n| 0 | Ada |"


def test_unknown_output_type_is_ignored() -> None:
    output: NotebookOutput = {"output_type": "future_output", "text": "noise"}

    assert convert_output(output) == ""


def test_statistics_count_outputs_seen() -> None:
    stats = ConversionStats()
    outputs: list[NotebookOutput] = [
        {"output_type": "stream", "text": "one"},
        {"output_type": "stream", "text": "two"},
    ]

    OutputProcessor().process(outputs, keep_outputs_config(), stats)

    assert stats.outputs_total == 2


def test_statistics_count_text_output_kept() -> None:
    stats = ConversionStats()
    output: NotebookOutput = {"output_type": "stream", "text": "hello"}

    OutputProcessor().process([output], keep_outputs_config(), stats)

    assert stats.text_outputs_kept == 1


def test_statistics_count_html_output_skipped() -> None:
    stats = ConversionStats()
    output: NotebookOutput = {
        "output_type": "display_data",
        "data": {"text/html": "<strong>hello</strong>"},
    }

    OutputProcessor().process([output], keep_outputs_config(), stats)

    assert stats.html_outputs_skipped == 1


def test_statistics_count_table_converted() -> None:
    stats = ConversionStats()
    output: NotebookOutput = {
        "output_type": "display_data",
        "data": {"text/html": PANDAS_TABLE},
    }

    OutputProcessor().process([output], keep_outputs_config(), stats)

    assert stats.tables_converted == 1

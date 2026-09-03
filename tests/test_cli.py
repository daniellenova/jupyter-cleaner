"""Проверки пользовательского интерфейса командной строки."""

import re
from pathlib import Path
from shutil import copyfile

from typer.testing import CliRunner

from jupyter_cleaner.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def copy_fixture(name: str, destination: Path) -> Path:
    """Копирует notebook в изолированный временный каталог."""
    return Path(copyfile(FIXTURES / name, destination / name))


def test_help_lists_convert_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "convert" in result.output


def test_convert_help_lists_supported_options() -> None:
    result = runner.invoke(app, ["convert", "--help"])
    output = ANSI_ESCAPE.sub("", result.output)

    assert result.exit_code == 0
    assert "--keep-outputs" in output
    assert "--no-tables" in output
    assert "--output" in output


def test_convert_file_creates_expected_markdown(tmp_path: Path) -> None:
    notebook = copy_fixture("simple.ipynb", tmp_path)

    result = runner.invoke(app, ["convert", str(notebook)])

    output = tmp_path / "simple.md"
    assert result.exit_code == 0
    assert output.exists()
    assert output.read_text(encoding="utf-8") == (
        "# Simple notebookA small fixture for tests.\n\n"
        '```python\nmessage = "hello"\nprint(message)\n```'
    )


def test_keep_outputs_includes_execution_result(tmp_path: Path) -> None:
    notebook = copy_fixture("simple.ipynb", tmp_path)

    result = runner.invoke(app, ["convert", str(notebook), "--keep-outputs"])

    assert result.exit_code == 0
    markdown = notebook.with_suffix(".md").read_text(encoding="utf-8")
    assert "```text\nhello\n```" in markdown


def test_no_tables_uses_plain_text_fallback(tmp_path: Path) -> None:
    notebook = copy_fixture("dataframe.ipynb", tmp_path)

    result = runner.invoke(
        app,
        ["convert", str(notebook), "--keep-outputs", "--no-tables"],
    )

    assert result.exit_code == 0
    markdown = notebook.with_suffix(".md").read_text(encoding="utf-8")
    assert "```text\n  name  score\n0  Ada     10\n1  Lin     20\n```" in markdown
    assert "|  | name | score |" not in markdown


def test_missing_file_reports_clear_error_without_traceback(tmp_path: Path) -> None:
    missing = tmp_path / "missing.ipynb"

    result = runner.invoke(app, ["convert", str(missing)])

    assert result.exit_code != 0
    assert f"Ошибка: файл '{missing}' не найден." in result.output
    assert "Traceback" not in result.output


def test_convert_directory_creates_markdown_for_each_notebook(tmp_path: Path) -> None:
    input_directory = tmp_path / "notebooks"
    input_directory.mkdir()
    copy_fixture("simple.ipynb", input_directory)
    copy_fixture("text_outputs.ipynb", input_directory)

    result = runner.invoke(app, ["convert", str(input_directory)])

    assert result.exit_code == 0
    assert (input_directory / "simple.md").exists()
    assert (input_directory / "text_outputs.md").exists()
    assert "Преобразовано: 2" in result.output
    assert "Ошибок: 0" in result.output

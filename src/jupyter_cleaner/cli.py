"""Командный интерфейс конвертера Jupyter notebook."""

from pathlib import Path
from typing import Annotated

import typer

from .config import ConversionConfig
from .converter import NotebookConverter, load_notebook
from .exceptions import InvalidNotebookError, NotebookNotFoundError
from .models import ConversionStats

app = typer.Typer(
    name="jupyter-cleaner",
    help="Преобразует Jupyter notebook в чистый и компактный Markdown.",
    add_completion=False,
)


@app.callback()
def main() -> None:
    """Команды для преобразования Jupyter notebook."""


def format_file_size(size_bytes: int) -> str:
    """Возвращает размер файла в удобочитаемом виде."""
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    size_kilobytes = size_bytes / 1024
    if size_kilobytes < 1024:
        value = f"{size_kilobytes:.1f}".rstrip("0").rstrip(".")
        return f"{value} КБ"
    value = f"{size_kilobytes / 1024:.1f}".rstrip("0").rstrip(".")
    return f"{value} МБ"


def add_file_size_stats(
        stats: ConversionStats, input_size: int, output_size: int
) -> None:
    """Добавляет размеры файлов в статистику запуска."""
    stats.input_size_bytes = input_size
    stats.output_size_bytes = output_size
    stats.size_reduction_percent = (
        (input_size - output_size) / input_size * 100 if input_size else 0.0
    )


def print_stats(stats: ConversionStats) -> None:
    """Печатает сводку преобразования."""
    typer.echo(f"Обработано ячеек: {stats.cells_total}")
    typer.echo(f"Кодовых: {stats.code_cells}")
    typer.echo(f"Текстовых: {stats.markdown_cells}")
    typer.echo(f"Удалено пустых: {stats.empty_cells_removed}")
    typer.echo(f"Всего результатов выполнения: {stats.outputs_total}")
    typer.echo(f"Сохранено текстовых результатов: {stats.text_outputs_kept}")
    typer.echo(f"HTML-представлений исключено: {stats.html_outputs_skipped}")
    typer.echo(f"Преобразовано таблиц: {stats.tables_converted}")


def print_file_size_stats(stats: ConversionStats) -> None:
    """Печатает размеры файлов и их изменение."""
    typer.echo("Размер:")
    typer.echo(
        f"{format_file_size(stats.input_size_bytes)} → "
        f"{format_file_size(stats.output_size_bytes)}"
    )
    if stats.size_reduction_percent >= 0:
        typer.echo(f"Уменьшение: {stats.size_reduction_percent:.1f} %")
    else:
        typer.echo(f"Изменение размера: {-stats.size_reduction_percent:+.1f} %")


@app.command()
def convert(
        file: Annotated[
            Path,
            typer.Argument(
                help="Путь к исходному notebook (.ipynb).",
                metavar="FILE",
                exists=False,
                dir_okay=False,
            ),
        ],
        keep_outputs: Annotated[
            bool,
            typer.Option(
                "--keep-outputs",
                help="Сохранять поддерживаемые результаты выполнения.",
            ),
        ] = False,
        no_tables: Annotated[
            bool,
            typer.Option(
                "--no-tables",
                help="Не преобразовывать HTML-таблицы в Markdown.",
            ),
        ] = False,
        output: Annotated[
            Path | None,
            typer.Option(
                "--output",
                "-o",
                help="Путь к выходному Markdown-файлу.",
                dir_okay=False,
            ),
        ] = None,
) -> None:
    """Преобразует один notebook в Markdown-файл."""
    try:
        notebook = load_notebook(file)
    except NotebookNotFoundError:
        typer.echo(f"Ошибка: файл '{file}' не найден.", err=True)
        raise typer.Exit(code=1) from None
    except InvalidNotebookError:
        typer.echo(
            f"Ошибка: файл '{file}' содержит некорректный JSON.",
            err=True,
        )
        raise typer.Exit(code=1) from None

    input_size = file.stat().st_size
    config = ConversionConfig(
        keep_outputs=keep_outputs,
        convert_tables=not no_tables,
    )
    result = NotebookConverter(config).convert(notebook)
    output_path = output if output is not None else file.with_suffix(".md")
    output_path.write_text(result.markdown_text, encoding="utf-8")
    add_file_size_stats(result.stats, input_size, output_path.stat().st_size)

    typer.echo(f"Создан файл: {output_path}")
    print_stats(result.stats)
    print_file_size_stats(result.stats)

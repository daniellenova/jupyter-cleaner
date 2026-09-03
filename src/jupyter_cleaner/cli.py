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


def add_file_size_stats(stats: ConversionStats, input_size: int, output_size: int) -> None:
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
        f"{format_file_size(stats.input_size_bytes)} → {format_file_size(stats.output_size_bytes)}"
    )
    if stats.size_reduction_percent >= 0:
        typer.echo(f"Уменьшение: {stats.size_reduction_percent:.1f} %")
    else:
        typer.echo(f"Изменение размера: {-stats.size_reduction_percent:+.1f} %")


def convert_file(file: Path, config: ConversionConfig, output: Path | None = None) -> None:
    """Преобразует один notebook и печатает его статистику."""
    notebook = load_notebook(file)
    input_size = file.stat().st_size
    result = NotebookConverter(config).convert(notebook)
    output_path = output if output is not None else file.with_suffix(".md")
    output_path.write_text(result.markdown_text, encoding="utf-8")
    add_file_size_stats(result.stats, input_size, output_path.stat().st_size)

    typer.echo(f"Создан файл: {output_path}")
    print_stats(result.stats)
    print_file_size_stats(result.stats)


@app.command()
def convert(
    path: Annotated[
        Path,
        typer.Argument(
            help="Путь к исходному notebook (.ipynb) или каталогу.",
            metavar="PATH",
            exists=False,
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
    """Преобразует notebook или все notebook-файлы в каталоге."""
    config = ConversionConfig(
        keep_outputs=keep_outputs,
        convert_tables=not no_tables,
    )

    if path.is_dir():
        if output is not None:
            typer.echo(
                "Ошибка: --output нельзя использовать при обработке каталога.",
                err=True,
            )
            raise typer.Exit(code=1)

        notebook_paths = sorted(path.glob("*.ipynb"), key=lambda item: item.name)
        if not notebook_paths:
            typer.echo("В каталоге не найдено файлов .ipynb.", err=True)
            raise typer.Exit(code=1)

        succeeded = 0
        failed = 0
        for notebook_path in notebook_paths:
            try:
                convert_file(notebook_path, config)
            except InvalidNotebookError:
                typer.echo(
                    f"Ошибка: файл '{notebook_path}' содержит некорректный JSON.",
                    err=True,
                )
                failed += 1
            except (KeyError, TypeError, OSError) as error:
                typer.echo(
                    f"Ошибка при обработке '{notebook_path}': {error}",
                    err=True,
                )
                failed += 1
            else:
                succeeded += 1

        typer.echo(f"Преобразовано: {succeeded}")
        typer.echo(f"Ошибок: {failed}")
        typer.echo(f"Всего: {len(notebook_paths)}")
        if failed:
            raise typer.Exit(code=1)
        return

    try:
        convert_file(path, config, output)
    except NotebookNotFoundError:
        typer.echo(f"Ошибка: файл '{path}' не найден.", err=True)
        raise typer.Exit(code=1) from None
    except InvalidNotebookError:
        typer.echo(
            f"Ошибка: файл '{path}' содержит некорректный JSON.",
            err=True,
        )
        raise typer.Exit(code=1) from None
